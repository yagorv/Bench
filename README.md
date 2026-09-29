# Agent Benchmark

Portable benchmark runner for comparing AI agents and one shot artifact tools. Every task is a self-contained package: fixed prompt, declared context files, inputs, optional starter project, and output contract. Each attempt starts from the same package and seed. The runner saves artifacts, logs, timings, provider usage when available, and the agent's separately reported usage receipt.

## Start here

Para instrucciones paso a paso en español, consulta [la guía rápida](docs/quickstart-es.md).
Para entregar directamente las pruebas a distintas herramientas, sigue [las instrucciones de los exámenes](benchmarks/tasks/README.md).

Requires Python 3.11 or newer. The runner itself uses only the Python standard library.

```sh
git clone https://github.com/yagorv/Bench.git
cd Bench
python3 -m agentbench list
python3 -m agentbench init
```

Edit `.agentbench/agents.json` to add local command profiles. It is ignored by Git, so credentials and machine-specific settings stay local. The template includes Claude Code and Codex CLI examples; install and authenticate them separately. Any other local CLI can be added as another command profile. For products used through a web/desktop interface, use the manual package flow below.

Run one long-form task five times, or run the complete long-form battery:

```sh
python3 -m agentbench run --agent claude-code --task python.workflow-scheduler.v1 --repetitions 5
python3 -m agentbench run --agent claude-code --all --repetitions 5 --rows 1000000 --seed 20260929
python3 -m agentbench report
python3 -m agentbench review --open
```

`results/runs/` contains each attempt, its exact prompt, inputs, logs, generated files, usage receipt, and `run.json`. `agentbench report` writes a quality-only CSV with pass/fail and artifact paths. `agentbench review --open` opens a local gallery with image, video, and audio previews and readable text outputs. Cost is not aggregated; compare it manually in each provider session.

## Use a web or desktop AI tool

This works for tools that do not offer a compatible local CLI. It creates the same portable package for ChatGPT, Devin, Gemini, or another interface; there is no requirement to install Claude Code.

```sh
python3 -m agentbench prepare --task data.clean-large-csv.v1 --agent "Product and model name" --rows 1000000 --seed 20260929
```

Upload the printed `task-package.zip` to a **new conversation/session** in the AI tool (or extract it and attach all contained files if ZIP upload is unsupported). Send the exact `prompt.md` printed by the command and ask it to return every required file from `submission/`, including `run-receipt.json`. Copy its returned files into the matching local `results/runs/<run-id>/workspace/submission/` folder. Then evaluate and add provider usage from the product's session details:

```sh
python3 -m agentbench evaluate --run-id "ID printed by prepare"
python3 -m agentbench report
python3 -m agentbench review --open
```

Repeat `prepare` for each attempt using the same task, row count, seed, tool settings, and model version. Review each generated output in the gallery; assess cost manually in the provider session. The optional receipt is saved with the run.

## Runnable task set

The main battery contains long-form tasks designed to require several minutes of multi-step work: cleaning a generated million-row dataset, reviewing a 12-defect multi-file Python service, and implementing a deterministic workflow scheduler with hidden contract tests. Each has an estimated work range in `agentbench list`; actual wall time is measured per run and can vary by tool, hardware, and model. `--all` runs only these long-form tasks. Short JSON, bug-fix, and artifact tasks remain available by ID as calibration checks. The audio jingle has exact pitch and duration checks plus a human listening step. The video storyboard's semantic content is for human review. Android tasks are planned, not yet part of the runnable battery.

## Fair comparison and output review

The harness controls task prompt, context, fixtures, seed, starting workspace, evaluator, timeout, and repetitions. Prompt and input hashes are stored per run. Configure the same network policy, model settings, permissions, and tool budgets for a controlled comparison. Each retry starts fresh. The runner saves outputs and quality results; the human review gallery links to each original artifact. Cost is reviewed by you in the provider session and is not included in the benchmark report.

Repeated inference is not perfectly deterministic for most hosted agents. Use at least five attempts and compare success rate and output quality. Lock model/version/settings where supported. Review costs separately in provider dashboards. See [the protocol](docs/protocol.md) for the controlled and native tracks.

## Verified suite (held-out inputs, generated exams)

[`benchmarks/verified-suite/`](benchmarks/verified-suite/README.md) is a separate, self-contained suite with its own runner (`bench.py`, standard library only, Python 3.10+). Its tasks are longer, requirements-style problems whose exam is **generated from a seed** and checked against inputs the tool never sees: a Kite interpreter and a bug-fixing variant, a three-CLI invoice pipeline (Formats Unification), log forensics from 55k to 2M tokens, and vehicle routing with a continuous score. Every task ships a reference solution that scores 1.0 and a self-test that also checks that an empty or deliberately broken solution does not. Its summary reports quality and time; it does not aggregate cost.

```sh
cd benchmarks/verified-suite
python3 bench.py demo     # all five tasks: empty = 0, reference = 1.0
python3 bench.py list
```

It records results in its own `results.jsonl` (score, optional provider telemetry, and time). Its report shows quality and time only; review cost directly in the provider panel. It does not use `python3 -m agentbench` or `benchmarks/tasks/`; the two runners do not share result formats.

## Extending it

Add a task directory under `benchmarks/tasks/<slug>/` with `task.json`, `prompt.md`, at least one declared file under `context/`, optional `inputs/` and `starter/`, and a hidden `expected.json`. Add an evaluator type in `agentbench/cli.py` if the current exact evaluators do not fit. The run receipt contract is [here](docs/run-receipt.schema.json), and the command adapter interface is [documented here](docs/adapters.md).

## Existing fixtures

`datasets/generate.py` generates a reproducible sharded dataset for larger future tasks. `android-app/` is an Android starter app and `benchmarks/android/` holds its task roadmap. See [the catalog](benchmarks/catalog.md).

## License

Apache-2.0. See [LICENSE](LICENSE).
