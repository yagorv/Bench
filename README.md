# Agent Exam Capsules

Portable Markdown exams for comparing AI agents and artifact generation tools. Every folder under `exams/` is already a self-contained exam with its task, context, inputs or starter project, and output instructions. Give the same folder to each product, collect its output, and review quality, elapsed time, and cost yourself.

## Start here

Para instrucciones en español, consulta [la guía rápida](docs/quickstart-es.md). Para elegir un examen listo para entregar, abre [`exams/`](exams/).

Reading and handing off an exam needs no Python. The optional package/evaluation runner requires Python 3.11 or newer and uses only the standard library.

```sh
git clone https://github.com/yagorv/Bench.git
cd Bench
```

Para empezar, abre `exams/` y elige una carpeta. En una sesión nueva del agente, envía `TASK.md` junto con todos los archivos de esa carpeta. Pídele los archivos que enumera su `README.md`. Cuando te devuelva el resultado, consulta `exams/review-guides/` para saber cómo abrirlo, escucharlo o ejecutarlo. No necesitas instalar Python ni preparar un paquete.

El ejecutor local es opcional y sirve para lanzar agentes con CLI compatible o aplicar comprobaciones automáticas. Para una revisión manual no tienes que usarlo.

Run one long-form task five times, or run the complete long-form battery:

```sh
python3 -m agentbench run --agent claude-code --task python.workflow-scheduler.v1 --repetitions 5
python3 -m agentbench run --agent claude-code --all --repetitions 5
python3 -m agentbench report
python3 -m agentbench review --open
```

`results/runs/` preserves outputs and copies the exact versioned inputs when using the optional runner. `agentbench report` writes a quality-only CSV with pass/fail and artifact paths. `agentbench review --open` opens a local gallery with image, video, and audio previews and readable text outputs. You can add personal ratings and notes, then download them as JSON. No cost report is generated.

## Runnable task set

The main battery contains long-form tasks designed to require several minutes of multi-step work: cleaning a fixed million-row CSV, normalizing one million JSON Lines records, reviewing a 12-defect multi-file Python service, and implementing a deterministic workflow scheduler with hidden contract tests. Each has an estimated work range in `agentbench list`; actual wall time is measured per run and can vary by tool, hardware, and model. `--all` runs only these long-form tasks. Short bug-fix and artifact tasks remain available by ID as calibration checks. The audio jingle has exact pitch and duration checks plus a human listening step. The video storyboard's semantic content is for human review. Android tasks are planned, not yet part of the runnable battery.

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
