from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    azure_tenant_id: str
    azure_client_id: str
    azure_client_secret: str
    azure_audience: str
    azure_ai_project_endpoint: str
    azure_ai_model_standard: str = "gpt-4.1-mini"
    azure_ai_model_thinking: str = "o4-mini"
    azure_ai_agent_invoice_name: str
    azure_ai_agent_inventory_name: str
    azure_ai_agent_sales_name: str
    azure_ai_agent_orchestrator_name: str
    azure_ai_agent_version: str = "1"
    azure_ai_agent_orchestrator_version: str = "2"
    backend_cors_origins: str = ""
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
