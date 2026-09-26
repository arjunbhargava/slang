"""Build provider clients from validated config.

Each provider module exposes a `from_config(config)` constructor. Imports are
lazy so that an unused provider's SDK is never loaded.
"""

from __future__ import annotations

from importlib import import_module

from slang.config import ModelConfig, STTConfig, TTSConfig
from slang.models.base import ModelClient
from slang.speech.stt import SpeechToText
from slang.speech.tts import TextToSpeech


def create_model_client(config: ModelConfig) -> ModelClient:
    return import_module(f"slang.models.{config.provider.value}").from_config(config)


def create_stt(config: STTConfig) -> SpeechToText:
    return import_module(f"slang.speech.{config.provider.value}").from_config(config)


def create_tts(config: TTSConfig) -> TextToSpeech:
    return import_module(f"slang.speech.{config.provider.value}").from_config(config)
