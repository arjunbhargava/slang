"""Streaming speech-to-text interface.

One session per learner turn. The client streams raw PCM while the learner
holds push-to-talk; manual stop calls `finish()`, which flushes the provider
and returns the committed transcript. Partial text is feedback only and never
enters the conversation.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Protocol

from slang.domain import PCM_16K_MONO, AudioFormat, Transcript

PartialCallback = Callable[[str], None]


@dataclass(frozen=True)
class STTOptions:
    language_hints: tuple[str, ...]
    """ISO 639-1 codes, English first, e.g. ("en", "es")."""
    audio_format: AudioFormat = PCM_16K_MONO
    max_duration_s: float = 60.0


class STTSession(Protocol):
    async def send_audio(self, pcm: bytes) -> None: ...

    async def finish(self) -> Transcript:
        """Flush, wait for final text, close the connection."""
        ...

    async def cancel(self) -> None:
        """Discard the turn and close the connection. Idempotent."""
        ...


class SpeechToText(Protocol):
    name: str

    async def open_session(
        self, options: STTOptions, on_partial: PartialCallback | None = None
    ) -> STTSession:
        """Raise `slang.errors.ProviderError` on failure."""
        ...


async def transcribe_pcm(
    stt: SpeechToText,
    chunks: Iterable[bytes],
    options: STTOptions,
    on_partial: PartialCallback | None = None,
) -> Transcript:
    """Run a prerecorded clip through the same streaming path as live audio."""
    session = await stt.open_session(options, on_partial)
    try:
        for chunk in chunks:
            await session.send_audio(chunk)
        return await session.finish()
    except BaseException:
        await session.cancel()
        raise


def split_pcm(pcm: bytes, audio_format: AudioFormat = PCM_16K_MONO, chunk_ms: int = 100):
    """Yield fixed-duration chunks, as the browser client would send them."""
    size = audio_format.bytes_per_second * chunk_ms // 1000
    size -= size % (audio_format.sample_width_bytes * audio_format.channels)
    for start in range(0, len(pcm), size):
        yield pcm[start : start + size]
