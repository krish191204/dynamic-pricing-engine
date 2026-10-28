"""Arena: tests. Owner: Thomas.

Scores the same four-week mean on the last complete week (MAPE).
"""

from __future__ import annotations

from app.agents.base import Agent
from app.context import RunContext


class EvaluationAgent(Agent):
    name = "evaluation"
    arena = "testing"
    owner = "Thomas"

    def run(self, ctx: RunContext) -> RunContext:
        if ctx.failed:
            return ctx
        # The check hides the latest week and applies the same four-week mean.
        # Four weeks can produce a price with no miss percentage.
        if len(ctx.weekly) < 5:
            ctx.evaluation_note = "Not enough weeks to score a hold-out forecast."
            self.note(ctx, ctx.evaluation_note)
            return ctx
        history = [point.quantity for point in ctx.weekly[:-1]]
        actual = ctx.weekly[-1].quantity
        predicted = sum(history[-4:]) / 4
        if actual == 0:
            ctx.evaluation_note = "Last week sold zero units, so MAPE is undefined."
        else:
            # MAPE = |guess - actual| / actual. The guess uses the four weeks before the last one.
            ctx.mape = round(abs(predicted - actual) / actual * 100, 1)
            ctx.evaluation_note = (
                f"The same average, tested on the latest week, was off by {ctx.mape}% "
                f"(it guessed {predicted:.1f}, actual sales were {actual:g})."
            )
            # 50% is the line where the page calls the price a weak guess.
            if ctx.mape >= 50:
                ctx.evaluation_note += " Treat the price as a weak guess."
        self.note(ctx, ctx.evaluation_note)
        return ctx
