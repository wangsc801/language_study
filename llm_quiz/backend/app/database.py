"""SQLite persistence for quiz questions (shared across languages).

Uses SQLAlchemy 2.0 async ORM with the aiosqlite driver.

Schema notes:
- ``quizzes.batch_id`` is a foreign key onto ``quiz_batches.batch_id`` (referential
  integrity enforced via ``PRAGMA foreign_keys``).
- ``language`` lives on ``quiz_batches`` only (no redundancy on ``quizzes``) -> 3NF.
- ``quiz_templates`` is a per-(language, slug) registry of prompt templates.
- ``quizzes`` keeps only queryable/display-list columns (``category``, ``sub_category``,
  ``keyword``, ``sentence``, ``sentence_quiz``, ``translation``, ``right_answer``); the full
  renderable question (options, answer position, furigana, etc.) lives in ``result_json``.
"""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    event,
    func,
    select,
    text,
)
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import settings
from app.schemas import ProcessedQuestion


class Base(DeclarativeBase):
    pass


class QuizBatch(Base):
    __tablename__ = "quiz_batches"
    __table_args__ = (
        Index("idx_batches_language", "language"),
        Index("idx_batches_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    language: Mapped[str] = mapped_column(Text, nullable=False)
    num_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ai_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("datetime('now','localtime')")
    )


class Quiz(Base):
    """One fill-in-the-blank multiple-choice question.

    Keeps only the queryable / display-list columns as indexed fields (used for
    frequency and history listing). The complete, renderable question is stored in
    ``result_json`` (the full processed payload); fields like options, answer
    position and furigana are reconstructed from it rather than duplicated here.
    """
    __tablename__ = "quizzes"
    __table_args__ = (
        Index("idx_quizzes_keyword", "keyword"),
        Index("idx_quizzes_created", "created_at"),
        Index("idx_quizzes_batch", "batch_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[str] = mapped_column(
        Text, ForeignKey("quiz_batches.batch_id"), nullable=False
    )
    category: Mapped[str] = mapped_column(Text, nullable=False)
    sub_category: Mapped[str] = mapped_column(Text, nullable=False)
    keyword: Mapped[str] = mapped_column(Text, nullable=False)
    lang: Mapped[str] = mapped_column(Text, nullable=False)
    sentence: Mapped[str] = mapped_column(Text, nullable=False)
    sentence_quiz: Mapped[str | None] = mapped_column(Text, nullable=True)
    translation: Mapped[str] = mapped_column(Text, nullable=False)
    right_answer: Mapped[str] = mapped_column(Text, nullable=False)
    result_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("datetime('now','localtime')")
    )


class Language(Base):
    __tablename__ = "languages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    language_code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("datetime('now','localtime')")
    )


class QuizTemplate(Base):
    __tablename__ = "quiz_templates"
    __table_args__ = (UniqueConstraint("language_id", "slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    language_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("languages.id"), nullable=False
    )
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    system: Mapped[str] = mapped_column(Text, nullable=False)
    user: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("datetime('now','localtime')")
    )


_engine = create_async_engine(
    f"sqlite+aiosqlite:///{settings.db_path.as_posix()}", echo=False
)
SessionLocal = async_sessionmaker(_engine, expire_on_commit=False)

# Enforce FK referential integrity on SQLite (off by default).
@event.listens_for(_engine.sync_engine, "connect")
def _enable_foreign_keys(dbapi_conn, _record):
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON")
    cur.close()


async def init_db() -> None:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ---------------------------------------------------------------------------
# quiz_batches / quizzes
# ---------------------------------------------------------------------------


def _to_model(q: ProcessedQuestion, batch_id: str, lang: str) -> Quiz:
    """Persist a question. Indexed columns mirror the underlying schema fields;
    the full payload is kept verbatim in ``result_json`` so no renderable data
    is lost when the lean columns are dropped."""
    return Quiz(
        batch_id=batch_id,
        category=q.category,
        sub_category=q.type,
        keyword=q.verb,
        lang=lang,
        sentence=q.sentence,
        sentence_quiz=q.sentenceQuiz,
        translation=q.translation,
        right_answer=q.rightAnswer,
        result_json=json.dumps(q.model_dump(), ensure_ascii=False),
    )


async def insert_questions(
    questions: list[ProcessedQuestion],
    batch_id: str,
    language: str,
    ai_response: str | None = None,
) -> list[int]:
    """Insert one batch (and its quizzes). Returns inserted row ids."""
    async with SessionLocal() as session:
        session.add(
            QuizBatch(
                batch_id=batch_id,
                language=language,
                num_questions=len(questions),
                ai_response=ai_response,
            )
        )
        # Persist the parent batch first so the quizzes.insert FK is satisfied.
        await session.flush()
        session.add_all([_to_model(q, batch_id, language) for q in questions])
        await session.flush()
        rows = await session.execute(
            select(Quiz.id).where(Quiz.batch_id == batch_id).order_by(Quiz.id)
        )
        ids = list(rows.scalars())
        await session.commit()
        return ids


async def get_frequent_keywords(
    language: str, limit: int = 20, since_days: int = 0
) -> list[dict[str, Any]]:
    """Top keywords for a language, using the denormalized ``quizzes.lang`` column."""
    count = func.count()
    stmt = select(Quiz.keyword, count.label("count")).where(Quiz.lang == language)
    if since_days > 0:
        stmt = stmt.where(
            Quiz.created_at >= func.datetime("now", "localtime", f"-{since_days} days")
        )
    stmt = (
        stmt.group_by(Quiz.keyword)
        .order_by(count.desc(), Quiz.keyword)
        .limit(limit)
    )
    async with SessionLocal() as session:
        result = await session.execute(stmt)
        return [{"keyword": row.keyword, "count": row.count} for row in result.all()]


async def list_quizzes(
    language: str, limit: int = 50, offset: int = 0
) -> list[dict[str, Any]]:
    stmt = (
        select(Quiz, QuizBatch.language)
        .join(QuizBatch, Quiz.batch_id == QuizBatch.batch_id)
        .where(QuizBatch.language == language)
        .order_by(Quiz.created_at.desc(), Quiz.id.desc())
        .limit(limit)
        .offset(offset)
    )
    async with SessionLocal() as session:
        result = await session.execute(stmt)
        return [_row_to_dict(q, lang) for q, lang in result.all()]


async def get_quiz(quiz_id: int) -> dict[str, Any] | None:
    stmt = (
        select(Quiz, QuizBatch.language)
        .join(QuizBatch, Quiz.batch_id == QuizBatch.batch_id)
        .where(Quiz.id == quiz_id)
    )
    async with SessionLocal() as session:
        row = (await session.execute(stmt)).first()
        return _row_to_dict(row[0], row[1]) if row else None


def _row_to_dict(q: Quiz, language: str) -> dict[str, Any]:
    """Reassemble a question from its lean columns plus the full ``result_json``
    payload, then delegate the public JSON shape to the language engine so each
    language's question serialization is customized (furigana, option labels, …).

    The engine's ``question_view`` returns pure question content (no metadata);
    read APIs attach id/language/batch_id/created_at here for navigation."""
    record = json.loads(q.result_json)
    from app.engines import get_engine

    view = get_engine(language).question_view(record)
    view.update(id=q.id, language=language, batch_id=q.batch_id, created_at=q.created_at)
    return view
    return d


# ---------------------------------------------------------------------------
# languages
# ---------------------------------------------------------------------------


async def list_languages() -> list[dict[str, Any]]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Language).order_by(Language.language_code)
        )
        return [
            {
                "id": l.id,
                "language_code": l.language_code,
                "display_name": l.display_name,
            }
            for l in result.scalars()
        ]


async def get_language_by_code(language_code: str) -> dict[str, Any] | None:
    async with SessionLocal() as session:
        l = (
            await session.execute(
                select(Language).where(Language.language_code == language_code)
            )
        ).scalar_one_or_none()
        if l is None:
            return None
        return {
            "id": l.id,
            "language_code": l.language_code,
            "display_name": l.display_name,
        }


async def create_language(
    language_code: str, display_name: str
) -> dict[str, Any] | None:
    """Insert a new language. Returns the row, or None if the code already exists."""
    async with SessionLocal() as session:
        exists = (
            await session.execute(
                select(Language.id).where(Language.language_code == language_code)
            )
        ).scalar_one_or_none()
        if exists is not None:
            return None
        l = Language(language_code=language_code, display_name=display_name)
        session.add(l)
        await session.commit()
        return {
            "id": l.id,
            "language_code": l.language_code,
            "display_name": l.display_name,
        }


async def update_language(
    language_code: str,
    *,
    new_code: str | None = None,
    display_name: str | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Update a language. ``language_code`` locates the row; ``new_code`` renames the
    code (uniqueness checked). Returns ``(row, None)`` / ``(None, "conflict")`` /
    ``(None, "missing")``."""
    async with SessionLocal() as session:
        l = (
            await session.execute(
                select(Language).where(Language.language_code == language_code)
            )
        ).scalar_one_or_none()
        if l is None:
            return None, "missing"
        final_code = new_code if new_code is not None else language_code
        if final_code != language_code:
            collision = (
                await session.execute(
                    select(Language.id).where(Language.language_code == final_code)
                )
            ).scalar_one_or_none()
            if collision is not None:
                return None, "conflict"
        if new_code is not None:
            l.language_code = final_code
        if display_name is not None:
            l.display_name = display_name
        await session.commit()
        return {
            "id": l.id,
            "language_code": l.language_code,
            "display_name": l.display_name,
        }, None


async def upsert_languages(seeds: list[dict[str, str]]) -> None:
    """Insert-or-ignore languages (idempotent seed). Does not overwrite edits."""
    async with SessionLocal() as session:
        for doc in seeds:
            await session.execute(
                sqlite_insert(Language)
                .values(
                    language_code=doc["language_code"],
                    display_name=doc["display_name"],
                )
                .on_conflict_do_nothing(index_elements=["language_code"])
            )
        await session.commit()


# ---------------------------------------------------------------------------
# quiz_templates
# ---------------------------------------------------------------------------


async def _language_id(language_code: str) -> int | None:
    async with SessionLocal() as session:
        return (
            await session.execute(
                select(Language.id).where(Language.language_code == language_code)
            )
        ).scalar_one_or_none()


async def upsert_prompt_templates(language_code: str, docs: list[dict[str, str]]) -> None:
    """Insert-or-ignore prompt templates for a language (idempotent seed)."""
    lang_id = await _language_id(language_code)
    if lang_id is None:
        return
    async with SessionLocal() as session:
        for doc in docs:
            await session.execute(
                sqlite_insert(QuizTemplate)
                .values(
                    language_id=lang_id,
                    slug=doc["slug"],
                    title=doc["title"],
                    system=doc["system"],
                    user=doc["user"],
                )
                .on_conflict_do_nothing(index_elements=["language_id", "slug"])
            )
        await session.commit()


async def list_prompt_templates() -> list[dict[str, Any]]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(QuizTemplate, Language.language_code, Language.display_name)
            .join(Language, QuizTemplate.language_id == Language.id)
            .order_by(Language.language_code, QuizTemplate.slug)
        )
        return [
            {
                "language_code": code,
                "display_name": display,
                "slug": t.slug,
                "title": t.title,
                "system": t.system,
                "user": t.user,
                "created_at": t.created_at,
            }
            for t, code, display in result.all()
        ]


async def get_prompt_template(
    language_code: str, slug: str | None = None
) -> dict[str, str] | None:
    """Return a template's prompt for generation. Selects by ``slug`` when given,
    else the language's first template. Returns None if nothing matches."""
    lang_id = await _language_id(language_code)
    if lang_id is None:
        return None
    async with SessionLocal() as session:
        stmt = select(QuizTemplate).where(QuizTemplate.language_id == lang_id)
        if slug:
            stmt = stmt.where(QuizTemplate.slug == slug)
        else:
            stmt = stmt.order_by(QuizTemplate.slug).limit(1)
        t = (await session.execute(stmt)).scalar_one_or_none()
        return {"system": t.system, "user": t.user} if t else None


async def create_prompt_template(
    language_code: str, slug: str, title: str, system: str, user: str
) -> dict[str, Any] | None:
    """Insert a new template. Returns the stored row, or None if (language, slug)
    already exists."""
    lang_id = await _language_id(language_code)
    if lang_id is None:
        return None
    async with SessionLocal() as session:
        exists = (
            await session.execute(
                select(QuizTemplate.id).where(
                    QuizTemplate.language_id == lang_id,
                    QuizTemplate.slug == slug,
                )
            )
        ).scalar_one_or_none()
        if exists is not None:
            return None
        t = QuizTemplate(
            language_id=lang_id, slug=slug, title=title, system=system, user=user
        )
        session.add(t)
        await session.commit()
        return {
            "language_id": lang_id,
            "slug": t.slug,
            "title": t.title,
            "system": t.system,
            "user": t.user,
        }


async def update_prompt_template(
    language_code: str,
    current_slug: str,
    *,
    slug: str | None = None,
    title: str | None = None,
    system: str | None = None,
    user: str | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Update an existing template. ``current_slug`` locates the row; any of the
    other fields may be overridden (``slug`` renames the key).

    Returns ``(row, None)`` on success, ``(None, "conflict")`` if the new slug
    collides with another row of the same language, or ``(None, "missing")``.
    """
    lang_id = await _language_id(language_code)
    if lang_id is None:
        return None, "missing"
    async with SessionLocal() as session:
        t = (
            await session.execute(
                select(QuizTemplate).where(
                    QuizTemplate.language_id == lang_id,
                    QuizTemplate.slug == current_slug,
                )
            )
        ).scalar_one_or_none()
        if t is None:
            return None, "missing"
        new_slug = slug if slug is not None else current_slug
        if new_slug != current_slug:
            collision = (
                await session.execute(
                    select(QuizTemplate.id).where(
                        QuizTemplate.language_id == lang_id,
                        QuizTemplate.slug == new_slug,
                    )
                )
            ).scalar_one_or_none()
            if collision is not None:
                return None, "conflict"
        if slug is not None:
            t.slug = new_slug
        if title is not None:
            t.title = title
        if system is not None:
            t.system = system
        if user is not None:
            t.user = user
        await session.commit()
        return {
            "language_id": lang_id,
            "slug": t.slug,
            "title": t.title,
            "system": t.system,
            "user": t.user,
        }, None