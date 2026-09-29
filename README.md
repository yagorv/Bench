# Agent Exam Capsules

Portable Markdown exams for comparing AI agents and artifact generation tools. Each capsule has a fixed `prompt.md`, context, inputs or starter files, and a clear output contract. Give the same Markdown and attachments to any product, collect its output, and review quality, elapsed time, and cost yourself. The optional local runner can package inputs and apply exact checks; you do not need it to ask an agent to take an exam.

## Start here

Para instrucciones paso a paso en español, consulta [la guía rápida](docs/quickstart-es.md).
Para elegir y entregar directamente los exámenes, sigue [las instrucciones de las cápsulas Markdown](benchmarks/tasks/README.md).

Reading and handing off an exam needs no Python. The optional package/evaluation runner requires Python 3.11 or newer and uses only the standard library.

```sh
git clone https://github.com/yagorv/Bench.git
cd Bench
```

Para el flujo principal no configures ninguna CLI: abre una tarea en `benchmarks/tasks/`, entrega su `prompt.md` junto con los archivos de contexto y entrada declarados en `task.json`, y recoge los archivos solicitados en `output_files`. Las instrucciones completas están en [la guía de cápsulas](benchmarks/tasks/README.md). La CLI que sigue es opcional, para automatizar ejecuciones o comprobaciones exactas.

Run one long-form task five times, or run the complete long-form battery:

```sh
python3 -m agentbench run --agent claude-code --task python.workflow-scheduler.v1 --repetitions 5
python3 -m agentbench run --agent claude-code --all --repetitions 5
python3 -m agentbench report
python3 -m agentbench review --open
```

`results/runs/` preserves outputs and copies the exact versioned inputs when using the optional runner. `agentbench report` writes a quality-only CSV with pass/fail and artifact paths. `agentbench review --open` opens a local gallery with image, video, and audio previews and readable text outputs. You can add personal ratings and notes, then download them as JSON. No cost report is generated.

## Use a web or desktop AI tool

This works for tools that do not offer a compatible local CLI. It creates the same portable package for ChatGPT, Devin, Gemini, or another interface; there is no requirement to install Claude Code.

```sh
python3 -m agentbench prepare --task data.clean-large-csv.v1 --agent "Product and model name"
```

Upload the printed `task-package.zip` to a **new conversation/session** in the AI tool (or extract it and attach all contained files if ZIP upload is unsupported). Send the exact `prompt.md` printed by the command and ask it to return every file listed in `output_files`. Copy the outputs into the matching local `results/runs/<run-id>/workspace/submission/` folder and evaluate them:

```sh
python3 -m agentbench evaluate --run-id "ID printed by prepare"
python3 -m agentbench report
python3 -m agentbench review --open
```

Prepare one capsule per agent. The task and inputs are pinned in Git, so each package contains identical bytes; compare the `input_sha256` field in each `pending.json` if you want to verify this. Review each output in the gallery and assess cost manually in the provider session.

## Runnable task set

The main battery contains long-form tasks designed to require several minutes of multi-step work: cleaning a fixed million-row dataset, reviewing a 12-defect multi-file Python service, and implementing a deterministic workflow scheduler with hidden contract tests. Each has an estimated work range in `agentbench list`; actual wall time is measured per run and can vary by tool, hardware, and model. `--all` runs only these long-form tasks. Short JSON, bug-fix, and artifact tasks remain available by ID as calibration checks. The audio jingle has exact pitch and duration checks plus a human listening step. The video storyboard's semantic content is for human review. Android tasks are planned, not yet part of the runnable battery.

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

Add a task directory under `benchmarks/tasks/<slug>/` with `task.json`, `prompt.md`, context and input files, and any starter project needed. Keep hidden evaluator material outside the files given to the agent. Add an evaluator type in `agentbench/cli.py` when exact local checks help.

## Existing fixtures

`datasets/generate.py` generates a reproducible sharded dataset for larger future tasks. `android-app/` is an Android starter app and `benchmarks/android/` holds its task roadmap. See [the catalog](benchmarks/catalog.md).

## License

Apache-2.0. See [LICENSE](LICENSE).
