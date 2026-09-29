"""T04 - Forense de logs: 19 preguntas con definición exacta sobre un log ruidoso de 1,5k a 60k líneas."""
from __future__ import annotations

import math
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
from suite_lib import Report, fail_report, read_json, rng, write_json  # noqa: E402

ID = "t04_log_forensics"
TITLE = "Forense de logs (análisis de datos a escala)"
LEVELS = (1, 2, 3)
DELIVERABLES = ["answers.json"]
NEEDS = "Ejecutar código Python es prácticamente imprescindible a partir del nivel 2."
SIZES = {1: (1500, 40, 1), 2: (12000, 300, 3), 3: (60000, 1500, 7)}  # registros ≈, usuarios, días

ENDPOINTS = [  # svc, method, path, latencia base ms, peso
    ("auth", "POST", "/login", 120, 6), ("auth", "POST", "/token/refresh", 40, 5), ("auth", "GET", "/users/me", 30, 8),
    ("api", "GET", "/orders", 80, 10), ("api", "GET", "/products", 60, 14), ("api", "POST", "/cart", 90, 7), ("api", "GET", "/cart", 45, 8),
    ("billing", "POST", "/checkout", 350, 4), ("billing", "POST", "/payments", 420, 3), ("billing", "GET", "/invoices", 150, 3),
    ("search", "GET", "/search", 200, 9), ("search", "GET", "/suggest", 25, 9),
    ("media", "POST", "/upload", 800, 2), ("media", "GET", "/thumb", 70, 5),
]
MSG = {"ok": ["ok", "served from cache", "completed", "accepted", "no changes"],
       "warn": ["invalid parameter", "resource not found", "rate limited", 'client sent malformed "payload"'],
       "err": ["upstream timeout after 3 retries", "connection reset by peer", 'failed to parse "response" body', "database unavailable"]}
OFFSETS = [("Z", 0), ("+01:00", 60), ("+02:00", 120), ("-05:00", -300), ("+05:30", 330)]
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

TASK = """# Requirements — Log Forensics

## Introduction

A platform team exported the application log of a multi-service system (`input/app.log`, {lines} lines) and needs precise answers about it. There is no tooling provided:
you decide how to analyse the log. **Every answer has an exact definition below; there is a single correct value for each.** The log is noisy on purpose (mixed time zones,
out-of-order lines, duplicates, stack traces, comments and corrupt lines).

## Log format (normative)

A **record line** looks like this:

```
2026-03-14T08:15:22.123+01:00 [ERROR] svc=api req=r0001234 user=u0007 method=GET path=/orders status=503 dur_ms=245 msg="upstream timeout, \\"retry\\" failed" retry=1
```
- It starts with an ISO-8601 timestamp with **exactly three fractional digits** and a UTC offset (`Z` or `±HH:MM`), then a space, then `[INFO]`, `[WARN]` or `[ERROR]`, then a space, then the rest.
- The rest is a sequence of space-separated `key=value` pairs, in **any order**. A value is either a run of non-space characters, or a double-quoted string in which `\\"` stands for a literal quote (quoted values may contain spaces and `=`).
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
| `q06` | 95th percentile (nearest-rank) of `dur_ms` over records with `path == "{path}"` (int) |
| `q07` | Median (nearest-rank, p=50) of `dur_ms` per `svc` (object `svc → int`) |
| `q08` | The 3 most frequent `path` values as `[[path, count], …]`, ordered by count descending, ties by path ascending (list) |
| `q09` | The UTC minute with the most records: `{{"minute": "YYYY-MM-DDTHH:MM", "count": int}}`; ties → earliest minute |
| `q10` | Total number of **sessions**: for each user, sort that user's records by instant; a new session starts at the first record and whenever the gap to the previous record of that user is **strictly greater than 30 minutes (1 800 000 ms)** (int) |
| `q11` | The longest session by duration (last instant − first instant): `{{"user": id, "seconds": int}}` where `seconds` = duration in ms divided by 1000, rounded down; ties → smallest `user` string, then earliest start |
| `q12` | Earliest instant `t` (string `YYYY-MM-DDTHH:MM:SS.mmmZ`, UTC) of a server-error record such that at least **10** server-error records have an instant in the closed interval `[t, t + 60 000 ms]`; `null` if none |
| `q13` | Number of distinct `req` values that appear in 2 or more records of *R* (int) |
| `q14` | Number of records whose `dur_ms` is **strictly greater than 3 × the median (nearest-rank, p=50) `dur_ms` of the records with the same `path`** (int) |
| `q15` | For every service with at least 100 records: its server-error rate in **basis points**, rounded half up: `(2·e·10000 + n) // (2·n)` with `e` = server errors, `n` = records (object `svc → int`) |
| `q16` | `{{"first": ts, "last": ts}}`: earliest and latest instant in *R*, formatted `YYYY-MM-DDTHH:MM:SS.mmmZ` (UTC) |
| `q17` | The UTC hour of day (0–23), aggregated over all days, with the most `ERROR`-level records; ties → smallest hour (int) |
| `q18` | The user with the most distinct `path` values: `{{"user": id, "distinct_paths": int}}`; ties → smallest `user` string |
| `q19` | Sum of `dur_ms` over records with `svc == "{svc}"` and `status == 200` (int) |

### Requirement 2 — Output contract

#### Acceptance Criteria
1. THE deliverable SHALL be `answers.json`: one JSON object whose keys are `q01` … `q19` and whose values have exactly the types shown above (objects with exactly the listed keys).
2. Object keys of the `svc → int` answers are the service names as they appear in the log.
3. Each answer is scored independently as correct or incorrect (exact equality). A missing or malformed answer is incorrect.

### Requirement 3 — Environment, dependencies, safety
1. If you write code: Python 3.10+, standard library only; no network. Do not modify `input/app.log`.

## Deliverables and provided files
Deliver `answer/answers.json`. Provided (read-only): `input/app.log`.
"""


def to_iso(ms: int) -> str:
    dt = EPOCH + timedelta(milliseconds=ms)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def nearest_rank(vals, p):
    s = sorted(vals)
    return s[(p * len(s) + 99) // 100 - 1]


def answers_from_records(recs: list[dict], path_q: str, svc_q: str) -> dict:
    """Respuestas a partir de registros estructurados (dedupe ya aplicado). Definiciones = las del TASK.md."""
    a = {"q01": len(recs), "q02": sum(1 for r in recs if r["level"] == "ERROR")}
    per_svc = Counter(r["svc"] for r in recs)
    a["q03"] = dict(sorted(per_svc.items()))
    a["q04"] = len({r["user"] for r in recs})
    is5 = lambda r: r["status"] >= 500  # noqa: E731
    a["q05"] = sum(1 for r in recs if is5(r))
    a["q06"] = nearest_rank([r["dur_ms"] for r in recs if r["path"] == path_q], 95)
    by_svc = defaultdict(list)
    by_path = defaultdict(list)
    for r in recs:
        by_svc[r["svc"]].append(r["dur_ms"])
        by_path[r["path"]].append(r["dur_ms"])
    a["q07"] = {k: nearest_rank(v, 50) for k, v in sorted(by_svc.items())}
    pc = Counter(r["path"] for r in recs)
    a["q08"] = [[p, c] for p, c in sorted(pc.items(), key=lambda kv: (-kv[1], kv[0]))[:3]]
    mins = Counter(r["t"] // 60000 for r in recs)
    m, c = min(mins.items(), key=lambda kv: (-kv[1], kv[0]))
    a["q09"] = {"minute": to_iso(m * 60000)[:16], "count": c}
    users = defaultdict(list)
    for r in recs:
        users[r["user"]].append(r["t"])
    sessions, best = 0, None
    for u, ts in sorted(users.items()):
        ts.sort()
        start = prev = ts[0]
        sessions += 1
        spans = []
        for t in ts[1:]:
            if t - prev > 1_800_000:
                sessions += 1
                spans.append((prev - start, start))
                start = t
            prev = t
        spans.append((prev - start, start))
        for dur, st in spans:
            key = (-dur, u, st)
            if best is None or key < best:
                best = key
    a["q10"] = sessions
    a["q11"] = {"user": best[1], "seconds": (-best[0]) // 1000}
    e5 = sorted(r["t"] for r in recs if is5(r))
    a["q12"] = None
    j = 0
    for i, t in enumerate(e5):
        while j < len(e5) and e5[j] <= t + 60000:
            j += 1
        if j - i >= 10:
            a["q12"] = to_iso(t)
            break
    reqc = Counter(r["req"] for r in recs)
    a["q13"] = sum(1 for v in reqc.values() if v >= 2)
    med = {p: nearest_rank(v, 50) for p, v in by_path.items()}
    a["q14"] = sum(1 for r in recs if r["dur_ms"] > 3 * med[r["path"]])
    err_by = Counter(r["svc"] for r in recs if is5(r))
    a["q15"] = {s: (2 * err_by[s] * 10000 + n) // (2 * n) for s, n in sorted(per_svc.items()) if n >= 100}
    a["q16"] = {"first": to_iso(min(r["t"] for r in recs)), "last": to_iso(max(r["t"] for r in recs))}
    hours = Counter((r["t"] // 3_600_000) % 24 for r in recs if r["level"] == "ERROR")
    a["q17"] = min(hours.items(), key=lambda kv: (-kv[1], kv[0]))[0]
    dp = defaultdict(set)
    for r in recs:
        dp[r["user"]].add(r["path"])
    u, n = min(dp.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    a["q18"] = {"user": u, "distinct_paths": len(n)}
    a["q19"] = sum(r["dur_ms"] for r in recs if r["svc"] == svc_q and r["status"] == 200)
    return a


def generate(tool: Path, hidden: Path, seed: int, level: int) -> None:
    r = rng(seed, ID)
    N, U, days = SIZES[level]
    start0 = int((datetime(2026, 3, 14, tzinfo=timezone.utc) - EPOCH).total_seconds() * 1000)
    users = [f"u{i:04d}" for i in range(1, U + 1)]
    weights = [e[4] for e in ENDPOINTS]
    recs: list[dict] = []
    counter = [0]

    def new_req():
        counter[0] += 1
        return f"r{counter[0]:07d}"

    def make(u, t, force5=False, req=None):
        svc, method, path, base, _ = r.choices(ENDPOINTS, weights)[0]
        x = r.random()
        if force5 or x > 0.965:
            status = r.choice([500, 502, 503, 503])
        elif x > 0.90:
            status = r.choice([400, 404, 429])
        elif method == "POST":
            status = 201 if x < 0.4 else 200
        else:
            status = 304 if x < 0.05 else 200
        dur = max(1, int(r.lognormvariate(0, 0.55) * base))
        if status >= 500:
            dur = int(dur * r.uniform(1.5, 6))
        level = "ERROR" if status >= 500 else "WARN" if status >= 400 else "INFO"
        kind = "err" if status >= 500 else "warn" if status >= 400 else "ok"
        return {"t": t, "svc": svc, "level": level, "req": req or new_req(), "user": u, "method": method, "path": path,
                "status": status, "dur_ms": dur, "msg": r.choice(MSG[kind])}

    per_user = max(3, N // U)
    for u in users:
        t = start0 + r.randrange(0, days * 86_400_000)
        for _ in range(r.randint(max(1, per_user // 2), per_user * 3 // 2)):
            rec = make(u, t)
            recs.append(rec)
            if rec["status"] >= 500 and r.random() < 0.35:  # reintentos: misma req
                tt = t
                for k in range(r.randint(1, 2)):
                    tt += r.randint(200, 3000)
                    rr = make(u, tt, force5=r.random() < 0.3, req=rec["req"])
                    rr.update({"retry": k + 1, "path": rec["path"], "svc": rec["svc"], "method": rec["method"]})
                    recs.append(rr)
            g = r.random()
            t += r.randint(1_000, 600_000) if g < 0.92 else r.randint(1_800_001, 7_200_000) if g < 0.98 else 1_800_000
    span = days * 86_400_000
    for _ in range(1 + level):  # ráfagas que cumplen el umbral
        T = start0 + r.randrange(0, span)
        for _ in range(r.randint(14, 25)):
            recs.append(make(r.choice(users), T + r.randint(0, 55_000), force5=True))
    for _ in range(2):  # señuelos: 9 errores en <60 s
        T = start0 + r.randrange(0, span)
        for _ in range(9):
            recs.append(make(r.choice(users), T + r.randint(0, 50_000), force5=True))

    recs.sort(key=lambda x: (x["t"], x["req"], x.get("retry", 0)))

    def render(rec):
        label, off = r.choices(OFFSETS, [60, 15, 10, 10, 5])[0]
        dt = EPOCH + timedelta(milliseconds=rec["t"]) + timedelta(minutes=off)
        ts = dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}" + label
        pairs = [("svc", rec["svc"]), ("req", rec["req"]), ("user", rec["user"]), ("method", rec["method"]), ("path", rec["path"]),
                 ("status", str(rec["status"])), ("dur_ms", str(rec["dur_ms"])), ("msg", '"' + rec["msg"].replace('"', '\\"') + '"')]
        if "retry" in rec:
            pairs.append(("retry", str(rec["retry"])))
        r.shuffle(pairs)
        return f"{ts} [{rec['level']}] " + " ".join(f"{k}={v}" for k, v in pairs)

    blocks = []
    for rec in recs:
        block = [render(rec)]
        if rec["level"] == "ERROR" and r.random() < 0.3:
            block += [f"    at com.example.{r.choice(['Handler', 'Pool', 'Client'])}.run({r.choice(['A', 'B'])}.java:{r.randint(10, 400)})" for _ in range(r.randint(2, 4))]
        blocks.append(block)
    for _ in range(len(blocks) // 25):  # desorden local
        i = r.randrange(len(blocks))
        j = min(len(blocks) - 1, max(0, i + r.randint(-200, 200)))
        blocks[i], blocks[j] = blocks[j], blocks[i]
    for _ in range(max(2, len(blocks) // 100)):  # duplicados exactos posteriores
        i = r.randrange(len(blocks) - 1)
        blocks.insert(r.randrange(i + 1, len(blocks) + 1), [blocks[i][0]])
    lines = []
    for b in blocks:
        lines += b
        x = r.random()
        if x < 0.003:
            lines.append(f"# logrotate: rotated at block {r.randint(1, 999)}")
        elif x < 0.006:
            lines.append(r.choice(["--- service restart ---", "", "Segmentation noise 0x7f2c", "2026-13-40T99:99:99.000Z [INFO] impossible timestamp"]))
    (tool / "input").mkdir(parents=True, exist_ok=True)
    (tool / "input" / "app.log").write_text("\n".join(lines) + "\n", encoding="utf-8")

    cnt = Counter(x["path"] for x in recs)
    path_q = sorted(p for p, c in cnt.items() if c >= 30)[r.randrange(len([p for p, c in cnt.items() if c >= 30]))]
    svc_q = r.choice(sorted({x["svc"] for x in recs}))
    (tool / "TASK.md").write_text(TASK.format(lines=len(lines), path=path_q, svc=svc_q), encoding="utf-8")
    write_json(hidden / "expected.json", answers_from_records(recs, path_q, svc_q))


def evaluate(answer: Path, hidden: Path) -> dict:
    f = answer / "answers.json"
    if not f.exists():
        return fail_report("falta answers.json")
    exp = read_json(hidden / "expected.json")
    try:
        got = read_json(f)
        assert isinstance(got, dict)
    except Exception as e:  # noqa: BLE001
        return fail_report(f"JSON inválido: {type(e).__name__}")
    rep = Report()
    for k in sorted(exp):
        ok = k in got and got[k] == exp[k] and _same_types(got[k], exp[k])
        rep.add(k, ok, 1, "" if ok else f"esperado={str(exp[k])[:80]} obtenido={str(got.get(k))[:80]}")
    return rep.result()


def _same_types(a, b) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(_same_types(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return isinstance(b, list) and len(a) == len(b) and all(_same_types(x, y) for x, y in zip(a, b))
    return type(a) is type(b)


# ---------------------------------------------------------------- referencia: parsea el TEXTO (independiente del generador)
LINE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})\.(\d{3})(Z|[+-]\d{2}:\d{2}) \[(INFO|WARN|ERROR)\] (.*)$")
KV = re.compile(r'(\w+)=("(?:[^"\\]|\\.)*"|\S+)')


def parse_log(text: str) -> list[dict]:
    seen, recs = set(), []
    for line in text.split("\n"):
        m = LINE.match(line)
        if not m or line in seen:
            continue
        y, mo, d, h, mi, s, ms, tz, level, rest = m.groups()
        try:
            dt = datetime(int(y), int(mo), int(d), int(h), int(mi), int(s))
        except ValueError:
            continue
        off = 0 if tz == "Z" else (1 if tz[0] == "+" else -1) * (int(tz[1:3]) * 60 + int(tz[4:6]))
        t = int((dt - datetime(1970, 1, 1)).total_seconds()) * 1000 + int(ms) - off * 60000
        kv = {k: (v[1:-1].replace('\\"', '"') if v.startswith('"') else v) for k, v in KV.findall(rest)}
        if not all(k in kv for k in ("svc", "req", "user", "method", "path", "status", "dur_ms", "msg")):
            continue
        seen.add(line)
        recs.append({"t": t, "level": level, "svc": kv["svc"], "req": kv["req"], "user": kv["user"], "path": kv["path"],
                     "status": int(kv["status"]), "dur_ms": int(kv["dur_ms"])})
    return recs


def reference(tool: Path, hidden: Path, answer: Path) -> None:
    text = (tool / "input" / "app.log").read_text(encoding="utf-8")
    task = (tool / "TASK.md").read_text(encoding="utf-8")
    path_q = re.search(r'`path == "([^"]+)"`', task).group(1)
    svc_q = re.search(r'`svc == "([^"]+)"` and `status == 200`', task).group(1)
    answer.mkdir(parents=True, exist_ok=True)
    write_json(answer / "answers.json", answers_from_records(parse_log(text), path_q, svc_q))
