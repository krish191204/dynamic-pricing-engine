# Dynamic pricing and predictive inventory engine

One product goes in. Three answers come out: how many units to expect next week, a price to hold, mark down, raise, or match, and a stock alert (reorder, clear, or ok). A person still has to approve the price. This program does not change a live shop, a till, or a website.

Phase 1 is the part that runs today: a sales history you already have, numbers you type for stock and the market, and a recommendation on one page. Competitor feeds, automatic price changes, a forecast other than a four-week average, and several products in one run are later work. They are listed in [docs/PLAN.md](docs/PLAN.md).

The page asks you to sign in. An account is an email and a password. The password is stored as a hash in Postgres (`app_users`). A run is still not saved after you refresh.

## What you need

- Python 3.10 or newer
- A terminal
- A sales table with a date and a quantity, covering at least four separate weeks of one product

```bash
git clone https://github.com/krish191204/dynamic-pricing-engine.git
cd dynamic-pricing-engine
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows, activate with `.venv\Scripts\activate`.

Dependencies, from `requirements.txt`: FastAPI, uvicorn, python-multipart (file upload), psycopg (Postgres), pytest.

## Run the page

From the repository folder, with the virtual environment active:

```bash
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. Leave that terminal running. HTML is read on each request, so a page edit shows up on refresh. A Python edit needs the server to be started again.

Check the process without opening the page:

```bash
curl http://127.0.0.1:8000/health
```

A healthy process returns `{"status":"ok","agents":10}`.

## Sign in

Opening the page sends you to `/login`. Sign in, or create an account with the second button. The password is hashed before it is stored. Row level security is on for `app_users`, and the Supabase API roles cannot read that table. The app connects with the database password from `.env`.

Copy `.env.example` to `.env` and set `DATABASE_PASSWORD` and `SESSION_SECRET`. Do not commit `.env`.

| Variable | What it is |
|---|---|
| `DATABASE_HOST` | Session pooler host. This network is IPv4-only, and the direct `db.<project>.supabase.co` host is IPv6 unless the project has the IPv4 add-on. |
| `DATABASE_PORT` | `5432` for session mode. |
| `DATABASE_NAME` | `postgres` |
| `DATABASE_USER` | `postgres.<project-ref>` on the pooler. |
| `DATABASE_PASSWORD` | The database password. |
| `SESSION_SECRET` | A long random string used to sign the sign-in cookie. |

## Run the sample in the terminal

```bash
python3 -m app
```

That prints the dashboard for `data/sample_sales.csv`, product `JACKET-01`, stock 400, unit cost 40, 4 weeks until the stock loses value, market price 70, and a 15% sales fall if the price rises 10%. The expected result is match the market at 70, clear the stock, and a next-week forecast of 65. The same average, checked on the latest week, is off by 275%, so the result also says to treat the price as a weak guess. The same case is locked in `tests/test_pipeline.py`.

## Tests

```bash
python3 -m pytest tests -q
```

Run this from the repository folder so Python can import `app`. `tests/test_pipeline.py` covers the agent chain, the jacket sample, a product that is not in the file, the flawed bread file, a raise on thin stock, and the cost floor. `tests/test_intake.py` covers titled reports, a missing price, a UCI-style header, and the sample file.

## Fill in the form

Every number may be a decimal. Empty required fields are named before anything is sent.

| Field | What to enter |
|---|---|
| Product code | A code or name that appears in the sales table. Matching ignores case, spaces, underscores, and hyphens, so `bread-01` finds `BREAD-01`. |
| Stock on hand | Units you hold now, zero or more. The file is not asked for this. |
| Unit cost | What one unit costs you. A suggested price is not meant to sit below this. |
| Weeks until stock loses value | How long unsold units still have a sale. After that, leftover stock is treated as a total loss at unit cost. |
| Market price now | A price you have seen. There is no live feed. You type it. |
| Sales fall if price rises 10% | Your estimate. `15` means a 10% price rise cuts unit sales by 15%. `0` means demand does not move when the price moves. |
| Price now, if the report has no price | Used only when the table has dates and quantities, and neither a unit price nor a sales amount. |
| Sales report | A `.csv`, `.tsv`, or `.txt` file. |
| Or paste the table | The same kind of table, including the header row. |
| Use the built-in sample instead | Uses `data/sample_sales.csv`. |

History is chosen in this order:

1. Pasted text, if the box is not empty. A pasted table wins over a chosen file and over the sample tick.
2. Otherwise the chosen file, if there is one.
3. Otherwise the sample, and only when the box is ticked.

The sample rows are jackets (`JACKET-01`, prices around 80 to 85). After the run, the page shows the product name you typed, but the history is still the jacket file. If that jacket price and your unit cost cannot be the same product, the run stops. Untick the sample when you paste or upload your own table.

## Read the result

A finished run shows:

- The product code as it is spelled in the file.
- A headline: hold, mark down 15%, raise 10%, or match the market. The market price is pulled back to a 20% step when it is farther than that from the latest week.
- The sentence that names the profit of the chosen price.
- A pink caution when the hold-out miss is 50% or more. The headline is still the price. Read the caution before you treat the price as final.
- Next week's forecast, weeks of cover, and either the miss on the latest week or the current price when there are only four weeks.
- The stock sentence: reorder, clear, or ok.
- A table of the four prices, with demand and profit. The chosen row is marked. A negative profit is shown in red.
- One bar per week. The latest week is marked. The label under the chart is the four quantities that were averaged.
- Problems found while reading the file: warnings, then dropped rows.
- A note of which columns were used, and how many rows were skipped.

A failed run replaces that sheet with the error sentences. Fix the named input and run again. The page does not keep earlier runs.

## Sales table

The reader looks at the first 40 rows and uses the first row that contains both a date column and a quantity column. A title above that header is skipped. It tries a tab split, then a comma, then a semicolon.

There is no single required header. The first matching name wins. If `Description` appears before `StockCode`, the product is the description, and a code such as `85123A` will not match.

| Role | Accepted names |
|---|---|
| Date | date, sold on, invoice date, invoicedate, order date, orderdate, day, transaction date, sales date, week, week start, week ending, period, posting date |
| Quantity | quantity, qty, units, units sold, unit sold, sales qty, sales quantity, volume, items, count, qty sold, sold |
| Unit price | price, unit price, unitprice, selling price, asp, average price, avg price, sale price, net price |
| Sales amount | revenue, sales, net sales, amount, line total, sales amount, turnover |
| Product | product, sku, stockcode, stock code, item, item code, description, product name, product code, item name |
| Invoice | invoice, invoiceno, invoice no, invoice number, order, order id, orderid, document |

Price is taken in this order:

1. The unit-price column, when one exists.
2. Otherwise sales amount divided by quantity.
3. Otherwise the price you typed in "Price now, if the report has no price".

If a row has both a unit price and a sales amount, and those two disagree by more than 5 cents and more than 2% of the expected amount, the row is kept and a warning is added. The unit price is the one used afterwards.

Numbers may include a thousands comma and a leading `$`, `£`, or `€`. `1,200` is read as 1200. `1.200` is read as 1.2, so a thousands dot is wrong here.

Dates:

- `2024-08-05` and `2024/08/05` are year-month-day.
- `01/12/2010 08:26` uses the date and ignores the time after the space. That is the UCI Online Retail shape, read day-first when the file has no other date to compare with.
- A slash or dash date such as `03/04/2024` can be 3 April or 4 March. If the file also has an unambiguous date, the reading that sits within 45 days of those dates is kept, and the other reading is named in a warning or the row is skipped. If every date in the file is ambiguous, the day-first reading is kept and no warning is written.
- `2024-08-05T09:00:00` has no space before the time, so that row is skipped. Use a space, or a date alone.
- A blank date, a totals row, or a cell that is not a number is skipped. The intake note says how many rows were skipped.

A small titled report with no product column is valid. Every row is then treated as the product you typed, and the price is sales divided by units:

```text
Weekly sales report
Week ending	Units sold	Sales
2024-08-02	20	2000
2024-08-09	20	2000
2024-08-16	22	2200
2024-08-23	24	2400
2024-08-30	30	3000
```

## Files in `data/`

`data/sample_sales.csv` is a made-up jacket history. Columns are `date,product,price,quantity,invoice`. It includes one cancelled jacket invoice (`C1015`, quantity −5) and one hat row (`HAT-02`). Both are dropped when the product is `JACKET-01`. Weekly totals, Monday to Sunday, for the jacket are 160, 140, 140, 120, 70, 45, 25. The forecast uses the last four: (120 + 70 + 45 + 25) / 4 = 65. The latest week is priced at 85.

`data/flawed_sales.csv` is a bread extract with a title row, decimal units, a sales amount that does not match units times price, a cancelled invoice, a negative quantity, a zero price, a second product (`CAKE-02`), a totals row, an ambiguous `03/04/2024`, and a blank date. Run it as product `BREAD-01` (or `bread-01`), stock 200, unit cost 1.2, 2 weeks until value is lost, market price 1.80, sales fall 15. The checked result is a forecast of 27.5, a current price of 2.81, a markdown to 2.39, cake listed as another product, the April row skipped, and a weak-guess warning. The 3 April row is not in the weekly chart.

Anything you upload or paste is written under `data/uploads/`. That folder is gitignored. A paste always overwrites `data/uploads/pasted-report.txt`, so two people using one server at the same time will clash. Uploaded files keep the original file name only. A second upload of the same name replaces the first.

## How a run is calculated

`app/orchestrator.py` passes one `RunContext` through ten agents in a fixed order (`app/agents/__init__.py`). The first error stops the later agents. The dashboard agent still runs, so a failure returns a failed view instead of a crash.

| Order | Agent | File | What it adds |
|---|---|---|---|
| 1 | Requirements | `app/agents/requirements_agent.py` | Rejects a blank product, negative stock or cost, a missing file, a missing horizon, a missing market price, a missing sales-fall percent, or an override other than `hold`, `mark_down`, or `raise`. |
| 2 | Data | `app/agents/data_agent.py` | Reads the file as UTF-8 (an Excel BOM is accepted) and calls `app/intake.py`. |
| 3 | Cleaning | `app/agents/cleaning_agent.py` | Drops cancelled, non-positive, and other-product rows. Stops when fewer than four rows match. |
| 4 | Transform | `app/agents/transform_agent.py` | One quantity and one average price per Monday week. |
| 5 | Forecast | `app/agents/forecast_agent.py` | Mean of the last four weekly quantities, and the latest week's average price. |
| 6 | Inventory | `app/agents/inventory_agent.py` | Weeks of cover and reorder, clear, or ok. |
| 7 | Pricing | `app/agents/pricing_agent.py` | Four candidate prices and the one with the highest profit. |
| 8 | Guardrail | `app/agents/guardrail_agent.py` | Lifts a price that is under cost, then caps a one-step move at 20%. |
| 9 | Evaluation | `app/agents/evaluation_agent.py` | Hold-out miss of that same average on the latest week. |
| 10 | Dashboard | `app/agents/dashboard_agent.py` | The object the page draws. Applies an override when the API was given one. |

### Cleaning

A row is dropped, with a reason, when:

- the invoice starts with `C` or `c` (the UCI cancellation mark; an order number such as `C1001` is dropped by the same rule)
- quantity is zero or negative
- unit price is zero or negative
- the product is a different code from the one you typed

Codes are compared after case is folded and spaces, underscores, and hyphens are removed. `BREAD-01` and `BREAD01` are the same key, so both stay in one forecast. The page does not yet stop and ask which code you meant.

Fewer than four matching rows is an error. The error lists the codes that are in the file and how many usable rows each has. Other products are not mixed in to fill the gap.

### Weeks and the forecast

Each sale is added to the Monday of its week. The week's price is sales value divided by units, not the last invoice's price. If the latest week contains prices more than 5 cents apart, a warning says the current price is an average.

Weeks with no sales are left out. They are not stored as zero. A sale in January and the next sale in April are neighbouring points in the forecast.

The forecast is the arithmetic mean of the last four weekly quantities, rounded to two decimals. One unusual week moves that mean. If the latest week is under half or over double the mean of the three weeks before it, a warning is added and the mean is left as it is.

The current price is the average price of the latest week. That is the price the 15% and 10% steps move from.

### Stock alert

Weeks of cover = stock on hand / forecast.

- Cover under 2 weeks: reorder.
- Cover longer than the weeks-until-value-loss you typed: clear.
- Cover of 4 weeks or more, and the forecast under 70% of the earlier average: clear.
- Otherwise: ok.

The earlier average is the mean of the weeks before the last four. With only four weeks, that earlier average is those same four weeks. A forecast of zero sets the alert to review and leaves cover empty.

### Price

Four candidates are scored. Nothing between them is searched.

| Choice | Price before the caps |
|---|---|
| Hold | Latest week's average price |
| Mark down | That price × 0.85, rounded to cents |
| Raise | That price × 1.10, rounded to cents |
| Match market | The market price you typed |

If a candidate is more than 20% away from the current price, it is pulled back to current × 1.20 or current × 0.80 before the profit is calculated. A market price of 9800 against a history price of 85 becomes 102 for scoring, and the reason says so.

Demand moves in a straight line from the sales-fall percent:

```text
move = (candidate price − current price) / current price
demand factor = 1 + move × (−sales fall / 10)
next-week demand = max(0, forecast × demand factor)
```

A 10% rise with a sales fall of 15 gives a factor of 0.85. A 15% markdown with the same 15 gives a factor of 1.225. A sales fall of 0 leaves demand unchanged at every price, so the higher legal price wins.

Units that can be sold before the stock loses value:

```text
sellable = min(stock, next-week demand × weeks until value is lost)
wasted = stock − sellable
profit = (price − unit cost) × sellable − unit cost × wasted
```

The highest profit at or above unit cost is the recommendation. If every candidate is under cost, they are all kept and the guardrail moves the winner.

If unit cost is more than 1.5 times the history price, the run stops. The jacket sample and a cost of 10000 are rejected here. The message tells you to untick the sample or to use a history whose prices match the cost.

### Guardrail

After a price is chosen:

1. A suggestion below unit cost is raised to cost, and the action becomes hold.
2. A suggestion more than 20% away from the current price is pulled back to a 20% step.

The second step runs after the first. A history price of 10 and a unit cost of 15 can be lifted to 15 and then capped at 12, which is under cost. Both notes appear on the result.

### Hold-out miss

With five or more weeks, the latest week is hidden and the same four-week mean is applied to the four weeks before it.

```text
miss % = |guess − actual| / actual × 100
```

The sentence reports the guess and the actual sales. At 50% or more it adds "Treat the price as a weak guess." Four weeks can still produce a price; the evaluation line then says there were not enough weeks to score a hold-out. A latest week of zero sales leaves the miss undefined.

The miss does not change the price. It tells you how wrong that average was last time.

### Approval

A normal run has status `pending`. The form has no approve or override control. The API accepts `manager_override` as `hold`, `mark_down`, or `raise`. That replaces the chosen action, sets the price to the current price, 85% of it, or 110% of it, and lifts the result to unit cost if the override would go under cost. Status becomes `overridden`. The four-price table is not recalculated.

## HTTP API

The server binds to your machine only when you use `--host 127.0.0.1`. Do not put this process on a public network. `POST /runs` reads whatever filesystem path you send in `csv_path`.

`GET /` returns the page. `GET /health` returns the status above.

`POST /uploads` takes a multipart file field named `file`. The response is:

```json
{"csv_path": "/absolute/path/data/uploads/your-file.csv"}
```

`POST /runs` takes JSON:

```json
{
  "product_code": "JACKET-01",
  "stock_on_hand": 400,
  "unit_cost": 40,
  "weeks_until_value_loss": 4,
  "competitor_price": 70,
  "sales_drop_percent": 15,
  "stated_price": null,
  "csv_path": null,
  "report_text": null,
  "use_sample": true,
  "manager_override": null
}
```

`use_sample: true` reads `data/sample_sales.csv` and runs it as `JACKET-01`, then writes your `product_code` onto the dashboard. A non-empty `report_text` or a `csv_path` turns the sample off. Pasted text is saved to `data/uploads/pasted-report.txt` and that path is analysed.

A success body has three keys:

```json
{
  "dashboard": {},
  "agent_log": ["requirements: Phase 1 inputs accepted"],
  "errors": []
}
```

`agent_log` is one line per agent that finished, in order. `errors` is empty on success.

`dashboard` on success:

| Field | Meaning |
|---|---|
| `status` | `pending`, `overridden`, or `failed` |
| `product_code` | Spelling taken from the file |
| `history` | `{week, quantity, avg_price}` per Monday, oldest first. `week` is `YYYY-MM-DD` |
| `forecast_units` | Next week's units |
| `forecast_method` | The four quantities in the mean |
| `price_action` | `hold`, `mark_down`, `raise`, or `match_market` |
| `current_price` | Latest week's average price |
| `suggested_price` | Price after the guardrail |
| `pricing_reason` | Why that price won |
| `price_options` | Each choice: `action`, `price`, `demand`, `sellable`, `wasted`, `profit`, `below_cost` |
| `inventory_alert` | `reorder`, `clear`, `ok`, or `review` |
| `inventory_reason` | The cover sentence |
| `weeks_of_cover` | Stock / forecast, or null |
| `guardrails` | Floor and 20% notes |
| `evaluation` | Hold-out sentence |
| `mape` | Miss percent, or null |
| `dropped_rows` | Count of dropped rows |
| `dropped` | `Invoice …: reason` lines |
| `warnings` | Date, price, and odd-week notes |
| `intake_note` | Columns used and rows skipped |
| `weeks_until_value_loss`, `competitor_price`, `sales_drop_percent` | The numbers you sent |

A failed run still returns HTTP 200 from `POST /runs`. `errors` is filled, and `dashboard` is only:

```json
{"status": "failed", "errors": ["Enter the market price you can see right now."]}
```

There is no `GET /runs/{id}`. Closing the page drops the result.

Call the same pipeline from Python:

```python
from app.orchestrator import run_analysis

result = run_analysis(
    "data/flawed_sales.csv",
    "BREAD-01",
    stock_on_hand=200,
    unit_cost=1.2,
    weeks_until_value_loss=2,
    competitor_price=1.8,
    sales_drop_percent=15,
)
```

## When the result looks wrong

| What you see | What happened |
|---|---|
| Cost is "far above the price in the sales history" | The sample, or another cheap file, was analysed against a high unit cost. Use a history whose prices are near that cost. |
| "No rows match … This file has …" | The typed code is not in the table. Type one of the listed codes. A description column placed before the stock code makes the description the product. |
| Forecast is much larger than a normal week | Two codes collapsed into one key, a duplicate invoice was added again, or a refund was stored as a positive quantity. Those are not named as their own warnings yet. |
| "Raise to …" together with a miss over 50% | The price is still the highest-profit candidate. The caution is the accuracy check. The headline does not yet switch to "weak guess". |
| Hold at a price below your cost | The cost floor ran, then the 20% cap pulled the price back toward a much lower history price. |
| A market price you typed was ignored | It was more than 20% away from the latest week, so the match was capped before scoring. |
| Only four weeks, and no miss | A price is still produced. The hold-out needs a fifth week. |
| A quiet month looks like the next week | Empty weeks are not filled with zero, so the next dated week is treated as adjacent. |
| An order starting with C disappeared | Leading `C` means cancelled. |
| `03/04/2024` landed on the wrong month | With no `YYYY-MM-DD` date in the file, slash dates stay day-first and no warning is added. |

## Repository layout

```text
app/main.py                 HTTP routes and the sample/paste/upload choice
app/orchestrator.py         Runs the ten agents
app/context.py              RunContext, SalesRow, WeekPoint
app/intake.py               Header detection, dates, numbers
app/agents/                 One file per agent
app/static/index.html       The whole page, with no build step
data/sample_sales.csv       Jacket sample
data/flawed_sales.csv       Bread file with known data problems
tests/                      Pipeline and intake tests
docs/PLAN.md                Dates and what is still to build
docs/TEAM.md                Who owns which agent
docs/PROFILES.md            Per-person deliverables
```

`docs/TEAM.md` and `docs/PROFILES.md` describe the group's plan, including saved runs, a golden UCI product, and tests that are not in the tree yet. Where those files disagree with this README, the code and this README are the behaviour you can run today.

## Data you might add later

The sample and the flawed file are invented so the rules can be checked by hand. A real history the group planned to use is the UCI Online Retail set (Chen, Daqing, 2015, Online Retail, UCI Machine Learning Repository, CC BY 4.0). That file is not in this repository. Map `InvoiceDate` to the date, `StockCode` to the product, `UnitPrice` to the price, `Quantity` to the quantity, and `InvoiceNo` to the invoice before a run.

## Limits to keep in mind

- One product per run.
- The forecast is a four-week mean. It is meant to be recomputed with a calculator.
- Prices are recommendations. Status stays pending until an API override.
- The 20% cap can undo the cost floor.
- Hyphen and space differences do not keep two product codes apart.
- Duplicate invoices are summed. A positive-quantity return is counted as a sale.
- Slash dates with no ISO date in the file are read day-first, silently.
- The server is single-user. Pastes share one file, and `csv_path` is a local path.
