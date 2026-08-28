"""Mutable runtime LLM configuration.

Loaded at import time from environment defaults, then overridden by any values
persisted in ``data/llm_settings.json``. ``update``/``reset`` allow the settings
page to change config at runtime without restarting the service.
"""
from __future__ import annotations

import json
import os
import threading
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from app.config import settings as env_settings


@dataclass(frozen=True)
class LLMConfig:
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    llm_timeout: float
    llm_json_mode: bool


_STORE_DIR = Path(os.getenv("SETTINGS_DIR", "data"))
_STORE_PATH = _STORE_DIR / "llm_settings.json"


def _from_env() -> LLMConfig:
    return LLMConfig(
        llm_api_key=env_settings.llm_api_key,
        llm_base_url=env_settings.llm_base_url,
        llm_model=env_settings.llm_model,
        llm_timeout=env_settings.llm_timeout,
        llm_json_mode=env_settings.llm_json_mode,
    )


def _load() -> LLMConfig:
    cfg = _from_env()
    try:
        raw = json.loads(_STORE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return cfg
    for field in asdict(cfg):
        value = raw.get(field)
        if value is not None and type(value) is type(getattr(cfg, field)):
            cfg = replace(cfg, **{field: value})
    return cfg


def _persist(cfg: LLMConfig) -> None:
    _STORE_DIR.mkdir(parents=True, exist_ok=True)
    _STORE_PATH.write_text(
        json.dumps(asdict(cfg), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _destroy_store() -> None:
    try:
        _STORE_PATH.unlink()
    except OSError:
        pass


_lock = threading.Lock()
_state = _load()


def mask(key: str) -> str:
    """Hide all but the last 4 chars of a secret."""
    if not key:
        return ""
    if len(key) <= 4:
        return "*" * len(key)
    return f"...{key[-4:]}"


def get() -> LLMConfig:
    return _state


def view() -> dict:
    """API-shaped view of the current config (key masked)."""
    c = _state
    return {
        "llm_base_url": c.llm_base_url,
        "llm_model": c.llm_model,
        "llm_timeout": c.llm_timeout,
        "llm_json_mode": c.llm_json_mode,
        "llm_api_key_masked": mask(c.llm_api_key),
    }


def update(
    *,
    llm_api_key: str | None = None,
    llm_base_url: str | None = None,
    llm_model: str | None = None,
    llm_timeout: float | None = None,
    llm_json_mode: bool | None = None,
    save: bool = False,
) -> dict:
    global _state
    with _lock:
        c = _state
        kw = {}
        if llm_api_key is not None:
            kw["llm_api_key"] = llm_api_key
        if llm_base_url is not None:
            kw["llm_base_url"] = llm_base_url
        if llm_model is not None:
            kw["llm_model"] = llm_model
        if llm_timeout is not None:
            kw["llm_timeout"] = llm_timeout
        if llm_json_mode is not None:
            kw["llm_json_mode"] = llm_json_mode
        if kw:
            c = replace(c, **kw)
        _state = c
        if save:
            _persist(_state)
        return view()


def reset() -> dict:
    global _state
    with _lock:
        _state = _from_env()
        _destroy_store()
        return view()


async def test_connection() -> dict:
    """Fire a one-shot chat request against the current config."""
    from app.llm import chat_json  # deferred to avoid circular import

    try:
        await chat_json([{"role": "user", "content": "ping"}], temperature=0)
    except Exception as exc:  # noqa: BLE001 - surface any provider error to the UI
        return {"ok": False, "error": str(exc) or exc.__class__.__name__}
    return {"ok": True}