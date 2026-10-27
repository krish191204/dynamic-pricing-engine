"""Small HTTP API around the ten-agent pipeline. Phase 1 only."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.orchestrator import run_analysis

app = FastAPI(title="Dynamic pricing and inventory engine", version="0.1.0")

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "sample_sales.csv"
PAGE = Path(__file__).resolve().parent / "static" / "index.html"


class RunRequest(BaseModel):
    product_code: str = "JACKET-01"
    stock_on_hand: int = Field(ge=0, default=500)
    unit_cost: float = Field(ge=0, default=40)
    csv_path: str | None = None
    manager_override: str | None = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "agents": 10}


@app.get("/")
def home() -> FileResponse:
    return FileResponse(PAGE)


@app.post("/runs")
def create_run(body: RunRequest) -> dict:
    csv_path = body.csv_path or str(SAMPLE)
    return run_analysis(
        csv_path=csv_path,
        product_code=body.product_code,
        stock_on_hand=body.stock_on_hand,
        unit_cost=body.unit_cost,
        manager_override=body.manager_override,
    )
