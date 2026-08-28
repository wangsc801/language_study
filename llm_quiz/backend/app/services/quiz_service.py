"""Language-agnostic generation pipeline: history -> LLM -> validate -> enrich -> persist.

Every language-specific rule/annotation is delegated to a ``LanguageEngine``; this
module only orchestrates the flow shared by all languages.
"""
from __future__ import annotations

import uuid

from pydantic import ValidationError

from app.database import get_frequent_keywords, get_prompt_template, insert_questions
from app.engines.base import LanguageEngine
from app.llm import LLMError, _extract_json, chat_json
from app.schemas import ProcessedQuestion


class QuizGenerationError(RuntimeError):
    pass


async def resolve_avoid_verbs(language: str, avoid_verbs: list[str] | None, auto_exclude: int) -> list[str]:
    if avoid_verbs:
        return [v for v in dict.fromkeys(avoid_verbs)]
    if auto_exclude > 0:
        rows = await get_frequent_keywords(language, limit=auto_exclude)
        return [row["keyword"] for row in rows]
    return []


async def generate_quiz(
    engine: LanguageEngine,
    language: str,
    slug: str | None = None,
    avoid_verbs: list[str] | None = None,
    auto_exclude: int = 20,
) -> tuple[str, list[ProcessedQuestion]]:
    """Run the full pipeline and persist the batch. Returns ``(batch_id, questions)``."""
    avoid = await resolve_avoid_verbs(language, avoid_verbs, auto_exclude)
    template = await get_prompt_template(language, slug)
    if template is not None:
        system, user = template["system"], template["user"]
    else:
        doc = next((d for d in engine.prompt_docs() if d["slug"] == slug), None) if slug else None
        if doc is None:
            raise QuizGenerationError(f"模板不存在: {slug or '(未指定)'}")
        system, user = doc["system"], doc["user"]
    user = engine.render_user(user, avoid)
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    last_error: str | None = None
    content: str | None = None

    for attempt in range(2):
        try:
            content = await chat_json(messages)
            raw_items = _extract_json(content)
            questions = engine.validate_raw(raw_items, avoid)
            processed = [engine.enrich(q) for q in questions]
        except (ValidationError, ValueError, LLMError) as exc:
            last_error = str(exc)
            if attempt == 0:
                extra = [
                    {"role": "user", "content": f"输出无效：{last_error}\n请严格按契约重新输出完整的 JSON 数组。"}
                ]
                if content is not None:
                    extra.insert(0, {"role": "assistant", "content": content})
                messages = [*messages, *extra]
            continue
        break
    else:
        raise QuizGenerationError(f"LLM 生成失败（已自纠重试）: {last_error}")

    batch_id = str(uuid.uuid4())
    await insert_questions(processed, batch_id, language, ai_response=content)
    return batch_id, processed