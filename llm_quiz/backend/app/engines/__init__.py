"""Language engine registry.

Adding a new language = implement ``LanguageEngine`` in a new package under
``app/engines/`` and register it here (one line).
"""
from __future__ import annotations

from app.engines.base import LanguageEngine
from app.engines.german import GermanLanguageEngine
from app.engines.japanese import JapaneseLanguageEngine

REGISTRY: dict[str, type[LanguageEngine]] = {
    "ja": JapaneseLanguageEngine,
    "de": GermanLanguageEngine,
}

DEFAULT_LANGUAGE: str = "ja"

_INSTANCES: dict[str, LanguageEngine] = {}


class UnknownLanguageError(KeyError):
    pass


def get_engine(code: str) -> LanguageEngine:
    """Return a cached engine instance for ``code`` (raise if unknown)."""
    if code not in REGISTRY:
        raise UnknownLanguageError(code)
    if code not in _INSTANCES:
        _INSTANCES[code] = REGISTRY[code]()
    return _INSTANCES[code]