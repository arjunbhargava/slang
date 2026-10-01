"""App-owned conversation state for one isolated session.

Only committed learner transcripts enter the history. Context is bounded by
turn count and per-turn length. Provider and model are fixed per session.
"""

from __future__ import annotations

from dataclasses import dataclass

from slang.domain import LearnerLevel, Role, Transcript, Turn
from slang.languages import Language
from slang.models.base import ModelProvider, ModelRequest

DEFAULT_MAX_TURNS = 40
MAX_TURN_CHARS = 2_000


class ConversationStateError(RuntimeError):
    pass


@dataclass(frozen=True)
class SessionSettings:
    target: Language
    level: LearnerLevel
    model_provider: ModelProvider
    model: str


class Conversation:
    def __init__(self, settings: SessionSettings, *, max_turns: int = DEFAULT_MAX_TURNS) -> None:
        if max_turns < 2:
            raise ValueError("max_turns must be at least 2")
        self.settings = settings
        self._max_turns = max_turns
        self._turns: list[Turn] = []

    @property
    def turns(self) -> tuple[Turn, ...]:
        return tuple(self._turns)

    @property
    def awaiting_reply(self) -> bool:
        return bool(self._turns) and self._turns[-1].role is Role.LEARNER

    def commit_learner(self, transcript: Transcript) -> Turn:
        """Add a learner turn. Empty transcripts are rejected; callers skip them."""
        if transcript.is_empty:
            raise ConversationStateError("empty transcript")
        if self.awaiting_reply:
            raise ConversationStateError("previous learner turn has no tutor reply")
        turn = Turn(Role.LEARNER, transcript.text.strip()[:MAX_TURN_CHARS])
        self._turns.append(turn)
        self._trim()
        return turn

    def add_tutor(self, text: str) -> Turn:
        if not self.awaiting_reply:
            raise ConversationStateError("tutor reply without a pending learner turn")
        turn = Turn(Role.TUTOR, text.strip()[:MAX_TURN_CHARS])
        self._turns.append(turn)
        self._trim()
        return turn

    def discard_pending_learner(self) -> None:
        """Roll back an unanswered learner turn, e.g. after a provider error."""
        if self.awaiting_reply:
            self._turns.pop()

    def request(self, system: str, *, max_output_tokens: int = 400) -> ModelRequest:
        if not self.awaiting_reply:
            raise ConversationStateError("no pending learner turn to reply to")
        return ModelRequest(system=system, turns=self.turns, max_output_tokens=max_output_tokens)

    def _trim(self) -> None:
        excess = len(self._turns) - self._max_turns
        if excess > 0:
            del self._turns[:excess]
        while self._turns and self._turns[0].role is not Role.LEARNER:
            del self._turns[0]
