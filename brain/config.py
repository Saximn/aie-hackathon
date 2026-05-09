"""Runtime configuration helpers."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).with_name(".env")

load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    """Environment-backed settings for integrations."""

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    hyperspell_api_key: str = ""
    hyperspell_user_id: str = "omniforge:local"
    hyperspell_sources: list[str] = Field(default_factory=lambda: ["vault"])
    hyperspell_collection: str = "omniforge-agent-memory"


@lru_cache
def settings() -> Settings:
    return Settings()
