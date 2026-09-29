import argparse
import re
import sys

from formats_common import (COLUMNS, TEXT_LOOKUP, blank_record, clean_text, convert, detect_currency, emit, norm, read_text)

LABEL_RE = re.compile(r"^\s*(?P<label>[^:.]+?)\s*(?::|\.{3,}|\s{2,})\s*(?P<value>\S.*?)\s*$")


def parse_block(lines, first_lineno, path, warn):
    seps = [i for i, l in enumerate(lines) if re.fullmatch(r"\s*-{5,}\s*", l)]
    table, goods = set(), None
    if len(seps) >= 2:
        a, b = seps[0], seps[1]
        table = set(range(a, b + 1))
        descs = [clean_text(re.split(r"\s{2,}", l.strip(), maxsplit=1)[0]) for l in lines[a + 2:b] if l.strip()]
        goods = "; ".join(d for d in descs if d) or None
    found = {}
    for i, l in enumerate(lines):
        if i in table:
            continue
        m = LABEL_RE.match(l)
        if not m:
            continue
        field = TEXT_LOOKUP.get(norm(m.group("label")))
        if field and field not in found:
            found[field] = (m.group("value").strip(), first_lineno + i)
    if "INVOICE REF" not in found:
        return None
    rec = blank_record()
    for field, (raw, ln) in found.items():
        rec[field] = convert(field, raw, f"{path}:{ln}", warn)
    if goods is not None and rec["GOODS SERVICES"] is None:
        rec["GOODS SERVICES"] = goods
    rec["CURRENCY"] = detect_currency(found.get("TOTAL INVOICE AMOUNT", ("", 0))[0]) or detect_currency(found.get("TOTAL NET VALUE", ("", 0))[0])
    return rec


def process(text, path, warn):
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks, cur, start = [], [], 1
    for i, l in enumerate(lines, start=1):
        if re.fullmatch(r"\s*={10,}\s*", l):
            blocks.append((start, cur))
            cur, start = [], i + 1
        else:
            cur.append(l)
    blocks.append((start, cur))
    recs, skipped = [], 0
    for first, blk in blocks:
        if not any(x.strip() for x in blk):
            continue
        rec = parse_block(blk, first, path, warn)
        if rec is None:
            skipped += 1
        else:
            recs.append(rec)
    return recs, skipped


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("-o", "--output")
    ap.add_argument("--append", action="store_true")
    args = ap.parse_args(argv)
    warn = lambda m: print(m, file=sys.stderr)  # noqa: E731
    records, skipped = [], 0
    for path in args.files:
        try:
            text = read_text(path)
        except OSError as e:
            print(f"ERROR: cannot read {path}: {e}", file=sys.stderr)
            return 2
        r, s = process(text, path, warn)
        records += r
        skipped += s
    rc = emit(records, args.output, args.append)
    if rc == 0:
        print(f"SUMMARY files={len(args.files)} records={len(records)} skipped={skipped}", file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
