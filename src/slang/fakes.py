"""In-memory providers for tests and for running the app without API keys."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterable

from slang.domain import Transcript
from slang.languages import Language
from slang.models.base import ModelProvider, ModelReply, ModelRequest
from slang.speech.stt import PartialCallback, STTOptions


class FakeModelClient:
    provider = ModelProvider.ANTHROPIC
    model = "fake"

    def __init__(self, replies: Iterable[str] = ()) -> None:
        self._replies = list(replies)
        self.requests: list[ModelRequest] = []

    async def complete(self, request: ModelRequest) -> ModelReply:
        self.requests.append(request)
        if self._replies:
            return ModelReply(text=self._replies.pop(0))
        return ModelReply(text=f"(fake tutor) {request.turns[-1].text}")

    async def aclose(self) -> None:
        pass


class FakeSTTSession:
    def __init__(self, transcript: Transcript, on_partial: PartialCallback | None) -> None:
        self._transcript = transcript
        self._on_partial = on_partial
        self.audio = bytearray()
        self.closed = False

    async def send_audio(self, pcm: bytes) -> None:
        if self.closed:
            raise RuntimeError("session closed")
        self.audio.extend(pcm)
        if self._on_partial:
            self._on_partial(self._transcript.text[: len(self.audio) // 3200])

    async def finish(self) -> Transcript:
        self.closed = True
        return self._transcript

    async def cancel(self) -> None:
        self.closed = True


class FakeSpeechToText:
    name = "fake"

    def __init__(self, transcripts: Iterable[str] = ()) -> None:
        self._transcripts = list(transcripts)
        self.sessions: list[FakeSTTSession] = []
        self.options: list[STTOptions] = []

    async def open_session(
        self, options: STTOptions, on_partial: PartialCallback | None = None
    ) -> FakeSTTSession:
        text = self._transcripts.pop(0) if self._transcripts else ""
        session = FakeSTTSession(Transcript(text=text), on_partial)
        self.options.append(options)
        self.sessions.append(session)
        return session


class FakeTextToSpeech:
    name = "fake"
    mime_type = "audio/mpeg"

    def __init__(self, chunk_count: int = 3) -> None:
        self._chunk_count = chunk_count
        self.requests: list[tuple[str, str]] = []

    async def synthesize(self, text: str, *, language: Language) -> AsyncIterator[bytes]:
        self.requests.append((text, language.code))
        for index in range(self._chunk_count):
            yield bytes([index]) * 16
