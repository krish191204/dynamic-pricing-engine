"""Plain-language arithmetic for one run.

The suggestion still comes from the four-week mean and the sales-fall
percent the operator typed. This module only writes the working, and a
log-log slope from the weekly history so the page can put that slope
next to the typed guess.
"""

from __future__ import annotations

import math
from typing import Any

from app.factor_desk import factor_lines, score_sku_factors


def elasticity_from_weeks(weekly) -> dict[str, Any]:
    """OLS of log quantity on log price. Needs several different prices."""
    pairs = [
        (float(point.avg_price), float(point.quantity))
        for point in weekly
        if getattr(point, "avg_price", 0) > 0 and getattr(point, "quantity", 0) > 0
    ]
    distinct = {round(price, 2) for price, _qty in pairs}
    if len(pairs) < 4 or len(distinct) < 3:
        return {
            "usable": False,
            "weeks_used": len(pairs),
            "distinct_prices": len(distinct),
            "elasticity": None,
            "r_squared": None,
            "implied_drop_percent": None,
            "note": (
                "The weeks do not move price enough to read a slope. "
                "A desk would need more weeks where the shelf price actually changed."
            ),
        }
    xs = [math.log(price) for price, _qty in pairs]
    ys = [math.log(qty) for _price, qty in pairs]
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    var_x = sum((x - mean_x) ** 2 for x in xs)
    if var_x < 1e-12:
        return {
            "usable": False,
            "weeks_used": n,
            "distinct_prices": len(distinct),
            "elasticity": None,
            "r_squared": None,
            "implied_drop_percent": None,
            "note": "Every week is the same price, so a slope cannot be read.",
        }
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    slope = cov / var_x
    fitted = [mean_y + slope * (x - mean_x) for x in xs]
    sst = sum((y - mean_y) ** 2 for y in ys)
    sse = sum((y - yhat) ** 2 for y, yhat in zip(ys, fitted))
    r_squared = None if sst < 1e-12 else 1 - sse / sst
    implied = (1 - (1.1**slope)) * 100
    noisy = r_squared is not None and r_squared < 0.15
    note = (
        f"Across {n} weeks, log units on log price has slope {slope:.3f}. "
        f"A 10% higher price would cut units by about {implied:.1f}% if that slope held."
    )
    if noisy:
        note += " The fit is weak, so treat that percent as a sketch, not a fact."
    return {
        "usable": True,
        "weeks_used": n,
        "distinct_prices": len(distinct),
        "elasticity": round(slope, 3),
        "r_squared": None if r_squared is None else round(r_squared, 3),
        "implied_drop_percent": round(implied, 1),
        "note": note,
    }


def explain_run(ctx) -> dict[str, Any]:
    """Step list the page can print. Numbers match score_price and the agents.

    This is the 'show the working' layer. It must not pick a different price.
    """
    weekly = ctx.weekly or []
    last_four = [point.quantity for point in weekly[-4:]]
    forecast = ctx.forecast_units
    current = ctx.current_price
    drop = ctx.sales_drop_percent if ctx.sales_drop_percent is not None else 0
    suggested = ctx.suggested_price
    stock = ctx.stock_on_hand
    cost = ctx.unit_cost
    horizon = ctx.weeks_until_value_loss or 0
    chosen = next((row for row in ctx.price_options if row.get("action") == ctx.price_action), None)
    from_weeks = elasticity_from_weeks(weekly)

    forecast_lines = []
    if last_four and forecast is not None:
        shown = " + ".join(f"{qty:g}" for qty in last_four)
        forecast_lines.append(f"Last four weekly totals: {shown}.")
        forecast_lines.append(f"Next week = ({shown}) / {len(last_four)} = {forecast:g}.")
        forecast_lines.append("Empty weeks are skipped, not stored as zero.")
        forecast_lines.append(
            "A hired desk might try a smoother (ETS) or a slow-mover rule (Croston). "
            "This page keeps the mean until something beats the hold-out below."
        )

    demand_lines = []
    profit_lines = []
    if current and current > 0 and suggested is not None and forecast is not None:
        move = (suggested - current) / current
        factor = 1 + move * (-float(drop) / 10)
        demand = max(0.0, float(forecast) * factor)
        demand_lines.append(
            f"You typed: a 10% higher price cuts sales by {drop:g}%."
        )
        demand_lines.append(
            f"Price move = ({suggested:g} − {current:g}) / {current:g} = {move * 100:.1f}%."
        )
        demand_lines.append(
            f"Demand factor = 1 + {move:.4f} × (−{drop:g} / 10) = {factor:.4f}."
        )
        demand_lines.append(
            f"Next-week demand = {forecast:g} × {factor:.4f} = {demand:.1f}."
        )
        if from_weeks["usable"]:
            demand_lines.append(
                f"From your own weeks, the same 10% rise would cut sales by about "
                f"{from_weeks['implied_drop_percent']:g}% "
                f"(elasticity {from_weeks['elasticity']:g}, "
                f"R² {from_weeks['r_squared'] if from_weeks['r_squared'] is not None else 'n/a'}). "
                "The price still uses the percent you typed, so you can recompute it."
            )
        else:
            demand_lines.append(from_weeks["note"])

        if chosen:
            sellable = chosen["sellable"]
            wasted = chosen["wasted"]
            profit = chosen["profit"]
            profit_lines.append(
                f"Units you can sell before the stock goes off = "
                f"min({stock:g}, {chosen['demand']:g} × {horizon:g}) = {sellable:g}."
            )
            profit_lines.append(f"Left over = {stock:g} − {sellable:g} = {wasted:g}.")
            profit_lines.append(
                f"Profit = ({suggested:g} − {cost:g}) × {sellable:g} − {cost:g} × {wasted:g} = {profit:g}."
            )
            profit_lines.append(
                "Leftover stock is counted as a total loss at unit cost. "
                "That is the same idea as a newsvendor payoff, scored on four prices, not a fitted curve."
            )
            if suggested > 0:
                ratio = (suggested - cost) / suggested
                profit_lines.append(
                    f"Critical ratio at this price = ({suggested:g} − {cost:g}) / {suggested:g} = {ratio:.2f}. "
                    "A desk stocking from a demand distribution would aim at that quantile. "
                    "This page still uses the stock you typed."
                )

    cover_lines = []
    if forecast and forecast > 0 and ctx.weeks_of_cover is not None:
        cover_lines.append(
            f"Weeks of cover = {stock:g} / {forecast:g} = {ctx.weeks_of_cover:g}."
        )
        cover_lines.append("Under 2 weeks: reorder. Longer than the weeks-until-value-loss you typed: clear.")
        cover_lines.append(ctx.inventory_reason or "")

    holdout_lines = []
    if ctx.evaluation_note:
        holdout_lines.append(ctx.evaluation_note)
        if len(weekly) >= 5:
            hidden = weekly[-1].quantity
            guess = sum(point.quantity for point in weekly[-5:-1]) / 4
            holdout_lines.append(
                f"Hide the latest week ({hidden:g}). Mean of the four before it = {guess:.1f}."
            )
        holdout_lines.append(
            "The miss does not change the price. It tells you how wrong that average was last time."
        )

    factors = score_sku_factors(weekly)
    return {
        "promise": (
            "This run stands in for a pricing person a small shop cannot hire. "
            "Every line below is the arithmetic that produced the number on the page. "
            "Nothing is written to a till."
        ),
        "from_your_weeks": from_weeks,
        "factors": factors,
        "forecast": {"title": "How next week was counted", "lines": [line for line in forecast_lines if line]},
        "demand": {"title": "How demand moves with price", "lines": demand_lines},
        "profit": {"title": "How profit was scored", "lines": profit_lines},
        "cover": {"title": "How cover was counted", "lines": [line for line in cover_lines if line]},
        "holdout": {"title": "How the miss was counted", "lines": holdout_lines},
        "desk": {
            "title": "Factor desk on this product",
            "lines": factor_lines(factors),
        },
    }
