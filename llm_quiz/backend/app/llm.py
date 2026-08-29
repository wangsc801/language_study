"""OpenAI-compatible chat client for quiz generation.

Uses the ``openai`` SDK. ``llm_base_url`` is treated as a provider base URL exactly
as documented by that provider — the SDK appends the chat endpoint itself, so the
user does not need to (and should not) include ``/chat/completions`` in their value.
"""
from __future__ import annotations

import json
import re

from openai import AsyncOpenAI

from app.services.runtime_settings import get as get_llm_config

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class LLMError(RuntimeError):
    pass


def _extract_json(text: str) -> object:
    text = _FENCE_RE.sub("", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        start = min(pos for pos in (text.find("["), text.find("{")) if pos != -1) if (
            "[" in text or "{" in text
        ) else None
        if start is not None:
            try:
                return json.loads(text[start:])
            except json.JSONDecodeError:
                pass
        raise LLMError(f"LLM 输出不是合法 JSON: {exc}") from exc


def _mentions_json(messages: list[dict[str, str]]) -> bool:
    """Providers enforcing ``response_format=json_object`` require the literal word
    "json" in the prompt. Return True if any message content contains it."""
    return any("json" in (m.get("content") or "").lower() for m in messages)


async def chat_json(
    messages: list[dict[str, str]],
    temperature: float = 0.8,
) -> str:
    """Call the chat endpoint and return the raw assistant content."""
    cfg = get_llm_config()
    if not cfg.llm_api_key:
        raise LLMError("未配置 LLM_API_KEY")
    if cfg.llm_json_mode and not _mentions_json(messages):
        messages = [*messages, {"role": "user", "content": "请以 JSON 格式输出。"}]
    kwargs: dict = {
        "model": cfg.llm_model,
        "messages": messages,
        "temperature": temperature,
    }
    if cfg.llm_json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    kwargs["extra_body"] = {"thinking": {"type": "disabled"}}

    client = AsyncOpenAI(
        api_key=cfg.llm_api_key,
        base_url=cfg.llm_base_url,
        timeout=cfg.llm_timeout,
    )
    completion = await client.chat.completions.create(**kwargs)
    return completion.choices[0].message.content
