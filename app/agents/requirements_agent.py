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
        # Phase 1 will not guess a missing input. Each gap becomes an error and the run stops.
        if not ctx.product_code.strip():
            ctx.errors.append("Enter a product name or code.")
        if ctx.stock_on_hand < 0:
            ctx.errors.append("Enter stock on hand as zero or more.")
        if ctx.unit_cost < 0:
            ctx.errors.append("Enter the unit cost.")
        if not ctx.csv_path:
            ctx.errors.append("Add a sales history of at least four weeks.")
        if ctx.weeks_until_value_loss is None or ctx.weeks_until_value_loss <= 0:
            ctx.errors.append("Enter how many weeks until unsold stock loses its value.")
        if ctx.competitor_price is None or ctx.competitor_price <= 0:
            ctx.errors.append("Enter the market price you can see right now.")
        if ctx.sales_drop_percent is None or ctx.sales_drop_percent < 0:
            ctx.errors.append("Enter how many percent sales fall if your price rises 10%. Use 0 if demand does not move.")
        if ctx.manager_override and ctx.manager_override not in {"hold", "mark_down", "raise"}:
            ctx.errors.append("Override must be hold, mark_down, or raise.")
        if not ctx.failed:
            self.note(ctx, "Phase 1 inputs accepted")
        return ctx
