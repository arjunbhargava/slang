from slang.domain import PCM_16K_MONO
from slang.fakes import FakeSpeechToText, FakeTextToSpeech
from slang.languages import target_language
from slang.speech.stt import STTOptions, split_pcm, transcribe_pcm


def test_split_pcm_uses_whole_samples():
    pcm = bytes(PCM_16K_MONO.bytes_per_second)
    chunks = list(split_pcm(pcm, chunk_ms=30))
    assert all(len(chunk) % 2 == 0 for chunk in chunks)
    assert b"".join(chunks) == pcm


async def test_prerecorded_clip_uses_streaming_path():
    stt = FakeSpeechToText(["quiero un café, please"])
    partials: list[str] = []
    pcm = bytes(PCM_16K_MONO.bytes_per_second)
    transcript = await transcribe_pcm(
        stt, split_pcm(pcm), STTOptions(language_hints=("en", "es")), partials.append
    )
    assert transcript.text == "quiero un café, please"
    assert stt.sessions[0].audio == pcm
    assert stt.sessions[0].closed
    assert partials


async def test_tts_playback_can_stop_early():
    tts = FakeTextToSpeech(chunk_count=10)
    stream = tts.synthesize("hola", language=target_language("es", allow_unverified=True))
    received = [await anext(stream)]
    await stream.aclose()
    assert len(received) == 1
