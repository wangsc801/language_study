"""Environment configuration for the quiz service."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    llm_api_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    llm_base_url: str = field(default_factory=lambda: os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o-mini"))
    llm_timeout: float = field(default_factory=lambda: float(os.getenv("LLM_TIMEOUT", "60")))
    llm_json_mode: bool = field(default_factory=lambda: os.getenv("LLM_JSON_MODE", "true").lower() in {"1", "true", "yes"})
    db_path: Path = field(
        default_factory=lambda: Path(os.getenv("DB_PATH", "data/quizzes.db"))
    )
    llm_max_retries: int = field(default_factory=lambda: int(os.getenv("LLM_MAX_RETRIES", "1")))


settings = Settings()
