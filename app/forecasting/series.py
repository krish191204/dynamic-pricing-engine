"""Insert the Mondays that a sales file skipped."""

from __future__ import annotations

from datetime import date, timedelta

from app.context import WeekPoint

# More than this share of weeks at zero is intermittent demand.
ZERO_SHARE_LIMIT = 0.30


def zero_fill(points: list[WeekPoint]) -> tuple[list[WeekPoint], list[date]]:
    """Fill every Monday from the first week to the last.

    A missing week is 0 units and has no price. The weeks already in `points`
    are kept as they are. The first and last week are never invented.
    """
    if len(points) < 2:
        return list(points), []
    by_date = {point.week_start: point for point in points}
    day = points[0].week_start
    end = points[-1].week_start
    filled: list[WeekPoint] = []
    gaps: list[date] = []
    while day <= end:
        if day in by_date:
            filled.append(by_date[day])
        else:
            gaps.append(day)
            filled.append(WeekPoint(week_start=day, quantity=0.0, avg_price=None, filled=True))
        day += timedelta(days=7)
    return filled, gaps


def intermittent_demand(zero_weeks: int, total_weeks: int) -> bool:
    """True when zero weeks are strictly more than 30% of the series."""
    if total_weeks <= 0:
        return False
    return zero_weeks / total_weeks > ZERO_SHARE_LIMIT
