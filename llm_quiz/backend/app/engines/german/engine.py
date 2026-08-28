"""German dative/accusative masculine-article quiz engine.

The blank is a German article whose case (Dativ/Akkusativ) and definiteness
(definite/indefinite) are determined by the masculine noun it modifies. The LLM
returns only ``sentence``/``translation_en``/``hint_zh``; the engine derives the
answer article from the 【】-marked span and validates the four masculine article
forms.
"""
from __future__ import annotations

import re

from app.engines.base import LanguageEngine, shuffle_questions
from app.engines.german import prompt
from app.engines.german.schemas import (
    ACCUSATIVE_FORMS,
    DEFINITE_FORMS,
    DATIVE_FORMS,
    FALLBACK_VERB,
    CASE_COUNT,
    VALID_FORMS,
)
from app.schemas import ProcessedQuestion, RawQuestion


class GermanQuizRuleError(ValueError):
    """Raw LLM output violates the German article-composition rules."""


_ARTICLE_RE = re.compile(r"【([^】]+)】")
_NOUN_RE = re.compile(r"[A-Za-zÄÖÜäöüß]+")


def _parse_article(sentence: str) -> str:
    match = _ARTICLE_RE.search(sentence)
    if match is None:
        raise GermanQuizRuleError("句中缺少用【】包裹的考察冠词")
    answer = match.group(1).strip()
    if answer not in VALID_FORMS:
        raise GermanQuizRuleError(f"冠词形式非法: {answer}（应为 den/einen/dem/einem）")
    return answer


def _extract_noun(sentence: str, article: str) -> str:
    """Best-effort head noun right after the 【】 span, used as the cool-down key."""
    after = _ARTICLE_RE.split(sentence)[-1]
    match = _NOUN_RE.search(after)
    return match.group(0) if match else FALLBACK_VERB


def validate_raw_articles(data: object) -> list[RawQuestion]:
    if not isinstance(data, list):
        raise GermanQuizRuleError("LLM 输出不是 JSON 数组")
    if len(data) != 6:
        raise GermanQuizRuleError(f"必须恰好 6 个句子，实际: {len(data)}")

    questions: list[RawQuestion] = []
    acc = 0
    dat = 0
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise GermanQuizRuleError(f"第 {i + 1} 项不是对象")
        if "sentence" not in item or "translation_en" not in item:
            raise GermanQuizRuleError(
                f"第 {i + 1} 项缺少 sentence/translation_en 字段"
            )
        sentence = str(item["sentence"]).strip()
        translation = str(item["translation_en"]).strip()
        if not sentence or not translation:
            raise GermanQuizRuleError(f"第 {i + 1} 项 sentence/translation_en 不能为空")

        article = _parse_article(sentence)
        if article in ACCUSATIVE_FORMS:
            acc += 1
            case = "Akkusativ"
        elif article in DATIVE_FORMS:
            dat += 1
            case = "Dativ"
        else:  # unreachable given _parse_article's whitelist, defensive
            raise GermanQuizRuleError(f"第 {i + 1} 项冠词无法归类到第三/第四格: {article}")
        definiteness = "定冠词" if article in DEFINITE_FORMS else "不定冠词"

        questions.append(
            RawQuestion(
                category=case,
                type=definiteness,
                verb=_extract_noun(sentence, article),
                sentence=sentence,
                translation=translation,
                rightAnswer=article,
                hintZh=str(item.get("hint_zh")) if item.get("hint_zh") else None,
            )
        )

    if acc != CASE_COUNT or dat != CASE_COUNT:
        raise GermanQuizRuleError(
            f"第三格/第四格数量必须各 {CASE_COUNT} 个，实际 第三格={dat} 第四格={acc}"
        )
    # LLM emits the three Akkusativ then the three Dativ items; scramble before
    # returning so the stored/history order mixes cases naturally.
    return shuffle_questions(questions)


def enrich_article(q: RawQuestion) -> ProcessedQuestion:
    """Blank the 【】 span -> placeholder (fill-in-the-blank, no options)."""
    sentence_quiz = _ARTICLE_RE.sub("____", q.sentence)
    return ProcessedQuestion(
        **q.model_dump(),
        keywordFurigana="",
        sentenceFurigana="",
        sentenceQuiz=sentence_quiz,
    )


class GermanLanguageEngine(LanguageEngine):
    language_code = "de"
    display_name = "Deutsch / German"

    def validate_raw(self, data: object, _avoid_verbs: list[str]) -> list[RawQuestion]:
        return validate_raw_articles(data)

    def enrich(self, q: RawQuestion) -> ProcessedQuestion:
        return enrich_article(q)

    def question_view(self, record: dict) -> dict:
        return {
            "category": record["category"],
            "type": record["type"],
            "keyword": record["verb"],
            "sentence": record["sentence"],
            "sentenceQuiz": record["sentenceQuiz"],
            "translation": record["translation"],
            "rightAnswer": record["rightAnswer"],
            "hintZh": record.get("hintZh"),
        }

    def prompt_docs(self) -> list[dict[str, str]]:
        return [
            {
                "slug": "article-case",
                "title": "第三/第四格阳性冠词选择",
                "system": prompt.SYSTEM_PROMPT,
                "user": prompt.USER_TEMPLATE,
            }
        ]