from __future__ import annotations

import base64
from pathlib import Path
import sys

from .config import get_settings

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    CRYPTPROTECT_UI_FORBIDDEN = 0x01

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [
            ("cbData", wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_byte)),
        ]

    _crypt32 = ctypes.windll.crypt32
    _kernel32 = ctypes.windll.kernel32


def _secret_path() -> Path:
    settings = get_settings()
    secret_dir = settings.app_data_dir / "secure"
    secret_dir.mkdir(parents=True, exist_ok=True)
    return secret_dir / "openai_api_key.bin"


def _protect_windows(value: str) -> bytes:
    raw = value.encode("utf-8")
    input_buffer = ctypes.create_string_buffer(raw, len(raw))
    input_blob = DATA_BLOB(
        cbData=len(raw),
        pbData=ctypes.cast(input_buffer, ctypes.POINTER(ctypes.c_byte)),
    )
    output_blob = DATA_BLOB()

    if not _crypt32.CryptProtectData(
        ctypes.byref(input_blob),
        None,
        None,
        None,
        None,
        CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(output_blob),
    ):
        raise ctypes.WinError()

    try:
        encrypted = ctypes.string_at(output_blob.pbData, output_blob.cbData)
        return encrypted
    finally:
        _kernel32.LocalFree(output_blob.pbData)


def _unprotect_windows(payload: bytes) -> str:
    input_buffer = ctypes.create_string_buffer(payload, len(payload))
    input_blob = DATA_BLOB(
        cbData=len(payload),
        pbData=ctypes.cast(input_buffer, ctypes.POINTER(ctypes.c_byte)),
    )
    output_blob = DATA_BLOB()

    if not _crypt32.CryptUnprotectData(
        ctypes.byref(input_blob),
        None,
        None,
        None,
        None,
        CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(output_blob),
    ):
        raise ctypes.WinError()

    try:
        decrypted = ctypes.string_at(output_blob.pbData, output_blob.cbData)
        return decrypted.decode("utf-8")
    finally:
        _kernel32.LocalFree(output_blob.pbData)


def read_openai_api_key() -> str | None:
    path = _secret_path()
    if not path.exists():
        return None

    encoded = path.read_bytes()
    if not encoded:
        return None

    if sys.platform == "win32":
        protected = base64.b64decode(encoded)
        return _unprotect_windows(protected)

    return encoded.decode("utf-8")


def write_openai_api_key(value: str) -> None:
    path = _secret_path()
    if sys.platform == "win32":
        protected = _protect_windows(value)
        path.write_bytes(base64.b64encode(protected))
        return

    path.write_text(value, encoding="utf-8")


def clear_openai_api_key() -> None:
    path = _secret_path()
    if path.exists():
        path.unlink()
