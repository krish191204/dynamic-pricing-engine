# Agent profiles

Ten people. Each profile says what they own, what they deliver by each date, how they will do it, and how Thomas (test lead) will challenge them.

A grounded answer names a file, a test, or a number anyone can check in a minute. "It works on my machine" is not grounded. Vague items go on the list at the bottom and stay out of the demo.

Code today lives in `app/agents/`, `app/orchestrator.py`, `app/main.py`, `app/static/index.html`, and `tests/test_pipeline.py`.

---

## Krish — Scope and integration

**Mission.** Keep the ten agents in one order, and keep Phase 1 small enough to finish.

**Owns.** `app/orchestrator.py`, `app/agents/__init__.py`, `app/agents/inventory_agent.py`, `README.md`, `docs/DECISIONS.md`.

**Deliverables**

- 15 Nov: agent order in `AGENTS` matches this file; inventory rules (reorder under 2 weeks of cover, clear at 4 weeks when the forecast is soft) written as named constants; one real product runs through `python3 -m app`.
- 30 Nov: every new feature is either in `docs/DECISIONS.md` as Phase 1 or marked Phase 2.
- 8 Dec: opens and closes the demo; one paragraph in the report on what was cut.

**Method**

1. After each merge, run `python3 -m app` and check the log lists all ten agents.
2. Put cover thresholds in constants at the top of `inventory_agent.py`, same style as Sunny's price constants.
3. When someone proposes a feature, write one line in `docs/DECISIONS.md`: date, decision, why.
4. If two agents disagree (high forecast and high stock), the dashboard shows both messages. Do not average them into one soft call.

**Hands to / needs from.** Needs weekly series from Rohan and price action from Sunny. Hands the finished `RunContext` to Hei.

**Done when.** A new teammate clones the repo and sees a jacket result from `python3 -m app` in under five minutes, and `docs/DECISIONS.md` has a line for every cut.

**Risk.** The pitch grows back toward live pricing. Mitigation: Phase 2 list, reviewed each Friday.

**Thomas asks**

- How do you prove the chain still has ten agents after a merge? The test counts `agent_log` entries. It already expects 10 in `tests/test_pipeline.py`.
- What if inventory and pricing disagree? Both strings stay on the dashboard. A test asserts `inventory_alert` and `price_action` are both present.
- What is the fallback if the real file is late? The sample `data/sample_sales.csv` stays the demo until the golden file exists. The date is 15 Nov.

---

## Maheen — Requirements

**Mission.** Turn the project overview into checks a test can fail.

**Owns.** `app/agents/requirements_agent.py`, `docs/REQUIREMENTS.md`.

**Deliverables**

- 15 Nov: `docs/REQUIREMENTS.md` with one "shall" per line and one line of why. Each invalid input the file names is rejected in `RequirementsAgent.run` with a plain sentence.
- 30 Nov: the page's error list shows those sentences (with Alvin).
- 8 Dec: the requirements section of the report is this file, shortened.

**Method**

1. List Phase 1 inputs: product code, stock on hand at least 0, unit cost at least 0, a CSV path, override only `hold`, `mark_down`, or `raise`.
2. Add one `ctx.errors.append` per rule. Do not stack several rules into one sentence.
3. Add `tests/test_requirements.py` with one case per rejection.
4. Mark competitor prices and automatic price changes as "should" (later), not "shall".

**Hands to / needs from.** Needs the form fields from Alvin. Hands the error strings to Alvin and the shall-list to the report.

**Done when.** Every shall has a test, and a blank product code fails with the sentence in the doc.

**Risk.** Writing design (database, framework) into requirements. Mitigation: Thomas rejects a shall that names a tool.

**Thomas asks**

- Show me the test for a negative stock. `tests/test_requirements.py` posts stock `-1` and asserts the error text.
- What if the overview says "optimise profit" but the code uses three rules? The shall says "recommend hold, mark down, or raise". Optimisation is Phase 2 in the same doc.
- Who checks the wording? Alvin, before 30 Nov, because the page prints the strings as-is.

---

## Sufiyaan — Data

**Mission.** Give the team one real, cited sales file the rest of the pipeline can read.

**Owns.** `app/agents/data_agent.py`, `data/`, `docs/DATA.md`.

**Deliverables**

- 15 Nov: `docs/DATA.md` cites Chen (2015) and CC BY 4.0. One product exported to `data/` with columns `date,product,price,quantity,invoice` and dates as `YYYY-MM-DD`. The data agent returns a clear error for a missing column and a bad date instead of crashing.
- 30 Nov: a ten-row sample of that file is in the repo; the full Kaggle file is not (it is large; the doc says where it came from).
- 8 Dec: the citation is in the report and the demo narration.

**Method**

1. Download UCI Online Retail. Map `InvoiceDate` to `date`, `StockCode` to `product`, `UnitPrice` to `price`, `Quantity` to `quantity`, `InvoiceNo` to `invoice`.
2. Rohan names the StockCode. Export only that product.
3. Wrap date parsing in `DataAgent.run` so a bad date appends to `ctx.errors`.
4. Add two tests: missing `quantity` column, and a date that is not `YYYY-MM-DD`.

**Hands to / needs from.** Needs the StockCode from Rohan. Hands the CSV to Yuncho and Thomas.

**Done when.** `python3 -m app` on the real file returns no error, and both new tests fail on the old code and pass on the new code.

**Risk.** The file has no stock column, and dates are `dd/mm/yyyy`. Mitigation: the manager types stock; the export converts dates before anyone else sees them.

**Thomas asks**

- Where is the licence written? First lines of `docs/DATA.md`, including the Kaggle URL and CC BY 4.0.
- What if the export still has UK dates? A test row `09/12/2011` must produce an error, not a silent wrong month.
- What is in the repo if the download is blocked? The existing `data/sample_sales.csv` remains, and the real file is named in the doc as the source we could not refresh.

---

## Alex — Architecture and API

**Mission.** Keep the page, the API, and the ten agents as three separate pieces, and make a run survive a reload.

**Owns.** `app/main.py`, `docs/ARCHITECTURE.md`.

**Deliverables**

- 15 Nov: `docs/ARCHITECTURE.md` with the four boxes (page, API, agents, files) and the ten-agent chain. `POST /runs` documented with one example.
- 30 Nov: SQLite table for runs; `GET /runs/{id}` returns the same dashboard; upload endpoint saves a CSV and returns a path. `csv_path` from the client is not an arbitrary server path (only files under `data/uploads/`).
- 8 Dec: the architecture figure in the report and one slide.

**Method**

1. Draw the chain from `AGENTS` in `app/agents/__init__.py`. Do not add an eleventh agent.
2. Add a `runs` table: id, created time, request JSON, dashboard JSON.
3. Generate the id in `create_run` and return it next to `dashboard`.
4. Add `tests/test_api.py` with `TestClient`: post a run, get it back, and reject a `csv_path` outside the upload folder.

**Hands to / needs from.** Needs the dashboard shape from Hei and the form fields from Alvin. Hands the endpoints to Alvin. Any change to the JSON shape needs Krish's line in `docs/DECISIONS.md`.

**Done when.** A run fetched after a server restart matches the run just posted, and a path like `/etc/passwd` is rejected.

**Risk.** Arbitrary file reads through `csv_path`. Mitigation: the upload folder check, with a test.

**Thomas asks**

- Show me the test that a run survives restart. `tests/test_api.py` writes sqlite to a temp file, posts, builds a new app on the same file, and compares dashboards.
- What is the fallback if SQLite slips past 23 Nov? The page keeps using the sample path, and saved runs move to the "not yet grounded" list instead of the demo.
- Who can change the response shape? Krish, in writing, before Alvin changes the page.

---

## Yuncho — Data quality and guardrails

**Mission.** Keep only real sales, and keep every suggested price safe, with a list of what was dropped and why.

**Owns.** `app/agents/cleaning_agent.py`, `app/agents/guardrail_agent.py`.

**Deliverables**

- 15 Nov: docstring lists every drop rule. Rows for the wrong product are counted in `ctx.dropped` (today they vanish). `MAX_STEP = 0.20` is a named constant. The real product file runs clean.
- 30 Nov: dropped reasons appear in the dashboard box (with Hei). One test per rule and per guardrail.
- 8 Dec: half a page in the report: counts per reason in the real file, and the two guardrail numbers.

**Method**

1. Keep the order: cancelled invoice (starts with `C`), non-positive quantity, non-positive price, wrong product.
2. Add `tests/fixtures/dirty.csv` with one row per rule and assert the full `dropped` list.
3. After the 20% cap, check the floor again so the cap cannot push the price back under cost.
4. Run Sufiyaan's export and record counts per reason.

**Hands to / needs from.** Needs the export from Sufiyaan and the percents from Sunny. Hands `clean_rows` to Rohan and `dropped` plus `guardrail_notes` to Hei.

**Done when.** `dirty.csv` yields exactly the expected reasons, and no run has `suggested_price` below `unit_cost`.

**Risk.** The cap undoes the floor. Mitigation: a test with cost 13 and current price 10 must end at 13, not 12.

**Thomas asks**

- How do you prove only the right rows were dropped? The fixture has one row per rule. The test asserts the full list and the count of rows kept.
- Show the floor-then-cap bug. Cost 13, current price 10. After the fix the price is 13 and both notes are present.
- What does a manager see if every row is cancelled? The existing "need at least 4 clean rows" error, plus the dropped reasons. A test reads `result["errors"]`.

---

## Rohan — Weekly series

**Mission.** Turn invoice lines into weekly totals a person can recompute, and pick a real product with enough history.

**Owns.** `app/agents/transform_agent.py`. The demo StockCode, written with Sufiyaan in `docs/DATA.md`.

**Deliverables**

- 15 Nov: Monday week start written in the docstring. A StockCode with at least 12 weeks and no gap over one week (candidate `85123A`, checked, not assumed). The real file runs through `python3 -m app`.
- 30 Nov: missing weeks filled with quantity 0 and flagged. A test with four hand-summed weeks. The last partial week flagged.
- 8 Dec: one report paragraph on the product choice, plus the spreadsheet as an appendix.

**Method**

1. `week_start` is Monday. A test checks Wednesday 4 Sep 2024 becomes Monday 2 Sep 2024.
2. After Yuncho's drops, count distinct weeks per StockCode. Keep codes with at least 12 weeks and no gap over one week.
3. Hand-sum four weeks in a spreadsheet: quantity, and average price weighted by quantity.
4. Put those numbers in `tests/test_transform.py`.
5. Tell Sunny and Thomas the week count before the golden file is frozen.

**Hands to / needs from.** Needs clean rows from Yuncho and `YYYY-MM-DD` dates from Sufiyaan. Hands `ctx.weekly` to Sunny and Thomas.

**Done when.** The test totals match the spreadsheet to the unit, and the demo product has at least 12 weeks.

**Risk.** The UCI file ends on a Friday, so the last week is short. Mitigation: flag it, and let Thomas say whether MAPE skips it.

**Thomas asks**

- How do you prove the totals? Four weeks summed by hand. The test fails if the code differs by one unit.
- What if a return makes a week negative? Yuncho drops quantity below 1 before this agent runs. An assert checks no week is negative, so a rule change shows up at once.
- Why that StockCode? A written filter (at least 12 weeks, no gap over one week). The counts go in `docs/DATA.md`.

---

## Sunny — Pricing and forecast

**Mission.** Keep the forecast and the three price rules simple enough to predict from a table.

**Owns.** `app/agents/forecast_agent.py`, `app/agents/pricing_agent.py`, `docs/PRICING.md`.

**Deliverables**

- 15 Nov: `docs/PRICING.md` table matches the code. Thresholds `0.7`, `1.3`, markdown `0.85`, raise `1.10` are named constants. Forecast stays the mean of the last four weeks.
- 30 Nov: one tiny file per action (hold, mark down, raise) in `tests/test_pricing.py`. Reason text agreed with Hei. One worked example from the real product in the doc.
- 8 Dec: the report defends the thresholds and shows Thomas's MAPE. The demo walks through one run from the table.

**Method**

1. Copy the three branches in `PricingAgent.run` into the table. Note that with fewer than five weeks there is no earlier average, so the action is hold.
2. Replace the numbers in code with constants. A test reads the constants and the numbers written in the doc.
3. Build the three tiny files the way `test_thin_stock_can_raise_when_forecast_jumps` already does, choosing stock so cover is under 2 weeks, between 2 and 4, or at least 4.
4. Run the real product at three stock levels and record which rule fires.
5. Run the same product at 0.6/1.4 and 0.8/1.2 and write which actions change. That is the defence of 0.7 and 1.3.

**Hands to / needs from.** Needs `ctx.weekly` from Rohan and the guardrail constants from Yuncho. Hands the forecast, the action, and the reason text to Krish, Hei, and Thomas.

**Done when.** Someone with only the table and the weekly numbers names the action for all three tests.

**Risk.** A short or jumpy series makes the mean look silly. Mitigation: keep the mean, publish the MAPE, and log any other method as Phase 2.

**Thomas asks**

- Why 0.7 and 1.3? They are a 30% band around the earlier average. The sensitivity table shows what changes at 0.6/1.4 and 0.8/1.2.
- How do I know the doc matches the code? The test asserts the numbers in `docs/PRICING.md` equal the constants.
- Is hold-on-short-history a bug? No. Under five weeks there is nothing to compare. The doc says so, and a four-week file test expects hold.

---

## Hei — Dashboard

**Mission.** A manager can read the result in ten seconds, including on a phone.

**Owns.** `app/agents/dashboard_agent.py` and the result section of `app/static/index.html`.

**Deliverables**

- 15 Nov: the forecast is its own bar after the history, in a different colour. A "what we checked" box shows dropped rows and guardrail notes. The page is readable at 375px width.
- 30 Nov: the same layout renders a saved run from `GET /runs/{id}`. The approval name sits next to the status.
- 8 Dec: phone and desktop screenshots in the report, and two minutes of the demo.

**Method**

1. Add the forecast as the last bar, with its own CSS class.
2. Put `dropped_reasons` on the dashboard dict, agreed with Yuncho, so the box lists reasons and not only a count.
3. Stack the form under 600px width. Check there is no sideways scroll at 375px.
4. Add `tests/test_dashboard.py`: every key the page reads exists; a failed run has status `failed`; an override below cost is lifted to cost.
5. Freeze reason wording with Sunny before the layout is treated as final.

**Hands to / needs from.** Reads the context after the other agents. Hands the dashboard dict to Alex's store. Needs status names from Alvin.

**Done when.** A person outside the team states the price action and the stock alert from the page alone.

**Risk.** A JSON change breaks the page. Mitigation: the test asserts every key the page reads.

**Thomas asks**

- Show the test for "what we checked". `test_dashboard.py` expects `dropped_rows == 1` on the sample and a non-empty reason list.
- What number proves the phone layout? At 375px, the page is no wider than the screen. The pull request includes that screenshot.
- What if there is no forecast? The forecast bar is skipped and the text says "no forecast". A short file still returns the other keys.

---

## Alvin — Interface flow

**Mission.** The manager uploads their own file, always sees the state, and leaves a name on the approval.

**Owns.** The form and status in `app/static/index.html`.

**Deliverables**

- 15 Nov: four visible states: waiting, running, finished, failed. Failed lists every error string.
- 30 Nov: a file field that posts to Alex's upload endpoint. An "Approved by" field stored with the run.
- 8 Dec: a demo path of upload, fail, fix, rerun.

**Method**

1. Add a status line. Set it before the request, on success, and on error. Remove the automatic run on page load so "waiting" is real.
2. Render `errors` as a list, not one string.
3. On submit, send the file to `POST /uploads`, then send the returned path as `csv_path`.
4. Send `approved_by` with the override. Alex stores it.
5. Until 23 Nov, if upload is late, keep a text field for a path inside `data/`.
6. Each state gets one screenshot in the pull request.

**Hands to / needs from.** Needs Maheen's error sentences and Alex's upload and save. Hands field names to Hei so the result layout does not clash.

**Done when.** A CSV missing `quantity` shows the data agent's exact error, and `GET /runs/{id}` returns the typed approval name.

**Risk.** Upload slips. Mitigation: the path field stays until 23 Nov. The demo still uses the real file in `data/`.

**Thomas asks**

- Show the failed-state test. A request test posts a CSV with no `date` column and asserts `errors` is not empty. The screenshot shows the same text.
- What if upload is late? The path field remains until 23 Nov.
- What proves the name is saved? Post `approved_by: "Test Manager"`, fetch the run, assert equality in `tests/test_api.py`.

---

## Thomas — Test lead

**Mission.** Nothing reaches the demo without a test that proves it, and the forecast error is a published number every week.

**Owns.** `app/agents/evaluation_agent.py`, `tests/`, `docs/TESTING.md`, `tests/fixtures/golden.csv`, `tests/fixtures/expected.json`.

**Deliverables**

- 15 Nov: `docs/TESTING.md` with a row per agent. The golden file is the real product. `tests/test_golden.py` compares the dashboard to `expected.json`. At least one test per agent. Evaluation tests cover a short history, a zero-sales week, and one MAPE computed by hand.
- 30 Nov: API tests for post, get, upload, and `approved_by`. At least three weekly MAPE rows.
- 8 Dec: the "not yet grounded" list is empty or marked out of scope. The test table and the final MAPE are in the report.

**Method**

1. Freeze the golden file only after Sufiyaan and Rohan name the product. Run the pipeline once and save the dashboard as `expected.json`.
2. One test file per agent, using small CSVs the way `tests/test_pipeline.py` already does.
3. Monday: run `python3 -m pytest tests -q` and post the result. Friday: update the table and the MAPE row.
4. Review each pull request first. Ask for one change at a time.
5. The evaluation agent must use the same four-week mean as Sunny. If the forecast changes, the evaluation changes in the same pull request.

**Hands to / needs from.** Needs the real CSV, Rohan's spreadsheet, and each lead's tests. Hands pass/fail, the MAPE, and the grounded list to Krish.

**Done when.** Every agent has a test, the golden test passes on `main`, and the demo script has no item from the list below.

**Risk.** The golden numbers change every time a rule changes. Mitigation: a pull request that edits `expected.json` states the old number, the new number, and the owner's name.

### How the challenge works

Wednesday, first 15 minutes. Each lead gets 90 seconds. Thomas asks the five questions, plus up to two from that person's profile. Answers are written under that week in `docs/TESTING.md`.

A grounded answer names a file, a test, a number, or a date. Anything else goes on the list. Two weeks on the list becomes a scope decision for Krish. Listed items are not in the demo and not in the report.

A pull request merges only if the tests pass, new behaviour has a test, the author owns the files or the owner approved, and the golden-file rule is met. Review turnaround is 24 hours. Krish reviews if Thomas is away.

**Five questions for every lead**

1. Which test, in which file?
2. What is the fallback if your input is late?
3. What number proves it, and where is it written?
4. What is out of scope this week?
5. Who is waiting on you, and by when?

---

## Not yet grounded

Thomas owns this list. Start empty. Add a row when an answer is vague. Remove the row when a test or a number exists.

| Date | Owner | Item | Cleared |
|---|---|---|---|
| — | — | — | — |
