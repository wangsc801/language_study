"""Language registry CRUD (languages table is the authoritative source)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.database import (
    create_language,
    get_language_by_code,
    list_languages,
    update_language,
)
from app.schemas import LanguageCreate, LanguageInfo, LanguageUpdate

router = APIRouter(prefix="/api/languages", tags=["languages"])


@router.get("", response_model=list[LanguageInfo])
async def list_lang() -> list[LanguageInfo]:
    return [LanguageInfo(**row) for row in await list_languages()]


@router.post("", response_model=LanguageInfo, status_code=201)
async def create_lang(payload: LanguageCreate) -> LanguageInfo:
    row = await create_language(payload.language_code, payload.display_name)
    if row is None:
        raise HTTPException(
            status_code=409, detail=f"language_code 已存在: {payload.language_code}"
        )
    return LanguageInfo(**row)


@router.put("/{language_code}", response_model=LanguageInfo)
async def update_lang(language_code: str, payload: LanguageUpdate) -> LanguageInfo:
    if payload.language_code is None and payload.display_name is None:
        raise HTTPException(
            status_code=400, detail="至少提供 language_code/display_name 之一"
        )
    row, status = await update_language(
        language_code,
        new_code=payload.language_code,
        display_name=payload.display_name,
    )
    if status == "missing":
        raise HTTPException(status_code=404, detail=f"语言不存在: {language_code}")
    if status == "conflict":
        raise HTTPException(
            status_code=409, detail=f"language_code 已存在: {payload.language_code}"
        )
    return LanguageInfo(**row)