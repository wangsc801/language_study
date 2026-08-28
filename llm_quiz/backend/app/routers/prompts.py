"""LLM prompt templates, grouped per language (from the quiz_templates table)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import (
    create_prompt_template,
    get_language_by_code,
    list_prompt_templates,
    update_prompt_template,
)
from app.engines import get_engine
from app.schemas import PromptTemplateInfo, TemplateCreate

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


class TemplateUpdate(BaseModel):
    slug: str | None = None
    title: str | None = None
    system: str | None = None
    user: str | None = None


async def _check_language(language_code: str) -> None:
    if await get_language_by_code(language_code) is None:
        raise HTTPException(status_code=404, detail=f"不支持的语言: {language_code}")


def _to_info(language_code: str, row: dict[str, Any]) -> PromptTemplateInfo:
    return PromptTemplateInfo(
        language_code=language_code,
        display_name=row["display_name"],
        slug=row["slug"],
        title=row["title"],
        system=row["system"],
        user=row["user"],
    )


@router.get("", response_model=list[PromptTemplateInfo])
async def list_prompts() -> list[PromptTemplateInfo]:
    rows = await list_prompt_templates()
    return [_to_info(row["language_code"], row) for row in rows]


@router.post("", response_model=PromptTemplateInfo, status_code=201)
async def create_prompt(payload: TemplateCreate) -> PromptTemplateInfo:
    await _check_language(payload.language_code)
    row = await create_prompt_template(
        payload.language_code,
        payload.slug,
        payload.title,
        payload.system,
        payload.user,
    )
    if row is None:
        raise HTTPException(
            status_code=409,
            detail=f"模板 slug 已存在: {payload.slug}",
        )
    lang = await get_language_by_code(payload.language_code)
    row["display_name"] = lang["display_name"] if lang else payload.language_code
    return _to_info(payload.language_code, row)


@router.put("/{language_code}/{slug}", response_model=PromptTemplateInfo)
async def update_prompt(language_code: str, slug: str, payload: TemplateUpdate) -> PromptTemplateInfo:
    await _check_language(language_code)
    if payload.slug is None and payload.title is None and payload.system is None and payload.user is None:
        raise HTTPException(status_code=400, detail="至少提供 slug/title/system/user 之一")
    row, status = await update_prompt_template(
        language_code,
        slug,
        slug=payload.slug,
        title=payload.title,
        system=payload.system,
        user=payload.user,
    )
    if status == "missing":
        raise HTTPException(status_code=404, detail="模板不存在")
    if status == "conflict":
        raise HTTPException(status_code=409, detail=f"模板 slug 已存在: {payload.slug}")
    lang = await get_language_by_code(language_code)
    row["display_name"] = lang["display_name"] if lang else language_code
    return _to_info(language_code, row)


@router.post("/{language_code}/{slug}/reset", response_model=PromptTemplateInfo)
async def reset_prompt(language_code: str, slug: str) -> PromptTemplateInfo:
    await _check_language(language_code)
    engine = get_engine(language_code)
    doc = next((d for d in engine.prompt_docs() if d["slug"] == slug), None)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"该模板没有引擎默认值（无法重置）: {slug}")
    row, status = await update_prompt_template(
        language_code, slug, system=doc["system"], user=doc["user"]
    )
    if status == "missing":
        raise HTTPException(status_code=404, detail="模板不存在")
    lang = await get_language_by_code(language_code)
    row["display_name"] = lang["display_name"] if lang else language_code
    return _to_info(language_code, row)