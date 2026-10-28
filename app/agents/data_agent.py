"""Arena: data. Owner: Sufiyaan.

Loads a sales report. Column names can vary. A pasted table is accepted too.
"""

from __future__ import annotations

from pathlib import Path

from app.agents.base import Agent
from app.context import RunContext
from app.intake import read_sales_report


class DataAgent(Agent):
    name = "data"
    arena = "data"
    owner = "Sufiyaan"

    def run(self, ctx: RunContext) -> RunContext:
        if ctx.failed:
            return ctx
        path = Path(ctx.csv_path)
        if not path.is_file():
            ctx.errors.append("Add a sales report, or paste the table.")
            return ctx
        # utf-8-sig drops an Excel byte-order mark. Bad bytes are replaced, not rejected.
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        try:
            rows, note, warnings = read_sales_report(text, ctx.product_code, ctx.stated_price)
        except ValueError as error:
            ctx.errors.append(str(error))
            return ctx
        ctx.raw_rows = rows
        ctx.intake_note = note
        ctx.warnings.extend(warnings)
        self.note(ctx, note)
        return ctx
