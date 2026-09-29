Implement the deterministic workflow scheduling engine described in `context/context.md`. Build a modular Python package under `submission/flowbench/` and provide the CLI entry point `python -m flowbench INPUT.json --output OUTPUT.json`. Run it on `inputs/workflows.json` and save the result to `submission/schedules.json`. The hidden evaluator will also run additional workflows and invalid inputs. Match every validation, retry, dependency, ordering, and output rule in the context contract.

## Fixed task package

Read every file listed in `context_files` in `task.json`. Work from this task workspace, use relative paths, and write deliverables under `submission/`.

## Required usage receipt

Report only usage and cost you can actually inspect. Never estimate a billed cost. Write `submission/run-receipt.json` and include the identical JSON in your final response under `BENCHMARK_RUN_RECEIPT`. Use `null` for unavailable values and explain each unavailable value. Use this exact task ID:

```json
{
  "schema_version": 1,
  "task_id": "python.workflow-scheduler.v1",
  "status": "completed",
  "agent_reported": {
    "model": null,
    "input_tokens": null,
    "output_tokens": null,
    "cached_input_tokens": null,
    "model_calls": null,
    "tool_calls": null,
    "wall_time_ms": null,
    "cost": null,
    "cost_currency": null,
    "cost_basis": "unknown"
  },
  "unavailable_fields": [
    {"field": "cost", "reason": "Not exposed to this tool or session"}
  ]
}
```

`status` may be `completed`, `partial`, `failed`, or `timed_out`. `cost_basis` may be `provider_reported`, `rate_card_estimate`, `subscription`, or `unknown`. Keep provider usage distinct from an agent estimate.
