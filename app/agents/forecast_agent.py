"""Arena: demand forecast.

Predicts next week's unit sales as the mean of the last four weeks.
Explainable on purpose: a marker can recompute it by hand.
"""

from __future__ import annotations

from app.agents.base import Agent
from app.context import RunContext


class ForecastAgent(Agent):
    name = "forecast"
    arena = "demand forecast"
    owner = "Demand Forecast Agent"

    def run(self, ctx: RunContext) -> RunContext:
        if ctx.failed:
            return ctx
        last_four = [point.quantity for point in ctx.weekly[-4:]]
        ctx.forecast_units = round(sum(last_four) / len(last_four), 2)
        earlier = [point.quantity for point in ctx.weekly[:-4]] or last_four
        ctx.recent_average = round(sum(earlier) / len(earlier), 2)
        ctx.forecast_method = "mean of the last 4 weeks"
        ctx.current_price = ctx.weekly[-1].avg_price
        self.note(ctx, f"forecast {ctx.forecast_units} units")
        return ctx
