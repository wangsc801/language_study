"""Generic Pydantic models for the quiz service.

Domain-specific taxonomies (e.g. Japanese verb classes) live in each language
engine and are validated inside its ``validate_raw`` — here fields are free-form
``str`` so the HTTP layer stays language-neutral.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RawQuestion(BaseModel):
    """The minimal JSON that the LLM must return (no furigana, no explanations)."""

    category: str = Field(min_length=1)
    type: str
    verb: str = Field(min_length=1)
    sentence: str = Field(min_length=1)
    translation: str = Field(min_length=1)
    rightAnswer: str = Field(min_length=1)
    hintZh: str | None = None


class ProcessedQuestion(RawQuestion):
    """The enriched question returned by the service / persisted to SQLite."""

    keywordFurigana: str
    sentenceFurigana: str
    sentenceQuiz: str


class GenerateRequest(BaseModel):
    avoid_verbs: list[str] | None = None
    auto_exclude: int = Field(default=20, ge=0)


class GenerateResponse(BaseModel):
    batch_id: str
    # Questions are shaped by the language engine (optionally MCQ, optionally with
    # furigana), so the payload is left as free-form dicts.
    questions: list[dict[str, Any]]


class VerbFrequency(BaseModel):
    keyword: str
    count: int


class VerbFrequencyResponse(BaseModel):
    verbs: list[VerbFrequency]


class SettingsUpdate(BaseModel):
    """Runtime LLM settings for the /api/settings endpoint."""

    llm_api_key: str | None = None
    llm_base_url: str | None = None
    llm_model: str | None = None
    llm_timeout: float | None = Field(default=None, gt=0)
    llm_json_mode: bool | None = None
    save: bool = False


class SettingsView(BaseModel):
    llm_base_url: str
    llm_model: str
    llm_timeout: float
    llm_json_mode: bool
    llm_api_key_masked: str


class PromptTemplateInfo(BaseModel):
    language_code: str
    display_name: str
    slug: str
    title: str
    system: str
    user: str


class TemplateCreate(BaseModel):
    language_code: str = Field(min_length=1)
    slug: str = Field(min_length=1)
    title: str = Field(min_length=1)
    system: str = ""
    user: str = ""


class LanguageInfo(BaseModel):
    id: int
    language_code: str
    display_name: str


class LanguageCreate(BaseModel):
    language_code: str = Field(min_length=1)
    display_name: str = Field(min_length=1)


class LanguageUpdate(BaseModel):
    language_code: str | None = None
    display_name: str | None = None