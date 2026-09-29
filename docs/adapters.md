# Connect an AI product

## Command profile

The simplest integration is a command that accepts the benchmark prompt on standard input and writes requested files beneath `AGENTBENCH_SUBMISSION`. The process starts in the task workspace. In `.agentbench/agents.json`, each profile may use:

- `command`: an argument array; no shell is used. Placeholders include `{workspace}`, `{submission}`, `{prompt_file}`, `{run_dir}`, `{task_id}`, `{metrics_file}`, and `{repo}`.
- `stdin`: `prompt` (default) or `none`.
- `env`: environment variables to pass to the command. Values can reference local secrets with `${VARIABLE_NAME}`. Keep secrets out of profile JSON and command arguments.
- `timeout_seconds`, `parser`, and `capabilities`.

The repo's example file contains headless Claude Code and Codex CLI profiles. Check the installed product's own `--help` because CLI options and telemetry change by version. Set `parser` to `claude-code-json` only for Claude Code's JSON result format. The generic `json` parser recognizes common JSON result objects; it may not recognize every vendor's event stream.

## Adapter for a hosted or custom product

Products such as Devin may run in a remote workspace or expose an organization API rather than a local prompt-in/files-out command. Use a local adapter executable as the profile command. The adapter receives:

```text
AGENTBENCH_TASK_ID
AGENTBENCH_WORKSPACE
AGENTBENCH_SUBMISSION
AGENTBENCH_PROMPT_FILE
AGENTBENCH_METRICS_FILE
```

It should read the prompt file, create the vendor session with that exact prompt and task snapshot, wait for completion, then copy the resulting workspace artifacts into `AGENTBENCH_SUBMISSION`. For API products, include the task files in an immutable archive/repository snapshot and make the returned artifacts available to the adapter. Do not silently change the task, prompt, or evaluation.

When authoritative usage is available, write a JSON object to `AGENTBENCH_METRICS_FILE`, for example:

```json
{
  "provider_cost": 0.0123,
  "currency": "USD",
  "input_tokens": 1200,
  "output_tokens": 350,
  "cached_input_tokens": 0,
  "model_calls": 4,
  "tool_calls": 7,
  "provider_duration_ms": 42000,
  "source": "vendor-session-usage-api"
}
```

Only report values returned by the provider. If a subscription product does not disclose task-level spend, leave `provider_cost` null and identify the source/limitation. Never convert a monthly subscription into an invented per-run cost.

## Comparable tracks

Local CLI integrations run under the harness's task workspace and timeout. Remote agent services may have different machines and tool policies. Compare those in the **native** track unless you can give every product the same starting commit, network rules, model/tool budgets, and deadline. Store adapter version, product/model version, organization configuration, and any vendor ACU/credit consumption in the run artifacts. Cost fields need an explicit source and currency to be compared.

## Web/desktop products without a CLI adapter

Use `agentbench prepare --task TASK_ID --agent "Product/model"` to create a fresh run folder and `task-package.zip`. The package contains the task manifest, exact prompt, declared `context/` files, inputs, and starting files; it excludes evaluator reference data. Give that package (or all of its extracted files) and the exact `prompt.md` to a new session in the product. After it finishes, put its output files in the prepared workspace's `submission/` folder, then run `agentbench evaluate --run-id RUN_ID` with any provider-side cost, token, and elapsed-time values shown for that session. The agent's receipt and provider's figures are stored separately.

This mode lets a person operate a closed commercial UI while preserving the task package and evaluator. For strict controlled-track claims, prevent other chat context from leaking into the new session and apply equivalent product settings. If the product does not expose task-level usage, report cost as unavailable or report a disclosed unit such as ACUs with that unit named; do not infer a dollar amount from a subscription.
