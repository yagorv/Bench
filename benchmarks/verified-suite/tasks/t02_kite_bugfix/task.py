"""T02 - Corregir bugs en un intérprete existente (~600 líneas) usando su especificación. Mismos tests ocultos que T01."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_kite"))
import common  # noqa: E402
from mutations import MUTATIONS  # noqa: E402
from suite_lib import Report, fail_report, read_json, rng, write_json  # noqa: E402

ID = "t02_kite_bugfix"
TITLE = "Corregir bugs en un intérprete existente"
LEVELS = (1, 2, 3)  # nº de bugs inyectados: 3 / 6 / 10
N_BUGS = {1: 3, 2: 6, 3: 10}
DELIVERABLES = ["kite.py"]
INLINED_IN_TASK = {"kite.py"}
NEEDS = "No tool is mandatory; being able to run Python helps a lot to validate."

TASK = """# Task: fix a buggy interpreter

## Context
`kite.py` is an interpreter for the Kite language. It should comply with the specification below, but it contains **exactly {n} bugs** introduced on purpose
(each one at a different place in the file). There are no other differences with respect to the correct implementation.

## What to deliver
The **complete, corrected `kite.py`** (Python 3.10+, standard library only), with the same interface `run(source: str) -> str`.
- Change the minimum necessary: do not rewrite the interpreter or change its structure.
- The specification overrides the current behavior of the code: if the code and the specification disagree, the specification wins.
- The bugs are not visible in the examples below; you will have to review the code against the specification (and, if you can run Python, write your own test programs).

## How it is scored
About 350 hidden Kite programs are executed and the output is compared character by character. The score is the fraction of the tests that **failed with the original `kite.py`** and now pass
(tests that used to pass and stop passing are subtracted). Delivering the file unchanged scores 0. Limit per test program: 15 s.

---

{spec}

---

## Code to fix: `kite.py`
(The same content is in the attached file `kite.py`.)

```python
{code}```
"""


def _buggy(seed: int, level: int) -> str:
    src = (HERE.parent / "_kite" / "kite_ref.py").read_text(encoding="utf-8")
    chosen = rng(seed, "bugs").sample(MUTATIONS, N_BUGS[level])
    for _id, old, new in chosen:
        assert src.count(old) == 1, _id
        src = src.replace(old, new)
    return src


def generate(tool: Path, hidden: Path, seed: int, level: int) -> None:
    buggy = _buggy(seed, level)
    (tool / "kite.py").write_text(buggy, encoding="utf-8")
    (tool / "TASK.md").write_text(TASK.replace("{n}", str(N_BUGS[level])).replace("{spec}", common.spec_text()).replace("{code}", buggy), encoding="utf-8")
    common.write_examples(tool)
    tests = common.build_tests(seed)
    write_json(hidden / "tests.json", tests)
    tmp = hidden / "_buggy_tmp"
    tmp.mkdir()
    (tmp / "kite.py").write_text(buggy, encoding="utf-8")
    ok, _ = common.run_tests(tmp / "kite.py", tests)
    (tmp / "kite.py").unlink()
    tmp.rmdir()
    write_json(hidden / "baseline.json", {"passed": sum(ok.values()), "total": len(tests), "failing": sorted(i for i, v in ok.items() if not v)})


def evaluate(answer: Path, hidden: Path) -> dict:
    sol = answer / "kite.py"
    if not sol.exists():
        return fail_report("falta kite.py")
    tests = read_json(hidden / "tests.json")
    base = read_json(hidden / "baseline.json")
    ok, import_error = common.run_tests(sol, tests)
    rep = Report()
    if import_error:
        rep.add("importar_kite", False, 1, import_error)
    was_failing = set(base["failing"])
    fixed = sum(1 for i in was_failing if ok[i])
    regress = sum(1 for t in tests if t["id"] not in was_failing and not ok[t["id"]])
    net = max(0, fixed - regress)
    rep.add("tests_corregidos_netos", net / len(was_failing) if was_failing else 1.0, 10,
            f"arreglados={fixed}/{len(was_failing)} regresiones={regress}")
    for cat, (good, n, failing) in common.by_category(tests, ok).items():
        rep.add(f"categoria:{cat}", good / n, 0.0, f"{good}/{n}" + (f" fallan: {failing}" if failing else ""))
    return rep.result()


def reference(tool: Path, hidden: Path, answer: Path) -> None:
    import shutil
    answer.mkdir(parents=True, exist_ok=True)
    shutil.copy(HERE.parent / "_kite" / "kite_ref.py", answer / "kite.py")


def selftest_extra(tool: Path, hidden: Path):
    """Cada bug del catálogo, inyectado en solitario, debe ser detectado por los tests ocultos (y el original pasa 100 %)."""
    import tempfile
    tests = read_json(hidden / "tests.json")
    src = (HERE.parent / "_kite" / "kite_ref.py").read_text(encoding="utf-8")
    missed = []
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "kite.py"
        f.write_text(src, encoding="utf-8")
        ok, _ = common.run_tests(f, tests)
        if not all(ok.values()):
            return False, "el original no pasa el 100 %"
        for mid, old, new in MUTATIONS:
            f.write_text(src.replace(old, new), encoding="utf-8")
            ok, _ = common.run_tests(f, tests)
            if all(ok.values()):
                missed.append(mid)
    return (not missed), f"bugs_del_catalogo_sin_detectar={missed or 'ninguno'}"
