"""Arena: guardrails. Owner: Yuncho with Sunny.

Blocks a suggestion below unit cost, and caps a one-step move at 20%.
"""

from __future__ import annotations

from app.agents.base import Agent
from app.context import RunContext


class GuardrailAgent(Agent):
    name = "guardrail"
    arena = "guardrails"
    owner = "Guardrail Agent"

    def run(self, ctx: RunContext) -> RunContext:
        if ctx.failed:
            return ctx
        price = ctx.suggested_price or 0
        current = ctx.current_price or price
        # Order matters. The cost floor runs first. The 20% cap runs second and
        # can pull the price back under cost. Example: history 10, cost 15, result 12.
        if price < ctx.unit_cost:
            ctx.blocked = True
            ctx.suggested_price = round(ctx.unit_cost, 2)
            ctx.price_action = "hold"
            ctx.guardrail_notes.append(
                "Suggested price was below unit cost, so it was raised to cost and the action set to hold."
            )
        if current > 0 and ctx.suggested_price is not None:
            change = abs(ctx.suggested_price - current) / current
            if change > 0.20:
                direction = 1 if ctx.suggested_price > current else -1
                ctx.suggested_price = round(current * (1 + 0.20 * direction), 2)
                ctx.guardrail_notes.append("Change capped at 20% versus the current price.")
        if not ctx.guardrail_notes:
            ctx.guardrail_notes.append("Price stays above cost and within the 20% step limit.")
        self.note(ctx, "; ".join(ctx.guardrail_notes))
        return ctx
