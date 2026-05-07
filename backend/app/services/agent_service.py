from app.config import Settings
from app.models.agent import AgentInfo

_AGENT_DESCRIPTIONS = {
    "invoice": "AR/AP invoice analytics — DSO, aging, payment tracking, outstanding balances",  # noqa: E501
    "inventory": "Inventory analytics — stock levels, movements, reorder alerts, days-of-supply",  # noqa: E501
    "sales": "Sales analytics — revenue, gross margin, quota attainment, territory performance",  # noqa: E501
    "orchestrator": "Orchestrator — routes queries to domain agents and synthesizes responses",  # noqa: E501
}


def list_agents(settings: Settings) -> list[AgentInfo]:
    return [
        AgentInfo(
            name=settings.azure_ai_agent_invoice_name,
            description=_AGENT_DESCRIPTIONS["invoice"],
        ),
        AgentInfo(
            name=settings.azure_ai_agent_inventory_name,
            description=_AGENT_DESCRIPTIONS["inventory"],
        ),
        AgentInfo(
            name=settings.azure_ai_agent_sales_name,
            description=_AGENT_DESCRIPTIONS["sales"],
        ),
        AgentInfo(
            name=settings.azure_ai_agent_orchestrator_name,
            description=_AGENT_DESCRIPTIONS["orchestrator"],
        ),
    ]
