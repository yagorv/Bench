"""Piezas comunes de las tareas Kite."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent))
from kite_tests import build_tests, visible_examples  # noqa: E402
from suite_lib import Report, fail_report, run_cases  # noqa: E402


def spec_text() -> str:
    blocks = []
    for ex in visible_examples():
        blocks.append(f"**{ex['name']}**\n```kite\n{ex['src'].rstrip()}\n```\nExpected output (`run` returns exactly this):\n```text\n{ex['expected'] or '(empty)'}```")
    return (HERE / "KITE_SPEC.md").read_text(encoding="utf-8").replace("{examples}", "\n\n".join(blocks))


def write_examples(tool_dir: Path) -> None:
    d = tool_dir / "examples"
    d.mkdir(parents=True, exist_ok=True)
    for i, ex in enumerate(visible_examples(), 1):
        stem = f"{i:02d}_{ex['name'].replace(' ', '_').replace('/', '_')}"
        (d / f"{stem}.kite").write_text(ex["src"], encoding="utf-8")
        (d / f"{stem}.expected").write_text(ex["expected"], encoding="utf-8")


def make_chunks(tests, fn="run", size=1):
    chunks, cur = [], []
    for t in tests:
        case = {"id": t["id"], "fn": fn, "args": [t["src"]]}
        if t["cat"] == "deep":
            chunks.append([case])
            continue
        cur.append(case)
        if len(cur) >= size:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return chunks


def run_tests(solution: Path, tests):
    results, import_error = run_cases(solution, make_chunks(tests), per_case=15.0, chunk_timeout=40.0, mem_mb=3072)
    ok = {}
    for t in tests:
        res = results.get(t["id"])
        ok[t["id"]] = bool(res and res.get("ok") and res.get("value") == t["expected"])
    return ok, import_error


def by_category(tests, ok):
    cats = {}
    for t in tests:
        cats.setdefault(t["cat"], []).append(t["id"])
    return {c: (sum(ok[i] for i in ids), len(ids), [i for i in ids if not ok[i]][:5]) for c, ids in sorted(cats.items())}
