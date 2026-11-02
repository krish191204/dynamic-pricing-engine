from datetime import date, timedelta

from app.context import WeekPoint
from app.factor_desk import score_sku_factors, spearman
from app.orchestrator import run_analysis


def test_spearman_is_one_on_a_perfect_rank_and_minus_one_when_reversed():
    assert abs(spearman([1, 2, 3, 4, 5], [10, 20, 30, 40, 50]) - 1) < 1e-9
    assert abs(spearman([1, 2, 3, 4, 5], [50, 40, 30, 20, 10]) + 1) < 1e-9


def test_factor_uses_only_this_week_so_next_week_units_are_the_target():
    weeks = [
        WeekPoint(date(2024, 1, 1) + timedelta(weeks=i), 100 - i * 5, 10 + i)
        for i in range(12)
    ]
    report = score_sku_factors(weeks)
    assert report["usable"] is True
    assert report["lookahead"] == "none"
    assert report["target"] == "next week's units"
    assert report["window"] == 5
    slugs = {row["slug"] for row in report["factors"]}
    assert slugs == {"shelf_price", "units_sold", "sales_value"}
    assert all(row["lookahead"] == "none" for row in report["factors"])


def test_jacket_run_keeps_golden_price_and_adds_a_workbook():
    result = run_analysis(
        "data/sample_sales.csv",
        "JACKET-01",
        stock_on_hand=400,
        unit_cost=40,
        weeks_until_value_loss=4,
        competitor_price=70,
        sales_drop_percent=15,
    )
    board = result["dashboard"]
    assert board["price_action"] == "match_market"
    assert board["suggested_price"] == 70
    book = board["workbook"]
    assert " / 4 = 65" in " ".join(book["forecast"]["lines"])
    assert book["factors"]["weeks"] == 7
    assert any("Rank IC" in line for line in book["desk"]["lines"])
