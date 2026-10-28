"""Arena: dashboard and approval. Owners: Hei and Alvin.

Builds the manager view and applies an optional override.
Prices stay recommendations until a person approves them.
"""

from __future__ import annotations

from app.agents.base import Agent
from app.context import RunContext


class DashboardAgent(Agent):
    name = "dashboard"
    arena = "dashboard"
    owner = "Hei"

    def run(self, ctx: RunContext) -> RunContext:
        if ctx.failed:
            ctx.approval_status = "failed"
            ctx.dashboard = {"status": "failed", "errors": ctx.errors}
            return ctx
        action = ctx.price_action
        status = "pending"
        # The form does not send an override yet. The API accepts hold, mark_down, or raise.
        if ctx.manager_override:
            action = ctx.manager_override
            status = "overridden"
            if action == "hold":
                ctx.suggested_price = ctx.current_price
            elif action == "mark_down" and ctx.current_price is not None:
                ctx.suggested_price = round(ctx.current_price * 0.85, 2)
            elif action == "raise" and ctx.current_price is not None:
                ctx.suggested_price = round(ctx.current_price * 1.10, 2)
            # Same 15% / 10% steps as pricing. A markdown that lands under cost is lifted.
            if ctx.suggested_price is not None and ctx.suggested_price < ctx.unit_cost:
                ctx.suggested_price = round(ctx.unit_cost, 2)
                ctx.guardrail_notes.append("Override was lifted to unit cost.")
        ctx.approval_status = status
        ctx.price_action = action
        ctx.dashboard = {
            "status": status,
            "product_code": ctx.product_code,
            "history": [
                {"week": point.week_start.isoformat(), "quantity": point.quantity, "avg_price": point.avg_price}
                for point in ctx.weekly
            ],
            "forecast_units": ctx.forecast_units,
            "forecast_method": ctx.forecast_method,
            "price_action": action,
            "current_price": ctx.current_price,
            "suggested_price": ctx.suggested_price,
            "pricing_reason": ctx.pricing_reason,
            "inventory_alert": ctx.inventory_alert,
            "inventory_reason": ctx.inventory_reason,
            "weeks_of_cover": ctx.weeks_of_cover,
            "guardrails": ctx.guardrail_notes,
            "evaluation": ctx.evaluation_note,
            "mape": ctx.mape,
            "dropped_rows": len(ctx.dropped),
            "dropped": [
                f"Invoice {item['invoice']}: {item['reason']}" if item.get("invoice") else item["reason"]
                for item in ctx.dropped
            ],
            "warnings": list(ctx.warnings),
            "weeks_until_value_loss": ctx.weeks_until_value_loss,
            "competitor_price": ctx.competitor_price,
            "sales_drop_percent": ctx.sales_drop_percent,
            "price_options": ctx.price_options,
            "intake_note": ctx.intake_note,
        }
        self.note(ctx, f"view ready, approval {status}")
        return ctx
