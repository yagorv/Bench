"""Diccionarios normativos de T03. Fuente única: se renderizan en el TASK.md, los usa el generador y se copian a la referencia."""
import re
import unicodedata

COLUMNS = ["PROGRAM", "SELLER ID", "SELLER", "DEBTOR ID", "DEBTOR", "INVOICE REF", "GOODS SERVICES", "TOTAL INVOICE AMOUNT",
           "TOTAL NET VALUE", "DISCOUNT PERCENTAGE", "CURRENCY", "ISSUE DATE", "DUE DATE", "MARGIN"]

TEXT_LABELS = {  # campo -> etiquetas normalizadas aceptadas en facturas de texto
    "INVOICE REF": ["invoice no", "invoice number", "invoice ref", "factura n", "n factura", "numero de factura", "facture n", "n facture", "numero de facture"],
    "ISSUE DATE": ["invoice date", "issue date", "date of issue", "fecha de emision", "fecha factura", "date de facture", "date d emission"],
    "DUE DATE": ["due date", "payment due", "payment due date", "fecha de vencimiento", "vencimiento", "date d echeance", "echeance"],
    "SELLER": ["seller", "supplier", "vendor", "from", "proveedor", "emisor", "fournisseur"],
    "SELLER ID": ["seller id", "supplier id", "seller vat id", "supplier vat id", "nif proveedor", "nif emisor", "tva fournisseur"],
    "DEBTOR": ["bill to", "customer", "buyer", "cliente", "comprador", "client", "acheteur"],
    "DEBTOR ID": ["customer id", "buyer id", "customer vat id", "nif cliente", "nif comprador", "tva client"],
    "GOODS SERVICES": ["description", "goods", "services", "concepto", "descripcion", "designation"],
    "TOTAL INVOICE AMOUNT": ["total", "total due", "amount due", "invoice total", "total factura", "importe total", "total ttc", "montant ttc"],
    "TOTAL NET VALUE": ["subtotal", "net", "net amount", "net total", "base imponible", "total ht", "montant ht"],
    "DISCOUNT PERCENTAGE": ["discount", "discount rate", "descuento", "remise"],
}

HEADER_SYNONYMS = {  # columna -> cabeceras normalizadas aceptadas en hojas
    "PROGRAM": ["program", "programa", "programme", "scheme"],
    "SELLER ID": ["seller id", "id seller", "supplier id", "vendor id", "id proveedor"],
    "SELLER": ["seller", "supplier", "vendor", "proveedor", "fournisseur"],
    "DEBTOR ID": ["debtor id", "id debtor", "customer id", "buyer id", "id cliente"],
    "DEBTOR": ["debtor", "customer", "buyer", "cliente", "deudor"],
    "INVOICE REF": ["invoice ref", "invoice no", "invoice number", "invoice", "factura", "numero factura", "ref"],
    "GOODS SERVICES": ["goods services", "goods", "services", "description", "concepto", "item"],
    "TOTAL INVOICE AMOUNT": ["total invoice amount", "invoice amount", "gross amount", "amount", "importe", "total"],
    "TOTAL NET VALUE": ["total net value", "net value", "net amount", "net", "neto", "base"],
    "DISCOUNT PERCENTAGE": ["discount percentage", "discount pct", "discount", "disc", "descuento"],
    "CURRENCY": ["currency", "ccy", "moneda", "devise"],
    "ISSUE DATE": ["issue date", "invoice date", "date", "fecha emision", "fecha"],
    "DUE DATE": ["due date", "payment due", "fecha vencimiento", "vencimiento", "maturity"],
    "MARGIN": ["margin", "margen", "spread"],
}

SUMMARY_KEYWORDS = ["total", "totals", "grand total", "subtotal", "sum", "suma", "total general"]
GROUPED = ["PROGRAM", "SELLER ID", "SELLER", "DEBTOR ID", "DEBTOR", "CURRENCY"]


def norm(s: str) -> str:
    """N1 del TASK.md: NFD, quitar marcas combinantes, minúsculas, todo lo que no sea a-z0-9 -> espacio, colapsar."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


def md_table(d: dict, head: str) -> str:
    rows = [f"| {head} | Accepted labels |", "|---|---|"]
    for k, v in d.items():
        rows.append(f"| `{k}` | " + ", ".join(f"`{x}`" for x in v) + " |")
    return "\n".join(rows)
