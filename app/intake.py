"""Read a sales report that is not in one fixed layout.

Looks through the first rows for a header, then maps common column names
onto date, quantity, price, product, and invoice.
"""

from __future__ import annotations

import csv
import io
import re
from datetime import datetime

from app.context import SalesRow

ALIASES = {
    "date": {
        "date", "sold on", "invoice date", "invoicedate", "order date", "orderdate",
        "day", "transaction date", "sales date", "week", "week start", "week ending",
        "period", "posting date",
    },
    "quantity": {
        "quantity", "qty", "units", "units sold", "unit sold", "sales qty",
        "sales quantity", "volume", "items", "count", "qty sold", "sold",
    },
    "price": {
        "price", "unit price", "unitprice", "selling price", "asp", "average price",
        "avg price", "sale price", "net price",
    },
    "revenue": {
        "revenue", "sales", "net sales", "amount", "line total", "sales amount",
        "turnover",
    },
    "product": {
        "product", "sku", "stockcode", "stock code", "item", "item code",
        "description", "product name", "product code", "item name",
    },
    "invoice": {
        "invoice", "invoiceno", "invoice no", "invoice number", "order",
        "order id", "orderid", "document",
    },
}


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def _number(value: str) -> float:
    # "1,200" becomes 1200. "1.200" becomes 1.2, which is wrong for a thousands dot.
    cleaned = value.strip().replace(",", "").replace("$", "").replace("£", "").replace("€", "")
    return float(cleaned)


def _date_choices(value: str) -> tuple[list, str]:
    # Year-month-day is one date. A slash date such as 01/09/2024 is day/month
    # first (1 September) and month/day second (9 January). If the file has no
    # unambiguous date to compare with, the day/month reading is kept and no
    # warning is written.
    raw = value.strip()
    if not raw:
        raise ValueError(value)
    head = raw.split()[0]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return [datetime.strptime(head, fmt).date()], head
        except ValueError:
            continue
    found = []
    for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y", "%d/%m/%y", "%m/%d/%y"):
        try:
            day = datetime.strptime(head, fmt).date()
        except ValueError:
            continue
        if day not in found:
            found.append(day)
    if not found:
        raise ValueError(value)
    return found, head


def _header_map(fieldnames: list[str]) -> dict[str, str]:
    # The first matching column wins. Description before StockCode means the
    # product is the description, and a code such as 85123A will not match.
    found = {}
    for original in fieldnames:
        key = _norm(original)
        for role, names in ALIASES.items():
            if key in names and role not in found:
                found[role] = original
    return found


def read_sales_report(text: str, product_code: str, stated_price: float | None) -> tuple[list[SalesRow], str, list[str]]:
    rows_in = []
    header_index = None
    mapping = {}
    # Try tab, then comma, then semicolon. A title row above the header is skipped.
    for delimiter in ("\t", ",", ";"):
        parsed = list(csv.reader(io.StringIO(text), delimiter=delimiter))
        for index, row in enumerate(parsed[:40]):
            found = _header_map(row)
            if "date" in found and "quantity" in found:
                rows_in = parsed
                header_index = index
                mapping = found
                break
        if header_index is not None:
            break
    if header_index is None:
        if not rows_in:
            rows_in = list(csv.reader(io.StringIO(text)))
        seen = sorted({_norm(cell) for row in rows_in[:8] for cell in row if cell.strip()})
        shown = ", ".join(seen[:12]) or "none"
        raise ValueError(
            "Could not find a date and a quantity in this report. "
            f"Columns seen: {shown}. Export a table that has a date and units sold, or paste that table."
        )
    fieldnames = rows_in[header_index]
    body = rows_in[header_index + 1 :]
    dict_rows = [dict(zip(fieldnames, row)) for row in body if any(cell.strip() for cell in row)]
    if "price" not in mapping and "revenue" not in mapping and (stated_price is None or stated_price <= 0):
        raise ValueError("This report has no price or sales amount. Enter your current price.")
    pending = []
    skipped = 0
    warnings: list[str] = []
    for raw in dict_rows:
        try:
            choices, raw_date = _date_choices(raw.get(mapping["date"], ""))
            quantity = _number(raw.get(mapping["quantity"], ""))
            revenue = None
            if "price" in mapping:
                unit_price = _number(raw.get(mapping["price"], ""))
                revenue_cell = raw.get(mapping["revenue"], "").strip() if "revenue" in mapping else ""
                if revenue_cell:
                    revenue = _number(revenue_cell)
            elif "revenue" in mapping and quantity:
                # No unit-price column: price = sales amount / units.
                unit_price = _number(raw.get(mapping["revenue"], "")) / quantity
            else:
                unit_price = float(stated_price)
            product = raw.get(mapping["product"], "").strip() if "product" in mapping else product_code
            invoice = raw.get(mapping["invoice"], "").strip() if "invoice" in mapping else ""
        except (ValueError, TypeError, IndexError):
            skipped += 1
            continue
        if not product:
            product = product_code
        pending.append(
            {
                "choices": choices,
                "raw_date": raw_date,
                "quantity": quantity,
                "unit_price": unit_price,
                "revenue": revenue,
                "product": product,
                "invoice": invoice,
            }
        )
    # An unambiguous date (2024-08-05, or a slash date with only one valid reading) is an anchor.
    anchors = [item["choices"][0] for item in pending if len(item["choices"]) == 1]
    parsed: list[SalesRow] = []
    for item in pending:
        choices = item["choices"]
        if len(choices) == 1 or not anchors:
            sold_on = choices[0]
        else:
            def distance(day, anchors=anchors):
                return min(abs((day - anchor).days) for anchor in anchors)

            sold_on = min(choices, key=distance)
            label = f"invoice {item['invoice']}" if item["invoice"] else "a row"
            # Farther than 45 days from every anchor: drop the row instead of inventing a week.
            if distance(sold_on) > 45:
                skipped += 1
                warnings.append(
                    f"Date {item['raw_date']} on {label} is not in the same period as the other sales, so that row was skipped."
                )
                continue
            if sold_on != choices[0]:
                warnings.append(
                    f"Date {item['raw_date']} on {label} was read as {sold_on.strftime('%d %b %Y').lstrip('0')} so it sits with the other sales."
                )
        if item["revenue"] is not None and item["quantity"]:
            expected = item["quantity"] * item["unit_price"]
            # Warn only. The unit price is still the price used for the recommendation.
            if abs(item["revenue"] - expected) > max(0.05, 0.02 * abs(expected)):
                label = f"Invoice {item['invoice']}" if item["invoice"] else "One row"
                warnings.append(
                    f"{label}: sales amount {item['revenue']:g} does not equal {item['quantity']:g} × {item['unit_price']:g} = {expected:g}. The unit price was used."
                )
        parsed.append(
            SalesRow(
                sold_on=sold_on,
                product_code=item["product"],
                unit_price=item["unit_price"],
                quantity=item["quantity"],
                invoice=item["invoice"],
            )
        )
    if not parsed:
        raise ValueError("The report had a header, but no usable sales rows under it.")
    used = ", ".join(
        f"{role} from '{mapping[role]}'"
        for role in ("date", "quantity", "price", "revenue", "product")
        if role in mapping
    )
    if "price" not in mapping and "revenue" not in mapping:
        used += f", price from the {stated_price:g} you typed"
    note = f"Read {len(parsed)} rows ({used})."
    if skipped:
        note += f" Skipped {skipped} rows."
    return parsed, note, warnings
