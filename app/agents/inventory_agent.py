"""Arena: inventory.

Warns to reorder when cover is short, or to clear stock when cover is long
and the forecast is soft.
"""

from __future__ import annotations

from app.agents.base import Agent
from app.context import RunContext


class InventoryAgent(Agent):
    name = "inventory"
    arena = "inventory"
    owner = "Inventory Agent"

    def run(self, ctx: RunContext) -> RunContext:
        if ctx.failed:
            return ctx
        forecast = ctx.forecast_units or 0
        if forecast <= 0:
            ctx.weeks_of_cover = None
            ctx.inventory_alert = "review"
            ctx.inventory_reason = "Forecast is zero, so weeks of cover is undefined."
            return ctx
        cover = ctx.stock_on_hand / forecast
        ctx.weeks_of_cover = round(cover, 2)
        baseline = ctx.recent_average or forecast
        if cover < 2:
            ctx.inventory_alert = "reorder"
            ctx.inventory_reason = (
                f"About {ctx.weeks_of_cover} weeks of cover at the forecast rate."
            )
        elif cover >= 4 and forecast < 0.7 * baseline:
            ctx.inventory_alert = "clear"
            ctx.inventory_reason = (
                f"About {ctx.weeks_of_cover} weeks of cover and demand is below the earlier average."
            )
        else:
            ctx.inventory_alert = "ok"
            ctx.inventory_reason = f"About {ctx.weeks_of_cover} weeks of cover."
        self.note(ctx, ctx.inventory_alert)
        return ctx
