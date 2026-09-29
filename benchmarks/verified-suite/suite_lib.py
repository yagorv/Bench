"""Utilidades comunes. SOLO biblioteca estándar de Python (>= 3.10)."""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def rng(seed: int, salt: str = "") -> random.Random:
    """RNG determinista e independiente por (semilla, salt). random.Random(str) usa SHA-512: estable entre plataformas."""
    return random.Random(f"{seed}:{salt}")


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fingerprint(root: Path) -> dict[str, str]:
    out = {}
    root = Path(root)
    for p in sorted(root.rglob("*")):
        if p.is_file():
            out[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


class Report:
    """Comprobaciones con peso; cada valor va de 0.0 a 1.0."""

    def __init__(self) -> None:
        self.checks: list[dict] = []

    def add(self, name: str, value, weight: float = 1.0, detail: str = "") -> None:
        v = 1.0 if value is True else 0.0 if value is False else max(0.0, min(1.0, float(value)))
        self.checks.append({"name": name, "value": round(v, 6), "weight": weight, "detail": detail})

    def result(self) -> dict:
        total = sum(c["weight"] for c in self.checks)
        score = sum(c["value"] * c["weight"] for c in self.checks) / total if total else 0.0
        return {"score": round(score, 6), "passed": bool(self.checks) and all(c["value"] >= 0.999999 for c in self.checks),
                "checks": self.checks}


def fail_report(reason: str) -> dict:
    r = Report()
    r.add("entrega", False, 1.0, reason)
    return r.result()


def extract_code_block(text: str) -> str | None:
    """Devuelve el bloque ``` más largo de una respuesta de chat, o None si no hay bloques."""
    blocks = re.findall(r"```[^\n`]*\n(.*?)```", text, flags=re.S)
    return max(blocks, key=len) if blocks else None


# --------------------------------------------------------------------------- ejecución aislada de código entregado
_HARNESS = r'''
import sys, json, importlib.util, signal, os
sol_path, cases_path, out_path, per_case, mem_mb = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), int(sys.argv[5])
try:
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (mem_mb * 1024 * 1024, mem_mb * 1024 * 1024))
except Exception:
    pass
class _T(BaseException):
    pass
def _h(sig, frm):
    raise _T()
signal.signal(signal.SIGALRM, _h)
out = open(out_path, "a", encoding="utf-8")
def emit(o):
    out.write(json.dumps(o) + "\n"); out.flush()
real_stdout = sys.stdout
sys.stdout = open(os.devnull, "w")
try:
    spec = importlib.util.spec_from_file_location("solution", sol_path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.dirname(sol_path))
    spec.loader.exec_module(mod)
except BaseException as e:
    emit({"import_error": f"{type(e).__name__}: {e}"[:300]})
    sys.exit(0)
for case in json.load(open(cases_path, encoding="utf-8")):
    try:
        signal.setitimer(signal.ITIMER_REAL, per_case)
        try:
            val = getattr(mod, case["fn"])(*case["args"])
            res = {"id": case["id"], "ok": True, "value": val}
        except _T:
            res = {"id": case["id"], "ok": False, "err": "timeout"}
            signal.setitimer(signal.ITIMER_REAL, 0)
            emit(res)
            out.close()
            os._exit(0)  # un hilo colgado contaminaría los casos siguientes: el padre relanza un proceso limpio
        except BaseException as e:
            res = {"id": case["id"], "ok": False, "err": f"{type(e).__name__}: {e}"[:200]}
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
        try:
            json.dumps(res)
        except Exception:
            res = {"id": case["id"], "ok": False, "err": "resultado no serializable a JSON"}
        emit(res)
    except _T:
        pass
out.flush()
os._exit(0)
'''


def run_cases(solution: Path, chunks: list[list[dict]], per_case: float = 10.0, chunk_timeout: float = 120.0,
              mem_mb: int = 2048) -> tuple[dict[str, dict], str | None]:
    """Ejecuta casos {id, fn, args} contra `solution` en subprocesos aislados (un subproceso por chunk).

    Devuelve ({id: resultado}, error_de_import|None). Un fallo duro (segfault, timeout de chunk) solo pierde ese chunk.
    """
    results: dict[str, dict] = {}
    import_error = None
    with tempfile.TemporaryDirectory(prefix="bench_run_") as tmp:
        tmp = Path(tmp)
        (tmp / "harness.py").write_text(_HARNESS, encoding="utf-8")
        sol_copy = tmp / "solution_dir"
        sol_copy.mkdir()
        (sol_copy / "solution.py").write_text(Path(solution).read_text(encoding="utf-8"), encoding="utf-8")
        env = {"PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1", "PATH": os.environ.get("PATH", ""),
               "LANG": "C.UTF-8", "PYTHONIOENCODING": "utf-8"}
        for i, chunk in enumerate(chunks):
            remaining = list(chunk)
            launches = 0
            while remaining and launches <= len(chunk) + 1 and not import_error:
                launches += 1
                cfile, ofile = tmp / f"cases_{i}_{launches}.json", tmp / f"out_{i}_{launches}.jsonl"
                cfile.write_text(json.dumps(remaining), encoding="utf-8")
                try:
                    subprocess.run([sys.executable, "-I", str(tmp / "harness.py"), str(sol_copy / "solution.py"), str(cfile),
                                    str(ofile), str(per_case), str(mem_mb)], cwd=tmp, env=env, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=chunk_timeout)
                except subprocess.TimeoutExpired:
                    pass
                if ofile.exists():
                    for line in ofile.read_text(encoding="utf-8").splitlines():
                        try:
                            o = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if "import_error" in o:
                            import_error = o["import_error"]
                        else:
                            results[o["id"]] = o
                pending = [c for c in remaining if c["id"] not in results]
                if len(pending) == len(remaining) and pending and not import_error:
                    # sin progreso: el primer caso pendiente mató o colgó el proceso; se da por fallido y se sigue con el resto
                    results[pending[0]["id"]] = {"id": pending[0]["id"], "ok": False, "err": "el proceso murió o se colgó"}
                    pending = pending[1:]
                remaining = pending
    return results, import_error
