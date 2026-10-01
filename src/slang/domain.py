"""Provider-independent types shared by every module."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    LEARNER = "learner"
    TUTOR = "tutor"


class LearnerLevel(StrEnum):
    """CEFR levels."""

    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


@dataclass(frozen=True)
class TranscriptSegment:
    """A span of recognized speech.

    `language` is an ISO 639-1 code when the STT provider labels it. It is
    metadata only; `text` is always the original-language wording.
    """

    text: str
    language: str | None = None


@dataclass(frozen=True)
class Transcript:
    """A committed (final) transcript of one learner turn.

    `text` is what the learner said, in the languages they said it, without
    translation or grammar repair. `edited` records that the learner corrected
    a recognition error before sending.
    """

    text: str
    segments: tuple[TranscriptSegment, ...] = ()
    edited: bool = False

    @property
    def is_empty(self) -> bool:
        return not self.text.strip()

    def with_edit(self, text: str) -> Transcript:
        if text == self.text:
            return self
        return Transcript(text=text, segments=(), edited=True)


@dataclass(frozen=True)
class Turn:
    role: Role
    text: str


@dataclass(frozen=True)
class AudioFormat:
    """Raw PCM format. The browser client sends 16 kHz mono s16le."""

    sample_rate_hz: int = 16_000
    channels: int = 1
    sample_width_bytes: int = 2

    @property
    def bytes_per_second(self) -> int:
        return self.sample_rate_hz * self.channels * self.sample_width_bytes


PCM_16K_MONO = AudioFormat()
