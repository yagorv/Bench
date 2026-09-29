Implement submission/solution.py as a streaming CSV program. It must accept --input, --output, and --summary arguments. Input is inputs/events.csv. Trim and lowercase emails; reject malformed emails; keep the first valid row for each record_id; normalize event_time to UTC ISO-8601 seconds ending in Z; format amount to exactly two decimal places; sort by (event_time, record_id). Write cleaned.csv with columns record_id,email,event_time,amount and summary.json with integer keys input_rows,output_rows,rejected_rows,duplicate_rows. Do not read the entire input file into memory. The evaluator compares every output row and summary to a reference.

## Fixed task package

Read every file listed in `context_files` in `task.json`. The same package includes all task inputs and any starter files. Work from the task workspace, use relative paths, and write deliverables under `submission/`.
