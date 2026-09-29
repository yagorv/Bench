# Android task suite roadmap

Each task will use a pinned repository snapshot and a separate evaluator. Keep task prompts and evaluator-only assertions in separate files.

- Build configuration failure: repair Gradle or manifest configuration with dependency versions pinned.
- Functional bug: reproduce from a deterministic test, then verify the fix and regression coverage.
- Pull request review: inject known defects and score findings by defect coverage, severity, location accuracy, and false positives.
- Feature request: validate behavior through hidden instrumentation or unit tests plus existing regression tests.
- Performance regression: compare a fixed benchmark workload on a pinned emulator image and report runtime and memory separately.

Before publication, each task needs a clean baseline, a reference patch, hidden evaluator checks, a timeout, and a dry-run showing the baseline fails and the reference patch passes.
