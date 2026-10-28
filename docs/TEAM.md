# Team handbook

Full profiles, methods, and the test lead's challenges: [PROFILES.md](PROFILES.md).
The project plan, dates, and who depends on whom: [PLAN.md](PLAN.md).

Ten people, ten agents, one pipeline. Find your name, do the three tasks under it, tick the "done when" line, then tell the test lead.

Run everything from the repo folder:

```bash
cd dynamic-pricing-engine
python3 -m app                       # run the sample
python3 -m uvicorn app.main:app      # open http://127.0.0.1:8000
python3 -m pytest tests -q           # run the tests
```

How a change gets in:

1. Make a branch: `git checkout -b <yourname>/<short-task>`
2. Change only the files listed under your name unless you have asked the owner.
3. Run the tests. Red tests do not merge.
4. Push and open a pull request. Thomas (test lead) reviews first, then the owner of any other file you touched.

---

## Krish — Scope and integration

**Agent:** orchestrator (`app/orchestrator.py`)
**Also owns:** `README.md`, `docs/OUTLINE.md`

Do this:
1. Keep the agent order in `app/agents/__init__.py` matching `docs/OUTLINE.md`.
2. Run the sample every Friday and paste the dashboard JSON into the group chat.
3. Decide "Phase 1 or Phase 2" when someone proposes a feature. Write the decision in `docs/DECISIONS.md`.

Done when: a new teammate can clone, run `python3 -m app`, and see the jacket result in under five minutes.

Ask: Alex for API, Thomas for tests.

---

## Maheen — Requirements

**Agent:** requirements (`app/agents/requirements_agent.py`)
**Also owns:** `docs/REQUIREMENTS.md`

Do this:
1. Write one line per requirement: "The system shall …", then one line why. Keep to Phase 1.
2. Make the requirements agent reject every input the requirements say is invalid, with a plain message.
3. Add one test per rejection to `tests/test_requirements.py` with Thomas.

Done when: every "shall" has a matching check or test.

Ask: Krish for scope, Alvin for what the form sends.

---

## Sufiyaan — Data

**Agent:** data (`app/agents/data_agent.py`)
**Also owns:** `data/`, `docs/DATA.md`

Do this:
1. Download UCI Online Retail from Kaggle. Write the citation (Chen 2015, CC BY 4.0) in `docs/DATA.md`.
2. Export a small CSV for one real product into `data/` with columns `date,product,price,quantity,invoice`.
3. Make the data agent give a clear error for a missing column or a bad date, and test both.

Done when: the real product CSV runs through `python3 -m app` with no error.

Ask: Rohan for the product choice, Yuncho for which rows look wrong.

---

## Alex — Architecture and API

**Agent:** none; owns the service (`app/main.py`)
**Also owns:** `docs/ARCHITECTURE.md`

Do this:
1. Draw the four boxes (page, API, agents, data) and the ten-agent chain. Put the picture in `docs/ARCHITECTURE.md`.
2. Add `GET /runs/{id}` that returns a saved run, and store runs in a small SQLite table.
3. Add a request test for `POST /runs` and `GET /runs/{id}`.

Done when: a run can be fetched again after the page is reloaded.

Ask: Alvin for what the page needs, Krish before changing the response shape.

---

## Yuncho — Data quality and guardrails

**Agents:** cleaning (`app/agents/cleaning_agent.py`), guardrail (`app/agents/guardrail_agent.py`)

Do this:
1. List every row rule (cancelled, negative, zero price, wrong product) in the cleaning agent's docstring. Return the dropped count and reason to the dashboard.
2. Agree the two guardrail numbers (floor = cost, max step = 20%) with Sunny. Make them named constants.
3. Write a test for each rule and each guardrail.

Done when: a dirty file produces a dropped-row list that a manager can read.

Ask: Sunny for pricing rules, Rohan for how weeks are built.

---

## Rohan — Weekly series

**Agent:** transform (`app/agents/transform_agent.py`)

Do this:
1. Confirm the week starts on Monday and document it. Fill missing weeks with zero, and flag them.
2. Pick the demo product from the real dataset: at least 12 weeks, no long gaps. Tell Sufiyaan.
3. Hand-calculate four weeks in a spreadsheet and put the numbers in a test.

Done when: the test's weekly totals match your spreadsheet exactly.

Ask: Yuncho for row rules, the forecast owner for how many weeks they need.

---

## Sunny — Pricing

**Agents:** pricing (`app/agents/pricing_agent.py`), forecast (`app/agents/forecast_agent.py`)

Do this:
1. Write the three rules as a table in `docs/PRICING.md`: condition, action, percent. Match the code to the table.
2. Keep the forecast as a four-week mean. If you try anything else, keep the mean as the default and explain the change in the doc.
3. Add tests for hold, mark down, and raise using tiny hand-made files.

Done when: a teammate can predict the action from the table before running the code.

Ask: Yuncho for guardrails, Hei for how the reason text looks on the page.

---

## Hei — Dashboard

**Agent:** dashboard (`app/agents/dashboard_agent.py`)
**Also owns:** the result part of `app/static/index.html`

Do this:
1. Show the forecast as its own bar after the history bars, in a different colour.
2. Show dropped rows and guardrail notes in a small "what we checked" box.
3. Make the page readable on a phone width.

Done when: a manager understands the recommendation without reading any code.

Ask: Alvin for the form and status flow, Sunny for reason wording.

---

## Alvin — Interface flow

**Owns:** the form and status part of `app/static/index.html`

Do this:
1. Add a file upload field so a manager can use their own CSV, not only the sample.
2. Show the four states clearly: waiting, running, finished, failed. Failed shows the error list.
3. Add an "Approved by" name field that is saved with the override.

Done when: a failed upload tells the manager exactly what to fix.

Ask: Alex for the API fields, Hei before changing the result layout.

---

## Thomas — Test lead

**Agent:** evaluation (`app/agents/evaluation_agent.py`)
**Owns:** `tests/`, `docs/TESTING.md`

Do this:
1. Keep `tests/` green. Review every pull request first; ask for a test if a change has none.
2. Keep one golden file: `tests/fixtures/golden.csv` plus `expected.json`. Any change to the numbers needs the owner's sign-off.
3. Report the hold-out error (MAPE) on the real product each week in `docs/TESTING.md`.

Done when: every agent has at least one test, and the golden run matches `expected.json`.

Test lead duties, in order:
- Monday: run the full suite, post the result.
- Each pull request: run it, read it, approve or ask for one change.
- Friday: update the test table in `docs/TESTING.md` (agent, test file, pass/fail).

Ask: everyone. You are allowed to block a merge.

---

## Weekly rhythm

| Day | What | Who |
|---|---|---|
| Monday | Tests run, result posted | Thomas |
| Wednesday | 30-minute call: blockers only | Everyone |
| Friday | Sample run posted, decisions written | Krish |
| Every fortnight | Logbook entry on your own agent | Everyone |
