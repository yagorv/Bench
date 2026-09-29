# Agent Benchmark

An open, reproducible benchmark for comparing AI agents across data engineering, Android engineering, and one-shot artifact generation tasks.

Each task requires the agent to include a usage receipt with its final answer. The runner records timing and resource use independently and uses provider telemetry for billed cost when available. Agent-reported values and measured values are stored separately; unavailable usage must be marked explicitly rather than guessed. The benchmark fixes task inputs and evaluation rules, while repeated runs capture variation in agent outputs.

## Repository layout

- `benchmarks/data/`: data task definitions and evaluation contracts.
- `datasets/`: deterministic synthetic data generator. Generated data is not checked in.
- `android-app/`: small Android fixture repository for future build, bug-fix, review, and feature tasks.
- `benchmarks/android/`: initial Android task definitions.
- `benchmarks/one-shot/`: single-prompt artifact generation tasks across text, image, video, and spreadsheets.
- `docs/`: run protocol and scoring rules.
- `docs/run-receipt.schema.json`: required agent-reported usage receipt format.

## Generate a large dataset

Requires Python 3.11 or newer and no third-party packages:

```sh
python3 datasets/generate.py --rows 1000000 --seed 20260929 --output work/data
```

The generator writes deterministic CSV shards and a manifest containing row counts, SHA-256 checksums, parameters, and schema. Keep generated data outside Git; use the manifest to reproduce and verify it.

## Current status

This is the benchmark foundation. It defines a deterministic data workload, an Android starter app, and a first catalog of single-prompt artifact tasks. It does not yet run agents or publish a leaderboard. See [the run protocol](docs/protocol.md) and [contribution guide](CONTRIBUTING.md).

## License

Apache-2.0. See [LICENSE](LICENSE).
