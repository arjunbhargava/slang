"""Configuration from environment variables, validated before a session starts.

The provider is always selected explicitly; it is never inferred from which
keys happen to be present. Only the selected provider's key is required.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from slang.errors import ConfigError
from slang.models.base import ModelProvider

MODEL_KEY_VARS: dict[ModelProvider, str] = {
    ModelProvider.BEDROCK: "AWS_BEARER_TOKEN_BEDROCK",
    ModelProvider.OPENAI: "OPENAI_API_KEY",
    ModelProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
}


class STTProvider(StrEnum):
    SONIOX = "soniox"
    ASSEMBLYAI = "assemblyai"


STT_KEY_VARS: dict[STTProvider, str] = {
    STTProvider.SONIOX: "SONIOX_API_KEY",
    STTProvider.ASSEMBLYAI: "ASSEMBLYAI_API_KEY",
}


class TTSProvider(StrEnum):
    ELEVENLABS = "elevenlabs"


TTS_KEY_VARS: dict[TTSProvider, str] = {
    TTSProvider.ELEVENLABS: "ELEVENLABS_API_KEY",
}

MIN_ACCESS_TOKEN_LENGTH = 16


@dataclass(frozen=True)
class ModelConfig:
    provider: ModelProvider
    model: str
    api_key: str = field(repr=False)
    aws_region: str | None = None


@dataclass(frozen=True)
class STTConfig:
    provider: STTProvider
    api_key: str = field(repr=False)


@dataclass(frozen=True)
class TTSConfig:
    provider: TTSProvider
    api_key: str = field(repr=False)


@dataclass(frozen=True)
class WebConfig:
    access_token: str = field(repr=False)


def _get(env: Mapping[str, str], name: str) -> str | None:
    value = env.get(name, "").strip()
    return value or None


def _require(env: Mapping[str, str], name: str, why: str) -> str:
    value = _get(env, name)
    if value is None:
        raise ConfigError(f"{name} is required {why}")
    return value


def _choice[E: StrEnum](env: Mapping[str, str], name: str, enum: type[E]) -> E:
    raw = _require(env, name, "to select a provider")
    try:
        return enum(raw.lower())
    except ValueError:
        options = "|".join(member.value for member in enum)
        raise ConfigError(f"{name} must be one of {options}, got {raw!r}") from None


def load_model_config(env: Mapping[str, str] | None = None) -> ModelConfig:
    env = os.environ if env is None else env
    provider = _choice(env, "SLANG_MODEL_PROVIDER", ModelProvider)
    model = _require(env, "SLANG_MODEL", f"for provider {provider}")
    key_var = MODEL_KEY_VARS[provider]
    api_key = _require(env, key_var, f"for provider {provider}")
    region = None
    if provider is ModelProvider.BEDROCK:
        region = _require(env, "AWS_REGION", "for provider bedrock")
    return ModelConfig(provider=provider, model=model, api_key=api_key, aws_region=region)


def load_stt_config(env: Mapping[str, str] | None = None) -> STTConfig:
    env = os.environ if env is None else env
    provider = _choice(env, "SLANG_STT_PROVIDER", STTProvider)
    api_key = _require(env, STT_KEY_VARS[provider], f"for STT provider {provider}")
    return STTConfig(provider=provider, api_key=api_key)


def load_tts_config(env: Mapping[str, str] | None = None) -> TTSConfig:
    env = os.environ if env is None else env
    raw = _get(env, "SLANG_TTS_PROVIDER") or TTSProvider.ELEVENLABS.value
    try:
        provider = TTSProvider(raw.lower())
    except ValueError:
        raise ConfigError(f"SLANG_TTS_PROVIDER must be elevenlabs, got {raw!r}") from None
    api_key = _require(env, TTS_KEY_VARS[provider], f"for TTS provider {provider}")
    return TTSConfig(provider=provider, api_key=api_key)


def load_web_config(env: Mapping[str, str] | None = None) -> WebConfig:
    env = os.environ if env is None else env
    token = _require(env, "SLANG_ACCESS_TOKEN", "to serve the web app")
    if len(token) < MIN_ACCESS_TOKEN_LENGTH:
        raise ConfigError(f"SLANG_ACCESS_TOKEN must be at least {MIN_ACCESS_TOKEN_LENGTH} chars")
    return WebConfig(access_token=token)
