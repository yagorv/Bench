# Agent Benchmark

Portable benchmark runner for comparing AI agents and one shot artifact tools. Every task is a self-contained package: fixed prompt, declared context files, inputs, optional starter project, and output contract. Each attempt starts from the same package and seed. The runner saves artifacts, logs, timings, provider usage when available, and the agent's separately reported usage receipt.

## Start here

Para instrucciones paso a paso en español, consulta [la guía rápida](docs/quickstart-es.md).

Requires Python 3.11 or newer. The runner itself uses only the Python standard library.

```sh
git clone https://github.com/yagorv/Bench.git
cd Bench
python3 -m agentbench list
python3 -m agentbench init
```

Edit `.agentbench/agents.json` to add local command profiles. It is ignored by Git, so credentials and machine-specific settings stay local. The template includes Claude Code and Codex CLI examples; install and authenticate them separately. Any other local CLI can be added as another command profile. For products used through a web/desktop interface, use the manual package flow below.

Run one task five times, or run all tasks that a profile says it supports:

```sh
python3 -m agentbench run --agent claude-code --task python.fix-tax-calculation.v1 --repetitions 5
python3 -m agentbench run --agent claude-code --all --repetitions 5 --rows 1000000 --seed 20260929
python3 -m agentbench report
```

`results/runs/` contains one folder per attempt with the exact prompt, copied inputs, raw logs, submission, usage receipt, and `run.json`. `results/leaderboard.csv` aggregates pass rate, provider cost per attempt and per successful task where usage is complete, tokens where exposed, and median elapsed time. Keep the whole `results/` folder to archive or share a benchmark session.

## Use a web or desktop AI tool

This works for tools that do not offer a compatible local CLI. It creates the same portable package for ChatGPT, Devin, Gemini, or another interface; there is no requirement to install Claude Code.

```sh
python3 -m agentbench prepare --task data.clean-large-csv.v1 --agent "Product and model name" --rows 1000000 --seed 20260929
```

Upload the printed `task-package.zip` to a **new conversation/session** in the AI tool. Send the exact prompt from the printed `prompt.txt` and ask it to return every required file from `submission/`, including `run-receipt.json`. Copy its returned files into the matching local `results/runs/<run-id>/workspace/submission/` folder. Then evaluate and add provider usage from the product's session details:

```sh
python3 -m agentbench evaluate --run-id "ID printed by prepare" --provider-cost 0.12 --currency USD --input-tokens 12000 --output-tokens 2000 --wall-time-ms 95000 --usage-source "provider usage panel"
python3 -m agentbench report
```

Use the provider's actual per-session charge or usage units. If it only shows subscription pricing and no per-task usage, omit `--provider-cost`; do not invent a number. Repeat `prepare` for each attempt and use the same task, row count, seed, tool settings, and model version for comparisons. The run receipt reports what the agent says it used; the values passed to `evaluate` record provider-side usage separately.

## Runnable task set

Run `python3 -m agentbench list` for IDs and evaluator names. Structured transformation and one-shot artifact tasks are short calibration cases; code review has four seeded defects, and the data task grows to one million or more rows for the main comparison. The image and video evaluators currently score only file/container validity and dimensions; they do not claim to measure visual or semantic quality. Android tasks are planned, not yet part of the runnable battery.

## Fair comparison and cost

The harness controls task prompt, task context, fixtures, seed, starting workspace, evaluator, timeout, and repetitions. Prompt and input SHA-256 hashes are stored per run. Configure the same network policy, model settings, permissions, and tool budgets for a controlled comparison, and report product-native workflows separately. Each retry is a fresh workspace. It records wall time and output/evaluator results. Provider cost and tokens are captured from supported CLI telemetry, an adapter sidecar, or manual provider-session details; each agent also writes a receipt but those self-reported numbers are kept separate. Unknown cost stays `null`; subscription fees are not treated as per-task spend.

Repeated inference is not perfectly deterministic for most hosted agents. Use at least five attempts, publish all attempts, and compare success rate plus median/variation of time and cost. Lock model/version/settings where the vendor supports it. See [the protocol](docs/protocol.md) for the controlled and native tracks.

## Verified suite (held-out inputs, generated exams)

[`benchmarks/verified-suite/`](benchmarks/verified-suite/README.md) is a separate, self-contained suite with its own runner (`bench.py`, standard library only, Python 3.10+). Its tasks are longer, requirements-style problems whose exam is **generated from a seed** and checked against inputs the tool never sees: a Kite interpreter and a bug-fixing variant, a three-CLI invoice pipeline (Formats Unification), log forensics from 55k to 2M tokens, and vehicle routing with a continuous score. Every task ships a reference solution that scores 1.0 and a self-test that also checks that an empty or deliberately broken solution does not.

```sh
cd benchmarks/verified-suite
python3 bench.py demo     # all five tasks: empty = 0, reference = 1.0
python3 bench.py list
```

It records results in its own `results.jsonl` (score, cost, tokens, time) and reports cost per passed task and the Pareto frontier. It does not use `python3 -m agentbench` or `benchmarks/tasks/`; the two runners do not share result formats.

## Extending it

Add a task directory under `benchmarks/tasks/<slug>/` with `task.json`, `prompt.md`, at least one declared file under `context/`, optional `inputs/` and `starter/`, and a hidden `expected.json`. Add an evaluator type in `agentbench/cli.py` if the current exact evaluators do not fit. The run receipt contract is [here](docs/run-receipt.schema.json), and the command adapter interface is [documented here](docs/adapters.md).

## Existing fixtures

`datasets/generate.py` generates a reproducible sharded dataset for larger future tasks. `android-app/` is an Android starter app and `benchmarks/android/` holds its task roadmap. See [the catalog](benchmarks/catalog.md).

## License

Apache-2.0. See [LICENSE](LICENSE).
