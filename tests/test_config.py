import pytest

from slang.config import (
    STTProvider,
    load_model_config,
    load_stt_config,
    load_tts_config,
    load_web_config,
)
from slang.errors import ConfigError
from slang.models.base import ModelProvider


def test_anthropic_requires_only_its_key():
    config = load_model_config(
        {"SLANG_MODEL_PROVIDER": "anthropic", "SLANG_MODEL": "m", "ANTHROPIC_API_KEY": "k"}
    )
    assert config.provider is ModelProvider.ANTHROPIC
    assert config.aws_region is None
    assert "k" not in repr(config)


def test_provider_is_never_inferred_from_keys():
    with pytest.raises(ConfigError, match="SLANG_MODEL_PROVIDER"):
        load_model_config({"OPENAI_API_KEY": "k", "SLANG_MODEL": "m"})


def test_selected_provider_key_is_required_even_if_others_exist():
    with pytest.raises(ConfigError, match="OPENAI_API_KEY"):
        load_model_config(
            {"SLANG_MODEL_PROVIDER": "openai", "SLANG_MODEL": "m", "ANTHROPIC_API_KEY": "k"}
        )


def test_bedrock_requires_region():
    env = {"SLANG_MODEL_PROVIDER": "bedrock", "SLANG_MODEL": "m", "AWS_BEARER_TOKEN_BEDROCK": "k"}
    with pytest.raises(ConfigError, match="AWS_REGION"):
        load_model_config(env)
    assert load_model_config({**env, "AWS_REGION": "us-east-1"}).aws_region == "us-east-1"


def test_unknown_provider_lists_options():
    with pytest.raises(ConfigError, match="bedrock\\|openai\\|anthropic"):
        load_model_config({"SLANG_MODEL_PROVIDER": "gemini", "SLANG_MODEL": "m"})


def test_stt_and_tts():
    stt = load_stt_config({"SLANG_STT_PROVIDER": "soniox", "SONIOX_API_KEY": "k"})
    assert stt.provider is STTProvider.SONIOX
    with pytest.raises(ConfigError, match="ASSEMBLYAI_API_KEY"):
        load_stt_config({"SLANG_STT_PROVIDER": "assemblyai", "SONIOX_API_KEY": "k"})
    assert load_tts_config({"ELEVENLABS_API_KEY": "k"}).provider.value == "elevenlabs"


def test_web_token_length():
    with pytest.raises(ConfigError):
        load_web_config({"SLANG_ACCESS_TOKEN": "short"})
    assert load_web_config({"SLANG_ACCESS_TOKEN": "x" * 16}).access_token == "x" * 16
