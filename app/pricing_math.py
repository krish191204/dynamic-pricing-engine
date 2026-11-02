"""One profit score, shared by the four choices and the price slider.

The 20% step limit is applied by the pricing agent before it calls this,
and again by the guardrail on the suggestion. This function does not cap.
"""

from __future__ import annotations


def score_price(price, current, forecast, drop, stock, cost, horizon):
    """Profit, demand, and leftover stock at one price.

    drop is the percent sales fall if the price rises 10%. A drop of 0
    means demand does not move. Returns None when there is no current price.
    """
    if current is None or current <= 0:
        return None
    price = round(float(price), 2)
    # Relative price move from last week's average. 0.10 means 10% higher.
    move = (price - current) / current
    # drop/10 scales the typed "fall if price rises 10%" onto this move.
    # Example: drop 15, rise 10% → factor = 1 + 0.10 × (−1.5) = 0.85.
    factor = 1 + move * (-float(drop) / 10)
    demand = max(0.0, float(forecast) * factor)
    horizon = float(horizon or 0)
    stock = float(stock)
    cost = float(cost)
    if demand <= 0 or horizon <= 0:
        sellable = min(stock, demand)
    else:
        sellable = min(stock, demand * horizon)
    wasted = stock - sellable
    # Unsold stock is a total loss at unit cost (newsvendor-style payoff).
    profit = (price - cost) * sellable - cost * wasted
    return {
        "price": price,
        "demand": round(demand, 1),
        "sellable": round(sellable, 1),
        "wasted": round(wasted, 1),
        "profit": round(profit, 2),
        "below_cost": price < cost,
    }


def price_curve(current, forecast, drop, stock, cost, horizon, anchors=None):
    """Points from unit cost up to a little above the shelf price.

    The suggestion, the current price, and the market price are included
    when they are positive, so the slider can land on them exactly.
    """
    if current is None or current <= 0 or forecast is None:
        return []
    current = float(current)
    cost = float(cost or 0)
    low = round(cost, 2) if cost > 0 else round(current * 0.5, 2)
    top = max(current * 1.35, low)
    extra = [round(current, 2)]
    for anchor in anchors or []:
        if anchor is None:
            continue
        anchor = round(float(anchor), 2)
        if anchor <= 0:
            continue
        extra.append(anchor)
        if anchor > top:
            top = anchor
    if top <= low:
        top = low + 1
    prices = [round(low + (top - low) * i / 20, 2) for i in range(21)]
    prices.extend(extra)
    points = []
    seen = set()
    for price in sorted(prices):
        if price < low or price in seen:
            continue
        seen.add(price)
        point = score_price(price, current, forecast, drop, stock, cost, horizon)
        if point:
            points.append(point)
    return points
