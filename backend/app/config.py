from functools import lru_cache
import os
import sys
from pathlib import Path

from pydantic import BaseModel, Field


def resolve_bundle_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "app"
    return Path(__file__).resolve().parent


def resolve_app_data_dir() -> Path:
    env_path = os.getenv("NAVAGATOR_APP_DATA_DIR")
    if env_path:
        return Path(env_path)

    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "Navagator"

    return Path.home() / ".navagator"


def resolve_catalog_path() -> Path:
    env_path = os.getenv("NAVAGATOR_CATALOG_PATH")
    if env_path:
        return Path(env_path)
    return resolve_bundle_dir() / "data" / "tool_catalog.json"


def resolve_database_path() -> Path:
    env_path = os.getenv("NAVAGATOR_DATABASE_PATH")
    if env_path:
        return Path(env_path)

    if getattr(sys, "frozen", False):
        return resolve_app_data_dir() / "navagator.db"

    return Path(__file__).resolve().parent / "data" / "navagator.db"


class Settings(BaseModel):
    app_name: str = "Navagator"
    version: str = "0.1.0"
    local_profile_id: str = Field(
        default_factory=lambda: os.getenv("NAVAGATOR_PROFILE_ID", "default")
    )
    data_path: Path = Field(default_factory=resolve_catalog_path)
    database_path: Path = Field(default_factory=resolve_database_path)
    app_data_dir: Path = Field(default_factory=resolve_app_data_dir)
    openai_api_key: str | None = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY")
    )
    recommendation_model: str = Field(
        default_factory=lambda: os.getenv("NAVAGATOR_OPENAI_MODEL", "gpt-5.4")
    )
    recommendation_reasoning_effort: str = Field(
        default_factory=lambda: os.getenv("NAVAGATOR_REASONING_EFFORT", "low")
    )
    recommendation_verbosity: str = Field(
        default_factory=lambda: os.getenv("NAVAGATOR_VERBOSITY", "low")
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
