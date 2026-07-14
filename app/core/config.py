import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel, Field


class Settings(BaseModel):
    app_name: str = Field(default="ModelOps AI")
    app_env: str = Field(default="development")
    app_debug: bool = Field(default=False)
    app_version: str = Field(default="0.1.0")
    api_v1_prefix: str = Field(default="/api/v1")
    log_level: str = Field(default="INFO")
    ssh_connect_timeout_seconds: int = Field(default=15)
    execution_approval_token: str | None = Field(default=None)
    api_access_key: str | None = Field(default=None)
    database_path: str = Field(default="data/modelops.db")


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache
def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        app_name=os.getenv("APP_NAME", "ModelOps AI"),
        app_env=os.getenv("APP_ENV", "development"),
        app_debug=_get_bool("APP_DEBUG", False),
        app_version=os.getenv("APP_VERSION", "0.1.0"),
        api_v1_prefix=os.getenv("API_V1_PREFIX", "/api/v1"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        ssh_connect_timeout_seconds=int(os.getenv("SSH_CONNECT_TIMEOUT_SECONDS", "15")),
        execution_approval_token=(os.getenv("EXECUTION_APPROVAL_TOKEN") or None),
        api_access_key=(os.getenv("MODEL_OPS_API_KEY") or None),
        database_path=os.getenv("DATABASE_PATH", "data/modelops.db"),
    )
