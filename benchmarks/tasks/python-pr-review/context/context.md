# Fixed task context
Review the four supplied modules for real correctness or security defects. Use these exact defect identifiers and locations in findings:
- `path-traversal`, `inputs/cache.py`, line 7, severity `high`: caller-controlled path can escape the cache directory.
- `weak-password-hash`, `inputs/auth.py`, line 4, severity `high`: SHA-1 is unsuitable for password storage/verification.
- `float-money-rounding`, `inputs/payments.py`, line 2, severity `medium`: binary floating-point arithmetic can produce inaccurate currency totals; use decimal arithmetic.
- `shell-command-injection`, `inputs/parser.py`, line 5, severity `high`: a shell command includes untrusted path text.
Return exactly these four findings, no duplicates or unrelated notes as findings. Explanation text may be concise.
