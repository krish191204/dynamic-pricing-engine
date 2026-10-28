"""Small HTTP API around the ten-agent pipeline. Phase 1 only."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.orchestrator import run_analysis

app = FastAPI(title="Dynamic pricing and inventory engine", version="0.1.0")

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "sample_sales.csv"
UPLOADS = ROOT / "data" / "uploads"
PAGE = Path(__file__).resolve().parent / "static" / "index.html"


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


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "agents": 10}


@app.get("/")
def home() -> FileResponse:
    return FileResponse(PAGE)


@app.post("/uploads")
async def upload(file: UploadFile = File(...)) -> dict:
    UPLOADS.mkdir(parents=True, exist_ok=True)
    dest = UPLOADS / Path(file.filename or "upload.csv").name
    dest.write_bytes(await file.read())
    return {"csv_path": str(dest)}


@app.post("/runs")
def create_run(body: RunRequest) -> dict:
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