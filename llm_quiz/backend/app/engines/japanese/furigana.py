"""Kanji -> hiragana furigana annotation via fugashi + unidic.

All deterministic logic that used to live in the LLM prompt lives here, so the
model only has to produce raw JSON (see `app.engines.japanese.prompt`).
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fugashi import Tagger

_KANJI_RE = re.compile(r"[㐀-䶿一-鿿豈-﫿]")
_RUN_RE = re.compile(
    r"[㐀-䶿一-鿿豈-﫿]+|[^㐀-䶿一-鿿豈-﫿]+"
)
MARKER_RE = re.compile(r"【(.*?)】")

_KATAKANA = (
    "ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾ"
    "タダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポ"
    "マミムメモャヤュユョヨラリルレロヮワヲンーヴヵヶ"
)
_HIRAGANA = (
    "ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞ"
    "ただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽ"
    "まみむめもゃやゅゆょよらりるれろゎわをんーゔゕゖ"
)
assert len(_KATAKANA) == len(_HIRAGANA), "katakana/hiragana table mismatch"
_K2H = str.maketrans(_KATAKANA, _HIRAGANA)


class ContractError(ValueError):
    """The LLM output violates the JSON contract (e.g. missing 【】 marker)."""


_tagger: Tagger | None = None


def ensure_tagger() -> Tagger:
    """Lazily create the fugashi tagger (requires unidic-lite or unidic)."""
    global _tagger
    if _tagger is None:
        try:
            from fugashi import Tagger

            _tagger = Tagger()
        except Exception as exc:
            raise RuntimeError(
                "fugashi/unidic 不可用。请先执行: pip install fugashi unidic-lite"
            ) from exc
    return _tagger


def katakana_to_hiragana(text: str) -> str:
    return text.translate(_K2H)


_LONG_VOWEL = {
    "あ": "あ", "か": "あ", "が": "あ", "さ": "あ", "ざ": "あ", "た": "あ", "だ": "あ",
    "な": "あ", "は": "あ", "ば": "あ", "ぱ": "あ", "ま": "あ", "や": "あ", "ら": "あ", "わ": "あ",
    "い": "い", "き": "い", "ぎ": "い", "し": "い", "じ": "い", "ち": "い", "ぢ": "い", "に": "い",
    "ひ": "い", "び": "い", "ぴ": "い", "み": "い", "り": "い",
    "う": "う", "く": "う", "ぐ": "う", "す": "う", "ず": "う", "つ": "う", "づ": "う", "ぬ": "う",
    "ふ": "う", "ぶ": "う", "ぷ": "う", "む": "う", "ゆ": "う", "る": "う",
    "え": "い", "け": "い", "げ": "い", "せ": "い", "ぜ": "い", "て": "い", "で": "い", "ね": "い",
    "へ": "い", "べ": "い", "ぺ": "い", "め": "い", "れ": "い",
    "お": "う", "こ": "う", "ご": "う", "そ": "う", "ぞ": "う", "と": "う", "ど": "う", "の": "う",
    "ほ": "う", "ぼ": "う", "ぽ": "う", "も": "う", "よ": "う", "ろ": "う",
}


def expand_long_vowel(text: str) -> str:
    """Turn pronunciation-style long vowels into dictionary readings.

    unidic-lite only exposes pronunciation, so 学校 -> がっこー; expand to がっこう.
    """
    out: list[str] = []
    for ch in text:
        if ch == "ー" and out:
            out.append(_LONG_VOWEL.get(out[-1], "ー"))
        else:
            out.append(ch)
    return "".join(out)


def _token_reading(word: object) -> str:
    feat = getattr(word, "feature", None)
    if feat is None:
        return ""
    for attr in ("read", "pron", "lemma"):
        value = getattr(feat, attr, None)
        if value:
            return value
    return getattr(word, "surface", "")


def _annotate_token(surface: str, reading: str) -> str:
    """Annotate a single token; handles verb okurigana (遊んで -> 遊ん(あそん)で)."""
    if not _KANJI_RE.search(surface):
        return surface
    reading = expand_long_vowel(katakana_to_hiragana(reading))
    if not reading:
        return surface

    runs = [m.group(0) for m in _RUN_RE.finditer(surface)]
    kanji_runs = [r for r in runs if _KANJI_RE.search(r)]
    if len(kanji_runs) == 1:
        kanji = kanji_runs[0]
        idx = runs.index(kanji)
        leading = "".join(runs[:idx])
        trailing = "".join(runs[idx + 1 :])
        if not leading and trailing:
            trailing_h = katakana_to_hiragana(trailing)
            if reading.endswith(trailing_h) and len(reading) > len(trailing_h):
                return f"{kanji}({reading[: -len(trailing_h)]}){trailing}"
        if trailing and leading:
            return f"{surface}({reading})"
    return f"{surface}({reading})"


def annotate(text: str) -> str:
    """Add hiragana readings to all kanji in `text`. E.g. 遊んで -> 遊ん(あそん)で."""
    tagger = ensure_tagger()
    return "".join(_annotate_token(w.surface, _token_reading(w)) for w in tagger(text))


def split_marked(text: str) -> str | None:
    """Return the text wrapped in 【】, or None if absent."""
    m = MARKER_RE.search(text)
    return m.group(1) if m else None


def process_sentence(sentence: str) -> tuple[str, str, str]:
    """Split a sentence containing 【...】 into its pieces.

    Returns ``(marked, sentence_furigana, sentence_quiz)``:
      - marked: the target conjugation wrapped in 【】 (used to check rightAnswer)
      - sentence_furigana: whole annotated sentence (markers removed)
      - sentence_quiz: annotated sentence with 【...】 replaced by ``_____``
    """
    marked = split_marked(sentence)
    if marked is None:
        raise ContractError("例句未用【】标出目标变形")
    clean = sentence.replace(f"【{marked}】", marked)
    quiz = sentence.replace(f"【{marked}】", "_____")
    return marked, annotate(clean), annotate(quiz)