"""Shared state passed through the ten specialist agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class SalesRow:
    sold_on: date
    product_code: str
    unit_price: float
    quantity: float
    invoice: str = ""


@dataclass
class WeekPoint:
    week_start: date
    quantity: float
    avg_price: float


@dataclass
class RunContext:
    """One analysis run. Agents read and fill their own fields."""

    product_code: str
    stock_on_hand: float
    unit_cost: float
    csv_path: str
    # How long until unsold stock is worth nothing (spoilage, season, expiry).
    weeks_until_value_loss: float | None = None
    # A price observed in the market right now. The user supplies it.
    competitor_price: float | None = None
    # If our price rises 10%, sales fall by this many percent.
    sales_drop_percent: float | None = None
    # Used when the sales report has quantities and dates but no price column.
    stated_price: float | None = None
    intake_note: str = ""
    warnings: list[str] = field(default_factory=list)
    # Optional manager override after a recommendation: hold | mark_down | raise
    manager_override: str | None = None
    price_options: list[dict[str, Any]] = field(default_factory=list)

    raw_rows: list[SalesRow] = field(default_factory=list)  # every parsed line
    clean_rows: list[SalesRow] = field(default_factory=list)  # one product, after drops
    dropped: list[dict[str, Any]] = field(default_factory=list)  # invoice + reason
    weekly: list[WeekPoint] = field(default_factory=list)  # Monday buckets, oldest first

    forecast_units: float | None = None  # mean of the last four weekly quantities
    forecast_method: str = ""
    recent_average: float | None = None  # mean of the weeks before those four

    weeks_of_cover: float | None = None
    inventory_alert: str = ""
    inventory_reason: str = ""

    price_action: str = ""  # hold | mark_down | raise
    current_price: float | None = None
    suggested_price: float | None = None
    pricing_reason: str = ""

    guardrail_notes: list[str] = field(default_factory=list)
    blocked: bool = False

    mape: float | None = None
    evaluation_note: str = ""

    approval_status: str = "pending"  # pending | approved | overridden
    dashboard: dict[str, Any] = field(default_factory=dict)

    errors: list[str] = field(default_factory=list)
    agent_log: list[str] = field(default_factory=list)

    @property
    def failed(self) -> bool:
        # Any message in errors stops the later agents. Dashboard still runs.
        return bool(self.errors)
