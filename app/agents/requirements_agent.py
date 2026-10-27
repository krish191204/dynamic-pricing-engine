"""Arena: requirements. Owner: Maheen.

Checks that a Phase 1 run has the inputs the overview promised:
one product, stock on hand, unit cost, and a sales file.
"""

from __future__ import annotations

from app.agents.base import Agent
from app.context import RunContext


class RequirementsAgent(Agent):
    name = "requirements"
    arena = "requirements"
    owner = "Maheen"

    def run(self, ctx: RunContext) -> RunContext:
        if not ctx.product_code.strip():
            ctx.errors.append("A product code is required.")
        if ctx.stock_on_hand < 0:
            ctx.errors.append("Stock on hand cannot be negative.")
        if ctx.unit_cost < 0:
            ctx.errors.append("Unit cost cannot be negative.")
        if not ctx.csv_path:
            ctx.errors.append("A sales history file is required.")
        if ctx.manager_override and ctx.manager_override not in {"hold", "mark_down", "raise"}:
            ctx.errors.append("Override must be hold, mark_down, or raise.")
        if not ctx.failed:
            self.note(ctx, "Phase 1 inputs accepted")
        return ctx
