# Benchmark run protocol

## Comparison modes

1. **Controlled:** agents receive the same task, repository or dataset state, tool access, network policy, and time and resource budgets.
2. **Native:** each product uses its documented default workflow. Record the product configuration and report this separately from controlled runs.

Never combine results from these modes into one ranking.

## One-shot artifact tasks

One-shot tasks give each agent one fixed Markdown exam and require a deliverable without iterative user feedback. Freeze the prompt, attachments, output format, dimensions, duration or sheet schema, and deadline. Ask for the artifact and its saved path; do not ask the agent to estimate cost. Record whether it had access to image, video, spreadsheet, or code tools, then review the output yourself.

Use exact deterministic checks for structured artifacts: workbook sheet names, cell values, formulas, data types, and required formatting. For images and video, report machine-scored measures such as dimensions, duration, valid encoding, and task-specific similarity metrics separately from blinded human ratings. Do not present a perceptual score as an exact correctness check. Retain the raw artifact and evaluator version for every run.

For text-to-image or text-to-video tasks, fix the prompt and requested settings and use a seed when the service supports it. Record the seed and all generation parameters. If a provider does not expose seeds or model settings, record them as unavailable; repeated runs are still required.

## Reproducibility record

Every task package must be self-contained: its prompt, declared `context_files`, inputs, starter project, output contract, and fixed seed/size. The runner records SHA-256 hashes for the exact prompt and starting workspace. Evaluator reference outputs stay outside the package. For every run, save a machine-readable record with:

- benchmark commit, task ID and task version;
- starting Git commit or dataset manifest SHA-256;
- container image digest, OS, runtime and dependency versions;
- agent, model and tool versions and all available settings;
- CPU, memory, disk, network policy, timeout, and token or spend limits;
- UTC start and end times, wall time, exit status, and raw logs;
- provider-reported cost, currency, rate card date, token counts and tool calls, when available;
- evaluator version, public and hidden test results, and final score.

The Markdown exam asks for the output artifact only. Measure elapsed time and cost in the product's own session or billing panel. The optional runner stores output files and can apply deterministic checks; its summary does not publish costs.

The long-form battery is intended to require several minutes of multi-step work per task. `estimated_minutes` in each task manifest is a design estimate only. Do not insert artificial waits to force a duration; record the actual agent wall time. For the large CSV task, the scorecard also records the generated solution's execution time separately from the agent's elapsed time. For tasks with hidden tests, grader execution time is recorded separately as well.

If you choose to record usage, use the product's reported units and keep subscription pricing separate from marginal per-task charges. The optional runner records process wall time but does not measure isolated CPU time or peak memory. The benchmark does not calculate or publish cost per task.

Do not infer missing cost. If the provider does not expose per-task usage, leave it to manual qualitative comparison rather than guessing.

## Repeated runs

Run each task from a clean snapshot at least five times for exploratory comparisons. Publish every attempt, including failures and timeouts. Report success rate and median and interquartile range for time and cost. For stable claims, increase repetitions and publish confidence intervals. Fix random seeds wherever the agent or task harness supports them.

## Evaluation

Use exact checks for outputs that have an unambiguous expected result: tests, schemas, checksums, functional invariants, build status, and known seeded defects. Human ratings must use a written rubric, blinded reviewers, and separate reporting. Do not hide a subjective rating inside the deterministic score.

Report a scorecard by task category and modality. A single aggregate score is optional and must publish its weights. Do not merge exact software correctness, perceptual ratings, and human review into one unexplained number. Always show quality alongside cost and speed; a cheaper failed run is not a better result.
