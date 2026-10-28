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
        current = ctx.current_price or 0
        drop = ctx.sales_drop_percent if ctx.sales_drop_percent is not None else 0
        horizon = ctx.weeks_until_value_loss or 0
        # Four fixed choices, not a fitted price. 15% down, 10% up, or the typed market price.
        candidates = [
            ("hold", current),
            ("mark_down", round(current * 0.85, 2)),
            ("raise", round(current * 1.10, 2)),
        ]
        if ctx.competitor_price and ctx.competitor_price > 0:
            candidates.append(("match_market", round(ctx.competitor_price, 2)))

        options = []
        for action, price in candidates:
            if current <= 0:
                continue
            move = (price - current) / current
            # A market price far from history is pulled back to a 20% step before scoring.
            if abs(move) > 0.20:
                price = round(current * (1 + 0.20 * (1 if move > 0 else -1)), 2)
                move = (price - current) / current
            # drop is "sales fall this many percent if price rises 10%".
            # drop 0 means demand never moves, so the higher price always wins.
            factor = 1 + move * (-drop / 10)
            demand = max(0.0, forecast * factor)
            # Sell only what demand can take before the stock loses its value. The rest is wasted.
            if demand <= 0 or horizon <= 0:
                sellable = min(ctx.stock_on_hand, demand)
                wasted = ctx.stock_on_hand - sellable
            else:
                sellable = min(ctx.stock_on_hand, demand * horizon)
                wasted = ctx.stock_on_hand - sellable
            # Unsold stock past the horizon is a total loss at unit cost.
            profit = (price - ctx.unit_cost) * sellable - ctx.unit_cost * wasted
            options.append(
                {
                    "action": action,
                    "price": round(price, 2),
                    "demand": round(demand, 1),
                    "sellable": round(sellable, 1),
                    "wasted": round(wasted, 1),
                    "profit": round(profit, 2),
                    "below_cost": price < ctx.unit_cost,
                }
            )
        ctx.price_options = options
        # Cost more than 1.5 times the history price means the file and the form are different products.
        if current > 0 and ctx.unit_cost > current * 1.5:
            ctx.errors.append(
                f"Unit cost {ctx.unit_cost:g} is far above the price in the sales history ({current:g}). "
                "Those are not the same product. Untick the sample, or paste a history whose prices match this cost."
            )
            return ctx
        # Prefer a price at or above cost. If every choice is under cost, keep them and let the guardrail move the winner.
        legal = [option for option in options if not option["below_cost"]] or options
        best = max(legal, key=lambda option: option["profit"])
        ctx.price_action = best["action"]
        ctx.suggested_price = best["price"]
        capped = ""
        if ctx.competitor_price and abs(ctx.competitor_price - current) / current > 0.20:
            capped = (
                f" The market price {ctx.competitor_price:g} is more than 20% away from {current:g}, "
                f"so a match is limited to {best['price'] if best['action'] == 'match_market' else round(current * (1.2 if ctx.competitor_price > current else 0.8), 2)}."
            )
        ctx.pricing_reason = (
            f"Compared hold, a 15% markdown, a 10% rise, and the market price {ctx.competitor_price:g}. "
            f"The highest profit is {best['profit']} at {best['price']}."
            f"{capped}"
        )
        self.note(ctx, ctx.price_action)
        return ctx
