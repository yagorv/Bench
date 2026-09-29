# Contributing benchmark tasks

Every task must have a stable ID, a pinned starting revision or dataset manifest, explicit limits, and machine-checkable success criteria. Keep evaluator-only tests and expected answers out of the agent-visible task prompt. Record all changes to task definitions in version control.

One-shot tasks must pin the exact prompt, reference attachments, requested file format, output constraints, and available tool capabilities. Structured spreadsheet tasks should include a machine-readable workbook contract and hidden assertions. Image and video tasks must identify technical validity checks and any perceptual or human scoring rubric separately.

When adding a task, include a baseline that fails the evaluator and a reference solution that passes it. Verify that the evaluator rejects at least one plausible incorrect solution. Document any score that relies on human review and use reviewers who do not know which agent produced the change.

Benchmark submissions should include the commit, task IDs, agent and model versions, configuration, environment image digest, run logs, raw metrics, and provider-reported costs or a clear note that cost is unavailable.
