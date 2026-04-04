from functools import lru_cache
import os
import sys
from pathlib import Path

from pydantic import BaseModel, Field


def _get_env(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def resolve_bundle_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "app"
    return Path(__file__).resolve().parent


def resolve_app_data_dir() -> Path:
    env_path = _get_env("NAVIGATOR_APP_DATA_DIR", "NAVAGATOR_APP_DATA_DIR")
    if env_path:
        return Path(env_path)

    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "Navigator"

    legacy_local_path = Path.home() / ".navagator"
    if legacy_local_path.exists():
        return legacy_local_path
    return Path.home() / ".navigator"


def resolve_catalog_path() -> Path:
    env_path = _get_env("NAVIGATOR_CATALOG_PATH", "NAVAGATOR_CATALOG_PATH")
    if env_path:
        return Path(env_path)
    return resolve_bundle_dir() / "data" / "tool_catalog.json"


def resolve_database_path() -> Path:
    env_path = _get_env("NAVIGATOR_DATABASE_PATH", "NAVAGATOR_DATABASE_PATH")
    if env_path:
        return Path(env_path)

    if getattr(sys, "frozen", False):
        app_data_dir = resolve_app_data_dir()
        navigator_db = app_data_dir / "navigator.db"
        legacy_db = app_data_dir / "navagator.db"
        if legacy_db.exists() and not navigator_db.exists():
            return legacy_db
        return navigator_db

    data_dir = Path(__file__).resolve().parent / "data"
    navigator_db = data_dir / "navigator.db"
    legacy_db = data_dir / "navagator.db"
    if legacy_db.exists() and not navigator_db.exists():
        return legacy_db
    return navigator_db


class Settings(BaseModel):
    app_name: str = "Navigator"
    version: str = "0.1.0"
    local_profile_id: str = Field(
        default_factory=lambda: _get_env("NAVIGATOR_PROFILE_ID", "NAVAGATOR_PROFILE_ID") or "default"
    )
    data_path: Path = Field(default_factory=resolve_catalog_path)
    database_path: Path = Field(default_factory=resolve_database_path)
    app_data_dir: Path = Field(default_factory=resolve_app_data_dir)
    openai_api_key: str | None = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY")
    )
    recommendation_model: str = Field(
        default_factory=lambda: _get_env("NAVIGATOR_OPENAI_MODEL", "NAVAGATOR_OPENAI_MODEL") or "gpt-5.4"
    )
    recommendation_reasoning_effort: str = Field(
        default_factory=lambda: _get_env("NAVIGATOR_REASONING_EFFORT", "NAVAGATOR_REASONING_EFFORT") or "low"
    )
    recommendation_verbosity: str = Field(
        default_factory=lambda: _get_env("NAVIGATOR_VERBOSITY", "NAVAGATOR_VERBOSITY") or "low"
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
