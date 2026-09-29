Review every Python module under inputs/ as if reviewing a pull request. Return submission/findings.json with a findings array; every finding must contain rule_id, path, line, severity, and explanation. Report only the four seeded defects, exactly once each, with accurate one-based line numbers. Do not modify source files. The evaluator checks complete defect coverage and rejects extra findings.

The harness appends the required machine-readable usage receipt instructions. Include submission/run-receipt.json and report only usage you can actually inspect.
