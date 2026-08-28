"""Runtime LLM configuration endpoints (backing the /settings page)."""
from __future__ import annotations

from fastapi import APIRouter

from app.schemas import SettingsUpdate, SettingsView
from app.services import runtime_settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsView)
async def get_settings() -> SettingsView:
    return SettingsView(**runtime_settings.view())


@router.post("", response_model=SettingsView)
async def update_settings(payload: SettingsUpdate) -> SettingsView:
    current_masked = runtime_settings.view()["llm_api_key_masked"]
    api_key = payload.llm_api_key
    if api_key in (None, "", current_masked) or (api_key and api_key.startswith("...")):
        api_key = None  # empty / masked sentinel: keep the stored key
    return SettingsView(
        **runtime_settings.update(
            llm_api_key=api_key,
            llm_base_url=payload.llm_base_url,
            llm_model=payload.llm_model,
            llm_timeout=payload.llm_timeout,
            llm_json_mode=payload.llm_json_mode,
            save=payload.save,
        )
    )


@router.post("/reset", response_model=SettingsView)
async def reset_settings() -> SettingsView:
    return SettingsView(**runtime_settings.reset())


@router.post("/test")
async def test_settings() -> dict:
    return await runtime_settings.test_connection()