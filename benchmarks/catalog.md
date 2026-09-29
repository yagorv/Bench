# Benchmark catalog

The runnable tasks are versioned under `benchmarks/tasks/`. List the current suite with `python3 -m agentbench list`. Every run receives the same task prompt and input bytes for a given task, seed, and row count; each attempt starts from a new workspace. The evaluator is part of this repository and runs locally after the agent exits.

## Runnable now

| ID | Category | Task | Deterministic evaluator |
|---|---|---|---|
| `json.normalize-records.v1` | Structured output | Normalize, validate, deduplicate, and sort fixed JSON records | Exact JSON equality |
| `python.fix-tax-calculation.v1` | Software engineering | Fix a seeded calculation bug | Exact edge case and exception checks |
| `review.python-security-defect.v1` | Code review | Find a seeded path traversal issue | Expected rule, file, line, and severity |
| `data.clean-large-csv.v1` | Data engineering | Stream clean generated CSV events | Every canonical output row and summary compared |
| `oneshot.ascii-pgm.v1` | One shot text | Render a fixed pixel image as ASCII | Exact character rendering |
| `oneshot.xlsx-sales-report.v1` | One shot spreadsheet | Create a small sales workbook | Required cells, formula, sheet names, frozen header |
| `oneshot.png-artifact.v1` | One shot image | Generate a fixed-size PNG illustration | PNG encoding and 256×256 dimensions only |
| `oneshot.mp4-artifact.v1` | One shot video | Generate an MP4 clip from a fixed prompt | MP4 container structure only |

Image/video semantic quality, frame rate, and duration are not currently scored. Those outputs must be reported in a modality track, separately from exact software correctness, until pinned, reproducible perceptual evaluators are added. Android build, bug-fix, feature, and review tasks remain on the roadmap and are not included in `--all` yet.

## Planned expansions

- More data tasks: SQL aggregation, quality-defect detection, output-preserving ETL optimization, and multi-size scale curves.
- Android tasks: pinned build-fix fixtures, deterministic bug reproductions, known-defect review, and small features with regression tests.
- One shot tasks: presentation generation and more structured file formats.
- Image/video task-specific visual and temporal scoring, reported alongside blind human ratings rather than folded into exact pass/fail.

Each task addition should pin its prompt, input, output contract, evaluator, and capability requirements. Do not publish a deterministic score unless it can be recomputed from saved run artifacts and evaluator version.
