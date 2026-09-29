Create submission/quarterly-sales.xlsx from inputs/sales.csv. Include sheets named Transactions and Summary in that order. Transactions must contain all input rows, the header row, and freeze its header row. Add a revenue column in E with quantity × unit_price for each transaction. Summary must contain total revenue in B2 using a spreadsheet formula (SUM over Transactions revenue values). The evaluator checks required headers and row values, formula, sheet names, and frozen header.

## Fixed task package

Read every file listed in `context_files` in `task.json`. The same package includes all task inputs and any starter files. Work from the task workspace, use relative paths, and write deliverables under `submission/`.

## Required usage receipt

Report only usage and cost you can actually inspect. Never estimate a billed cost. Write a JSON file at `submission/run-receipt.json` and include the identical JSON in your final response under the label `BENCHMARK_RUN_RECEIPT`. Use `null` for unavailable values and explain each unavailable value. Use the exact task ID shown below:

```json
{
  "schema_version": 1,
  "task_id": "oneshot.xlsx-sales-report.v1",
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
