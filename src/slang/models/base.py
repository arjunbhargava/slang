"""Interface between the app-owned conversation and an LLM provider.

Each provider module maps `ModelRequest` to its own API and back. Provider
APIs and model IDs are not interchangeable; keep mappings small and explicit.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from slang.domain import Turn


class ModelProvider(StrEnum):
    BEDROCK = "bedrock"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass(frozen=True)
class ModelRequest:
    system: str
    turns: tuple[Turn, ...]
    """Oldest first. Starts with a learner turn and alternates roles."""
    max_output_tokens: int = 400
    temperature: float | None = None


@dataclass(frozen=True)
class ModelReply:
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class ModelClient(Protocol):
    provider: ModelProvider
    model: str

    async def complete(self, request: ModelRequest) -> ModelReply:
        """Raise `slang.errors.ProviderError` on failure."""
        ...

    async def aclose(self) -> None: ...
