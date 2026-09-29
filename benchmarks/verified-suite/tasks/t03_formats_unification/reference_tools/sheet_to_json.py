import argparse
import csv
import io
import sys
from collections import Counter

from formats_common import (COLUMNS, GROUPED, HEADER_LOOKUP, SUMMARY_KEYWORDS, blank_record, convert, detect_currency, emit, norm, read_text)


def detect_delimiter(text):
    lines = [l for l in text.replace("\r\n", "\n").split("\n") if l.strip()][:30]
    best, best_score = ",", (0, 0)
    for cand in (",", ";", "\t"):
        counts = [len(r) for r in csv.reader(lines, delimiter=cand) if len(r) >= 4]
        if not counts:
            continue
        freq = Counter(counts)
        m = max(freq.items(), key=lambda kv: (kv[1], kv[0]))
        score = (m[1], m[0])
        if score > best_score:
            best, best_score = cand, score
    return best


def process(text, path, warn, show_mapping):
    rows = list(csv.reader(io.StringIO(text, newline=""), delimiter=detect_delimiter(text)))
    header_idx = None
    for i, row in enumerate(rows[:30]):
        if sum(1 for c in row if norm(c) in HEADER_LOOKUP) >= 4:
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("no header row found")
    mapping = {}
    for idx, cell in enumerate(rows[header_idx]):
        col = HEADER_LOOKUP.get(norm(cell))
        if col and col not in mapping.values():
            mapping[idx] = col
    if show_mapping:
        print(f"HEADER_ROW {header_idx}", file=sys.stderr)
        for idx in sorted(mapping):
            print(f"COL {idx} -> {mapping[idx]}", file=sys.stderr)
    col_idx = {c: i for i, c in mapping.items()}
    recs, skipped, last = [], 0, {}
    for rn, row in enumerate(rows[header_idx + 1:], start=header_idx + 2):
        if not any(c.strip() for c in row):
            continue
        get = lambda col: (row[col_idx[col]].strip() if col in col_idx and col_idx[col] < len(row) else "")  # noqa: E731
        if any(norm(c) in SUMMARY_KEYWORDS for c in row):  # SUMMARY
            skipped += 1
            continue
        if get("TOTAL INVOICE AMOUNT") and not get("INVOICE REF") and not get("SELLER"):  # SUMMARY
            skipped += 1
            continue
        raw = {c: get(c) for c in COLUMNS}
        for col in GROUPED:  # FFILL
            if raw[col]:
                last[col] = raw[col]
            elif col in last:
                raw[col] = last[col]
        if not raw["INVOICE REF"]:
            skipped += 1
            continue
        rec = blank_record()
        for col in COLUMNS:
            rec[col] = convert(col, raw[col], f"{path}:{rn}", warn)
        if not raw["CURRENCY"]:
            rec["CURRENCY"] = detect_currency(raw["TOTAL INVOICE AMOUNT"]) or detect_currency(raw["TOTAL NET VALUE"])
        recs.append(rec)
    return recs, skipped


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("-o", "--output")
    ap.add_argument("--append", action="store_true")
    ap.add_argument("--show-mapping", action="store_true")
    args = ap.parse_args(argv)
    warn = lambda m: print(m, file=sys.stderr)  # noqa: E731
    records, skipped = [], 0
    for path in args.files:
        try:
            text = read_text(path)
            r, s = process(text, path, warn, args.show_mapping)
        except (OSError, ValueError) as e:
            print(f"ERROR: {path}: {e}", file=sys.stderr)
            return 2
        records += r
        skipped += s
    rc = emit(records, args.output, args.append)
    if rc == 0:
        print(f"SUMMARY files={len(args.files)} records={len(records)} skipped={skipped}", file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
