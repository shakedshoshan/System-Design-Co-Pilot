import logging
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_API_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _API_ROOT.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_REPO_ROOT / ".env", _API_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["local", "production"] = "local"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    database_url: str | None = None

    openai_api_key: str | None = None
    llm_model: str = "gpt-4o"
    llm_timeout_seconds: float = 120.0
    llm_max_output_chars: int = 32_000
    llm_context_message_limit: int = 50

    log_to_file: bool = True
    log_file: str | None = None
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_max_mb: int = 10
    log_backup_count: int = 5

    @field_validator("database_url", "log_file", "openai_api_key", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: object) -> object:
        if v == "":
            return None
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def json_logs(self) -> bool:
        return self.app_env == "production"

    @property
    def resolved_log_file(self) -> Path | None:
        if not self.log_to_file:
            return None
        if self.log_file:
            p = Path(self.log_file)
            return p if p.is_absolute() else _API_ROOT / p
        return _API_ROOT / "logs" / "app.log"

    @property
    def log_level_int(self) -> int:
        return getattr(logging, self.log_level.upper(), logging.INFO)


@lru_cache
def get_settings() -> Settings:
    return Settings()
