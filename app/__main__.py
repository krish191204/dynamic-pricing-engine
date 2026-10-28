"""Run the sample jacket case from the project overview."""

import json

from app.orchestrator import run_analysis
from pathlib import Path

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample_sales.csv"


def main() -> None:
    # Season ending: lots of stock, soft recent weeks -> markdown + clear.
    ending = run_analysis(
        str(SAMPLE),
        "SAMPLE-SKU",
        stock_on_hand=400,
        unit_cost=40,
        weeks_until_value_loss=4,
        competitor_price=70,
        sales_drop_percent=15,
    )
    # Cold snap file uses the same history; high stock cover still holds or clears
    # depending on the last four weeks in sample_sales.csv.
    print(json.dumps(ending["dashboard"], indent=2))
    print("--- agents ---")
    for line in ending["agent_log"]:
        print(line)


if __name__ == "__main__":
    main()
