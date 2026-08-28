"""Word/verb statistics endpoints, language-parametrized via ``{lang}``."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.database import get_frequent_keywords
from app.engines import UnknownLanguageError, get_engine
from app.schemas import VerbFrequencyResponse

router = APIRouter(prefix="/api/{lang}", tags=["verbs"])


@router.get("/verbs/frequent", response_model=VerbFrequencyResponse)
async def frequent(
    lang: str,
    limit: int = Query(default=20, ge=1, le=100),
    since_days: int = Query(default=0, ge=0),
) -> VerbFrequencyResponse:
    try:
        get_engine(lang)
    except UnknownLanguageError as exc:
        raise HTTPException(status_code=404, detail=f"不支持的语言: {lang}") from exc
    return VerbFrequencyResponse(
        verbs=await get_frequent_keywords(lang, limit=limit, since_days=since_days)
    )