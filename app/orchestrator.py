"""Arena: scope. Owner: Krish.

Runs the ten specialists in order and returns one dashboard payload.
"""

from __future__ import annotations

from app.agents import AGENTS
from app.context import RunContext


def run_analysis(
    csv_path: str,
    product_code: str,
    stock_on_hand: int,
    unit_cost: float,
    manager_override: str | None = None,
) -> dict:
    ctx = RunContext(
        product_code=product_code,
        stock_on_hand=stock_on_hand,
        unit_cost=unit_cost,
        csv_path=csv_path,
        manager_override=manager_override,
    )
    for agent in AGENTS:
        if ctx.failed and agent.name != "dashboard":
            continue
        agent.run(ctx)
    return {
        "dashboard": ctx.dashboard,
        "agent_log": ctx.agent_log,
        "errors": ctx.errors,
    }
