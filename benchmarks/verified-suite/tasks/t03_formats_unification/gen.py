"""Generador de T03: registros verdad -> facturas de texto (familias A/B/C) y hojas CSV/TSV caóticas, con el JSON esperado."""
import csv
import io
from datetime import date, timedelta
from decimal import Decimal

from dicts import COLUMNS, GROUPED, HEADER_SYNONYMS, TEXT_LABELS, norm

Q2 = Decimal("0.01")
SYM = {"USD": "$", "EUR": "€", "GBP": "£"}
NAMES = {"USD": ["US Dollar", "US Dollars"], "EUR": ["Euro", "Euros"], "GBP": ["Pound Sterling"], "CHF": ["Swiss Franc"]}
MONTHS = {"en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
          "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
          "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]}
A1 = ["Acme", "Globex", "Initech", "Umbrella", "Hooli", "Stark", "Wayne", "Soylent", "Tyrell", "Cyberdyne", "Aperture", "Lumière", "Ibérica",
      "Norte", "Levante", "Cantábrica", "Andaluza", "Ribera", "Galaica", "Núñez"]
A2 = ["Supplies", "Logistics", "Trading", "Industries", "Systems", "Foods", "Textiles", "Energy", "Labs", "Motors"]
SUF = ["Ltd", "S.L.", "S.A.", "SARL", "GmbH", "Inc", "& Co, Ltd"]
GOODS = ["Steel bolts M8 (box of 100)", "Tornillos M8 (caja 100)", "Consulting services Q1", "Papel A4 80 g", "Licencia de software anual",
         "Maintenance contract", "Transport fee", "Cable HDMI 2 m", "Toner cartridge", "Servicios de limpieza", "Pièces détachées",
         "Formation équipe", "Alquiler de equipo", "Office chairs", "Gestión de residuos"]
DISPLAY = {
    "A": {"INVOICE REF": ["Invoice No", "Invoice Number", "Invoice Ref"], "ISSUE DATE": ["Invoice Date", "Issue Date", "Date of Issue"],
          "DUE DATE": ["Due Date", "Payment Due", "Payment Due Date"], "SELLER": ["Seller", "Supplier", "Vendor", "From"],
          "SELLER ID": ["Seller ID", "Supplier ID", "Seller VAT ID", "Supplier VAT ID"], "DEBTOR": ["Bill To", "Customer", "Buyer"],
          "DEBTOR ID": ["Customer ID", "Buyer ID", "Customer VAT ID"], "GOODS SERVICES": ["Description", "Goods", "Services"],
          "TOTAL NET VALUE": ["Subtotal", "Net", "Net Amount", "Net Total"], "DISCOUNT PERCENTAGE": ["Discount", "Discount Rate"],
          "TOTAL INVOICE AMOUNT": ["Total", "Total Due", "Amount Due", "Invoice Total"]},
    "B": {"INVOICE REF": ["Factura Nº", "Factura N°", "Número de factura"], "ISSUE DATE": ["Fecha de emisión", "Fecha factura"],
          "DUE DATE": ["Fecha de vencimiento", "Vencimiento"], "SELLER": ["Proveedor", "Emisor"], "SELLER ID": ["NIF proveedor", "NIF emisor"],
          "DEBTOR": ["Cliente", "Comprador"], "DEBTOR ID": ["NIF cliente", "NIF comprador"], "TOTAL NET VALUE": ["Base imponible"],
          "DISCOUNT PERCENTAGE": ["Descuento"], "TOTAL INVOICE AMOUNT": ["Total factura", "Importe total"]},
    "C": {"INVOICE REF": ["N° Facture", "Facture N°", "Numéro de facture"], "ISSUE DATE": ["Date de facture", "Date d'émission"],
          "DUE DATE": ["Échéance", "Date d'échéance"], "SELLER": ["Fournisseur"], "SELLER ID": ["TVA fournisseur"], "DEBTOR": ["Acheteur", "Client"],
          "DEBTOR ID": ["TVA client"], "TOTAL NET VALUE": ["Montant HT", "Total HT"], "DISCOUNT PERCENTAGE": ["Remise"],
          "TOTAL INVOICE AMOUNT": ["Montant TTC", "Total TTC"]},
}
for _fam, _d in DISPLAY.items():
    for _f, _vs in _d.items():
        for _v in _vs:
            assert norm(_v) in TEXT_LABELS[_f], (_fam, _f, _v)
ACCENTS = {"emision": "emisión", "descripcion": "descripción", "numero": "número"}
EXTRA_HEADERS = ["Notes", "Status", "Batch", "Row"]
META = ["Receivables extract", "Generated: 2026-03-14", "Prepared by: Finance Team", "Confidential - internal use", "Source: ERP export", "Period: 2024-Q1"]

CFG = {
    1: dict(n_txt=10, n_sheet=10, txt_inv=(1, 2), mixed=False, junk=0.0, bad=0.0, crlf=0.0, enc=False, groups=(1, 2), rows=(3, 6), drop=0.12,
            grouped=0.4, subtotals=0.0, blanks=0.0, meta=(0, 2), extras=(0, 1), delims=[",", ";"], amount_only=0.0),
    2: dict(n_txt=30, n_sheet=30, txt_inv=(1, 3), mixed=False, junk=0.0, bad=0.0, crlf=0.0, enc=False, groups=(2, 4), rows=(3, 8), drop=0.3,
            grouped=0.6, subtotals=0.6, blanks=0.05, meta=(0, 4), extras=(0, 2), delims=[",", ";", "\t"], amount_only=0.3),
    3: dict(n_txt=60, n_sheet=60, txt_inv=(1, 4), mixed=True, junk=0.25, bad=0.05, crlf=0.3, enc=True, groups=(2, 6), rows=(3, 12), drop=0.35,
            grouped=0.7, subtotals=0.8, blanks=0.08, meta=(0, 5), extras=(0, 3), delims=[",", ";", "\t"], amount_only=0.5),
}
SAMPLE_CFG = dict(CFG[1], n_txt=0, n_sheet=0)


def party(r):
    name = f"{r.choice(A1)} {r.choice(A2)} {r.choice(SUF)}"
    c = r.choice(["ES", "GB", "FR", "DE", "US"])
    digits = lambda n: "".join(str(r.randrange(10)) for _ in range(n))  # noqa: E731
    pid = {"ES": lambda: r.choice("ABCDEFGHJ") + digits(8), "GB": lambda: "GB" + digits(9), "FR": lambda: "FR" + digits(11),
           "DE": lambda: "DE" + digits(9), "US": lambda: "US-" + digits(9)}[c]()
    return name, pid


def noise(r, s):
    if r.random() < 0.15:
        s = "  " + s
    if r.random() < 0.15:
        s = s + "   "
    if r.random() < 0.10 and " " in s:
        i = s.index(" ")
        s = s[:i] + "   " + s[i + 1:]
    return s


def fmt_dec(d, dec, thou, places=2):
    w, f = f"{d:.{places}f}".split(".")
    if thou:
        w = f"{int(w):,}".replace(",", thou)
    return w + dec + f


def decorate(r, num, cur, style):
    sym = SYM.get(cur)
    if style == "prefix":
        return f"{sym}{num}" if sym else f"{cur} {num}"
    if style == "suffix_sym":
        return f"{num} {sym}" if sym else f"{num} {cur}"
    if style == "name":
        return f"{num} {r.choice(NAMES[cur])}"
    if style == "none":
        return num
    return f"{num} {cur}"


def pct_str(r, d, eu, sign):
    s = format(d.normalize(), "f")
    s = s.replace(".", ",") if eu else s
    return s + ({"": "", "%": "%", " %": " %"}[sign] if sign is not None else "")


def fmt_date(r, d, style):
    if style == "iso":
        return d.isoformat()
    if style == "dmy":
        return d.strftime("%d/%m/%Y")
    if style == "dmy_dot":
        return d.strftime("%d.%m.%Y")
    if style == "en_long":
        name = MONTHS["en"][d.month - 1]
        return f"{r.choice([name, name[:3]])} {d.day}, {d.year}"
    if style == "es_long":
        return f"{d.day} de {MONTHS['es'][d.month - 1]} de {d.year}"
    return f"{d.day} {MONTHS['fr'][d.month - 1]} {d.year}"


def num_json(d):
    return None if d is None else int(d) if d == d.to_integral_value() else float(d)


def to_json_record(t):
    out = {}
    for c in COLUMNS:
        v = t[c]
        out[c] = v.isoformat() if isinstance(v, date) else num_json(v) if isinstance(v, Decimal) else v
    return out


class Ctx:
    def __init__(self, r):
        self.r = r
        self.n = 0

    def ref(self, fam):
        self.n += 1
        y = self.r.choice([2023, 2024, 2025])
        return {"A": f"INV-{y}-{self.n:04d}", "B": f"F-{self.n}{self.r.choice(['', '/' + str(y)[2:]])}", "C": f"FR-{y}-{self.n:03d}",
                "S": f"{self.r.choice(['INV', 'FAC', 'REF'])}{self.n:05d}"}[fam]


def gen_invoice(ctx, fam, cur):
    r = ctx.r
    net = Decimal(r.randrange(20000, 9000000)) / 100
    if r.random() < 0.12:
        net = Decimal(int(net // 100) * 100)
    disc = r.choice([None, None, Decimal("2.5"), Decimal("5"), Decimal("10"), Decimal("1.25")])
    tax = r.choice([Decimal(0), Decimal("0.21"), Decimal("0.10"), Decimal("0.20")])
    total = (net * (1 - (disc or Decimal(0)) / 100) * (1 + tax)).quantize(Q2)
    issue = date(r.choice([2023, 2024, 2025]), r.randint(1, 12), r.randint(1, 28))
    due = issue + timedelta(days=r.randint(15, 90)) if r.random() < 0.8 else None
    sname, sid = party(r)
    dname, did = party(r)
    t = {c: None for c in COLUMNS}
    t.update({"SELLER ID": sid, "SELLER": sname, "DEBTOR ID": did, "DEBTOR": dname, "INVOICE REF": ctx.ref(fam),
              "GOODS SERVICES": r.choice(GOODS), "TOTAL INVOICE AMOUNT": total, "TOTAL NET VALUE": net.quantize(Q2),
              "DISCOUNT PERCENTAGE": disc, "CURRENCY": cur, "ISSUE DATE": issue, "DUE DATE": due})
    return t


def label(r, fam, field):
    s = r.choice(DISPLAY[fam][field])
    return r.choice([s, s.upper(), s.lower()]) if fam == "A" else s


def render_text_invoice(r, ctx, fam, bad):
    """Devuelve (líneas, registro esperado, warnings[(COLUMNA, raw)])."""
    cur = {"A": lambda: r.choice(["USD", "GBP", "EUR", "CHF"]), "B": lambda: "EUR", "C": lambda: r.choice(["EUR", "CHF"])}[fam]()
    t = gen_invoice(ctx, fam, cur)
    for f in ("SELLER ID", "DEBTOR ID", "DUE DATE", "DISCOUNT PERCENTAGE"):
        if r.random() < 0.25:
            t[f] = None
    if fam == "C":
        t["GOODS SERVICES"] = None
    if fam == "A" and r.random() < 0.2:
        t["GOODS SERVICES"] = None
    descs = None
    if fam == "B":
        descs = r.sample(GOODS, r.randint(1, 4))
        t["GOODS SERVICES"] = "; ".join(descs)
    dstyle = {"A": ["iso", "en_long"], "B": ["dmy", "es_long"], "C": ["fr_long", "dmy_dot"]}[fam]
    ds = r.choice(dstyle)
    thou = {"A": [",", ""], "B": [".", ""], "C": [" ", "\u00a0", ""]}[fam]
    th = r.choice(thou)
    dec = "." if fam == "A" else ","
    dstyle_money = r.choice({"A": ["prefix", "suffix", "name"], "B": ["suffix", "suffix_sym"], "C": ["suffix", "suffix_sym"]}[fam])

    def money(d):
        if fam == "A" and d == d.to_integral_value() and d >= 1000 and r.random() < 0.5:
            return decorate(r, f"{int(d):,}", cur, dstyle_money)
        return decorate(r, fmt_dec(d, dec, th), cur, dstyle_money)

    eu = fam != "A"
    values = {"INVOICE REF": t["INVOICE REF"], "SELLER": t["SELLER"], "SELLER ID": t["SELLER ID"], "DEBTOR": t["DEBTOR"], "DEBTOR ID": t["DEBTOR ID"],
              "GOODS SERVICES": t["GOODS SERVICES"], "ISSUE DATE": fmt_date(r, t["ISSUE DATE"], ds),
              "DUE DATE": None if t["DUE DATE"] is None else fmt_date(r, t["DUE DATE"], ds),
              "TOTAL NET VALUE": money(t["TOTAL NET VALUE"]), "TOTAL INVOICE AMOUNT": money(t["TOTAL INVOICE AMOUNT"]),
              "DISCOUNT PERCENTAGE": None if t["DISCOUNT PERCENTAGE"] is None else pct_str(r, t["DISCOUNT PERCENTAGE"], eu, r.choice(["%", " %"] if eu else ["%", ""]))}
    warns = []
    if bad and r.random() < 0.5:
        if t["DUE DATE"] is not None:
            values["DUE DATE"] = r.choice(["n/a", "TBD", "31/02/2024"])
            warns.append(("DUE DATE", values["DUE DATE"]))
            t["DUE DATE"] = None
    elif bad:
        values["TOTAL INVOICE AMOUNT"] = r.choice(["pending", "TBD"])
        warns.append(("TOTAL INVOICE AMOUNT", values["TOTAL INVOICE AMOUNT"]))
        t["TOTAL INVOICE AMOUNT"] = None
    lines = []
    if fam == "A":
        lines.append("INVOICE")
        fields = [f for f in ["INVOICE REF", "ISSUE DATE", "DUE DATE", "SELLER", "SELLER ID", "DEBTOR", "DEBTOR ID", "GOODS SERVICES", "TOTAL NET VALUE",
                              "DISCOUNT PERCENTAGE", "TOTAL INVOICE AMOUNT"] if values[f] is not None]
        r.shuffle(fields)
        for f in fields:
            lines.append(f"{label(r, 'A', f)}{r.choice([': ', ' : ', ':  '])}{noise(r, values[f])}")
    elif fam == "C":
        lines.append("FACTURE")
        fields = [f for f in ["INVOICE REF", "ISSUE DATE", "DUE DATE", "SELLER", "SELLER ID", "DEBTOR", "DEBTOR ID", "TOTAL NET VALUE", "DISCOUNT PERCENTAGE",
                              "TOTAL INVOICE AMOUNT"] if values[f] is not None]
        r.shuffle(fields)
        for f in fields:
            lines.append(f"{label(r, 'C', f)} {'.' * r.randint(3, 20)} {values[f]}")
    else:
        lines.append("FACTURA")
        head = [f for f in ["INVOICE REF", "ISSUE DATE", "DUE DATE", "SELLER", "SELLER ID", "DEBTOR", "DEBTOR ID", "DISCOUNT PERCENTAGE"] if values[f] is not None]
        r.shuffle(head)
        for f in head:
            lines.append(f"{label(r, 'B', f)}: {noise(r, values[f])}")
        sep = "-" * r.randint(5, 45)
        lines += [sep, "Descripción".ljust(28) + "Cant".rjust(6) + "Precio".rjust(9) + "Importe".rjust(10)]
        for dsc in descs:
            q = r.randint(1, 200)
            p = Decimal(r.randrange(50, 20000)) / 100
            lines.append(dsc.ljust(max(28, len(dsc) + 2)) + str(q).rjust(6) + fmt_dec(p, ",", "").rjust(9) + fmt_dec(p * q, ",", "").rjust(10))
        lines.append(sep)
        for f in ("TOTAL NET VALUE", "TOTAL INVOICE AMOUNT"):
            lines.append(f"{label(r, 'B', f)}:".ljust(24) + values[f].rjust(20))
    return lines, to_json_record(t), warns


def render_text_file(r, ctx, cfg, fam_fixed=None, n_inv=None):
    n = n_inv or r.randint(*cfg["txt_inv"])
    fam = fam_fixed or r.choice("ABC")
    blocks, recs, warns, skipped = [], [], [], 0
    for _ in range(n):
        f = r.choice("ABC") if cfg["mixed"] and not fam_fixed else fam
        lines, rec, w = render_text_invoice(r, ctx, f, r.random() < cfg["bad"])
        blocks.append(lines)
        recs.append(rec)
        warns += w
    if r.random() < cfg["junk"]:
        blocks.insert(r.randint(0, len(blocks)), ["Thank you for your business.", "Page 1 of 1"])
        skipped += 1
    out = []
    for i, b in enumerate(blocks):
        if i:
            out.append("=" * r.randint(10, 30))
        out += b
    nl = "\r\n" if r.random() < cfg["crlf"] else "\n"
    text = nl.join(out) + nl
    return text, recs, warns, skipped


def encode_text(r, text, cfg):
    if cfg["enc"]:
        x = r.random()
        if x < 0.2:
            return ("\ufeff" + text).encode("utf-8")
        if x < 0.4:
            try:
                return text.encode("latin-1")
            except UnicodeEncodeError:
                pass
    return text.encode("utf-8")


# ------------------------------------------------------------------ hojas
def header_display(r, syn):
    words = [ACCENTS.get(w, w) if r.random() < 0.5 else w for w in syn.split()]
    kind = r.choice(["title", "upper", "snake", "dash", "plain"])
    return {"title": " ".join(w.capitalize() for w in words), "upper": " ".join(words).upper(), "snake": "_".join(words),
            "dash": "-".join(w.capitalize() for w in words), "plain": " ".join(words)}[kind]


def render_sheet(r, ctx, cfg, sample_style=None):
    """Devuelve (bytes, ext, registros esperados, warnings, skipped, mapping{'header_row','cols'})."""
    keep = list(COLUMNS)
    mandatory = {"INVOICE REF", "SELLER", "TOTAL INVOICE AMOUNT"}
    dropped = {c for c in COLUMNS if c not in mandatory and r.random() < cfg["drop"]}
    while len(COLUMNS) - len(dropped) < 6:
        dropped.discard(r.choice(sorted(dropped)))
    keep = [c for c in COLUMNS if c not in dropped]
    r.shuffle(keep)
    delim = r.choice(cfg["delims"])
    grouped = r.random() < cfg["grouped"]
    num_style = r.choice(["us", "us_nogroup", "eu", "eu_nogroup", "eu_space", "ch"])
    dec, th = {"us": (".", ","), "us_nogroup": (".", ""), "eu": (",", "."), "eu_nogroup": (",", ""), "eu_space": (",", " "), "ch": (".", "'")}[num_style]
    eu = dec == ","
    decor = r.choice(["none", "prefix", "suffix", "name", "suffix_sym"]) if "CURRENCY" in keep else r.choice(["prefix", "suffix", "name", "suffix_sym"])
    dstyle = r.choice(["iso", "dmy", "dmy_dot", "en_long", "es_long", "fr_long"])
    cur_disp = r.choice(["code", "name", "symbol"])
    cur_text = lambda c: c if cur_disp == "code" else (r.choice(NAMES[c]) if cur_disp == "name" else SYM.get(c, c))  # noqa: E731

    def money(d, cur):
        return decorate(r, fmt_dec(d, dec, th), cur, decor)

    headers = {c: header_display(r, r.choice(HEADER_SYNONYMS[c])) for c in keep}
    cols = list(keep)
    for _ in range(r.randint(*cfg["extras"])):
        cols.insert(r.randint(0, len(cols)), "@" + r.choice(EXTRA_HEADERS))
    idx = {c: i for i, c in enumerate(cols)}
    ncols = len(cols)
    amount_col = idx["TOTAL INVOICE AMOUNT"]

    rows, recs, warns, skipped = [], [], [], 0
    label_cols = sorted({0, idx["INVOICE REF"], idx["SELLER"]} - {amount_col}) or [(amount_col + 1) % ncols]

    def summary_row(amount, cur, grand=False):
        cells = [""] * ncols
        cells[r.choice(label_cols)] = r.choice(["Total", "Grand Total", "TOTALS", "Suma", "Total general", "Sum"] if grand else ["Subtotal", "SUBTOTAL", "subtotal"])
        cells[amount_col] = money(amount, cur)
        return cells

    for g in range(r.randint(*cfg["groups"])):
        program = f"PRG-{r.randint(100, 999)}"
        cur = r.choice(["EUR", "USD", "GBP", "CHF"])
        sname, sid = party(r)
        dname, did = party(r)
        group_total = Decimal(0)
        n_rows = r.randint(*cfg["rows"])
        mid = r.randint(2, n_rows - 2) if (n_rows >= 6 and r.random() < cfg["subtotals"] * 0.4) else None
        for k in range(n_rows):
            if mid is not None and k == mid:  # subtotal corriente a mitad de grupo
                rows.append(summary_row(group_total, cur))
                skipped += 1
            t = gen_invoice(ctx, "S", cur)
            t.update({"PROGRAM": program, "SELLER": sname, "SELLER ID": sid, "DEBTOR": dname, "DEBTOR ID": did,
                      "MARGIN": (Decimal(r.randrange(50, 500)) / 100) if r.random() < 0.8 else None})
            group_total += t["TOTAL INVOICE AMOUNT"]
            bad_cell = None
            if r.random() < cfg["bad"]:
                bad_cell = r.choice(["DUE DATE", "TOTAL NET VALUE"])
            cells = [""] * ncols
            for c in keep:
                v = t[c]
                if c in dropped:
                    continue
                if c in GROUPED:
                    s = cur_text(cur) if c == "CURRENCY" else v
                    cells[idx[c]] = noise(r, s) if (not grouped or k == 0) else ""
                elif c in ("ISSUE DATE", "DUE DATE"):
                    cells[idx[c]] = "" if v is None else fmt_date(r, v, dstyle)
                elif c in ("TOTAL INVOICE AMOUNT", "TOTAL NET VALUE"):
                    cells[idx[c]] = money(v, cur)
                elif c in ("DISCOUNT PERCENTAGE", "MARGIN"):
                    cells[idx[c]] = "" if v is None else pct_str(r, v, eu, r.choice(["", "%"]) if not eu else r.choice(["", " %"]))
                elif c == "INVOICE REF":
                    cells[idx[c]] = v
                else:
                    cells[idx[c]] = noise(r, v)
            for c in cols:
                if c.startswith("@"):
                    cells[idx[c]] = {"@Notes": r.choice(["", "call back", "disputed", "ok"]), "@Status": r.choice(["open", "paid", "overdue"]),
                                     "@Batch": f"B{r.randint(1, 30)}", "@Row": str(len(rows) + 1)}[c]
            if bad_cell and bad_cell in keep and bad_cell not in dropped and (bad_cell != "DUE DATE" or t["DUE DATE"] is not None):
                raw = r.choice(["n/a", "TBD", "31/02/2024"]) if bad_cell == "DUE DATE" else r.choice(["TBD", "pending"])
                cells[idx[bad_cell]] = raw
                warns.append((bad_cell, raw))
                t[bad_cell] = None
            rec = {c: (None if (c in dropped and c != "CURRENCY") else t[c]) for c in COLUMNS}  # CURRENCY se infiere del importe (R3.8)
            recs.append(to_json_record(rec))
            rows.append(cells)
            if r.random() < cfg["blanks"]:
                rows.append([""] * ncols)
        if r.random() < cfg["subtotals"]:
            rows.append(summary_row(group_total, cur))
            skipped += 1
    if r.random() < cfg["subtotals"]:
        rows.append(summary_row(Decimal(r.randrange(100000, 90000000)) / 100, r.choice(["EUR", "USD"]), grand=True))
        skipped += 1
    if r.random() < cfg["amount_only"]:
        cells = [""] * ncols
        cells[amount_col] = money(Decimal(r.randrange(100000, 90000000)) / 100, "EUR")
        rows.append(cells)
        skipped += 1
    # bloque de metadatos + cabecera + filas
    nl = "\r\n" if r.random() < cfg["crlf"] else "\n"
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=delim, lineterminator=nl)
    meta_n = r.randint(*cfg["meta"])
    for m in r.sample(META, meta_n):
        if r.random() < 0.5:
            buf.write(m + nl)
        else:
            w.writerow([m] + [""] * (ncols - 1))
    header_row = meta_n
    w.writerow([headers[c] if not c.startswith("@") else c[1:] for c in cols])
    w.writerows(rows)
    mapping = {"header_row": header_row, "cols": {str(idx[c]): c for c in keep}}
    return encode_text(r, buf.getvalue(), cfg), (".tsv" if delim == "\t" else ".csv"), recs, warns, skipped, mapping
