"""Arena: data. Owner: Sufiyaan.

Loads a sales CSV: date, product, price, quantity, optional invoice.
Public retail files are expected; this agent does not call a live shop.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from app.agents.base import Agent
from app.context import RunContext, SalesRow


class DataAgent(Agent):
    name = "data"
    arena = "data"
    owner = "Sufiyaan"

    def run(self, ctx: RunContext) -> RunContext:
        if ctx.failed:
            return ctx
        path = Path(ctx.csv_path)
        if not path.is_file():
            ctx.errors.append(f"Sales file not found: {ctx.csv_path}")
            return ctx
        rows: list[SalesRow] = []
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            required = {"date", "product", "price", "quantity"}
            if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
                ctx.errors.append("CSV must include date, product, price, and quantity.")
                return ctx
            for raw in reader:
                sold_on = datetime.strptime(raw["date"].strip(), "%Y-%m-%d").date()
                rows.append(
                    SalesRow(
                        sold_on=sold_on,
                        product_code=raw["product"].strip(),
                        unit_price=float(raw["price"]),
                        quantity=int(float(raw["quantity"])),
                        invoice=(raw.get("invoice") or "").strip(),
                    )
                )
        ctx.raw_rows = rows
        self.note(ctx, f"loaded {len(rows)} rows")
        return ctx
