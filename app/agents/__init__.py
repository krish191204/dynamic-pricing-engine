"""Ten specialist agents for one pricing-and-inventory run."""

from app.agents.cleaning_agent import CleaningAgent
from app.agents.dashboard_agent import DashboardAgent
from app.agents.data_agent import DataAgent
from app.agents.evaluation_agent import EvaluationAgent
from app.agents.forecast_agent import ForecastAgent
from app.agents.guardrail_agent import GuardrailAgent
from app.agents.inventory_agent import InventoryAgent
from app.agents.pricing_agent import PricingAgent
from app.agents.requirements_agent import RequirementsAgent
from app.agents.transform_agent import TransformAgent

# Fixed order. A later agent reads what the earlier ones wrote on the context.
# Dashboard still runs after a failure so the page can show the error.
AGENTS = [
    RequirementsAgent(),
    DataAgent(),
    CleaningAgent(),
    TransformAgent(),
    ForecastAgent(),
    InventoryAgent(),
    PricingAgent(),
    GuardrailAgent(),
    EvaluationAgent(),
    DashboardAgent(),
]
