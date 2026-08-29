"""Language engine abstraction shared by all supported languages.

A language engine owns every piece of logic that is specific to how a language
builds and validates a "fill-in-blank conjugation" quiz: the LLM prompt, the raw
JSON validation rules, and the enrichment step (furigana/romaji/annotation).

Generic infrastructure (LLM client, persistence, HTTP routers) only talks to the
engine through this interface, so adding a new language == adding one engine
package and registering it in ``app.engines.REGISTRY``.
"""
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas import ProcessedQuestion, RawQuestion


class LanguageEngine(ABC):
    """Contract every language must implement."""

    language_code: str
    display_name: str

    def render_user(self, user: str, avoid_verbs: list[str]) -> str:
        """Substitute placeholders into a user-edit template before sending to the LLM.

        ``avoid_verbs`` is the list of words/items the model must not repeat.
        Override per language to fill language-specific placeholders.
        """
        avoid = "、".join(avoid_verbs) if avoid_verbs else "（无，自由选词）"
        return user.replace("{avoid}", avoid)

    @abstractmethod
    def validate_raw(self, data: object, avoid_verbs: list[str]) -> list[RawQuestion]:
        """Strictly validate the raw JSON returned by the LLM.

        Raise ``ValueError`` (or a subclass) with a Chinese explanation on any
        contract violation so the pipeline can self-correct and retry.
        """

    @abstractmethod
    def enrich(self, q: RawQuestion) -> ProcessedQuestion:
        """Annotate pronunciation + blank the sentence (language-specific)."""

    def prompt_docs(self) -> list[dict[str, str]]:
        """Prompt templates this language supports (one per slug, not filled).

        Each entry: ``{"slug": str, "title": str, "system": str, "user": str}``.
        ``slug`` is the stable identifier used in URLs; ``title`` is the display label.
        Override per language; seeded into ``quiz_templates`` at startup.
        """
        return []

    def question_view(self, record: dict) -> dict:
        """Public JSON shape for one stored question, as returned by the read APIs
        (/quiz/history, /quiz/{id}).

        ``record`` is the full processed payload (see ``result_json``) merged with
        ``id``/``language``/``batch_id``/``created_at``. Override per language to
        customize the shape — e.g. Japanese exposes furigana and ``incorrectOptions``,
        while German omits furigana entirely.
        """
        return dict(record)

    def protected_words(self) -> set[str]:
        """Words that this language's templates structurally require, so they must
        be excluded from the auto-derived ``{avoid}`` list (e.g. Japanese カ変/サ変
        fallbacks 来る/する). Default: nothing is protected."""
        return set()

    def init(self) -> None:
        """Startup hook (e.g. load a tagger/dictionary). Default: no-op."""


def shuffle_options(
    right_answer: str,
    incorrect_answers: list[str],
    rng: random.Random | None = None,
) -> tuple[list[str], int]:
    """Shuffle the four options; return ``(options, 1-based answer_position)``."""
    rng = rng or random.Random()
    options = [right_answer, *incorrect_answers]
    rng.shuffle(options)
    return options, options.index(right_answer) + 1


def shuffle_questions(questions: list[RawQuestion], rng: random.Random | None = None) -> list[RawQuestion]:
    """Shuffle question order in place of the returned list.

    LLMs often emit questions in a grouped order (e.g. German always sends the
    three Akkusativ items then the three Dativ ones); scrambling before
    persisting keeps the stored/history order natural. Returns a new list.
    """
    rng = rng or random.Random()
    shuffled = list(questions)
    rng.shuffle(shuffled)
    return shuffled


async def frequent_keywords(language: str, limit: int = 20) -> list[str]:
    """Top ``limit`` most frequent ``keyword`` values for a language (empty list if
    no data yet). Used by engines to build an avoidance list for generation."""
    from app.database import get_frequent_keywords

    rows = await get_frequent_keywords(language, limit=limit)
    return [row["keyword"] for row in rows]