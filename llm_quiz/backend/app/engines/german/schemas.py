"""German grammar vocabulary for the dative/accusative article quiz.

Articles are the four masculine determinations relevant to Dativ/Akkusativ. The
``ArticleForm`` distinguishes whether an article definite or indefinite so we can
label each question's ``type``; the case (Dativ/Akkusativ) is derived from which
of the four forms is the answer.
"""
from __future__ import annotations

from typing import Literal

ArticleForm = Literal["den", "einen", "dem", "einem"]

DefiniteForm = Literal["den", "dem"]
IndefiniteForm = Literal["einen", "einem"]

ACCUSATIVE_FORMS = frozenset({"den", "einen"})
DATIVE_FORMS = frozenset({"dem", "einem"})
DEFINITE_FORMS = frozenset({"den", "dem"})

VALID_FORMS = frozenset({"den", "einen", "dem", "einem"})

Case = Literal["Akkusativ", "Dativ"]
Definiteness = Literal["定冠词", "不定冠词"]

# "verb" fallback when a masculine noun isn't reliably extractable after 【】.
FALLBACK_VERB = "（冠词）"

REQUIRED_ITEMS = 6
CASE_COUNT = 3  # 6 个句子中，第三格与第四格必须各 3 个