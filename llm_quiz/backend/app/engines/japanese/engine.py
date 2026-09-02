"""Japanese verb-conjugation quiz engine."""
from __future__ import annotations

from app.engines.base import LanguageEngine
from app.engines.japanese import furigana, prompt
from app.engines.japanese.schemas import (
    VALID_CATEGORIES,
    VALID_TYPES,
)
from app.schemas import ProcessedQuestion, RawQuestion


class QuizRuleError(ValueError):
    """Raw LLM output violates the Japanese composition rules."""


def validate_raw_questions(data: object, avoid_verbs: list[str]) -> list[RawQuestion]:
    if not isinstance(data, list):
        raise QuizRuleError("LLM 输出不是 JSON 数组")
    if not data:
        raise QuizRuleError("LLM 输出为空数组")

    questions = [RawQuestion.model_validate(item) for item in data]

    for q in questions:
        if q.category not in VALID_CATEGORIES:
            raise QuizRuleError(f"非法动词分类: {q.category}")

    verbs = [q.verb for q in questions]
    if len(set(verbs)) != len(verbs):
        raise QuizRuleError("存在重复动词")
    # 宽容度策略：avoid_verbs 仅作为 prompt 提示，不再拦截命中回避词的返回，
    # 以免 LLM 偶发命中时整个批次 502。重复动词仍不允许。

    for q in questions:
        if q.type not in VALID_TYPES:
            raise QuizRuleError(f"【{q.verb}】type 非法（应为 て形/た形/ます形）: {q.type}")
        if not q.hintZh:
            raise QuizRuleError(f"【{q.verb}】缺少提示 hintZh")
        if q.rightAnswer in q.hintZh:
            raise QuizRuleError(f"【{q.verb}】提示中不能直接出现答案")

    return questions


def enrich_question(q: RawQuestion) -> ProcessedQuestion:
    """furigana annotation + blanking. Fill-in-the-blank: no options to shuffle."""
    marked, sentence_furigana, sentence_quiz = furigana.process_sentence(q.sentence)
    if marked != q.rightAnswer:
        raise furigana.ContractError(
            f"【{q.verb}】例句标注【{marked}】与 rightAnswer({q.rightAnswer}) 不一致"
        )
    return ProcessedQuestion(
        **q.model_dump(),
        keywordFurigana=furigana.annotate(q.verb),
        sentenceFurigana=sentence_furigana,
        sentenceQuiz=sentence_quiz,
    )


class JapaneseLanguageEngine(LanguageEngine):
    language_code = "ja"
    display_name = "日本語 / Japanese"

    def validate_raw(self, data: object, avoid_verbs: list[str]) -> list[RawQuestion]:
        return validate_raw_questions(data, avoid_verbs)

    def enrich(self, q: RawQuestion) -> ProcessedQuestion:
        return enrich_question(q)

    def protected_words(self) -> set[str]:
        # The模板固定要求从 来る/する 中出 2 道 カ/サ変, 这两个词不能设 avoid,
        # 否则约束互相矛盾必然 502。给足宽容度, 始终允许被选中。
        return {"来る", "する"}

    def question_view(self, record: dict) -> dict:
        return {
            "category": record["category"],
            "type": record["type"],
            "keyword": record["verb"],
            "keywordFurigana": record.get("keywordFurigana") or "",
            "sentence": record["sentence"],
            "sentenceFurigana": record.get("sentenceFurigana") or "",
            "sentenceQuiz": record["sentenceQuiz"],
            "translation": record["translation"],
            "rightAnswer": record["rightAnswer"],
            "hintZh": record.get("hintZh"),
        }

    def prompt_docs(self) -> list[dict[str, str]]:
        return [
            {
                "slug": "verb-conjugation",
                "title": "动词变形填空",
                "system": prompt.SYSTEM_PROMPT,
                "user": prompt.USER_TEMPLATE,
            }
        ]

    def init(self) -> None:
        furigana.ensure_tagger()