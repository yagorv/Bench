# Requirements — Test Suite Author

## Introduction

`shopcart.py` is a small pricing library (cart totals, quantity discounts, coupons, tax and shipping). It is provided in `fixtures/shopcart.py`; its docstrings and the tables in `fixtures/SPEC.md` define the intended behaviour. **You write the automated test suite.** Your suite will be run against the correct implementation and against many defective variants of it (each variant contains a subtle change: an off-by-one, a wrong operator, a changed constant, a removed check…). Your score is the share of defective variants your suite detects, provided it passes on the correct implementation.

You may not see the defective variants. Write tests that check the **documented behaviour**, boundaries included.

## Requirements

### Requirement 1 — The suite passes on the correct implementation

**User Story:** As a maintainer, I want a suite that is green on correct code, so a red result always means a real defect.

#### Acceptance Criteria
1. WHEN run against the provided `shopcart.py` THEN every test SHALL pass (no failures, errors, skips or expected failures).
2. THE suite SHALL be deterministic: no randomness, no clock, no network, no dependence on test order or on the current directory. Two consecutive runs SHALL give identical results.
3. THE whole suite SHALL finish in under 30 seconds.

### Requirement 2 — Behavioural coverage

**User Story:** As a maintainer, I want every documented rule verified at its boundaries, so regressions are caught.

#### Acceptance Criteria
1. EVERY rule in `SPEC.md` SHALL be covered by at least one test that asserts the exact documented result (values, types, and exception classes).
2. FOR every threshold in the spec (quantity tiers, free-shipping limit, coupon minimums) THE suite SHALL test the value just below, exactly at, and just above the threshold.
3. FOR every documented error condition THE suite SHALL assert the specific exception class raised.
4. WHEN a function is documented as pure THEN a test SHALL verify that its inputs are not mutated.

### Requirement 3 — Test hygiene

#### Acceptance Criteria
1. THE suite SHALL be a single file `tests/test_shopcart.py` using only `unittest`; it SHALL import the library with `import shopcart` (the verifier puts the module under test on `sys.path`).
2. EVERY test method SHALL contain at least one assertion, SHALL be named `test_<function>_<scenario>`, and SHALL check one behaviour.
3. THE suite SHALL be at most 500 lines.
4. THE tests SHALL NOT read the source of `shopcart`, inspect its bytecode, patch its internals, tamper with `sys.modules`, or compare against a copy of the implementation. They assert behaviour only.

### Requirement 4 — Environment, dependencies, safety

#### Acceptance Criteria
1. THE suite SHALL run on Python 3.10+ with only the standard library.
2. THE suite SHALL NOT use the network, spawn subprocesses, or write outside the system temp directory (cleaned up).

## Deliverables and provided files
Deliver `answer/tests/test_shopcart.py`. Provided (read-only): `fixtures/shopcart.py`, `fixtures/SPEC.md`.
