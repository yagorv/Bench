import argparse
import csv
import json
import sys

from formats_common import norm


def fmt(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() else repr(v)
    return str(v)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--template", default="template.csv")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("-o", "--output", required=True)
    args = ap.parse_args(argv)
    try:
        with open(args.template, newline="", encoding="utf-8-sig") as f:
            header = next(csv.reader(f))
        with open(args.input, encoding="utf-8-sig") as f:
            records = json.load(f)
        assert isinstance(records, list)
    except (OSError, ValueError, StopIteration, AssertionError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    by_norm = {norm(h): h for h in header}
    rows, seen, unknown = [], set(), False
    for rec in records:
        row = {h: "" for h in header}
        for k, v in rec.items():
            h = k if k in row else by_norm.get(norm(k))
            if h is None:
                unknown = True
                if k not in seen:
                    seen.add(k)
                    print(f'WARNING: unknown field "{k}" ignored', file=sys.stderr)
                continue
            row[h] = fmt(v)
        rows.append([row[h] for h in header])
    if unknown and args.strict:
        return 2
    out = sys.stdout if args.output == "-" else open(args.output, "w", encoding="utf-8", newline="")
    try:
        w = csv.writer(out, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    finally:
        if out is not sys.stdout:
            out.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
