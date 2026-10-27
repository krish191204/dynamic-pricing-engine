# Dynamic pricing and predictive inventory engine

Phase 1 of the group project: ten specialist agents answer two questions for one product.

1. How many units next week? (mean of the last four weeks)
2. What should the price be now? (hold, mark down, or raise), plus a stock alert.

Recommendations stay pending until a manager sends an override. Nothing here changes a live shop.

## Agents

| Order | Agent | Arena |
|------:|-------|--------|
| 1 | Requirements | Inputs for Phase 1 |
| 2 | Data | Load the sales CSV |
| 3 | Cleaning | Drop cancelled and non-positive rows |
| 4 | Transform | Weekly quantity and average price |
| 5 | Forecast | Next week's demand |
| 6 | Inventory | Reorder, clear, or ok |
| 7 | Pricing | Hold, mark down, or raise |
| 8 | Guardrail | Not below cost; at most 20% in one step |
| 9 | Evaluation | Hold-out MAPE on the latest week |
| 10 | Dashboard | Chart data, reason, approval status |

## Run

```bash
cd dynamic_pricing_engine
python3 -m app
python3 -m pytest tests -q
```

API (optional):

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

`POST /runs` with JSON:

```json
{"product_code": "JACKET-01", "stock_on_hand": 400, "unit_cost": 40}
```

CSV columns: `date`, `product`, `price`, `quantity`, optional `invoice`. A leading `C` on the invoice marks a cancellation.
