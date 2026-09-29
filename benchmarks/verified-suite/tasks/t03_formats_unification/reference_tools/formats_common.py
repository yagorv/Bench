"""Shared module: column list, dictionaries and the N1-N5 helpers used by all three tools."""
import datetime
import json
import os
import re
import sys
import unicodedata

# __DICTS__

TEXT_LOOKUP = {lab: field for field, labs in TEXT_LABELS.items() for lab in labs}
HEADER_LOOKUP = {}
for _col, _syns in HEADER_SYNONYMS.items():
    for _s in _syns:
        HEADER_LOOKUP.setdefault(_s, _col)

_MONTHS = {}
for _i, _names in enumerate([
        ("january", "jan", "enero", "janvier"), ("february", "feb", "febrero", "fevrier"), ("march", "mar", "marzo", "mars"),
        ("april", "apr", "abril", "avril"), ("may", "mayo", "mai"), ("june", "jun", "junio", "juin"), ("july", "jul", "julio", "juillet"),
        ("august", "aug", "agosto", "aout"), ("september", "sep", "septiembre", "septembre"), ("october", "oct", "octubre", "octobre"),
        ("november", "nov", "noviembre", "novembre"), ("december", "dec", "diciembre", "decembre")], start=1):
    for _n in _names:
        _MONTHS[_n] = _i

_CUR_TOKENS = {"€": "EUR", "eur": "EUR", "euro": "EUR", "euros": "EUR", "$": "USD", "usd": "USD", "us dollar": "USD", "us dollars": "USD",
               "£": "GBP", "gbp": "GBP", "pound sterling": "GBP", "chf": "CHF", "swiss franc": "CHF"}


def norm(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


def clean_text(s):
    s = " ".join(str(s).split())
    return s or None


def parse_number(raw):
    s = raw.strip()
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg, s = True, s[1:-1]
    s = re.sub(r"(?i)euros?|usd|gbp|chf|eur|us dollars?|pound sterling|swiss francs?", "", s)
    s = re.sub(r"[€$£%'\s]", "", s)
    if s.startswith("-"):
        neg, s = True, s[1:]
    if not re.fullmatch(r"[0-9.,]+", s) or not re.search(r"[0-9]", s):
        raise ValueError(raw)
    if "." in s and "," in s:
        dec = "." if s.rfind(".") > s.rfind(",") else ","
        thou = "," if dec == "." else "."
        s = s.replace(thou, "").replace(dec, ".")
    else:
        sep = "." if "." in s else "," if "," in s else None
        if sep:
            if s.count(sep) > 1:
                s = s.replace(sep, "")
            else:
                head, tail = s.split(sep)
                if len(tail) == 3 and 1 <= len(head) <= 3 and head != "0":
                    s = head + tail
                else:
                    s = head + "." + tail
    if s.count(".") > 1:
        raise ValueError(raw)
    v = float(s)
    v = -v if neg else v
    return int(v) if v == int(v) else v


def parse_date(raw):
    s = raw.strip()
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        y, mo, d = map(int, m.groups())
    elif re.fullmatch(r"\d{1,2}[/.]\d{1,2}[/.]\d{4}", s):
        d, mo, y = map(int, re.split(r"[/.]", s))
    else:
        m = re.fullmatch(r"([^\W\d_]+)\.? (\d{1,2}), (\d{4})", s)
        if m:
            mo, d, y = _MONTHS.get(norm(m.group(1))), int(m.group(2)), int(m.group(3))
        else:
            m = re.fullmatch(r"(\d{1,2}) (?:de )?([^\W\d_]+)(?: de)? (\d{4})", s)
            if not m:
                raise ValueError(raw)
            d, mo, y = int(m.group(1)), _MONTHS.get(norm(m.group(2))), int(m.group(3))
        if mo is None:
            raise ValueError(raw)
    return datetime.date(y, mo, d).isoformat()


def parse_currency(raw):
    key = " ".join(raw.strip().casefold().split())
    if key not in _CUR_TOKENS:
        raise ValueError(raw)
    return _CUR_TOKENS[key]


def detect_currency(raw):
    s = raw.casefold()
    for sym, code in (("€", "EUR"), ("$", "USD"), ("£", "GBP")):
        if sym in s:
            return code
    for pat, code in ((r"\b(?:eur|euros?)\b", "EUR"), (r"\busd\b|\bus dollars?\b", "USD"), (r"\bgbp\b|\bpound sterling\b", "GBP"),
                      (r"\bchf\b|\bswiss francs?\b", "CHF")):
        if re.search(pat, s):
            return code
    return None


FIELD_PARSERS = {"TOTAL INVOICE AMOUNT": parse_number, "TOTAL NET VALUE": parse_number, "DISCOUNT PERCENTAGE": parse_number,
                 "MARGIN": parse_number, "ISSUE DATE": parse_date, "DUE DATE": parse_date, "CURRENCY": parse_currency}


def convert(column, raw, where, warn):
    """Apply N2-N5 to one raw value. Unparseable -> None + WARNING."""
    raw = " ".join(raw.split())
    if not raw:
        return None
    parser = FIELD_PARSERS.get(column)
    if parser is None:
        return clean_text(raw)
    try:
        return parser(raw)
    except ValueError:
        warn(f'WARNING: {where}: cannot parse {column} "{raw}"')
        return None


def blank_record():
    return {c: None for c in COLUMNS}


def read_text(path):
    with open(path, "rb") as f:
        data = f.read()
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("latin-1")
    return text


def emit(records, output, append):
    """Write the JSON array. Returns the exit code."""
    if output not in (None, "-") and append and os.path.exists(output):
        try:
            with open(output, encoding="utf-8") as f:
                existing = json.load(f)
            if not isinstance(existing, list):
                raise ValueError("not an array")
        except (ValueError, OSError):
            print(f"ERROR: append target {output} is not a JSON array", file=sys.stderr)
            return 3
        records = existing + records
    text = json.dumps(records, ensure_ascii=False, indent=2) + "\n"
    if output in (None, "-"):
        sys.stdout.buffer.write(text.encode("utf-8"))
        sys.stdout.flush()
    else:
        with open(output, "w", encoding="utf-8", newline="") as f:
            f.write(text)
    return 0
