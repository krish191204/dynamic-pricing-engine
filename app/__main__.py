"""Run the sample jacket case from the project overview."""

import json

from app.orchestrator import run_analysis
from pathlib import Path

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample_sales.csv"


def main() -> None:
    # High stock and a falling jacket series. The market price is inside the 20% step, so the run matches it.
    ending = run_analysis(
        str(SAMPLE),
        "JACKET-01",
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
