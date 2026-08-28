"""Quiz endpoints, language-parametrized via the ``{lang}`` path segment."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.database import get_quiz, list_quizzes
from app.engines import UnknownLanguageError, get_engine
from app.schemas import GenerateRequest, GenerateResponse
from app.services.quiz_service import QuizGenerationError, generate_quiz

# Flat router: generation is parametrized by lang + template slug via query params.
flat_router = APIRouter(prefix="/api/quiz", tags=["quiz"])

router = APIRouter(prefix="/api/{lang}", tags=["quiz"])


@flat_router.post("/generate", response_model=GenerateResponse)
async def generate(
    lang: str = Query(...),
    slug: str = Query(..., description="模板 slug，如 verb-conjugation"),
    req: GenerateRequest | None = None,
) -> GenerateResponse:
    engine = _engine_for(lang)
    try:
        batch_id, questions = await generate_quiz(
            engine=engine,
            language=lang,
            slug=slug,
            avoid_verbs=req.avoid_verbs if req else None,
            auto_exclude=req.auto_exclude if req else 20,
        )
    except QuizGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    views = [engine.question_view(pq.model_dump()) for pq in questions]
    return GenerateResponse(batch_id=batch_id, questions=views)


@router.get("/quiz/history")
async def history(
    lang: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    _engine_for(lang)
    return await list_quizzes(lang, limit=limit, offset=offset)


@router.get("/quiz/{quiz_id}")
async def get_question(lang: str, quiz_id: int):
    _engine_for(lang)
    row = await get_quiz(quiz_id)
    if row is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    return row


def _engine_for(lang: str):
    try:
        return get_engine(lang)
    except UnknownLanguageError as exc:
        raise HTTPException(status_code=404, detail=f"不支持的语言: {lang}") from exc