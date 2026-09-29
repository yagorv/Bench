# Benchmark catalog

The runnable tasks are versioned under `benchmarks/tasks/`. List the current suite with `python3 -m agentbench list`. Every run receives the same task prompt and input bytes for a given task, seed, and row count; each attempt starts from a new workspace. The evaluator is part of this repository and runs locally after the agent exits.

## Long-form battery

`python3 -m agentbench run --agent <id> --all` runs only these tasks. Each is scoped for several minutes of multi-step work; estimates are ranges, not enforced minimum runtimes. The runner measures actual elapsed time and output quality.

| ID | Category | Task | Deterministic evaluator |
|---|---|---|---|
| `data.clean-large-csv.v1` | Data engineering | Stream, normalize, validate, deduplicate, and sort up to a million generated events | Every canonical output row and summary compared; solution runtime measured |
| `review.python-security-defect.v1` | Code review | Review a multi-file Python service and identify 12 seeded defects | Exact defect locations and severities; rejects missing and extra findings |
| `python.workflow-scheduler.v1` | Software engineering | Implement a modular deterministic dependency scheduler with retries, failures, skips, CLI, and validation | Hidden contract suite across supplied and generated workflows |

Estimated work ranges are recorded in each `task.json`; they are planning estimates, not runtime guarantees. Actual wall time depends on the agent, model, hardware, and product configuration and is measured in the run record.

## Calibration tasks

These short tasks remain runnable by ID or category. They are excluded from `--all` so they do not dilute the multi-minute main battery.

| ID | Task | Evaluator |
|---|---|---|
| `json.normalize-records.v1` | Normalize and sort fixed JSON records | Exact JSON equality |
| `python.fix-tax-calculation.v1` | Fix a small seeded calculation bug | Edge case and exception checks |
| `oneshot.ascii-pgm.v1` | Render a fixed pixel image as ASCII | Exact character rendering |
| `oneshot.xlsx-sales-report.v1` | Create a sales workbook | Required cells, formula, sheet names, frozen header |
| `oneshot.png-artifact.v1` | Generate a fixed-size PNG illustration | PNG encoding and dimensions only |
| `oneshot.mp4-artifact.v1` | Generate an MP4 clip | MP4 container structure only |

Image/video semantic quality, frame rate, and duration are not currently scored. Those outputs must be reported in a modality track, separately from exact software correctness, until pinned, reproducible perceptual evaluators are added. Android build, bug-fix, feature, and review tasks remain on the roadmap and are not included in `--all` yet.

## Verified suite (separate runner)

Five longer tasks live in [`verified-suite/`](verified-suite/README.md) and are run with its own `bench.py`, not with `python3 -m agentbench`. They are not part of `--all`. Difficulty scales by level (1 to 3) through data volume, not by changing the task.

| Task | Category | Deterministic evaluator |
|---|---|---|
| `t01_kite_interpreter` | Implement from a formal specification | 348 hidden programs, output compared character by character |
| `t02_kite_bugfix` | Read and fix code (3, 6 or 10 injected bugs) | Same hidden tests; net tests fixed, regressions subtract |
| `t03_formats_unification` | Requirements to a three-CLI pipeline | Field accuracy over 20, 60 or 120 hidden files, CLI contract, robustness, stdlib-only check |
| `t04_log_forensics` | Data analysis at scale | 19 exact answers; the log is about 55k, 425k or 2M tokens |
| `t05_vrp` | Optimization | Feasibility, then `min(1, reference_distance / distance)` |

## Planned expansions

- More data tasks: SQL aggregation, quality-defect detection, output-preserving ETL optimization, and multi-size scale curves.
- Android tasks: pinned build-fix fixtures, deterministic bug reproductions, known-defect review, and small features with regression tests.
- One shot tasks: presentation generation and more structured file formats.
- Image/video task-specific visual and temporal scoring, reported alongside blind human ratings rather than folded into exact pass/fail.

Each task addition should pin its prompt, input, output contract, evaluator, and capability requirements. Do not publish a deterministic score unless it can be recomputed from saved run artifacts and evaluator version.
