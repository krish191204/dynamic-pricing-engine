"""Arena: pipeline / data quality. Owner: Yuncho.

Drops cancelled invoices, non-positive quantities, and rows for other products.
"""

from __future__ import annotations

from app.agents.base import Agent
from app.context import RunContext


class CleaningAgent(Agent):
    name = "cleaning"
    arena = "data quality"
    owner = "Yuncho"

    def run(self, ctx: RunContext) -> RunContext:
        if ctx.failed:
            return ctx
        kept = []
        for row in ctx.raw_rows:
            if row.invoice.upper().startswith("C"):
                ctx.dropped.append({"invoice": row.invoice, "reason": "cancelled"})
                continue
            if row.quantity <= 0:
                ctx.dropped.append({"invoice": row.invoice, "reason": "non-positive quantity"})
                continue
            if row.unit_price <= 0:
                ctx.dropped.append({"invoice": row.invoice, "reason": "non-positive price"})
                continue
            if row.product_code != ctx.product_code:
                continue
            kept.append(row)
        ctx.clean_rows = kept
        if len(kept) < 4:
            ctx.errors.append(
                f"Need at least 4 clean sales rows for {ctx.product_code}; found {len(kept)}."
            )
        else:
            self.note(ctx, f"kept {len(kept)} rows, dropped {len(ctx.dropped)}")
        return ctx
