#!/usr/bin/env python3
"""CLI de la suite. SOLO biblioteca estándar.

  list | generate | evaluate | reference | demo | run | report | selftest
Flujo manual (cualquier herramienta): generate -> pegar PROMPT_CHAT.txt -> guardar la respuesta -> evaluate --response -> record.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from suite_lib import extract_code_block, fail_report, fingerprint  # noqa: E402

INLINE_LIMIT = 300_000  # bytes de datos que se incrustan en PROMPT_CHAT_INLINE.txt


def load_tasks() -> dict:
    tasks = {}
    for d in sorted((ROOT / "tasks").glob("t[0-9][0-9]_*")):
        spec = importlib.util.spec_from_file_location(f"{d.name}.task", d / "task.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.DIR = d
        tasks[d.name] = mod
    return tasks


def resolve(tasks: dict, key: str):
    m = [k for k in tasks if k == key or k.split("_", 1)[0] == key or k.startswith(key)]
    if len(m) != 1:
        sys.exit(f"Tarea '{key}' no encontrada o ambigua. Disponibles: {', '.join(tasks)}")
    return tasks[m[0]]


AGENT_PROMPT = """You are working in the current directory. Read `TASK.md`: it contains the complete specification of the task. The data files it mentions are in this directory.
Write the deliverable(s) ({names}) inside the `answer/` subdirectory, with exactly those names (keep any sub-directory shown). Do not modify anything outside `answer/`.
There is no internet access and nobody to ask: interpret what the specification says. When you finish, reply with a single line summarizing what you delivered.
"""

CHAT_PROMPT = """I am giving you a complete, self-contained task. I cannot answer questions: follow the specification to the letter.
Reply with the COMPLETE content of every deliverable, each one in its own Markdown code block (```), preceded by a line containing only the file name/path. Add no explanations.
Deliverable(s): {names}
{attach}
===== TASK.md =====
{task}
"""


def data_files(task, tool: Path) -> list[Path]:
    skip = set(getattr(task, "INLINED_IN_TASK", set()))
    return [p for p in sorted(tool.rglob("*")) if p.is_file() and p.name != "TASK.md" and not p.name.startswith("PROMPT_")
            and "answer" not in p.relative_to(tool).parts and "examples" not in p.relative_to(tool).parts
            and str(p.relative_to(tool)) not in skip]


def write_prompts(task, tool: Path) -> None:
    names = ", ".join(f"`{n}`" for n in task.DELIVERABLES)
    body = (tool / "TASK.md").read_text(encoding="utf-8")
    (tool / "PROMPT_AGENT.txt").write_text(AGENT_PROMPT.format(names=names), encoding="utf-8")
    files = data_files(task, tool)
    if files:
        listing = "\n".join(f"- `{p.relative_to(tool)}` ({p.stat().st_size:,} bytes)" for p in files)
        attach = f"This task uses the following data files, which I **attach**:\n{listing}\n"
    else:
        attach = "This task uses no attached files: everything is in the text.\n"
    (tool / "PROMPT_CHAT.txt").write_text(CHAT_PROMPT.format(names=names, attach=attach, task=body), encoding="utf-8")
    total = sum(p.stat().st_size for p in files)
    if files and total <= INLINE_LIMIT:
        inl = CHAT_PROMPT.format(names=names, attach="The data files are embedded at the end of this message.\n", task=body)
        for p in files:
            inl += f"\n===== FILE: {p.relative_to(tool)} =====\n{p.read_text(encoding='utf-8', errors='replace')}\n"
        (tool / "PROMPT_CHAT_INLINE.txt").write_text(inl, encoding="utf-8")


def prepare(task, run_dir: Path, seed: int, level: int) -> tuple[Path, Path]:
    """Crea run_dir/for_tool (lo único que ve la herramienta) y run_dir/hidden (solo evaluador)."""
    if run_dir.exists():
        shutil.rmtree(run_dir)
    tool, hidden = run_dir / "for_tool", run_dir / "hidden"
    (tool / "answer").mkdir(parents=True)
    hidden.mkdir()
    task.generate(tool, hidden, seed, level)
    write_prompts(task, tool)
    return tool, hidden


def safe_evaluate(task, answer: Path, hidden: Path) -> dict:
    try:
        return task.evaluate(answer, hidden)
    except Exception as e:  # noqa: BLE001
        return fail_report(f"error al evaluar la entrega: {type(e).__name__}: {e}")


FENCE = re.compile(r"^(?P<f>`{3,}|~{3,})[^\n]*\n(?P<body>.*?)^(?P=f)[ \t]*$", re.M | re.S)


def code_blocks(text: str) -> list[tuple[str, str]]:
    """[(línea previa al bloque, contenido)] de cada bloque de código de una respuesta de chat."""
    out = []
    for m in FENCE.finditer(text):
        before = text[:m.start()].rstrip().splitlines()
        label = re.sub(r"^[`*#>\s-]+|[`*#:\s]+$", "", before[-1]) if before else ""
        out.append((label, m.group("body")))
    return out


def ingest_response(task, run_dir: Path, response: Path) -> None:
    """Guarda en answer/ los entregables a partir de una respuesta de chat (bloques de código precedidos por el nombre del fichero)."""
    ans = run_dir / "for_tool" / "answer"
    ans.mkdir(parents=True, exist_ok=True)
    text = response.read_text(encoding="utf-8")
    if len(task.DELIVERABLES) == 1:
        block = extract_code_block(text)
        (ans / task.DELIVERABLES[0]).write_text(block if block is not None else text, encoding="utf-8")
        return
    blocks = code_blocks(text)
    missing = []
    for d in task.DELIVERABLES:
        hit = next((body for label, body in blocks if label.endswith(d) or label.endswith(Path(d).name)), None)
        if hit is None:
            missing.append(d)
            continue
        (ans / d).parent.mkdir(parents=True, exist_ok=True)
        (ans / d).write_text(hit, encoding="utf-8")
    if missing:
        print(f"AVISO: no encontré en la respuesta estos entregables: {', '.join(missing)}")


# ------------------------------------------------------------------ comandos
def cmd_list(tasks, a):
    for k, t in tasks.items():
        print(f"{k:26s} niveles={t.LEVELS}  entregable={','.join(t.DELIVERABLES)}  {t.TITLE}")


def cmd_generate(tasks, a):
    t = resolve(tasks, a.task)
    tool, hidden = prepare(t, Path(a.out), a.seed, a.level)
    (Path(a.out) / "meta.json").write_text(json.dumps({"level": a.level, "seed": a.seed}))
    print(f"Listo.\n  Para la herramienta: {tool}\n    - PROMPT_AGENT.txt: para agentes (Claude Code, Codex CLI, Cursor agent...)\n"
          f"    - PROMPT_CHAT.txt / PROMPT_CHAT_INLINE.txt: para chats (ChatGPT, Gemini, Claude.ai...)\n  Oculto (NO compartir): {hidden}")


def cmd_evaluate(tasks, a):
    t = resolve(tasks, a.task)
    d = Path(a.dir)
    if a.response:
        ingest_response(t, d, Path(a.response))
    res = safe_evaluate(t, d / "for_tool" / "answer", d / "hidden")
    print(json.dumps(res, ensure_ascii=False, indent=1) if a.verbose else
          f"score={res['score']:.4f} passed={res['passed']}\n" + "\n".join(
              f"  {'✓' if c['value'] >= 0.999999 else '✗'} {c['name']}: {c['value']:.3f} {c['detail']}" for c in res["checks"]))
    if a.tool:
        _record(t, d, res, a)


def cmd_reference(tasks, a):
    t = resolve(tasks, a.task)
    d = Path(a.dir)
    t.reference(d / "for_tool", d / "hidden", d / "for_tool" / "answer")
    print(f"Solución de referencia escrita en {d / 'for_tool' / 'answer'} (para demostrar el flujo; evalúala con 'evaluate').")


def cmd_demo(tasks, a):
    """Recorre todas las tareas: genera, evalúa una entrega vacía (debe dar ~0), escribe la referencia y evalúa (debe dar 1.0)."""
    base = Path(a.out)
    print(f"{'tarea':26s} {'vacía':>7s} {'referencia':>11s} {'seg':>6s}  directorio")
    for k, t in tasks.items():
        if a.task and a.task not in k:
            continue
        t0 = time.time()
        d = base / k
        tool, hidden = prepare(t, d, a.seed, a.level if a.level in t.LEVELS else t.LEVELS[0])
        empty = safe_evaluate(t, tool / "answer", hidden)["score"]
        t.reference(tool, hidden, tool / "answer")
        ref = safe_evaluate(t, tool / "answer", hidden)["score"]
        for p in (tool / "answer").rglob("__pycache__"):
            shutil.rmtree(p, ignore_errors=True)
        shutil.rmtree(tool / "answer")
        (tool / "answer").mkdir()
        print(f"{k:26s} {empty:7.3f} {ref:11.3f} {time.time() - t0:6.1f}  {d}")
    print("\nCada directorio contiene for_tool/ (lo que ve la herramienta: TASK.md + PROMPT_*.txt) y hidden/ (solo evaluador).")


def _record(t, d: Path, res: dict, a, wall=None, rc=None, source="manual"):
    meta = json.loads((d / "meta.json").read_text()) if (d / "meta.json").exists() else {}
    rec = {
        "task": t.DIR.name, "level": meta.get("level"), "seed": meta.get("seed"), "tool": a.tool,
        "score": res["score"], "passed": res["passed"],
        "measured": {"wall_seconds": wall if wall is not None else (a.minutes * 60 if getattr(a, "minutes", None) else None),
                     "cost_usd": getattr(a, "cost_usd", None), "input_tokens": getattr(a, "input_tokens", None),
                     "output_tokens": getattr(a, "output_tokens", None), "source": source},
        "notes": getattr(a, "notes", None), "return_code": rc,
        "failed_checks": [c["name"] for c in res["checks"] if c["value"] < 0.999999],
    }
    with open(a.results, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"→ registrado en {a.results}")


def cmd_run(tasks, a):
    t = resolve(tasks, a.task)
    for rep in range(1, a.repeat + 1):
        d = Path(a.workdir).resolve() / f"{t.DIR.name}_L{a.level}_s{a.seed}_{a.tool}_r{rep}"
        tool, hidden = prepare(t, d, a.seed, a.level)
        (d / "meta.json").write_text(json.dumps({"level": a.level, "seed": a.seed}))
        cmd = a.cmd.replace("{tool_dir}", str(tool)).replace("{prompt_file}", str(tool / "PROMPT_AGENT.txt"))
        print(f"→ {a.tool} · {t.DIR.name} L{a.level} seed={a.seed} rep={rep}\n  $ {cmd}")
        before = {k: v for k, v in fingerprint(tool).items() if not k.startswith("answer/")}
        t0 = time.perf_counter()
        try:
            p = subprocess.run(cmd, shell=True, cwd=tool, capture_output=True, text=True, timeout=a.timeout)
            rc, out, err = p.returncode, p.stdout, p.stderr
        except subprocess.TimeoutExpired:
            rc, out, err = -1, "", "TIMEOUT"
        wall = time.perf_counter() - t0
        (d / "stdout.txt").write_text(out or "", encoding="utf-8")
        (d / "stderr.txt").write_text(err or "", encoding="utf-8")
        res = safe_evaluate(t, tool / "answer", hidden)
        after = {k: v for k, v in fingerprint(tool).items() if not k.startswith("answer/")}
        if after != before:  # anti-trampas: fuera de answer/ es solo lectura
            res = {**res, "score": 0.0, "passed": False, "checks": res["checks"] + [
                {"name": "ficheros_modificados_fuera_de_answer", "value": 0.0, "weight": 1.0, "detail": "la herramienta cambió ficheros de entrada"}]}
            print("  ⚠ se modificaron ficheros fuera de answer/: ejecución invalidada")
        tel = {}
        if a.telemetry:
            try:
                tel = json.loads(Path(a.telemetry).read_text())
            except Exception:  # noqa: BLE001
                tel = {}
        a.cost_usd, a.input_tokens, a.output_tokens = tel.get("cost_usd"), tel.get("input_tokens"), tel.get("output_tokens")
        a.minutes, a.notes = None, None
        _record(t, d, res, a, wall=round(wall, 2), rc=rc, source="telemetry_file" if tel else "unavailable")
        print(f"  score={res['score']:.4f} passed={res['passed']} tiempo={wall:.1f}s")
        if rc != 0:
            print(f"  ⚠ la herramienta terminó con código {rc}: {(err or '').strip()[-300:]}")


def cmd_report(tasks, a):
    recs = [json.loads(l) for l in Path(a.results).read_text().splitlines() if l.strip()]
    by_tool: dict[str, list] = {}
    for r in recs:
        by_tool.setdefault(r["tool"], []).append(r)
    rows = []
    for tool, rs in by_tool.items():
        n = len(rs)
        costs = [r["measured"]["cost_usd"] for r in rs if r["measured"].get("cost_usd") is not None]
        passes = sum(1 for r in rs if r["passed"])
        secs = [r["measured"]["wall_seconds"] for r in rs if r["measured"].get("wall_seconds") is not None]
        tot = sum(costs) if len(costs) == n else None
        rows.append({"tool": tool, "n": n, "score": sum(r["score"] for r in rs) / n, "pass": passes / n,
                     "cost": tot / n if tot is not None else None, "cpp": tot / passes if (tot is not None and passes) else None,
                     "secs": sum(secs) / len(secs) if secs else None})
    costed = [r for r in rows if r["cost"] is not None]
    for r in rows:
        r["pareto"] = r["cost"] is not None and not any(o is not r and o["score"] >= r["score"] and o["cost"] <= r["cost"]
                                                         and (o["score"] > r["score"] or o["cost"] < r["cost"]) for o in costed)
    rows.sort(key=lambda r: (-r["score"], r["cost"] if r["cost"] is not None else 9e9))
    f = lambda v, p: "n/d" if v is None else f"{v:{p}}"  # noqa: E731
    print("| Herramienta | Ejec. | Puntuación media | % superadas | Coste medio (USD) | Coste por tarea superada | Tiempo medio (s) | Pareto |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['tool']} | {r['n']} | {r['score']:.3f} | {r['pass']:.0%} | {f(r['cost'], '.4f')} | {f(r['cpp'], '.4f')} | {f(r['secs'], '.0f')} | {'★' if r['pareto'] else ''} |")


def cmd_selftest(tasks, a):
    keys = [resolve(tasks, a.task).DIR.name] if a.task else list(tasks)
    bad = 0
    for k in keys:
        t = tasks[k]
        levels = [int(x) for x in a.levels.split(",")] if a.levels else list(t.LEVELS)
        for lvl in levels:
            if lvl not in t.LEVELS:
                continue
            with tempfile.TemporaryDirectory() as tmp:
                tmp = Path(tmp)
                t0 = time.time()
                tool1, h1 = prepare(t, tmp / "r1", a.seed, lvl)
                tool2, h2 = prepare(t, tmp / "r2", a.seed, lvl)
                fp = lambda d: fingerprint(d)  # noqa: E731
                det = fp(tmp / "r1") == fp(tmp / "r2")
                tool3, h3 = prepare(t, tmp / "r3", a.seed + 1, lvl)
                differs = fp(tmp / "r1" / "hidden") != fp(tmp / "r3" / "hidden") or fp(tool1) != fp(tool3)
                empty = safe_evaluate(t, tool1 / "answer", h1)["score"]
                t.reference(tool1, h1, tool1 / "answer")
                ref = safe_evaluate(t, tool1 / "answer", h1)
                ref2 = safe_evaluate(t, tool1 / "answer", h1)
                eval_det = ref == ref2
                extra_ok, extra_msg = (True, "")
                if a.extra and hasattr(t, "selftest_extra"):
                    extra_ok, extra_msg = t.selftest_extra(tool2, h2)
                ok = det and differs and eval_det and ref["score"] >= 0.999999 and empty < 0.05 and extra_ok
                bad += 0 if ok else 1
                print(f"[{'OK' if ok else 'FALLO'}] {k} L{lvl}: generacion_determinista={det} semilla_cambia={differs} evaluador_determinista={eval_det} "
                      f"referencia={ref['score']:.3f} vacio={empty:.3f} {extra_msg} ({time.time() - t0:.1f}s)")
                if ref["score"] < 0.999999:
                    for c in ref["checks"]:
                        if c["value"] < 0.999999:
                            print("     ✗", c["name"], c["detail"])
    sys.exit(1 if bad else 0)


def main():
    tasks = load_tasks()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    s = sub.add_parser("generate"); s.add_argument("task"); s.add_argument("--level", type=int, default=1)
    s.add_argument("--seed", type=int, default=1); s.add_argument("--out", required=True); s.set_defaults(fn=cmd_generate)
    s = sub.add_parser("evaluate", help="evalúa una entrega; con --tool también la registra (flujo manual)")
    s.add_argument("task"); s.add_argument("--dir", required=True)
    s.add_argument("--response", help="respuesta de chat guardada en un fichero (se extrae el bloque de código)")
    s.add_argument("--verbose", action="store_true")
    s.add_argument("--tool"); s.add_argument("--cost-usd", type=float); s.add_argument("--input-tokens", type=int)
    s.add_argument("--output-tokens", type=int); s.add_argument("--minutes", type=float); s.add_argument("--notes")
    s.add_argument("--results", default="results.jsonl"); s.set_defaults(fn=cmd_evaluate)
    s = sub.add_parser("reference", help="escribe la solución de referencia en un directorio generado (demostración del flujo)")
    s.add_argument("task"); s.add_argument("--dir", required=True); s.set_defaults(fn=cmd_reference)
    s = sub.add_parser("demo", help="prueba rápida de extremo a extremo con la solución de referencia en todas las tareas")
    s.add_argument("--task"); s.add_argument("--level", type=int, default=1); s.add_argument("--seed", type=int, default=1)
    s.add_argument("--out", default="runs/demo"); s.set_defaults(fn=cmd_demo)
    s = sub.add_parser("run", help="ejecuta un agente de línea de comandos y lo evalúa"); s.add_argument("task"); s.add_argument("--tool", required=True)
    s.add_argument("--cmd", required=True, help="Comando (shell). Placeholders: {tool_dir} {prompt_file}")
    s.add_argument("--level", type=int, default=1); s.add_argument("--seed", type=int, default=1)
    s.add_argument("--repeat", type=int, default=1); s.add_argument("--timeout", type=int, default=3600)
    s.add_argument("--telemetry", help="JSON con {cost_usd,input_tokens,output_tokens}")
    s.add_argument("--workdir", default="work"); s.add_argument("--results", default="results.jsonl"); s.set_defaults(fn=cmd_run)
    s = sub.add_parser("report"); s.add_argument("--results", default="results.jsonl"); s.set_defaults(fn=cmd_report)
    s = sub.add_parser("selftest"); s.add_argument("--task"); s.add_argument("--levels"); s.add_argument("--seed", type=int, default=20260929)
    s.add_argument("--extra", action="store_true", help="comprobaciones adicionales (más lentas)"); s.set_defaults(fn=cmd_selftest)
    a = p.parse_args()
    a.fn(tasks, a)


if __name__ == "__main__":
    main()
