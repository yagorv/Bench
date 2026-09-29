# Requirements — Log Forensics

## Introduction

A platform team exported the application log of a multi-service system (`input/app.log`, 1613 lines) and needs precise answers about it. There is no tooling provided:
you decide how to analyse the log. **Every answer has an exact definition below; there is a single correct value for each.** The log is noisy on purpose (mixed time zones,
out-of-order lines, duplicates, stack traces, comments and corrupt lines).

## Log format (normative)

A **record line** looks like this:

```
2026-03-14T08:15:22.123+01:00 [ERROR] svc=api req=r0001234 user=u0007 method=GET path=/orders status=503 dur_ms=245 msg="upstream timeout, \"retry\" failed" retry=1
```
- It starts with an ISO-8601 timestamp with **exactly three fractional digits** and a UTC offset (`Z` or `±HH:MM`), then a space, then `[INFO]`, `[WARN]` or `[ERROR]`, then a space, then the rest.
- The rest is a sequence of space-separated `key=value` pairs, in **any order**. A value is either a run of non-space characters, or a double-quoted string in which `\"` stands for a literal quote (quoted values may contain spaces and `=`).
- Every record has `svc`, `req`, `user`, `method`, `path`, `status` (integer), `dur_ms` (integer) and `msg`. `retry` is optional and irrelevant to the questions.
- **Every other line is not a record and must be ignored**: stack-trace lines (start with whitespace), comments (start with `#`), blank lines and any line that does not start with a valid timestamp as above.
- **Duplicates**: if a record line appears more than once with byte-identical content, only its **first** occurrence counts.
- Lines are **not** in chronological order. The instant of a record is its timestamp converted to UTC (millisecond precision). "Minute", "hour" and "day" always mean **UTC**.
- `level` means the bracketed level of the line. A "server error" is a record with `status >= 500` (independent of its level).

## Requirements

### Requirement 1 — Answer the 19 questions

**User Story:** As an SRE, I want exact answers to these questions, so I can write the incident report without re-reading the log.

#### Acceptance Criteria
Let *R* be the set of records after ignoring non-record lines and removing duplicates. **Nearest-rank percentile**: sort the values ascending; for `n` values and percentile `p`, the result is the value at 1-based rank `ceil(p·n/100)` (integer arithmetic: `(p·n + 99) // 100`).

| Key | Answer (JSON type) |
|---|---|
| `q01` | Number of records in *R* (int) |
| `q02` | Number of records with level `ERROR` (int) |
| `q03` | Number of records per `svc`, for every service present (object `svc → int`) |
| `q04` | Number of distinct `user` values (int) |
| `q05` | Number of server errors (int) |
| `q06` | 95th percentile (nearest-rank) of `dur_ms` over records with `path == "/checkout"` (int) |
| `q07` | Median (nearest-rank, p=50) of `dur_ms` per `svc` (object `svc → int`) |
| `q08` | The 3 most frequent `path` values as `[[path, count], …]`, ordered by count descending, ties by path ascending (list) |
| `q09` | The UTC minute with the most records: `{"minute": "YYYY-MM-DDTHH:MM", "count": int}`; ties → earliest minute |
| `q10` | Total number of **sessions**: for each user, sort that user's records by instant; a new session starts at the first record and whenever the gap to the previous record of that user is **strictly greater than 30 minutes (1 800 000 ms)** (int) |
| `q11` | The longest session by duration (last instant − first instant): `{"user": id, "seconds": int}` where `seconds` = duration in ms divided by 1000, rounded down; ties → smallest `user` string, then earliest start |
| `q12` | Earliest instant `t` (string `YYYY-MM-DDTHH:MM:SS.mmmZ`, UTC) of a server-error record such that at least **10** server-error records have an instant in the closed interval `[t, t + 60 000 ms]`; `null` if none |
| `q13` | Number of distinct `req` values that appear in 2 or more records of *R* (int) |
| `q14` | Number of records whose `dur_ms` is **strictly greater than 3 × the median (nearest-rank, p=50) `dur_ms` of the records with the same `path`** (int) |
| `q15` | For every service with at least 100 records: its server-error rate in **basis points**, rounded half up: `(2·e·10000 + n) // (2·n)` with `e` = server errors, `n` = records (object `svc → int`) |
| `q16` | `{"first": ts, "last": ts}`: earliest and latest instant in *R*, formatted `YYYY-MM-DDTHH:MM:SS.mmmZ` (UTC) |
| `q17` | The UTC hour of day (0–23), aggregated over all days, with the most `ERROR`-level records; ties → smallest hour (int) |
| `q18` | The user with the most distinct `path` values: `{"user": id, "distinct_paths": int}`; ties → smallest `user` string |
| `q19` | Sum of `dur_ms` over records with `svc == "billing"` and `status == 200` (int) |

### Requirement 2 — Output contract

#### Acceptance Criteria
1. THE deliverable SHALL be `answers.json`: one JSON object whose keys are `q01` … `q19` and whose values have exactly the types shown above (objects with exactly the listed keys).
2. Object keys of the `svc → int` answers are the service names as they appear in the log.
3. Each answer is scored independently as correct or incorrect (exact equality). A missing or malformed answer is incorrect.

### Requirement 3 — Environment, dependencies, safety
1. If you write code: Python 3.10+, standard library only; no network. Do not modify `input/app.log`.

## Deliverables and provided files
Deliver `answer/answers.json`. Provided (read-only): `input/app.log`.
