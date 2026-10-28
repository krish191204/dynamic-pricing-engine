from pathlib import Path

from app.orchestrator import run_analysis

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample_sales.csv"


def analyse(csv_path, product, **extra):
    fields = {
        "stock_on_hand": 0,
        "unit_cost": 0,
        "weeks_until_value_loss": 4,
        "competitor_price": 70,
        "sales_drop_percent": 15,
    }
    fields.update(extra)
    return run_analysis(
        str(csv_path),
        product,
        fields.pop("stock_on_hand"),
        fields.pop("unit_cost"),
        **fields,
    )


def test_refuses_to_forecast_without_market_inputs():
    result = run_analysis(str(SAMPLE), "ANY-SKU", stock_on_hand=10, unit_cost=5)
    assert any("market price" in error for error in result["errors"])
    assert any("loses its value" in error for error in result["errors"])
    assert result["dashboard"]["status"] == "failed"


def test_ten_agents_run_and_recommend_markdown_when_stock_is_high():
    result = analyse(SAMPLE, "JACKET-01", stock_on_hand=400, unit_cost=40)
    assert result["errors"] == []
    assert len(result["agent_log"]) == 10
    board = result["dashboard"]
    assert board["price_action"] == "match_market"
    assert board["suggested_price"] == 70
    assert board["inventory_alert"] == "clear"
    assert board["suggested_price"] >= 40
    assert board["status"] == "pending"


def test_cancelled_invoice_is_dropped():
    result = analyse(SAMPLE, "JACKET-01", stock_on_hand=400, unit_cost=40)
    dropped = result["dashboard"]["dropped"]
    assert any("cancelled" in line for line in dropped)
    assert any("HAT-02" in line for line in dropped)
    assert result["dashboard"]["dropped_rows"] == 2


def test_unknown_product_is_not_mixed_with_other_rows():
    flawed = Path(__file__).resolve().parents[1] / "data" / "flawed_sales.csv"
    result = analyse(
        flawed,
        "Fresh bread",
        stock_on_hand=200,
        unit_cost=1.2,
        weeks_until_value_loss=2,
        competitor_price=1.8,
        sales_drop_percent=15,
    )
    assert result["dashboard"]["status"] == "failed"
    assert any("BREAD-01" in error and "CAKE-02" in error for error in result["errors"])


def test_flawed_bread_file_stays_on_one_product_and_names_problems():
    flawed = Path(__file__).resolve().parents[1] / "data" / "flawed_sales.csv"
    result = analyse(
        flawed,
        "bread-01",
        stock_on_hand=200,
        unit_cost=1.2,
        weeks_until_value_loss=2,
        competitor_price=1.8,
        sales_drop_percent=15,
    )
    assert result["errors"] == []
    board = result["dashboard"]
    assert board["product_code"] == "BREAD-01"
    assert board["forecast_units"] == 27.5
    assert board["current_price"] == 2.81
    assert board["suggested_price"] == 2.39
    assert all(week["week"] != "2024-04-01" for week in board["history"])
    text = " ".join(board["warnings"] + board["dropped"])
    assert "CAKE-02" in text
    assert "03/04/2024" in text
    assert "does not equal" in text
    assert "weak guess" in board["evaluation"]


def test_thin_stock_can_raise_when_forecast_jumps(tmp_path: Path):
    csv_path = tmp_path / "surge.csv"
    # Earlier weeks are quiet, last four weeks jump.
    lines = ["date,product,price,quantity,invoice"]
    quiet = ["2024-08-05", "2024-08-12", "2024-08-19", "2024-08-26"]
    busy = ["2024-09-02", "2024-09-09", "2024-09-16", "2024-09-23"]
    for index, day in enumerate(quiet):
        lines.append(f"{day},PHONE-1,100,20,Q{index}")
    for index, day in enumerate(busy):
        lines.append(f"{day},PHONE-1,100,80,B{index}")
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result = analyse(
        csv_path,
        "PHONE-1",
        stock_on_hand=30,
        unit_cost=50,
        weeks_until_value_loss=12,
        competitor_price=110,
        sales_drop_percent=10,
    )
    assert result["dashboard"]["price_action"] == "raise"
    assert result["dashboard"]["inventory_alert"] == "reorder"


def test_guardrail_blocks_price_below_cost(tmp_path: Path):
    csv_path = tmp_path / "cheap.csv"
    lines = ["date,product,price,quantity,invoice"]
    days = ["2024-08-05", "2024-08-12", "2024-08-19", "2024-08-26", "2024-09-02"]
    for index, day in enumerate(days):
        qty = 10 if index < 4 else 2
        lines.append(f"{day},MUG-1,10,{qty},M{index}")
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # Cost is above the current price, so a markdown would fall through the floor.
    result = analyse(
        csv_path,
        "MUG-1",
        stock_on_hand=500,
        unit_cost=12,
        weeks_until_value_loss=8,
        competitor_price=9,
        sales_drop_percent=10,
    )
    assert result["dashboard"]["suggested_price"] >= 12
    assert any("below unit cost" in note for note in result["dashboard"]["guardrails"])
