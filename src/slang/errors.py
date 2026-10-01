"""Errors surfaced to the learner. Never fall back to another provider on failure."""

from __future__ import annotations

from enum import StrEnum


class ProviderErrorKind(StrEnum):
    AUTH = "auth"
    QUOTA = "quota"
    RATE_LIMIT = "rate_limit"
    BAD_REQUEST = "bad_request"
    UNAVAILABLE = "unavailable"
    OTHER = "other"


class ConfigError(ValueError):
    """Invalid or incomplete configuration, detected before a session starts."""


class ProviderError(RuntimeError):
    """A model, STT, or TTS provider call failed.

    `message` must be safe to show the learner: no API keys, request bodies,
    or transcript text.
    """

    def __init__(self, provider: str, kind: ProviderErrorKind, message: str) -> None:
        super().__init__(f"{provider}: {kind}: {message}")
        self.provider = provider
        self.kind = kind
        self.message = message
