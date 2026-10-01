"""Curated target-language list.

A language is exposed to learners only after end-to-end evaluation: STT on
English + that language, TTS voice quality in both, and tutoring output.
Provider-specific codes and voices are added here once tested.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Language:
    code: str
    """ISO 639-1."""
    name: str
    native_name: str
    verified: bool = False
    tts_voice_id: str | None = None


ENGLISH = Language(code="en", name="English", native_name="English", verified=True)

CANDIDATES: tuple[Language, ...] = (
    Language("es", "Spanish", "Español"),
    Language("fr", "French", "Français"),
    Language("de", "German", "Deutsch"),
    Language("it", "Italian", "Italiano"),
    Language("pt", "Portuguese", "Português"),
    Language("nl", "Dutch", "Nederlands"),
    Language("hi", "Hindi", "हिन्दी"),
    Language("ja", "Japanese", "日本語"),
    Language("ru", "Russian", "Русский"),
)

_BY_CODE = {language.code: language for language in CANDIDATES}


class UnknownLanguageError(ValueError):
    pass


def target_language(code: str, *, allow_unverified: bool = False) -> Language:
    """Look up a curated target language by ISO 639-1 code."""
    language = _BY_CODE.get(code)
    if language is None:
        raise UnknownLanguageError(f"{code!r} is not in the curated language list")
    if not language.verified and not allow_unverified:
        raise UnknownLanguageError(f"{language.name} has not passed end-to-end evaluation")
    return language


def available_targets(*, include_unverified: bool = False) -> tuple[Language, ...]:
    return tuple(lang for lang in CANDIDATES if lang.verified or include_unverified)
