from pathlib import Path

from app.orchestrator import run_analysis

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample_sales.csv"


def test_ten_agents_run_and_recommend_markdown_when_stock_is_high():
    result = run_analysis(str(SAMPLE), "JACKET-01", stock_on_hand=400, unit_cost=40)
    assert result["errors"] == []
    assert len(result["agent_log"]) == 10
    board = result["dashboard"]
    assert board["price_action"] == "mark_down"
    assert board["inventory_alert"] == "clear"
    assert board["suggested_price"] >= 40
    assert board["status"] == "pending"


def test_cancelled_invoice_is_dropped():
    result = run_analysis(str(SAMPLE), "JACKET-01", stock_on_hand=400, unit_cost=40)
    assert result["dashboard"]["dropped_rows"] == 1


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
    result = run_analysis(str(csv_path), "PHONE-1", stock_on_hand=30, unit_cost=50)
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
    result = run_analysis(str(csv_path), "MUG-1", stock_on_hand=500, unit_cost=12)
    assert result["dashboard"]["suggested_price"] >= 12
    assert any("below unit cost" in note for note in result["dashboard"]["guardrails"])
