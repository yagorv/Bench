# Required final answer contract

Every benchmark task, including artifact-generation tasks, requires the agent's final answer to include:

1. The requested deliverable or its exact saved path.
2. A JSON run receipt conforming to [`../../docs/run-receipt.schema.json`](../../docs/run-receipt.schema.json).
3. A short result summary and any known limitations.

The receipt is the agent's self-report. Agents must give `null` for metrics they cannot inspect and explain the limitation in `unavailable_fields`; they must not estimate from memory. The benchmark runner records process timing and usage independently, and provider telemetry is authoritative for billed cost when available. Scoreboards display these sources separately.
