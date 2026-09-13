from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed application configuration."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "development"
    app_name: str = "Asteria Analyst AI"
    database_url: str = "sqlite:///./data/asteria.db"
    jwt_secret_key: str = "development-only-change-me-at-least-32-bytes"
    jwt_access_token_expire_minutes: int = 60
    llm_provider: str = "mock"
    data_upload_directory: Path = Path("./data/uploads")
    export_directory: Path = Path("./data/exports")
    max_upload_size_mb: int = 100
    allowed_file_types: str = "csv,xlsx,parquet"
    max_query_rows: int = 5000
    default_query_rows: int = 500
    query_timeout_seconds: int = 20
    max_query_joins: int = 5
    max_agent_steps: int = Field(default=6, ge=1, le=12)
    frontend_url: str = "http://localhost:5173"

    @property
    def allowed_extensions(self) -> set[str]:
        return {f".{value.strip().lower()}" for value in self.allowed_file_types.split(",")}


@lru_cache
def get_settings() -> Settings:
    return Settings()
