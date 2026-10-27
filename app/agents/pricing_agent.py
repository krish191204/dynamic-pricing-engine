"""Arena: pricing rules. Owner: Sunny.

Recommends hold, mark down, or raise from the forecast and weeks of cover.
This is a recommendation, not a live price change.
"""

from __future__ import annotations

from app.agents.base import Agent
from app.context import RunContext


class PricingAgent(Agent):
    name = "pricing"
    arena = "pricing"
    owner = "Sunny"

    def run(self, ctx: RunContext) -> RunContext:
        if ctx.failed:
            return ctx
        forecast = ctx.forecast_units or 0
        baseline = ctx.recent_average or forecast
        cover = ctx.weeks_of_cover if ctx.weeks_of_cover is not None else 0
        price = ctx.current_price or 0

        if forecast < 0.7 * baseline and cover >= 4:
            ctx.price_action = "mark_down"
            ctx.suggested_price = round(price * 0.85, 2)
            ctx.pricing_reason = "Forecast is soft and stock cover is high, so suggest a 15% markdown."
        elif forecast > 1.3 * baseline and cover < 2:
            ctx.price_action = "raise"
            ctx.suggested_price = round(price * 1.10, 2)
            ctx.pricing_reason = "Forecast jumped and stock cover is thin, so suggest a 10% rise."
        else:
            ctx.price_action = "hold"
            ctx.suggested_price = round(price, 2)
            ctx.pricing_reason = "Forecast is close to the earlier average, so hold the current price."
        self.note(ctx, ctx.price_action)
        return ctx
