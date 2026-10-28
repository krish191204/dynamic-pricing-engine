"""Arena: data shape. Owner: Rohan.

Turns invoice lines into one quantity and average price per calendar week.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from app.agents.base import Agent
from app.context import RunContext, WeekPoint


def week_start(day):
    # Monday. A Friday "week ending" is stored on the Monday of that week.
    # Missing weeks stay missing. They are not filled with zero.
    return day - timedelta(days=day.weekday())


class TransformAgent(Agent):
    name = "transform"
    arena = "weekly series"
    owner = "Rohan"

    def run(self, ctx: RunContext) -> RunContext:
        if ctx.failed:
            return ctx
        # Sum units and sales value onto the Monday of each row's date.
        buckets: dict = defaultdict(lambda: {"qty": 0, "value": 0.0})
        for row in ctx.clean_rows:
            key = week_start(row.sold_on)
            buckets[key]["qty"] += row.quantity
            buckets[key]["value"] += row.quantity * row.unit_price
        weekly = []
        for start in sorted(buckets):
            qty = buckets[start]["qty"]
            # Average price is sales value divided by units, not the last invoice's price.
            avg = buckets[start]["value"] / qty if qty else 0.0
            weekly.append(WeekPoint(week_start=start, quantity=qty, avg_price=round(avg, 2)))
        ctx.weekly = weekly
        if weekly:
            last = weekly[-1].week_start
            prices = [row.unit_price for row in ctx.clean_rows if week_start(row.sold_on) == last]
            # More than 5 cents of spread means the "current price" is a blend, not a shelf price.
            if len(prices) >= 2 and max(prices) - min(prices) > 0.05:
                ctx.warnings.append(
                    f"Last week mixes prices from {min(prices):g} to {max(prices):g}. "
                    f"The price used, {weekly[-1].avg_price:g}, is the average."
                )
        if len(weekly) < 4:
            ctx.errors.append("Need at least 4 weeks of history after aggregation.")
        else:
            self.note(ctx, f"{len(weekly)} weekly points")
        return ctx
