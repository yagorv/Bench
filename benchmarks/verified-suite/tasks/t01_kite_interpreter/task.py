"""T01 - Implementar desde cero un intérprete de un lenguaje inventado (Kite). Evaluación: ~350 programas ocultos."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_kite"))
import common  # noqa: E402
from suite_lib import Report, fail_report, write_json, read_json  # noqa: E402

ID = "t01_kite_interpreter"
TITLE = "Implementar un intérprete (lenguaje Kite)"
LEVELS = (1,)
DELIVERABLES = ["solution.py"]
NEEDS = "No tool is mandatory; being able to run Python helps a lot to validate."

TASK = """# Task: implement an interpreter for the Kite language

## What to deliver
A single file **`solution.py`** (Python 3.10+, **standard library only**) that defines
`run(source: str) -> str`: it executes the Kite program `source` and returns everything it prints, according to the specification below.

## Rules
- No external dependencies, no file access and no network. The module is imported once and `run` is called hundreds of times: every call must be independent (no shared state).
- `run` must never raise exceptions to the caller: errors of the Kite program are returned as text as defined in §8.
- You may change the recursion limit and the stack size (`sys.setrecursionlimit`, `threading.stack_size`); they are not changed for you.
- Limit per test program: 15 s. Memory: 3 GB.

## How it is scored
About 350 hidden Kite programs are executed (arithmetic, logic, strings, collections, control flow, functions and closures, scopes, runtime errors and syntax errors,
deep recursion) and the output is compared **character by character**. Score = fraction of correct programs. The examples in the specification are only a sample;
the hidden ones cover every section, including edge cases and error cases.

---

{spec}
"""


def generate(tool: Path, hidden: Path, seed: int, level: int) -> None:
    (tool / "TASK.md").write_text(TASK.replace("{spec}", common.spec_text()), encoding="utf-8")
    common.write_examples(tool)
    write_json(hidden / "tests.json", common.build_tests(seed))


def evaluate(answer: Path, hidden: Path) -> dict:
    sol = answer / "solution.py"
    if not sol.exists():
        return fail_report("falta solution.py")
    tests = read_json(hidden / "tests.json")
    ok, import_error = common.run_tests(sol, tests)
    rep = Report()
    if import_error:
        rep.add("importar_solution", False, 1, import_error)
    for cat, (good, n, failing) in common.by_category(tests, ok).items():
        rep.add(f"categoria:{cat}", good / n, n, f"{good}/{n}" + (f" fallan: {failing}" if failing else ""))
    return rep.result()


def reference(tool: Path, hidden: Path, answer: Path) -> None:
    answer.mkdir(parents=True, exist_ok=True)
    shutil.copy(HERE.parent / "_kite" / "kite_ref.py", answer / "solution.py")
