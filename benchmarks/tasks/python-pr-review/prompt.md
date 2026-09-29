Review every Python module under inputs/ as if reviewing a pull request. Return submission/findings.json with a findings array; every finding must contain rule_id, path, line, severity, and explanation. Report only the four seeded defects, exactly once each, with accurate one-based line numbers. Do not modify source files. The evaluator checks complete defect coverage and rejects extra findings.

## Fixed task package

Read every file listed in `context_files` in `task.json`. The same package includes all task inputs and any starter files. Work from the task workspace, use relative paths, and write deliverables under `submission/`.

## Required usage receipt

Report only usage and cost you can actually inspect. Never estimate a billed cost. Write a JSON file at `submission/run-receipt.json` and include the identical JSON in your final response under the label `BENCHMARK_RUN_RECEIPT`. Use `null` for unavailable values and explain each unavailable value. Use the exact task ID shown below:

```json
{
  "schema_version": 1,
  "task_id": "review.python-security-defect.v1",
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
