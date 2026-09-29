Convert inputs/portrait.pgm to ASCII art and write submission/art.txt as UTF-8. Use this exact ramp from darkest to lightest: @%#*+=-:. (space). Map each pixel with index = min(9, pixel * 9 // (maximum + 1)); preserve image width and height, trimming trailing spaces on each line. No title, Markdown fences, or commentary in art.txt.

## Fixed task package

Read every file listed in `context_files` in `task.json`. The same package includes all task inputs and any starter files. Work from the task workspace, use relative paths, and write deliverables under `submission/`.

## Required usage receipt

Report only usage and cost you can actually inspect. Never estimate a billed cost. Write a JSON file at `submission/run-receipt.json` and include the identical JSON in your final response under the label `BENCHMARK_RUN_RECEIPT`. Use `null` for unavailable values and explain each unavailable value. Use the exact task ID shown below:

```json
{
  "schema_version": 1,
  "task_id": "oneshot.ascii-pgm.v1",
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
