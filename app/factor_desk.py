"""QuantSkills-style factor checks on one product's weeks.

The factory at quantskills/skill-quant-factor-skill-factory scores OHLCV
factors with coverage, rolling Rank IC, ICIR, Q5-Q1, and a no-lookahead
rule. This module uses the same checklist on a shop panel:

  date   -> week start
  symbol -> product code
  close  -> average shelf price that week
  volume -> units sold that week

The target is next week's units, not a stock return. Factor values at week
t use only that week's price and units. The suggestion on the page still
comes from the four-week mean; these numbers are the desk report.
"""

from __future__ import annotations

import math
from typing import Any


# Five weeks, standing in for the factory's five-day Rank IC window.
WINDOW = 5


def _ranks(values: list[float]) -> list[float]:
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(ordered):
        j = i
        while j + 1 < len(ordered) and ordered[j + 1][1] == ordered[i][1]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[ordered[k][0]] = avg
        i = j + 1
    return ranks


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if den_x < 1e-12 or den_y < 1e-12:
        return None
    return num / (den_x * den_y)


def spearman(xs: list[float], ys: list[float]) -> float | None:
    """Pearson correlation of the ranks. 1 = same order, −1 = reversed."""
    if len(xs) != len(ys) or len(xs) < 3:
        return None
    return _pearson(_ranks(xs), _ranks(ys))


def _mean(xs: list[float]) -> float | None:
    return None if not xs else sum(xs) / len(xs)


def _std(xs: list[float]) -> float | None:
    if len(xs) < 2:
        return None
    mean = sum(xs) / len(xs)
    var = sum((x - mean) ** 2 for x in xs) / (len(xs) - 1)
    return math.sqrt(var) if var > 0 else 0.0


def _rolling_rank_ic(factor: list[float], forward: list[float], window: int = WINDOW) -> list[float]:
    ics: list[float] = []
    n = min(len(factor), len(forward))
    for end in range(window, n + 1):
        value = spearman(factor[end - window : end], forward[end - window : end])
        if value is not None:
            ics.append(value)
    return ics


def _quintile_spread(factor: list[float], forward: list[float]) -> float | None:
    pairs = [(f, y) for f, y in zip(factor, forward)]
    if len(pairs) < 10:
        return None
    pairs.sort(key=lambda item: item[0])
    width = max(1, len(pairs) // 5)
    low = [item[1] for item in pairs[:width]]
    high = [item[1] for item in pairs[-width:]]
    return sum(high) / len(high) - sum(low) / len(low)


def score_sku_factors(weekly) -> dict[str, Any]:
    """Coverage, Rank IC, ICIR, Q5-Q1 on this product. No other SKUs.

    Does not change suggested_price. The page prints this on the Trust step.
    """
    prices = [float(point.avg_price) for point in weekly]
    units = [float(point.quantity) for point in weekly]
    n = len(prices)
    if n < WINDOW + 1:
        return {
            "usable": False,
            "window": WINDOW,
            "weeks": n,
            "factors": [],
            "note": (
                f"Need at least {WINDOW + 1} weeks to roll a {WINDOW}-week Rank IC "
                "the way a factor desk would. This file is too short."
            ),
        }
    # Target at week t is units in week t+1. Using units[t+1] in the factor
    # itself would be lookahead; that is why factor series are prices[:-1].
    forward = units[1:]
    series = {
        "shelf_price": prices[:-1],
        "units_sold": units[:-1],
        "sales_value": [p * q for p, q in zip(prices[:-1], units[:-1])],
    }
    labels = {
        "shelf_price": "This week's shelf price",
        "units_sold": "This week's units",
        "sales_value": "This week's sales value (price × units)",
    }
    rows = []
    for slug, factor in series.items():
        pairs = [(f, y) for f, y in zip(factor, forward) if f > 0 and y > 0]
        coverage = len(pairs) / max(len(forward), 1)
        ics = _rolling_rank_ic(factor, forward)
        mean_ic = _mean(ics)
        std_ic = _std(ics)
        icir = None if mean_ic is None or std_ic in (None, 0) else mean_ic / std_ic
        spread = _quintile_spread(factor, forward)
        status = "pass" if coverage >= 0.5 and len(ics) >= 3 else "review"
        rows.append(
            {
                "slug": slug,
                "name": labels[slug],
                "coverage": round(coverage, 3),
                "windows": len(ics),
                "rank_ic": None if mean_ic is None else round(mean_ic, 3),
                "icir": None if icir is None else round(icir, 3),
                "q5_q1": None if spread is None else round(spread, 1),
                "lookahead": "none",
                "status": status,
            }
        )
    price_row = next(row for row in rows if row["slug"] == "shelf_price")
    ic = price_row["rank_ic"]
    if ic is None:
        story = "Not enough moving prices to score Rank IC."
    elif ic < -0.05:
        story = (
            f"Higher-price weeks tend to come before quieter next weeks "
            f"(Rank IC {ic} on a {WINDOW}-week roll). That is the sign a desk wants "
            "if a price cut is supposed to lift units."
        )
    elif ic > 0.05:
        story = (
            f"Higher-price weeks tend to come before busier next weeks "
            f"(Rank IC {ic}). Price here is probably tracking demand, not causing it."
        )
    else:
        story = (
            f"Shelf price barely ranks with next week's units (Rank IC {ic}). "
            "Your typed sales-fall percent is doing the work the history will not."
        )
    return {
        "usable": True,
        "window": WINDOW,
        "weeks": n,
        "target": "next week's units",
        "lookahead": "none",
        "factors": rows,
        "note": story,
        "source": "QuantSkills factor checklist (coverage, Rank IC, ICIR, Q5-Q1, no lookahead), scored on this SKU.",
    }


def factor_lines(report: dict[str, Any]) -> list[str]:
    if not report.get("usable"):
        return [report.get("note") or ""]
    lines = [
        report["note"],
        (
            f"Panel: {report['weeks']} weeks of one product. Target is {report['target']}. "
            f"Factor at week t uses only week t. Rolling window is {report['window']} weeks."
        ),
    ]
    for row in report.get("factors") or []:
        ic = "n/a" if row["rank_ic"] is None else f"{row['rank_ic']}"
        icir = "n/a" if row["icir"] is None else f"{row['icir']}"
        spread = "n/a" if row["q5_q1"] is None else f"{row['q5_q1']:g} units"
        lines.append(
            f"{row['name']}: coverage {row['coverage']:g}, Rank IC {ic}, "
            f"ICIR {icir}, Q5−Q1 {spread}, lookahead {row['lookahead']}, {row['status']}."
        )
    lines.append(report["source"])
    return [line for line in lines if line]
