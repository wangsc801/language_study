"""Japanese-specific grammar vocabulary used by validation rules.

These literals are Japanese-domain concepts (verb classes, onbin types); they
are intentionally NOT part of the generic schema so other languages can impose
their own taxonomies.
"""
from __future__ import annotations

from typing import Literal

Category = Literal["一段动词", "五段动词", "カ変动词", "サ変动词"]
FormType = Literal["て形", "た形", "ます形"]

VALID_CATEGORIES = {"一段动词", "五段动词", "カ変动词", "サ変动词"}
VALID_TYPES = set(FormType.__args__)