"""T03 - Formats Unification (edición offline): 3 CLIs desde requisitos; se evalúan con ficheros retenidos."""
from __future__ import annotations

import ast
import csv
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent))
import gen  # noqa: E402
from dicts import COLUMNS, GROUPED, HEADER_SYNONYMS, SUMMARY_KEYWORDS, TEXT_LABELS, md_table  # noqa: E402
from suite_lib import Report, fail_report, read_json, rng, write_json  # noqa: E402

ID = "t03_formats_unification"
TITLE = "Formats Unification (pipeline de 3 CLIs, offline)"
LEVELS = (1, 2, 3)
DELIVERABLES = ["tools/txt_to_json.py", "tools/sheet_to_json.py", "tools/json_to_csv.py", "tools/formats_common.py"]
NEEDS = "Ejecutar código Python ayuda mucho a validar los CLIs contra las muestras."


def fmt_cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() else repr(v)
    return str(v)


def expected_csv(records, header=COLUMNS) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    for rec in records:
        w.writerow([fmt_cell(rec.get(c)) for c in header])
    return buf.getvalue()


def dump_json(recs) -> str:
    return json.dumps(recs, ensure_ascii=False, indent=2) + "\n"


def generate(tool: Path, hidden: Path, seed: int, level: int) -> None:
    r = rng(seed, ID)
    cfg = gen.CFG[level]
    ctx = gen.Ctx(r)
    meta = {}
    for i in range(cfg["n_txt"]):
        text, recs, warns, skipped = gen.render_text_file(r, ctx, cfg)
        name = f"corpus/txt/c{i:03d}.txt"
        (hidden / name).parent.mkdir(parents=True, exist_ok=True)
        (hidden / name).write_bytes(gen.encode_text(r, text, cfg))
        meta[name] = {"kind": "txt", "records": recs, "skipped": skipped, "warnings": warns}
    for i in range(cfg["n_sheet"]):
        data, ext, recs, warns, skipped, mapping = gen.render_sheet(r, ctx, cfg)
        name = f"corpus/sheets/c{i:03d}{ext}"
        (hidden / name).parent.mkdir(parents=True, exist_ok=True)
        (hidden / name).write_bytes(data)
        meta[name] = {"kind": "sheet", "records": recs, "skipped": skipped, "warnings": warns, "mapping": mapping}
    write_json(hidden / "meta.json", meta)

    # --- muestras visibles (mismo generador, estilos fijos y sin casos extremos de nivel 3)
    rs = rng(seed, ID + ":samples")
    sctx = gen.Ctx(rs)
    (tool / "samples" / "txt").mkdir(parents=True)
    (tool / "samples" / "sheets").mkdir()
    (tool / "samples" / "expected").mkdir()
    all_records = []

    def put(rel, data, recs):
        (tool / "samples" / rel).write_bytes(data)
        stem = Path(rel).stem
        (tool / "samples" / "expected" / f"{stem}.json").write_text(dump_json(recs), encoding="utf-8")
        all_records.extend(recs)

    for stem, fam in (("sample_a", "A"), ("sample_b", "B"), ("sample_c", "C")):
        text, recs, _, _ = gen.render_text_file(rs, sctx, gen.SAMPLE_CFG, fam_fixed=fam, n_inv=2)
        put(f"txt/{stem}.txt", text.encode("utf-8"), recs)
    base = dict(gen.CFG[1], groups=(2, 2), rows=(3, 4))
    styles = [("sample_1", dict(base, meta=(1, 1), delims=[","], grouped=0.0, subtotals=0.0, drop=0.1)),
              ("sample_2", dict(gen.CFG[2], groups=(2, 2), rows=(3, 4), meta=(2, 2), delims=[";"], grouped=1.0, subtotals=1.0, amount_only=1.0,
                                drop=0.2, blanks=0.1, crlf=0.0)),
              ("sample_3", dict(base, meta=(3, 3), delims=["\t"], grouped=0.0, subtotals=0.0, drop=0.2, extras=(1, 2)))]
    for stem, scfg in styles:
        data, ext, recs, _, _, _ = gen.render_sheet(rs, sctx, scfg)
        put(f"sheets/{stem}{ext}", data, recs)
    (tool / "samples" / "expected" / "unified.csv").write_text(expected_csv(all_records), encoding="utf-8", newline="")
    with open(tool / "template.csv", "w", encoding="utf-8", newline="") as f:
        csv.writer(f, lineterminator="\n").writerow(COLUMNS)
    task = (HERE / "TASK.md.tmpl").read_text(encoding="utf-8")
    task = task.replace("{{TEXT_TABLE}}", md_table(TEXT_LABELS, "Field")).replace("{{HEADER_TABLE}}", md_table(HEADER_SYNONYMS, "Column"))
    (tool / "TASK.md").write_text(task, encoding="utf-8")


# ================================================================== evaluación
def veq(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, bool) or isinstance(b, bool):
        return False
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) < 1e-9
    return isinstance(a, str) and isinstance(b, str) and a == b


def import_violations(tools: Path) -> list[str]:
    local = {p.stem for p in tools.glob("*.py")}
    banned = {"socket", "urllib", "http", "ftplib", "smtplib", "subprocess", "ssl", "telnetlib", "xmlrpc", "asyncio", "multiprocessing", "ctypes"}
    std = set(sys.stdlib_module_names)
    out = []
    for p in sorted(tools.glob("*.py")):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError:
            out.append(f"{p.name}: error de sintaxis")
            continue
        for node in ast.walk(tree):
            mods = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module] if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module else []
            for m in mods:
                top = m.split(".")[0]
                if top in banned or (top not in std and top not in local):
                    out.append(f"{p.name}: import {m}")
    return out


class Runner:
    def __init__(self, ws: Path):
        self.ws = ws
        guard = Path(tempfile.mkdtemp(prefix="t03_guard_"))
        (guard / "sitecustomize.py").write_text(
            "import socket\n\ndef _b(*a, **k):\n    raise OSError('network disabled by the benchmark')\n"
            "socket.socket.connect = _b\nsocket.create_connection = _b\nsocket.getaddrinfo = _b\n", encoding="utf-8")
        self.guard = guard
        import os
        self.env = {"PATH": os.environ.get("PATH", ""), "PYTHONPATH": str(guard), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0",
                    "LANG": "C.UTF-8", "PYTHONIOENCODING": "utf-8"}

    def __call__(self, script: str, args: list[str], timeout=30):
        try:
            p = subprocess.run([sys.executable, str(self.ws / "tools" / script), *args], cwd=self.ws, env=self.env, capture_output=True,
                               timeout=timeout, stdin=subprocess.DEVNULL)
            return p.returncode, p.stdout, p.stderr.decode("utf-8", "replace")
        except subprocess.TimeoutExpired:
            return -9, b"", "TIMEOUT"

    def close(self):
        shutil.rmtree(self.guard, ignore_errors=True)


def jparse(out: bytes):
    try:
        v = json.loads(out.decode("utf-8"))
        return v if isinstance(v, list) else None
    except Exception:  # noqa: BLE001
        return None


PROBE_TXT = "INVOICE\nInvoice No: PROBE-1\nInvoice Date: 2024-02-30\nSeller: Probe Ltd\nTotal: pending\nSubtotal: 100.00 USD\n"
PROBE_SHEET = ("INVOICE REF,SELLER,TOTAL INVOICE AMOUNT,TOTAL NET VALUE,ISSUE DATE,CURRENCY\n"
               "P1,Probe Ltd,pending,100.00 USD,2024-13-01,\nP2,Probe Ltd,50.00 USD,40.00,05/03/2024,USD\n")


def blank(**kw):
    d = {c: None for c in COLUMNS}
    d.update(kw)
    return d


def evaluate(answer: Path, hidden: Path) -> dict:
    tools = answer / "tools"
    missing = [f for f in ("txt_to_json.py", "sheet_to_json.py", "json_to_csv.py") if not (tools / f).exists()]
    if missing:
        return fail_report(f"faltan tools/{', tools/'.join(missing)}")
    ws = Path(tempfile.mkdtemp(prefix="t03_ws_"))
    try:
        return _evaluate(ws, answer, hidden)
    finally:
        shutil.rmtree(ws, ignore_errors=True)


def _evaluate(ws: Path, answer: Path, hidden: Path) -> dict:
    meta = read_json(hidden / "meta.json")
    shutil.copytree(answer / "tools", ws / "tools", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy(answer.parent / "template.csv", ws / "template.csv")
    shutil.copytree(hidden / "corpus", ws / "corpus")
    (ws / "out").mkdir()
    base_files = {str(p.relative_to(ws)) for p in ws.rglob("*") if p.is_file()}
    run = Runner(ws)
    rep = Report()
    try:
        # ---------------- exactitud por campo / registros / orden
        tot = ok = rec_tot = rec_ok = got_total = spurious = 0
        per_col, per_kind, order_scores = Counter(), {"txt": [0, 0], "sheet": [0, 0]}, []
        col_tot = Counter()
        stdout_cache = {}
        for name, m in meta.items():
            script = "txt_to_json.py" if m["kind"] == "txt" else "sheet_to_json.py"
            rc, out, err = run(script, [name])
            got = jparse(out)
            stdout_cache[name] = (rc, out, err, got)
            by_ref = {}
            for g in got or []:
                if isinstance(g, dict) and isinstance(g.get("INVOICE REF"), str):
                    by_ref.setdefault(g["INVOICE REF"], g)
            for e in m["records"]:
                g = by_ref.get(e["INVOICE REF"])
                rec_tot += 1
                all_ok = g is not None and list(g.keys()) == COLUMNS
                for c in COLUMNS:
                    tot += 1
                    col_tot[c] += 1
                    good = g is not None and c in g and veq(g[c], e[c])
                    ok += good
                    per_col[c] += good
                    per_kind[m["kind"]][0] += good
                    per_kind[m["kind"]][1] += 1
                    all_ok = all_ok and good
                rec_ok += all_ok
            exp_set = {e["INVOICE REF"] for e in m["records"]}
            seen_refs = set()
            for g in got or []:
                got_total += 1
                ref = g.get("INVOICE REF") if isinstance(g, dict) else None
                if ref not in exp_set or ref in seen_refs:
                    spurious += 1
                seen_refs.add(ref)
            exp_refs = [e["INVOICE REF"] for e in m["records"]]
            got_refs = [g.get("INVOICE REF") if isinstance(g, dict) else None for g in (got or [])]
            order_scores.append(1.0 if got_refs == exp_refs else 0.5 if sorted(map(str, got_refs)) == sorted(exp_refs) else 0.0)
        kd = ", ".join(f"{k}={v[0]}/{v[1]}" for k, v in per_kind.items() if v[1])
        rep.add("exactitud_por_campo", ok / tot, 45, f"{ok}/{tot} campos ({kd})")
        rep.add("registros_completos", rec_ok / rec_tot, 15, f"{rec_ok}/{rec_tot}")
        rep.add("orden_de_registros", sum(order_scores) / len(order_scores), 2, f"{len(order_scores)} ficheros")
        rep.add("sin_registros_espurios", 1 - spurious / max(1, got_total), 3, f"{spurious} espurios de {got_total} registros emitidos")
        for c in COLUMNS:
            rep.add(f"campo:{c}", per_col[c] / col_tot[c], 0.0, f"{per_col[c]}/{col_tot[c]}")

        # ---------------- json_to_csv (con los JSON esperados, para aislar esta herramienta)
        names = list(meta)[:8]
        good = 0
        for i, name in enumerate(names):
            jp = ws / "out" / f"exp{i}.json"
            jp.write_text(dump_json(meta[name]["records"]), encoding="utf-8")
            cp = ws / "out" / f"exp{i}.csv"
            rc, _, _ = run("json_to_csv.py", [str(jp), "-o", str(cp)])
            good += rc == 0 and cp.exists() and cp.read_bytes() == expected_csv(meta[name]["records"]).encode("utf-8")
        rep.add("json_to_csv_byte_a_byte", good / len(names), 10, f"{good}/{len(names)}")

        # ---------------- CLI
        txt = [n for n, m in meta.items() if m["kind"] == "txt"]
        sheets = [n for n, m in meta.items() if m["kind"] == "sheet"]
        t0, t1, s0 = txt[0], txt[1], sheets[0]
        t_skip = next((n for n in txt if meta[n]["skipped"] > 0), t0)
        s_skip = next((n for n in sheets if meta[n]["skipped"] > 0), s0)
        so = lambda n: stdout_cache[n][1]  # noqa: E731
        checks = {}

        def check(key, fn):
            try:
                checks[key] = bool(fn())
            except Exception:  # noqa: BLE001
                checks[key] = False

        check("txt_-o_-_igual_stdout", lambda: (lambda r: r[0] == 0 and r[1] == so(t0))(run("txt_to_json.py", [t0, "-o", "-"])))
        check("sheet_-o_-_igual_stdout", lambda: (lambda r: r[0] == 0 and r[1] == so(s0))(run("sheet_to_json.py", [s0, "-o", "-"])))
        check("json_formato_exacto", lambda: stdout_cache[t0][3] is not None and so(t0) == dump_json(stdout_cache[t0][3]).encode("utf-8")
              and all(list(x.keys()) == COLUMNS for x in stdout_cache[t0][3]))
        p_o = ws / "out" / "o1.json"
        check("txt_-o_fichero_igual_stdout", lambda: run("txt_to_json.py", [t0, "-o", str(p_o)])[0] == 0 and p_o.read_bytes() == so(t0))
        p_a = ws / "out" / "app.json"

        def append_flow():
            r1 = run("txt_to_json.py", [t0, "-o", str(p_a), "--append"])
            first = jparse(p_a.read_bytes()) == stdout_cache[t0][3]
            r2 = run("txt_to_json.py", [t1, "-o", str(p_a), "--append"])
            return r1[0] == 0 and first and r2[0] == 0 and jparse(p_a.read_bytes()) == stdout_cache[t0][3] + stdout_cache[t1][3]
        check("append_crea_y_anade", append_flow)
        p_b = ws / "out" / "bad.json"

        def bad_append(script, f):
            p_b.write_text('{"a": 1}', encoding="utf-8")
            before = p_b.read_bytes()
            r = run(script, [f, "-o", str(p_b), "--append"])
            return r[0] == 3 and p_b.read_bytes() == before
        check("txt_append_no_array_exit3", lambda: bad_append("txt_to_json.py", t0))
        check("sheet_append_no_array_exit3", lambda: bad_append("sheet_to_json.py", s0))
        check("entrada_inexistente_exit2", lambda: run("txt_to_json.py", ["corpus/no_existe.txt"])[0] == 2 and run("sheet_to_json.py", ["corpus/no_existe.csv"])[0] == 2)

        def summary_ok(name, script):
            err = stdout_cache[name][2]
            want = f"SUMMARY files=1 records={len(meta[name]['records'])} skipped={meta[name]['skipped']}"
            lines = [l for l in err.splitlines() if l.startswith("SUMMARY")]
            return stdout_cache[name][0] == 0 and lines == [want] and err.strip().splitlines()[-1] == want
        check("txt_summary_exacto", lambda: summary_ok(t_skip, "txt"))
        check("sheet_summary_exacto", lambda: summary_ok(s_skip, "sheet"))

        def mapping_ok():
            rc, out, err = run("sheet_to_json.py", [s0, "--show-mapping", "-o", "-"])
            mp = meta[s0]["mapping"]
            want = [f"HEADER_ROW {mp['header_row']}"] + [f"COL {i} -> {mp['cols'][str(i)]}" for i in sorted(int(k) for k in mp["cols"])]
            got = [l for l in err.splitlines() if l.startswith(("HEADER_ROW", "COL "))]
            return rc == 0 and got == want
        check("show_mapping_exacto", mapping_ok)

        def multi_ok():
            rc, out, err = run("txt_to_json.py", [t0, t1])
            return rc == 0 and jparse(out) == stdout_cache[t0][3] + stdout_cache[t1][3] and "SUMMARY files=2 " in err
        check("varios_ficheros_en_orden", multi_ok)

        def j2c(records, args_extra=(), tpl=None):
            jp = ws / "out" / "in.json"
            jp.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
            cp = ws / "out" / "res.csv"
            if cp.exists():
                cp.unlink()
            return run("json_to_csv.py", [*args_extra, "-o", str(cp), str(jp)]), cp
        unk = [{"INVOICE REF": "X1", "FOO": 1}, {"INVOICE REF": "X2", "FOO": 2}]

        def strict_ok():
            (rc, _, _), cp = j2c(unk, ["--strict"])
            return rc == 2 and not cp.exists()
        check("csv_strict_exit2_sin_fichero", strict_ok)

        def nonstrict_ok():
            (rc, _, err), cp = j2c(unk)
            warns = [l for l in err.splitlines() if l.startswith("WARNING")]
            return rc == 0 and warns == ['WARNING: unknown field "FOO" ignored'] and cp.read_text(encoding="utf-8") == expected_csv([{"INVOICE REF": "X1"}, {"INVOICE REF": "X2"}])
        check("csv_campo_desconocido_aviso_una_vez", nonstrict_ok)

        def keynorm_ok():
            (rc, _, _), cp = j2c([{"seller_id": "S1", "Invoice-Ref": "R1", "total invoice amount": 12.5}])
            return rc == 0 and cp.read_text(encoding="utf-8") == expected_csv([{"SELLER ID": "S1", "INVOICE REF": "R1", "TOTAL INVOICE AMOUNT": 12.5}])
        check("csv_normaliza_claves", keynorm_ok)

        def tpl_ok():
            tp = ws / "out" / "tpl.csv"
            tp.write_text("INVOICE REF,SELLER,CURRENCY\n", encoding="utf-8")
            (rc, _, _), cp = j2c([{"CURRENCY": "EUR", "SELLER": "A, B", "INVOICE REF": "R1"}], ["--template", str(tp)])
            return rc == 0 and cp.read_text(encoding="utf-8") == 'INVOICE REF,SELLER,CURRENCY\nR1,"A, B",EUR\n'
        check("csv_--template_personalizada", tpl_ok)

        def stdout_ok():
            jp = ws / "out" / "in2.json"
            jp.write_text(json.dumps([{"INVOICE REF": "R9"}]), encoding="utf-8")
            rc, out, _ = run("json_to_csv.py", ["-o", "-", str(jp)])
            return rc == 0 and out.decode("utf-8") == expected_csv([{"INVOICE REF": "R9"}])
        check("csv_-o_-_a_stdout", stdout_ok)

        def fmt_ok():
            recs = [{"INVOICE REF": 'R"1', "GOODS SERVICES": "line1\nline2, x", "TOTAL INVOICE AMOUNT": 1200.0, "TOTAL NET VALUE": 0.5, "DISCOUNT PERCENTAGE": 2, "MARGIN": None}]
            (rc, _, _), cp = j2c(recs)
            return rc == 0 and cp.read_bytes() == expected_csv(recs).encode("utf-8")
        check("csv_formato_de_valores", fmt_ok)
        n_ok = sum(checks.values())
        rep.add("cli", n_ok / len(checks), 10, f"{n_ok}/{len(checks)}; fallan: {[k for k, v in checks.items() if not v]}")

        # ---------------- robustez (sondas fijas + avisos del corpus)
        def probe(script, text, name, exp, warns):
            pth = ws / "out" / name
            pth.write_text(text, encoding="utf-8")
            rc, out, err = run(script, [str(pth)])
            recs_ok = rc == 0 and jparse(out) == exp
            w_ok = all(re.search(rf'^WARNING: .+:\d+: cannot parse {re.escape(c)} "{re.escape(raw)}"$', err, re.M) for c, raw in warns)
            return 0.5 * recs_ok + 0.5 * w_ok
        scores = [probe("txt_to_json.py", PROBE_TXT, "probe.txt", [gen.to_json_record(blank(**{"INVOICE REF": "PROBE-1", "SELLER": "Probe Ltd", "TOTAL NET VALUE": None}))] and
                       [blank(**{"INVOICE REF": "PROBE-1", "SELLER": "Probe Ltd", "TOTAL NET VALUE": 100, "CURRENCY": "USD"})],
                       [("ISSUE DATE", "2024-02-30"), ("TOTAL INVOICE AMOUNT", "pending")]),
                  probe("sheet_to_json.py", PROBE_SHEET, "probe.csv",
                        [blank(**{"INVOICE REF": "P1", "SELLER": "Probe Ltd", "TOTAL NET VALUE": 100, "CURRENCY": "USD"}),
                         blank(**{"INVOICE REF": "P2", "SELLER": "Probe Ltd", "TOTAL INVOICE AMOUNT": 50, "TOTAL NET VALUE": 40, "CURRENCY": "USD", "ISSUE DATE": "2024-03-05"})],
                       [("TOTAL INVOICE AMOUNT", "pending"), ("ISSUE DATE", "2024-13-01")])]
        cw = [(n, m) for n, m in meta.items() if m["warnings"]]
        if cw:
            got_w = 0
            for n, m in cw:
                err = stdout_cache[n][2]
                got_w += all(re.search(rf'^WARNING: .+:\d+: cannot parse {re.escape(c)} "{re.escape(raw)}"$', err, re.M) for c, raw in m["warnings"])
            scores.append(got_w / len(cw))
        rep.add("robustez_valores_no_parseables", sum(scores) / len(scores), 5, f"sondas={[round(s, 2) for s in scores]}")

        # ---------------- determinismo + efectos secundarios
        d_ok = []
        for script, f in (("txt_to_json.py", t0), ("sheet_to_json.py", s0)):
            a, b = run(script, [f]), run(script, [f])
            d_ok.append(a[0] == 0 and a[1] == b[1])
        jp = ws / "out" / "exp0.json"
        c1, c2 = ws / "out" / "d1.csv", ws / "out" / "d2.csv"
        run("json_to_csv.py", [str(jp), "-o", str(c1)])
        run("json_to_csv.py", [str(jp), "-o", str(c2)])
        d_ok.append(c1.exists() and c1.read_bytes() == c2.read_bytes())
        new = {str(p.relative_to(ws)) for p in ws.rglob("*") if p.is_file()} - base_files
        stray = sorted(n for n in new if not n.startswith("out/"))
        rep.add("determinismo_y_sin_efectos_secundarios", (sum(d_ok) / len(d_ok)) * (0.0 if stray else 1.0), 5, f"determinismo={d_ok} ficheros_nuevos_fuera_de_out={stray}")

        # ---------------- solo stdlib, sin red ni subprocesos
        viol = import_violations(answer / "tools")
        rep.add("solo_stdlib_sin_red", not viol, 5, "; ".join(viol[:5]) or "ok")
        common_ok = (answer / "tools" / "formats_common.py").exists()
        rep.add("modulo_compartido_formats_common", common_ok, 0.0, "existe" if common_ok else "falta tools/formats_common.py")
    finally:
        run.close()
    return rep.result()


# ================================================================== referencia
def reference(tool: Path, hidden: Path, answer: Path) -> None:
    dst = answer / "tools"
    dst.mkdir(parents=True, exist_ok=True)
    for f in (HERE / "reference_tools").glob("*.py"):
        text = f.read_text(encoding="utf-8")
        if f.name == "formats_common.py":
            lits = "\n".join(f"{n} = {v!r}" for n, v in (("COLUMNS", COLUMNS), ("TEXT_LABELS", TEXT_LABELS), ("HEADER_SYNONYMS", HEADER_SYNONYMS),
                                                          ("SUMMARY_KEYWORDS", SUMMARY_KEYWORDS), ("GROUPED", GROUPED)))
            text = text.replace("# __DICTS__", lits)
        (dst / f.name).write_text(text, encoding="utf-8")


def selftest_extra(tool: Path, hidden: Path):
    """1) las muestras visibles cuadran con las reglas (la referencia las reproduce); 2) romper una regla baja la nota."""
    ans = tool / "answer"
    reference(tool, hidden, ans)
    ws = Path(tempfile.mkdtemp(prefix="t03_self_"))
    try:
        shutil.copytree(ans / "tools", ws / "tools")
        shutil.copy(tool / "template.csv", ws / "template.csv")
        run = Runner(ws)
        bad = []
        for p in sorted((tool / "samples").glob("*/*.*")):
            if p.parent.name == "expected":
                continue
            script = "txt_to_json.py" if p.parent.name == "txt" else "sheet_to_json.py"
            rc, out, _ = run(script, [str(p)])
            if out.decode("utf-8") != (tool / "samples" / "expected" / f"{p.stem}.json").read_text(encoding="utf-8"):
                bad.append(p.name)
        recs = []
        for stem in ("sample_a", "sample_b", "sample_c", "sample_1", "sample_2", "sample_3"):
            recs += json.loads((tool / "samples" / "expected" / f"{stem}.json").read_text(encoding="utf-8"))
        jp = ws / "all.json"
        jp.write_text(json.dumps(recs), encoding="utf-8")
        rc, out, _ = run("json_to_csv.py", [str(jp), "-o", "-"])
        if out.decode("utf-8") != (tool / "samples" / "expected" / "unified.csv").read_text(encoding="utf-8"):
            bad.append("unified.csv")
        run.close()
    finally:
        shutil.rmtree(ws, ignore_errors=True)
    if bad:
        return False, f"muestras_inconsistentes={bad}"
    base = evaluate(ans, hidden)["score"]
    msgs = []
    ok = True
    meta = read_json(hidden / "meta.json")
    has_summary = any(m["kind"] == "sheet" and m["skipped"] > 0 for m in meta.values())
    for label, old, new in (("sin_forward_fill", "for col in GROUPED:  # FFILL", "for col in []:  # FFILL"),
                            ("sin_filas_resumen", "if any(norm(c) in SUMMARY_KEYWORDS for c in row):  # SUMMARY", "if False:  # SUMMARY")):
        if label == "sin_filas_resumen" and not has_summary:
            continue
        p = ans / "tools" / "sheet_to_json.py"
        src = p.read_text(encoding="utf-8")
        assert old in src, label
        p.write_text(src.replace(old, new), encoding="utf-8")
        s = evaluate(ans, hidden)["score"]
        p.write_text(src, encoding="utf-8")
        good = 0.3 < s < base - 0.005
        ok = ok and good
        msgs.append(f"{label}={s:.3f}")
    return ok, f"referencia={base:.3f} mutantes[{', '.join(msgs)}] muestras_ok"
