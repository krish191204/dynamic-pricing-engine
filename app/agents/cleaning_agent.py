"""Arena: pipeline / data quality. Owner: Yuncho.

Drops cancelled invoices, non-positive quantities, and rows for other products.
A product name that does not match the file stops the run.
"""

from __future__ import annotations

import re

from app.agents.base import Agent
from app.context import RunContext


def product_key(value: str) -> str:
    # "BREAD-01" and "BREAD01" become the same key. That is convenient for a
    # typed hyphen, and it also merges two real codes. The page should ask
    # before pricing when more than one original code shares a key.
    text = value.strip().casefold()
    text = text.replace("–", "-").replace("—", "-").replace("−", "-")
    return re.sub(r"[\s_\-]+", "", text)


class CleaningAgent(Agent):
    name = "cleaning"
    arena = "data quality"
    owner = "Yuncho"

    def run(self, ctx: RunContext) -> RunContext:
        if ctx.failed:
            return ctx
        target = product_key(ctx.product_code)
        usable = []
        for row in ctx.raw_rows:
            # UCI marks a cancelled invoice with a leading C. A real order
            # number such as C1001 is removed by the same rule.
            if row.invoice.upper().startswith("C"):
                ctx.dropped.append({"invoice": row.invoice, "reason": "cancelled"})
                continue
            if row.quantity <= 0:
                ctx.dropped.append({"invoice": row.invoice, "reason": "quantity is not positive"})
                continue
            if row.unit_price <= 0:
                ctx.dropped.append({"invoice": row.invoice, "reason": "price is not positive"})
                continue
            usable.append(row)
        # Other products are listed as dropped. They are not folded into this forecast.
        matched = [row for row in usable if product_key(row.product_code) == target]
        for row in usable:
            if product_key(row.product_code) != target:
                ctx.dropped.append({"invoice": row.invoice, "reason": f"other product {row.product_code}"})
        # Fewer than four matching rows stops the run. It does not switch to every product in the file.
        if len(matched) < 4:
            if matched:
                ctx.errors.append(
                    f"Need at least 4 clean sales rows for {ctx.product_code}; found {len(matched)}."
                )
            else:
                counts: dict[str, int] = {}
                order: list[str] = []
                for row in usable:
                    if row.product_code not in counts:
                        order.append(row.product_code)
                        counts[row.product_code] = 0
                    counts[row.product_code] += 1
                listed = ", ".join(f"{code} ({counts[code]} rows)" for code in order)
                if listed:
                    ctx.errors.append(
                        f"No rows match {ctx.product_code}. This file has {listed}. Type one of those codes."
                    )
                else:
                    ctx.errors.append(f"No usable sales rows for {ctx.product_code}.")
            return ctx
        # Show the code as it is written in the file, not the text the user typed.
        ctx.product_code = matched[0].product_code
        ctx.clean_rows = matched
        self.note(ctx, f"kept {len(matched)} rows, dropped {len(ctx.dropped)}")
        return ctx
