# Requirements — Formats Unification (offline edition)

## Introduction

Formats Unification is a Python toolchain that converts heterogeneous invoice inputs (plain-text invoice exports and arbitrary-layout CSV/TSV sheets) into a single standardized CSV file. The standardization target is a template whose first row defines 14 fixed columns in a fixed order.

The system is a pipeline around a common intermediate contract — a JSON array of records whose keys are the standardized column names:

```
invoices/*.txt  -> tools/txt_to_json.py   -\
                                             > JSON array -> tools/json_to_csv.py -> filled .csv
sheets/*.csv    -> tools/sheet_to_json.py -/
```

There is no network, no LLM and no third-party package: all extraction is deterministic and rule-based, using **only the rules in this document**. Where this document gives a dictionary or a rule, it is normative and complete. Your solution will be evaluated on many input files you cannot see, which follow these rules with different phrasing, column orders, delimiters, values and edge cases.

The 14 standardized columns (exact names, in the order of `template.csv`):
`PROGRAM`, `SELLER ID`, `SELLER`, `DEBTOR ID`, `DEBTOR`, `INVOICE REF`, `GOODS SERVICES`, `TOTAL INVOICE AMOUNT`, `TOTAL NET VALUE`, `DISCOUNT PERCENTAGE`, `CURRENCY`, `ISSUE DATE`, `DUE DATE`, `MARGIN`.

| Column | Type in JSON | Meaning |
|---|---|---|
| `PROGRAM`, `SELLER ID`, `SELLER`, `DEBTOR ID`, `DEBTOR`, `INVOICE REF`, `GOODS SERVICES` | string or `null` | free text |
| `TOTAL INVOICE AMOUNT`, `TOTAL NET VALUE` | number or `null` | monetary amount |
| `DISCOUNT PERCENTAGE`, `MARGIN` | number or `null` | percentage value (`2.5` means 2.5 %) |
| `CURRENCY` | string or `null` | ISO 4217 code: `EUR`, `USD`, `GBP`, `CHF` |
| `ISSUE DATE`, `DUE DATE` | string or `null` | `YYYY-MM-DD` |

## Shared normalization rules (apply in every tool)

**N1 — Label/header normalization.** To compare a label or header with a dictionary: decompose it canonically (Unicode NFD) and delete the combining marks, lowercase it, replace every character that is not `a-z` or `0-9` by a space (so `º`, `°`, punctuation, dots and underscores become spaces), collapse runs of spaces, trim. (`"Factura Nº:"` → `"factura n"`, `"N° Facture"` → `"n facture"`, `"Date d'échéance"` → `"date d echeance"`, `"payment_due"` → `"payment due"`.)

**N2 — Raw values.** Before interpreting any value, trim it and collapse every run of whitespace inside it to one space. A text value is the result of that step; if it is empty, the field is `null`.

**N3 — Numbers.** Remove currency symbols (`€ $ £`), currency codes and names (see N5), `%`, apostrophes and all whitespace (including NBSP and thin spaces). Then:
1. If both `.` and `,` appear, the rightmost one is the decimal separator and the other one is a thousands separator.
2. If only one kind of separator appears: if it appears more than once it is a thousands separator; if it appears once, it is a thousands separator **only** when exactly 3 digits follow it and the part before it has 1–3 digits and is not `0` (`1,234` → 1234; `12,50` → 12.5; `1.5` → 1.5; `0,125` → 0.125).
3. A leading `-` or surrounding parentheses mean negative. Anything else that is not a number → cannot parse.
The JSON value is an integer when there is no fractional part, otherwise a float.

**N4 — Dates.** Accepted inputs: `YYYY-MM-DD`; `DD/MM/YYYY` and `DD.MM.YYYY` (day first, always; 1–2 digit day/month); `Month D, YYYY` (English month name, full or 3-letter); `D de <mes> de YYYY` (Spanish month names); `D <mois> YYYY` (French month names). Month names are compared after N1. Output `YYYY-MM-DD`. A two-digit year or an impossible calendar date → cannot parse.

**N5 — Currency.** `€`, `EUR`, `Euro`, `Euros` → `EUR`; `$`, `USD`, `US Dollar`, `US Dollars` → `USD`; `£`, `GBP`, `Pound Sterling` → `GBP`; `CHF`, `Swiss Franc` → `CHF`. Matching is case-insensitive. To *find* the currency inside an amount string (e.g. `1,234.50 USD`, `€ 12,00`), look for any of these symbols/codes/names in it.

## Requirements

### Requirement 1 — JSON to CSV (the final step)

**User Story:** As an operator, I want to fill the standardized template from a JSON array of records, so the output columns and their order always match the template regardless of the JSON key order.

#### Acceptance Criteria
1. WHEN given a JSON array of objects and an output path THEN the system SHALL write the template header row followed by one row per object.
2. THE system SHALL derive the column order from the header row of the template (`--template PATH`, default `template.csv` in the current directory), independent of JSON key order.
3. WHEN a JSON key does not exactly match a header THEN the system SHALL match it by N1-normalized comparison (`seller_id`, `Seller-ID` → `SELLER ID`).
4. WHEN a JSON key has no matching column THEN the system SHALL skip it and print `WARNING: unknown field "<key>" ignored` to stderr once per distinct key; WHEN `--strict` is set THEN it SHALL exit with code 2 and SHALL NOT create the output file.
5. THE system SHALL write `null`/absent values as empty cells; numbers in shortest decimal form without exponent or thousands separators (`1200.5`, `1200`, `1200.0` → `1200`); strings unchanged.
6. THE CSV SHALL be UTF-8 without BOM, `\n` line endings, quoting per RFC 4180 (quote a field only when it contains the delimiter, a quote or a line break) — Python's `csv.writer` defaults with `lineterminator="\n"`.

### Requirement 2 — Text invoices to JSON

**User Story:** As an operator, I want to convert plain-text invoice exports into standardized records without manual data entry.

#### Acceptance Criteria
1. THE tool SHALL accept one or more text files. A file may contain several blocks separated by a line made only of 10 or more `=` characters. A block with an `INVOICE REF` yields one record; a non-blank block without one yields no record and counts as **skipped**; blank blocks are ignored (not counted).
2. THE tool SHALL recognise three layout families (examples below) and SHALL extract fields by the label dictionary below. A **label line** is: optional indentation, the label text (which contains no `:` and no `.`), then a separator — `:`, or 3 or more dots, or 2 or more spaces — then the value (the rest of the line, trimmed). The **first** separator after the label text ends the label. Labels are compared after N1.
3. THE tool SHALL apply N2–N5 to every extracted value. Lines inside a line-item table block (criterion 7) are never treated as label lines.
4. THE tool SHALL set `PROGRAM` and `MARGIN` to `null` (they never appear in text invoices) and SHALL set to `null` any field whose label is absent — it SHALL NOT invent values.
5. WHEN a label appears more than once in one block THEN the first occurrence SHALL be used.
6. THE `CURRENCY` SHALL be found (N5) in the raw value of `TOTAL INVOICE AMOUNT`; if there is no currency indication there, in the raw value of `TOTAL NET VALUE`; otherwise `null`.
7. FOR layout family B, WHEN the block has two separator lines made of 5 or more `-`, the text between them is a line-item table: its first line is the column header; every following non-blank line is a row whose description is the text before the first run of two or more spaces. `GOODS SERVICES` SHALL be the row descriptions joined with `; ` (unless a `GOODS SERVICES` label line exists in the block).

**Label dictionary (normative; compare after N1):**

| Field | Accepted labels |
|---|---|
| `INVOICE REF` | `invoice no`, `invoice number`, `invoice ref`, `factura n`, `n factura`, `numero de factura`, `facture n`, `n facture`, `numero de facture` |
| `ISSUE DATE` | `invoice date`, `issue date`, `date of issue`, `fecha de emision`, `fecha factura`, `date de facture`, `date d emission` |
| `DUE DATE` | `due date`, `payment due`, `payment due date`, `fecha de vencimiento`, `vencimiento`, `date d echeance`, `echeance` |
| `SELLER` | `seller`, `supplier`, `vendor`, `from`, `proveedor`, `emisor`, `fournisseur` |
| `SELLER ID` | `seller id`, `supplier id`, `seller vat id`, `supplier vat id`, `nif proveedor`, `nif emisor`, `tva fournisseur` |
| `DEBTOR` | `bill to`, `customer`, `buyer`, `cliente`, `comprador`, `client`, `acheteur` |
| `DEBTOR ID` | `customer id`, `buyer id`, `customer vat id`, `nif cliente`, `nif comprador`, `tva client` |
| `GOODS SERVICES` | `description`, `goods`, `services`, `concepto`, `descripcion`, `designation` |
| `TOTAL INVOICE AMOUNT` | `total`, `total due`, `amount due`, `invoice total`, `total factura`, `importe total`, `total ttc`, `montant ttc` |
| `TOTAL NET VALUE` | `subtotal`, `net`, `net amount`, `net total`, `base imponible`, `total ht`, `montant ht` |
| `DISCOUNT PERCENTAGE` | `discount`, `discount rate`, `descuento`, `remise` |

**Layout family A — labelled lines**
```
INVOICE
Invoice No: INV-2024-0042
Invoice Date: March 5, 2024
Due Date: 2024-04-04
Seller: Acme Supplies Ltd
Seller VAT ID: GB123456789
Customer: Globex Corp
Customer ID: C-5521
Description: Steel bolts M8 (box of 100)
Subtotal: $1,200.00
Discount: 2.5%
Total Due: $1,170.00
```

**Layout family B — line-item table**
```
FACTURA
Factura Nº: F-778
Fecha de emisión: 05/03/2024
Vencimiento: 04/04/2024
Proveedor: Suministros Ibéricos S.L.
NIF proveedor: B12345678
Cliente: Globex Iberia
NIF cliente: A87654321
-----------------------------------------
Descripción              Cant   Precio   Importe
Tornillos M8              100     0,12     12,00
Tuercas M8                100     0,08      8,00
-----------------------------------------
Base imponible:                        20,00 EUR
Total factura:                         24,20 EUR
```

**Layout family C — dot leaders**
```
FACTURE
N° Facture ................ FR-2024-118
Date de facture ........... 5 mars 2024
Échéance .................. 4 avril 2024
Fournisseur ............... Atelier Lumière SARL
Acheteur .................. Globex France
Remise .................... 2,5 %
Montant HT ................ 1 200,00 EUR
Montant TTC ............... 1 440,00 EUR
```

### Requirement 3 — Arbitrary sheets to JSON

**User Story:** As an operator, I want to convert arbitrary-format CSV/TSV sheets (different columns, header not on row 1, metadata blocks, grouped rows, total rows) into the standardized JSON.

#### Acceptance Criteria
1. THE tool SHALL detect the delimiter among `,`, `;` and tab as follows. For each candidate, parse the first 30 non-empty lines with a CSV parser (RFC 4180 quoting) and keep the lines that yield 4 or more fields. Let `m` be the most frequent field count among them (ties → the larger count) and `f` its frequency. Choose the candidate with the largest pair `(f, m)` compared lexicographically; ties resolve in the order `,` `;` tab.
2. THE tool SHALL take as header the **first row (within the first 30 rows) with at least 4 cells that match the header dictionary** after N1; rows before it (titles, metadata) are ignored. Rows are those produced by a CSV parser, every line counting as a row (blank lines included).
3. THE tool SHALL map each header cell to a standardized column using the header dictionary; unmatched columns are ignored; WHEN two columns map to the same target THEN the leftmost SHALL win.
4. THE tool SHALL read every row after the header to the end of the file. Fully blank rows (all cells empty after trimming) are skipped and **not** counted.
5. THE tool SHALL forward-fill the grouped columns `PROGRAM`, `SELLER ID`, `SELLER`, `DEBTOR ID`, `DEBTOR` and `CURRENCY`: an empty cell takes the last non-empty raw value seen in that column (`null` if none yet).
6. THE tool SHALL detect **summary rows** and skip them (counted as skipped) without updating the forward-fill state. A row is a summary row when (a) any cell of the row, after N1, is exactly one of `total`, `totals`, `grand total`, `subtotal`, `sum`, `suma`, `total general`; OR (b) the `TOTAL INVOICE AMOUNT` cell is non-empty while the `INVOICE REF` and `SELLER` cells are both empty (before forward-fill).
7. A remaining row SHALL produce a record only if its `INVOICE REF` is non-empty; otherwise the row is skipped and counted.
8. THE tool SHALL apply N2–N5 to every value. WHEN, after forward-fill, the `CURRENCY` cell is empty or the column is absent THEN the currency SHALL be found (N5) in the raw `TOTAL INVOICE AMOUNT` cell and, failing that, in the raw `TOTAL NET VALUE` cell; otherwise `null`.
9. THE tool SHALL, with `--show-mapping`, print to stderr `HEADER_ROW <index0>` and then one line `COL <index0> -> <STANDARD NAME>` per mapped column (ascending index) for each input file.

**Header dictionary (normative; compare after N1):**

| Column | Accepted labels |
|---|---|
| `PROGRAM` | `program`, `programa`, `programme`, `scheme` |
| `SELLER ID` | `seller id`, `id seller`, `supplier id`, `vendor id`, `id proveedor` |
| `SELLER` | `seller`, `supplier`, `vendor`, `proveedor`, `fournisseur` |
| `DEBTOR ID` | `debtor id`, `id debtor`, `customer id`, `buyer id`, `id cliente` |
| `DEBTOR` | `debtor`, `customer`, `buyer`, `cliente`, `deudor` |
| `INVOICE REF` | `invoice ref`, `invoice no`, `invoice number`, `invoice`, `factura`, `numero factura`, `ref` |
| `GOODS SERVICES` | `goods services`, `goods`, `services`, `description`, `concepto`, `item` |
| `TOTAL INVOICE AMOUNT` | `total invoice amount`, `invoice amount`, `gross amount`, `amount`, `importe`, `total` |
| `TOTAL NET VALUE` | `total net value`, `net value`, `net amount`, `net`, `neto`, `base` |
| `DISCOUNT PERCENTAGE` | `discount percentage`, `discount pct`, `discount`, `disc`, `descuento` |
| `CURRENCY` | `currency`, `ccy`, `moneda`, `devise` |
| `ISSUE DATE` | `issue date`, `invoice date`, `date`, `fecha emision`, `fecha` |
| `DUE DATE` | `due date`, `payment due`, `fecha vencimiento`, `vencimiento`, `maturity` |
| `MARGIN` | `margin`, `margen`, `spread` |

### Requirement 4 — Command-line contract

**User Story:** As an operator, I want predictable command lines, output destinations and exit codes so the tools can be scripted.

#### Acceptance Criteria
1. THE tools SHALL be invoked exactly as:
   - `python tools/txt_to_json.py [-o OUT] [--append] FILE...`
   - `python tools/sheet_to_json.py [-o OUT] [--append] [--show-mapping] FILE...`
   - `python tools/json_to_csv.py [--template PATH] [--strict] -o OUT INPUT.json`
2. THE `-o/--output` option SHALL accept `-` for stdout; for the two `*_to_json` tools stdout is the default. Only the JSON (or CSV) goes to stdout; everything else goes to stderr.
3. THE JSON output SHALL be an array of objects with all 14 keys in template order (absent → `null`), UTF-8, `ensure_ascii=false`, indent 2, trailing newline (`json.dumps(records, ensure_ascii=False, indent=2) + "\n"`). Record order = file order as given, then block/row order.
4. WHEN `--append` is set and the output file exists and holds a JSON array THEN the new records SHALL be appended to it; WHEN the file is missing THEN it SHALL be created; WHEN it exists but is not a JSON array THEN the tool SHALL exit with code 3 leaving the file unchanged.
5. Exit codes: `0` success (even if rows were skipped); `2` usage error, unreadable/nonexistent input, or `--strict` violation; `3` invalid append target.
6. THE `*_to_json` tools SHALL print exactly one line to stderr at the end of a successful run: `SUMMARY files=<n> records=<m> skipped=<k>` (`skipped` = skipped blocks for the text tool; summary rows plus rows dropped by Requirement 3.7 for the sheet tool).

### Requirement 5 — Robustness and determinism

**User Story:** As an operator, I want one bad value to never take down a whole file, and identical inputs to always give identical outputs.

#### Acceptance Criteria
1. WHEN a value cannot be parsed (N3/N4/N5) THEN the field SHALL be `null`, the record SHALL still be emitted, and stderr SHALL get one line `WARNING: <file>:<position>: cannot parse <COLUMN> "<raw>"`, where `<file>` is the path as given, `<position>` a 1-based line (text) or row (sheet) number, `<COLUMN>` the standardized column name and `<raw>` the value after N2.
2. THE tools SHALL read input as UTF-8 (a BOM is tolerated) and fall back to Latin-1 when the bytes are not valid UTF-8; CRLF and LF both SHALL work.
3. Running a tool twice on the same inputs SHALL produce byte-identical outputs (no timestamps, no dependency on locale, time zone, hash order, or the current directory except for `template.csv`).
4. A shared module `tools/formats_common.py` SHALL hold the column list, the dictionaries and the N1–N5 helpers, so that the three tools cannot drift apart.

### Requirement 6 — Environment, dependencies, safety

#### Acceptance Criteria
1. THE tools SHALL run on Python 3.10+ using only the standard library (no `pip install`).
2. THE tools SHALL NOT use the network, spawn subprocesses, or read or write any path other than the given inputs, the `-o` target and the system temp directory.
3. Temporary files SHALL be cleaned up; every run SHALL be safe to repeat.

## Deliverables and provided files

Deliver in `answer/`: `tools/txt_to_json.py`, `tools/sheet_to_json.py`, `tools/json_to_csv.py`, `tools/formats_common.py`.

Provided (read-only): `template.csv`; `samples/txt/*.txt`, `samples/sheets/*.{csv,tsv}` and, for each, `samples/expected/<name>.json` — the exact expected output of the corresponding `*_to_json` tool — plus `samples/expected/unified.csv`, the expected output of `json_to_csv.py` for the concatenation of all sample records (in the order: sample_a, sample_b, sample_c, sample_1, sample_2, sample_3). The samples show each layout family and several sheet features, **but the evaluation uses other files** that follow the same rules. Follow the rules above, not the samples' surface form.
