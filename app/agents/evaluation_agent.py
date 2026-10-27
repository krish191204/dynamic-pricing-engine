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
            ctx.mape = round(abs(predicted - actual) / actual * 100, 1)
            ctx.evaluation_note = (
                f"Hold-out MAPE on the latest week is {ctx.mape}% "
                f"(predicted {predicted:.1f}, actual {actual})."
            )
        self.note(ctx, ctx.evaluation_note)
        return ctx
