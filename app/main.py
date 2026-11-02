"""The doors the browser uses. Phase 1 only.

This file is the back office: it does not price anything itself. It
receives a form, chooses which sales table to use, and calls
run_analysis (the ten clerks). Nothing here writes to a shop till.

Start it with:
    python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
Then open http://127.0.0.1:8000
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from html import escape
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

from app.orchestrator import run_analysis

# FastAPI turns the functions below into HTTP addresses (routes).
app = FastAPI(title="Dynamic pricing and inventory engine", version="0.1.0")

ROOT = Path(__file__).resolve().parents[1]
# Built-in sample: real UCI extract of StockCode 85123A (hanging-heart holder).
SAMPLE = ROOT / "data" / "uci_85123A.csv"
UPLOADS = ROOT / "data" / "uploads"
PAGE = Path(__file__).resolve().parent / "static" / "index.html"
LOGIN_PAGE = Path(__file__).resolve().parent / "static" / "login.html"

# Course gate. Not a user database.
LOGIN_USER = "SE123"
LOGIN_PASS = "SE123"
COOKIE = "session"
# Signs the cookie so a made-up value is rejected. Not an environment secret.
COOKIE_SECRET = b"comp-s350f-dynamic-pricing-session"
TOKEN = hmac.new(COOKIE_SECRET, b"ok", hashlib.sha256).hexdigest()


class RunRequest(BaseModel):
    """JSON body of POST /runs. Field() rejects numbers that cannot be a shop input."""

    product_code: str
    stock_on_hand: float = Field(ge=0)
    unit_cost: float = Field(ge=0)
    weeks_until_value_loss: float = Field(gt=0)
    competitor_price: float = Field(gt=0)  # Typed by the operator. There is no live feed (C1).
    sales_drop_percent: float = Field(ge=0)  # Guess: sales fall this many % if price rises 10%.
    stated_price: float | None = Field(default=None, gt=0)
    csv_path: str | None = None
    report_text: str | None = None
    use_sample: bool = False
    manager_override: str | None = None  # API-only: hold, mark_down, or raise. The form does not send this.


def _signed_in(request: Request) -> bool:
    return secrets.compare_digest(request.cookies.get(COOKIE) or "", TOKEN)


def _login_html(error: str = "") -> HTMLResponse:
    html = LOGIN_PAGE.read_text(encoding="utf-8")
    block = f'<p class="error" role="alert">{escape(error)}</p>' if error else ""
    return HTMLResponse(html.replace("<!--ERROR-->", block))


def _need_sign_in() -> JSONResponse:
    return JSONResponse({"errors": ["Sign in again."]}, status_code=401)


@app.get("/health")
def health() -> dict:
    """Tiny check that the process is up. Used by a human or a monitor, not by the page."""
    return {"status": "ok", "agents": 10}


@app.get("/login")
def login_form(request: Request):
    if _signed_in(request):
        return RedirectResponse("/", status_code=303)
    return _login_html()


@app.post("/login")
def login_submit(username: str = Form(""), password: str = Form("")):
    user_ok = secrets.compare_digest(username.strip(), LOGIN_USER)
    pass_ok = secrets.compare_digest(password, LOGIN_PASS)
    if not (user_ok and pass_ok):
        return _login_html("Username or password is wrong.")
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        COOKIE,
        TOKEN,
        httponly=True,
        samesite="lax",
        max_age=14 * 24 * 3600,
        path="/",
    )
    return response


@app.post("/logout")
def logout() -> RedirectResponse:
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(COOKIE, path="/")
    return response


@app.get("/")
def home(request: Request):
    if not _signed_in(request):
        return RedirectResponse("/login", status_code=303)
    return FileResponse(PAGE)


@app.post("/uploads")
async def upload(request: Request, file: UploadFile = File(...)) -> dict:
    if not _signed_in(request):
        return _need_sign_in()
    UPLOADS.mkdir(parents=True, exist_ok=True)
    dest = UPLOADS / Path(file.filename or "upload.csv").name
    dest.write_bytes(await file.read())
    return {"csv_path": str(dest)}


@app.post("/runs")
def create_run(body: RunRequest, request: Request) -> dict:
    if not _signed_in(request):
        return _need_sign_in()
    pasted = (body.report_text or "").strip()
    # A paste or an upload wins over the sample checkbox. The sample file is
    # the UCI hanging-heart holder, and its prices must not be used for another product's cost.
    if pasted or (body.csv_path and not body.use_sample):
        body.use_sample = False
    if body.use_sample:
        # The sample rows are 85123A. The typed name is put back on the dashboard after the run.
        csv_path = str(SAMPLE)
        product_code = "85123A"
    elif body.report_text and body.report_text.strip():
        UPLOADS.mkdir(parents=True, exist_ok=True)
        # One shared file. Two people pasting at once overwrite each other.
        pasted_file = UPLOADS / "pasted-report.txt"
        pasted_file.write_text(body.report_text, encoding="utf-8")
        csv_path = str(pasted_file)
        product_code = body.product_code
    else:
        csv_path = body.csv_path or ""
        product_code = body.product_code
    result = run_analysis(
        csv_path=csv_path,
        product_code=product_code,
        stock_on_hand=body.stock_on_hand,
        unit_cost=body.unit_cost,
        manager_override=body.manager_override,
        weeks_until_value_loss=body.weeks_until_value_loss,
        competitor_price=body.competitor_price,
        sales_drop_percent=body.sales_drop_percent,
        stated_price=body.stated_price,
    )
    if body.use_sample and result.get("dashboard"):
        result["dashboard"]["product_code"] = body.product_code
    return result
