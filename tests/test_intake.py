from pathlib import Path

from app.intake import read_sales_report
from app.orchestrator import run_analysis

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample_sales.csv"


def test_reads_a_titled_sales_report_with_revenue():
    text = """Weekly sales report
Store: North
Week ending\tUnits sold\tSales
2024-08-02\t20\t2000
2024-08-09\t20\t2000
2024-08-16\t22\t2200
2024-08-23\t24\t2400
2024-08-30\t30\t3000
"""
    rows, note, _warnings = read_sales_report(text, "Milk", None)
    assert len(rows) == 5
    assert rows[0].unit_price == 100
    assert "Units sold" in note


def test_asks_for_a_price_when_the_report_has_none(tmp_path: Path):
    path = tmp_path / "qty-only.txt"
    path.write_text(
        "Order date,Qty\n2024-08-05,10\n2024-08-12,10\n2024-08-19,10\n2024-08-26,12\n",
        encoding="utf-8",
    )
    result = run_analysis(
        str(path),
        "Bread",
        40,
        1,
        weeks_until_value_loss=2,
        competitor_price=2,
        sales_drop_percent=10,
    )
    assert any("current price" in error for error in result["errors"])


def test_uci_style_header_loads():
    text = """InvoiceNo,StockCode,Description,Quantity,InvoiceDate,UnitPrice
536365,85123A,WHITE MUG,6,01/12/2010 08:26,2.55
536365,71053,WHITE MUG,6,08/12/2010 08:26,2.55
536366,84406B,CREAM CUP,8,15/12/2010 08:26,2.75
536367,84406B,CREAM CUP,6,22/12/2010 08:26,2.75
"""
    rows, note, _warnings = read_sales_report(text, "MUG", None)
    assert len(rows) == 4
    assert "InvoiceDate" in note
    assert rows[0].invoice == "536365"


def test_existing_sample_still_loads():
    rows, note, _warnings = read_sales_report(SAMPLE.read_text(encoding="utf-8"), "JACKET-01", None)
    assert len(rows) == 16
    assert "quantity" in note or "Quantity" in note or "quantity" in note.lower()
