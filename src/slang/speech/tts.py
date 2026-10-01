"""Text-to-speech interface.

Audio is streamed so playback can start early and be stopped: the consumer
stops iterating (or calls `aclose()` on the iterator) and the provider request
is abandoned.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from slang.languages import Language


class TextToSpeech(Protocol):
    name: str
    mime_type: str
    """Container of the yielded bytes, e.g. "audio/mpeg" (plays on iOS Safari)."""

    def synthesize(self, text: str, *, language: Language) -> AsyncIterator[bytes]:
        """`text` may mix English and `language`. Raise `ProviderError` on failure."""
        ...
