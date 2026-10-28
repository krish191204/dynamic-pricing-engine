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
        # Hand-checkable on purpose: add the last four weekly totals and divide by 4.
        # One odd week moves the result. The latest week is not a second forecast yet.
        last_four = [point.quantity for point in ctx.weekly[-4:]]
        ctx.forecast_units = round(sum(last_four) / len(last_four), 2)
        earlier = [point.quantity for point in ctx.weekly[:-4]] or last_four
        ctx.recent_average = round(sum(earlier) / len(earlier), 2)
        shown = ", ".join(f"{qty:g}" for qty in last_four)
        ctx.forecast_method = f"mean of the last 4 weeks ({shown})"
        # The price we move from is the average price of the latest week, not a typed shelf price.
        ctx.current_price = ctx.weekly[-1].avg_price
        prior = last_four[:-1]
        if prior:
            baseline = sum(prior) / len(prior)
            last = last_four[-1]
            # Half or double the recent pace. The warning does not change the average.
            if baseline and (last < 0.5 * baseline or last > 2 * baseline):
                ctx.warnings.append(
                    f"Last week sold {last:g} units. The three weeks before it averaged {baseline:.1f}. "
                    "The forecast is the average of all four, so one odd week moves it."
                )
        self.note(ctx, f"forecast {ctx.forecast_units} units")
        return ctx
