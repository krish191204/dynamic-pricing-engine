"""Arena: data shape. Owner: Rohan.

Turns invoice lines into one quantity and average price per calendar week.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from app.agents.base import Agent
from app.context import RunContext, WeekPoint


def week_start(day):
    return day - timedelta(days=day.weekday())


class TransformAgent(Agent):
    name = "transform"
    arena = "weekly series"
    owner = "Rohan"

    def run(self, ctx: RunContext) -> RunContext:
        if ctx.failed:
            return ctx
        buckets: dict = defaultdict(lambda: {"qty": 0, "value": 0.0})
        for row in ctx.clean_rows:
            key = week_start(row.sold_on)
            buckets[key]["qty"] += row.quantity
            buckets[key]["value"] += row.quantity * row.unit_price
        weekly = []
        for start in sorted(buckets):
            qty = buckets[start]["qty"]
            avg = buckets[start]["value"] / qty if qty else 0.0
            weekly.append(WeekPoint(week_start=start, quantity=qty, avg_price=round(avg, 2)))
        ctx.weekly = weekly
        if len(weekly) < 4:
            ctx.errors.append("Need at least 4 weeks of history after aggregation.")
        else:
            self.note(ctx, f"{len(weekly)} weekly points")
        return ctx
