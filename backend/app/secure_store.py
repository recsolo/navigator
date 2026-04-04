from __future__ import annotations

import os
from pathlib import Path
import sys

from .config import get_settings

SERVICE_NAME = "Navigator"
LEGACY_SERVICE_NAME = "Navagator"


def _get_env(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def _secret_backend() -> str:
    explicit = _get_env("NAVIGATOR_SECRET_BACKEND", "NAVAGATOR_SECRET_BACKEND")
    if explicit:
        return explicit.lower()
    if sys.platform == "win32":
        return "wincred"
    return "file"


def _credential_name(profile_id: str) -> str:
    return f"{profile_id}:openai_api_key"


def _load_keyring():
    try:
        import keyring  # type: ignore
        from keyring.errors import PasswordDeleteError  # type: ignore
    except ImportError:
        return None, None
    return keyring, PasswordDeleteError


def _secret_path(profile_id: str) -> Path:
    settings = get_settings()
    secret_dir = settings.app_data_dir / "secure"
    secret_dir.mkdir(parents=True, exist_ok=True)
    safe_profile = profile_id.replace("\\", "_").replace("/", "_")
    return secret_dir / f"openai_api_key_{safe_profile}.txt"


def _read_file_secret(profile_id: str) -> str | None:
    path = _secret_path(profile_id)
    if not path.exists():
        return None
    value = path.read_text(encoding="utf-8").strip()
    return value or None


def _write_file_secret(profile_id: str, value: str) -> None:
    _secret_path(profile_id).write_text(value, encoding="utf-8")


def _clear_file_secret(profile_id: str) -> None:
    path = _secret_path(profile_id)
    if path.exists():
        path.unlink()


def _read_windows_credential(profile_id: str) -> str | None:
    keyring, _ = _load_keyring()
    if keyring is None:
        return None
    credential = _credential_name(profile_id)
    return keyring.get_password(SERVICE_NAME, credential) or keyring.get_password(
        LEGACY_SERVICE_NAME, credential
    )


def _write_windows_credential(profile_id: str, value: str) -> None:
    keyring, _ = _load_keyring()
    if keyring is None:
        raise RuntimeError("keyring is not installed")
    keyring.set_password(SERVICE_NAME, _credential_name(profile_id), value)


def _clear_windows_credential(profile_id: str) -> None:
    keyring, password_delete_error = _load_keyring()
    if keyring is None:
        return
    for service_name in (SERVICE_NAME, LEGACY_SERVICE_NAME):
        try:
            keyring.delete_password(service_name, _credential_name(profile_id))
        except password_delete_error:
            continue


def read_openai_api_key(profile_id: str = "default") -> str | None:
    backend = _secret_backend()
    if backend == "wincred":
        value = _read_windows_credential(profile_id)
        if value:
            return value
        legacy_value = _read_file_secret(profile_id)
        if legacy_value:
            try:
                _write_windows_credential(profile_id, legacy_value)
                _clear_file_secret(profile_id)
            except RuntimeError:
                pass
            return legacy_value
        return None
    return _read_file_secret(profile_id)


def write_openai_api_key(profile_id: str, value: str) -> None:
    if _secret_backend() == "wincred":
        try:
            _write_windows_credential(profile_id, value)
            _clear_file_secret(profile_id)
            return
        except RuntimeError:
            pass
    _write_file_secret(profile_id, value)


def clear_openai_api_key(profile_id: str = "default") -> None:
    if _secret_backend() == "wincred":
        _clear_windows_credential(profile_id)
    _clear_file_secret(profile_id)
