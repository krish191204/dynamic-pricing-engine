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
    quantity: int
    invoice: str = ""


@dataclass
class WeekPoint:
    week_start: date
    quantity: int
    avg_price: float


@dataclass
class RunContext:
    """One analysis run. Agents read and fill their own fields."""

    product_code: str
    stock_on_hand: int
    unit_cost: float
    csv_path: str
    # Optional manager override after a recommendation: hold | mark_down | raise
    manager_override: str | None = None

    raw_rows: list[SalesRow] = field(default_factory=list)
    clean_rows: list[SalesRow] = field(default_factory=list)
    dropped: list[dict[str, Any]] = field(default_factory=list)
    weekly: list[WeekPoint] = field(default_factory=list)

    forecast_units: float | None = None
    forecast_method: str = ""
    recent_average: float | None = None

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
        return bool(self.errors)
