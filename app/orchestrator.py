"""Arena: scope. Owner: Krish.

Runs the ten specialists in order and returns one dashboard payload.
"""

from __future__ import annotations

from app.agents import AGENTS
from app.context import RunContext


def run_analysis(
    csv_path: str,
    product_code: str,
    stock_on_hand: float,
    unit_cost: float,
    manager_override: str | None = None,
    weeks_until_value_loss: float | None = None,
    competitor_price: float | None = None,
    sales_drop_percent: float | None = None,
    stated_price: float | None = None,
) -> dict:
    # One context object is passed down the line. Each agent fills its own fields.
    ctx = RunContext(
        product_code=product_code,
        stock_on_hand=stock_on_hand,
        unit_cost=unit_cost,
        csv_path=csv_path,
        manager_override=manager_override,
        weeks_until_value_loss=weeks_until_value_loss,
        competitor_price=competitor_price,
        sales_drop_percent=sales_drop_percent,
        stated_price=stated_price,
    )
    for agent in AGENTS:
        # Stop the chain after the first error, but still build the failed view.
        if ctx.failed and agent.name != "dashboard":
            continue
        agent.run(ctx)
    # The page reads dashboard. agent_log is the ten one-line notes, in order.
    return {
        "dashboard": ctx.dashboard,
        "agent_log": ctx.agent_log,
        "errors": ctx.errors,
    }
