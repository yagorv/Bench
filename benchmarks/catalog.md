# Proposed benchmark catalog

This catalog defines the first set of comparable tasks for Agent Benchmark. Task definitions are proposals until each has an immutable fixture, an evaluator, a reference result, and a dry run that proves the baseline fails and the reference solution passes.

## First release

| Priority | ID | Task | Artifact | Success oracle | Main measurements |
|---|---|---|---|---|---|
| P0 | `oneshot.ascii-image.v1` | Convert one fixed public-domain portrait image to ASCII | `art.txt` | Dimensions and character set; SSIM or perceptual similarity to a reference glyph rendering; separate blind recognizability score | Cost, time, output length |
| P0 | `oneshot.image-mona-lisa.v1` | Generate one image from a fixed prompt and settings | PNG | Decodes, expected dimensions; prompt adherence and composition scored separately by a fixed evaluator and blind reviewers | Provider cost/credits, time, retries, seed availability |
| P0 | `oneshot.xlsx-sales-report.v1` | Create a workbook from a small fixed CSV | XLSX | Sheet names, rows, formulas, formula results, formats, freeze panes, and totals checked by code | Cost, time, tool calls, output size |
| P0 | `data.large-csv-cleaning.v1` | Clean and deduplicate sharded event data | Script and output files | Exact accepted/rejected/duplicate counts, schema, normalization rules, sort order, checksum of canonical output | Cost, time, peak RAM, CPU, bytes read/written |
| P0 | `android.build-fix.v1` | Repair a seeded Gradle or manifest build break | Git patch | Debug build succeeds, existing tests pass, dependency versions remain pinned | Cost, time, tool calls, build duration |
| P0 | `android.functional-bug.v1` | Fix one reproducible app bug | Git patch | Hidden regression test passes and existing tests still pass | Cost, time, tests run, build duration |
| P0 | `android.pr-review.v1` | Review a PR containing known seeded defects | Structured findings | Defect recall and precision, location accuracy, severity agreement, false positives | Cost, time, calls, findings count |
| P0 | `data.optimize-etl.v1` | Improve a deliberately slow transform without changing results | Script and benchmark report | Golden output equality plus correctness suite; resource ceiling | Cost, time, peak RAM, CPU, speedup |
| P1 | `oneshot.video-mona-lisa.v1` | Generate a short clip from a fixed prompt or source frame | MP4 | Valid decode, duration, resolution, frame rate; temporal consistency and prompt adherence evaluated separately | Provider cost/credits, time, retries, seed availability |
| P1 | `oneshot.ascii-mona-lisa.v1` | Draw a recognizable portrait using ASCII only | TXT | Allowed characters and size limits; blinded 1-5 recognizability and craft rubric | Cost, time, output length |
| P1 | `data.sql-aggregate.v1` | Write SQL to answer fixed aggregation questions on a large dataset | SQL and result table | Exact result rows and values, query runs within a resource limit | Cost, time, query runtime, peak RAM |
| P1 | `data.data-quality.v1` | Find and implement checks for injected data defects | Script and report | Defect precision/recall against a hidden labeled set; output schema | Cost, time, checks written, memory |
| P1 | `android.feature.v1` | Add a small user-visible app feature | Git patch | Hidden behavior tests and existing regression suite pass | Cost, time, tests, patch size |
| P1 | `android.performance.v1` | Remove a seeded performance regression | Git patch | Fixed emulator benchmark meets latency and memory thresholds; correctness unchanged | Cost, time, p50/p95 runtime, peak memory |
| P2 | `oneshot.presentation.v1` | Create a short slide deck from fixed source material | PPTX | Slide count, required text and images, parseable file; blind readability rubric | Cost, time, tool calls, output size |
| P2 | `data.scale-curve.v1` | Run one correct transform at increasing dataset sizes | Script and output | Canonical output matches at every size | Cost per size, time, memory, throughput, scaling curve |

P0 is the smallest useful first release. P1 expands coverage after the evaluator and run receipt are working. P2 is optional and should not delay the first published results.

## Task design details

### One-shot artifact generation

Use fixed prompts, attachments, output formats, dimensions, and deadlines. A one-shot run gets one initial instruction and no clarification turn. Count retries or repair prompts as part of that same run and record them. Compare image/video agents only in tracks with the same modality capability; publish native-capability runs separately.

For ASCII conversion, provide one pinned public-domain input image and use the same resize and luminance rules. This tests faithful conversion. Keep freeform ASCII drawing as a separate creative task: two valid pictures will not have identical text, so score its recognition and craft with a blind rubric, not byte equality.

For images and video, exact checks cover file validity and requested technical properties. Evaluate visual quality, prompt adherence, and temporal consistency as distinct measures. Fix generation settings and seed when available; preserve every raw artifact. Machine perceptual metrics are signals, not proof of correctness.

For spreadsheet output, include a small source CSV in the first release and then a separate larger workbook task. Recalculate formulas in a pinned spreadsheet engine before checking cached results. Validate workbook structure, values, formulas, formats, and totals independently so agents cannot pass by making a visually plausible but incorrect sheet.

### Data tasks

Generate synthetic records from a fixed seed and versioned schema. Include known, deterministic cases: mixed-case and padded emails, malformed emails, timestamp format variations, duplicate IDs, missing fields, and valid boundary values. Publish the generator and small development fixtures. Keep evaluator labels and some holdout seeds private until a task version retires.

Use three published workload sizes: 100 thousand rows for iteration, 1 million for the main comparison, and 10 million for scaling. Add 100 million only when storage and run budgets permit. Never commit generated bulk data; store generator version, parameters, manifest, shard checksums, and exact source commit with each run.

Cleaning success is based on a canonical normalized result and exact summary counts. Optimization success requires identical canonical results before performance is scored. Report wall time and peak memory from the isolated runner; use the same machine image and warm/cold-cache policy for both agents.

### Android engineering

Keep one clean app commit and derive each task from a separate immutable fixture commit. For bug and feature work, provide a deterministic reproduction and hidden regression tests. For build repair, pin the Gradle wrapper, plugin, JDK, SDK, emulator image, and dependencies. Cache dependencies before disabling network access.

For PR review, seed defects with a fixed severity and line range. Score each finding against the hidden defect inventory: true positive, false positive, missed defect, severity match, and location overlap. Do not score the amount of review text. Use multiple PRs so one pattern does not dominate the score.

### Cost and performance report

For every attempt, publish:

- pass/fail and exact evaluator breakdown;
- provider billed cost and currency, when authoritative data is available;
- input, output, and cached tokens; model calls and tool calls;
- wall-clock duration, CPU time, peak resident memory, and artifact size where measurable;
- cost per successful task, computed only for successful attempts and alongside cost per attempt;
- the agent's self-reported run receipt, kept separate from runner and provider telemetry;
- any unavailable metric and its reason.

Keep API usage cost separate from subscription price. For image or video products billed by credits, report the credit quantity and the provider's dated conversion to currency. If no authoritative charge data exists, show cost as unavailable; do not rank an agent as cheaper based only on its own estimate.

## Publication gates

A task can move from `draft` to `ready` only after it has:

1. A versioned prompt, input fixture, start commit or data manifest, limits, and capability requirements.
2. A machine-readable task manifest and documented evaluator.
3. A baseline run that fails and a reference solution that passes.
4. An evaluator check showing at least one plausible wrong answer fails.
5. At least five trial runs to reveal flaky setup or scoring.
6. A response receipt, runner record, raw logs, and retained output artifact.

Report exact deterministic success separately from perceptual metrics and human ratings. Publish per-task results first; any aggregate score must expose its weights and must not combine capability tracks.
