# Workflow scheduler contract

Implement a deterministic discrete-time scheduler for the JSON workflows in `inputs/workflows.json`. Do not use third-party libraries, wall-clock time, threads, or randomness. All timestamps are integer time units starting at zero; durations and retry delays are simulated, never slept.

Each workflow has `workflow_id` (non-empty string), positive integer `workers`, and a `tasks` array. Every task has a unique non-empty `id`, positive integer `duration`, `depends_on` (array of other task IDs, default empty), non-negative integer `fail_attempts` (default zero), and positive integer `max_attempts` (default one). The first `fail_attempts` attempts fail; later attempts succeed. Reject booleans where integers are required, duplicate IDs/dependencies, missing dependencies, self-dependencies, cycles, invalid types, and `fail_attempts > max_attempts` with a non-zero exit and a useful error.

## Scheduling rules

- A task is eligible when all dependencies succeeded and its retry delay has expired. At a given time, launch eligible tasks in lexicographic task-ID order until all worker slots are occupied.
- Running an attempt consumes one worker for exactly `duration` simulated time units. At a timestamp, first process all finishing attempts in task-ID order, then propagate skipped tasks in task-ID order, then launch eligible work in task-ID order.
- An attempt among the first `fail_attempts` ends in a retry if attempts remain. The retry becomes eligible after `2 ** (attempt_number - 1)` time units from that attempt's finish. If no attempts remain, mark the task failed permanently.
- Any pending task with a failed or skipped dependency is skipped at the current time. Skipping propagates through descendants. Independent work continues.
- Successful tasks do not rerun. The workflow ends when all tasks are terminal. Input order must not affect scheduling or result content.

## Output contract

The CLI accepts `python -m flowbench INPUT.json --output OUTPUT.json`. The input is an array of workflows; output is an array in input-workflow order. Each result contains `workflow_id`, `status` (`succeeded` if every task succeeds, otherwise `failed`), `finished_at` (latest terminal time), `events`, and `tasks`.

Events are objects with exactly `time`, `event`, `task_id`, and `attempt`. Event types are `start`, `retry`, `succeeded`, `failed`, and `skipped`. `start` occurs when an attempt begins. `retry` occurs when a failed attempt finishes and includes its attempt number; the retry delay is implied by the contract. `succeeded` and `failed` occur when a task becomes terminal. `skipped` uses attempt 0. Events are ordered by simulation rules above.

Task result objects have exactly `task_id`, `state` (`succeeded`, `failed`, or `skipped`), `attempts`, `started_at`, and `finished_at`. `started_at` is the first start time, or null if never started. Task result rows are sorted by ID. The output JSON must be stable and contain no machine timestamps or nondeterministic fields.

Implement the solution as a maintainable package under `submission/flowbench/` with a CLI entry point. Add any tests you find useful, but the hidden evaluator uses additional workflows and invalid-input cases. Aim to handle the complete contract rather than only the supplied examples.
