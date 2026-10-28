"""Small HTTP API around the ten-agent pipeline. Phase 1 only."""

from __future__ import annotations

from contextlib import asynccontextmanager
from html import escape
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

from app.auth import (
    COOKIE,
    AuthError,
    authenticate,
    create_account,
    email_for,
    ensure_schema,
    read_session,
    sign_session,
)
from app.orchestrator import run_analysis

@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        ensure_schema()
    except AuthError:
        # The page still opens. Sign-in reports that storage is unavailable.
        pass
    yield


app = FastAPI(title="Dynamic pricing and inventory engine", version="0.1.0", lifespan=lifespan)

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "sample_sales.csv"
UPLOADS = ROOT / "data" / "uploads"
PAGE = Path(__file__).resolve().parent / "static" / "index.html"
LOGIN_PAGE = Path(__file__).resolve().parent / "static" / "login.html"
SESSION_MAX_AGE = 14 * 24 * 3600


class RunRequest(BaseModel):
    product_code: str
    stock_on_hand: float = Field(ge=0)
    unit_cost: float = Field(ge=0)
    weeks_until_value_loss: float = Field(gt=0)
    competitor_price: float = Field(gt=0)
    sales_drop_percent: float = Field(ge=0)
    stated_price: float | None = Field(default=None, gt=0)
    csv_path: str | None = None
    report_text: str | None = None
    use_sample: bool = False
    manager_override: str | None = None


def _user_id(request: Request) -> int | None:
    return read_session(request.cookies.get(COOKIE))


def _sign_in_required() -> JSONResponse:
    return JSONResponse({"errors": ["Sign in again."]}, status_code=401)


def _login_html(error: str = "") -> HTMLResponse:
    html = LOGIN_PAGE.read_text(encoding="utf-8")
    block = f'<p class="error" role="alert">{escape(error)}</p>' if error else ""
    return HTMLResponse(html.replace("<!--ERROR-->", block))


def _remember(response: RedirectResponse, request: Request, user_id: int) -> RedirectResponse:
    response.set_cookie(
        COOKIE,
        sign_session(user_id),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
        path="/",
    )
    return response


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "agents": 10}


@app.get("/login")
def login_form(request: Request):
    if _user_id(request) is not None:
        return RedirectResponse("/", status_code=303)
    return _login_html()


@app.post("/login")
def login_submit(
    request: Request,
    email: str = Form(""),
    password: str = Form(""),
    mode: str = Form("login"),
):
    try:
        user_id = create_account(email, password) if mode == "signup" else authenticate(email, password)
    except AuthError as exc:
        return _login_html(str(exc))
    return _remember(RedirectResponse("/", status_code=303), request, user_id)


@app.post("/logout")
def logout() -> RedirectResponse:
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(COOKIE, path="/")
    return response


@app.get("/me")
def me(request: Request):
    user_id = _user_id(request)
    email = email_for(user_id) if user_id is not None else None
    if not email:
        return _sign_in_required()
    return {"email": email}


@app.get("/")
def home(request: Request):
    if _user_id(request) is None:
        return RedirectResponse("/login", status_code=303)
    return FileResponse(PAGE)


@app.post("/uploads")
async def upload(request: Request, file: UploadFile = File(...)) -> dict:
    if _user_id(request) is None:
        return _sign_in_required()
    UPLOADS.mkdir(parents=True, exist_ok=True)
    dest = UPLOADS / Path(file.filename or "upload.csv").name
    dest.write_bytes(await file.read())
    return {"csv_path": str(dest)}


@app.post("/runs")
def create_run(body: RunRequest, request: Request) -> dict:
    if _user_id(request) is None:
        return _sign_in_required()
    pasted = (body.report_text or "").strip()
    # A paste or an upload wins over the sample checkbox. The sample file is
    # jackets, and its prices must not be used for another product's cost.
    if pasted or (body.csv_path and not body.use_sample):
        body.use_sample = False
    if body.use_sample:
        # The sample rows are JACKET-01. The typed name is put back on the dashboard after the run.
        csv_path = str(SAMPLE)
        product_code = "JACKET-01"
    elif body.report_text and body.report_text.strip():
        UPLOADS.mkdir(parents=True, exist_ok=True)
        # One shared file. Two people pasting at once overwrite each other.
        pasted = UPLOADS / "pasted-report.txt"
        pasted.write_text(body.report_text, encoding="utf-8")
        csv_path = str(pasted)
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