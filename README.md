# slang

A reusable voice-first language-learning tool. Choose a language to practise,
speak naturally, and switch to English whenever you need an explanation or help
finding a word. The tutor follows the switch and helps you return to practice.

Status: design draft. No application or setup commands exist yet.

## Product requirements

- English is always the base language. Users select a target language from a
  curated list, not arbitrary provider language codes.
- Support both switching languages between turns and mixing them within a sentence.
- Transcribe what the learner actually says, in the original languages. Do not
  translate everything into English or silently repair grammatical mistakes.
- Use an application-managed conversational agent to interpret the transcript,
  maintain context, and guide practice at the learner's selected level. Support
  Bedrock, OpenAI, and Anthropic model calls authenticated by API keys.
- Speak short responses in the target language; use English for explanations when
  requested, then return to practice. Avoid correcting every sentence by default.
- Show the transcript and tutor response. Let users correct recognition errors;
  do not mistake transcription uncertainty for a learner error.
- Test the first version with manual push-to-talk and stoppable playback.
  Product UI, hands-free turn detection, and spoken interruptions are deferred.

Cursor cloud agents are an implementation workflow, not part of the runtime
architecture. Their setup and task briefs will be documented separately.

## Runtime design

```text
microphone -> streaming STT -> conversation agent -> multilingual TTS -> speaker
                                      |
                          Bedrock / OpenAI / Anthropic

The interface displays the transcript and conversation.
```

Keep speech recognition, tutoring, and speech synthesis separate. This lets us
select speech models for bilingual quality rather than requiring everything to
run in AWS. Ship one STT provider and one TTS provider initially, not a provider
framework or automatic fallback chain.

Only committed transcripts enter the conversation. Partial transcripts are for
feedback while speaking. Preserve the original text; language labels, when
available, are metadata rather than a required intermediate markup format.

For a browser implementation, provider credentials stay on the backend. Do not
expose model-provider or long-lived speech-provider keys in client bundles, API
responses, logs, or committed files.
Keep sessions isolated, bound recording duration and conversation context, and
avoid retaining raw audio or logging transcripts by default.

### First version: terminal test harness

Use a minimal terminal harness to validate the bilingual conversation loop, not
build a product UI:

- Select the target language, learner level, model provider, and model at startup.
- Press Enter to start recording, then Enter again to stop. Manual stop defines
  the turn boundary; do not rely on automatic silence detection.
- Finalize transcription, print it, and allow accepting, editing, or discarding it
  before sending it to the conversation agent. Skip empty transcripts.
- Print the tutor response and play its synthesized speech. Allow playback to be
  stopped; keep the microphone inactive during playback to avoid feedback.
- Repeat with conversation context intact; provide a clean exit that closes audio
  devices and provider connections.

Text input and prerecorded-audio input should exercise the same conversation
path without requiring a microphone. These are testing entry points, not separate
products. Browser/mobile UI, visual design, VAD, and full-duplex audio are deferred.

### Model providers and conversation ownership

The app owns the tutoring instructions, selected language and level, conversation
history, and turn handling. "Agent" means this application logic making model
calls, not the managed Agents for Amazon Bedrock service.

Support three explicitly selected model providers:

| Provider | Authentication | Configuration |
|---|---|---|
| Bedrock Runtime / Converse | Bedrock API key via `AWS_BEARER_TOKEN_BEDROCK` | Model or inference-profile ID and AWS region |
| OpenAI | OpenAI API key via `OPENAI_API_KEY` | OpenAI model ID |
| Anthropic | Anthropic API key via `ANTHROPIC_API_KEY` | Anthropic model ID |

Proposed app configuration: `SLANG_MODEL_PROVIDER=bedrock|openai|anthropic` and
`SLANG_MODEL` for the selected provider's model ID; Bedrock additionally needs
`AWS_REGION`. These are design settings, not implemented setup instructions.
Only the selected provider's key is required. Validate configuration before
starting a session; do not infer the provider from whichever keys happen to exist.

Use the same application-owned conversation representation and tutoring policy
for all three providers, with small provider-specific request/response mappings.
Provider APIs and model IDs are not assumed interchangeable. Keep the provider
and model fixed for a session; a changed selection takes effect in a new session.
STT/TTS selection is independent of the model provider.

Surface authentication, quota, and provider errors clearly. Do not silently switch
providers on failure, since that changes billing and who receives the transcript.
Test shared conversation behavior and each provider's mapping without credentials;
make live smoke tests opt-in for whichever providers are configured.

[AWS documents Bedrock API key support for Converse](https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys-use.html).
Managed Agents / `InvokeAgent`, agent aliases, and IAM user creation are not part
of this design.

## Speech-to-text research

The relevant distinction is native code-switching versus selecting one language
per recording or turn. A model advertising many languages does not necessarily
preserve two languages within the same sentence.

Capabilities below come from provider documentation, not our own measurements.
Model versions in search snippets were sometimes older than the live docs;
recheck exact model IDs when implementation begins.

| Candidate | Documented capability | Assessment for slang |
|---|---|---|
| Soniox `stt-rt-v5` | Streaming across 60+ languages; mixed-language speech within a sentence; language hints such as `["en", "es"]` | Provisional first choice: broad coverage and an explicit fit for bilingual sessions. Actual learner-speech accuracy is untested. |
| AssemblyAI `universal-3-6-pro` | Current streaming guide lists 32 languages, native mid-sentence switching, and `language_codes` to bias toward an expected pair | Strong comparison candidate. Do not confuse it with the older Universal-Streaming Multilingual model, which switches per turn. |
| Deepgram Flux Multilingual `flux-general-multi` | Native code-switching, language hints, and conversational turn/interrupt awareness across 10 languages | Strong candidate when hands-free turn timing is central. Its language pool is narrower. Nova-3 also supports code-switching via `language=multi`. |
| ElevenLabs Scribe v2 Realtime | 90+ languages; realtime transcription; advertised automatic language switching; optional transcript cleanup | Worth comparing, especially if using ElevenLabs TTS. Verify short intra-sentence switches; leave cleanup/rewriting disabled. |
| Mistral Voxtral Mini 4B Realtime | Open-weight realtime transcription across 13 languages; model card reports sub-500ms delay at a tested operating point | Relevant if self-hosting becomes a requirement. The model card alone does not establish reliable learner code-switching. |

Sources:

- Soniox: [models](https://soniox.com/docs/stt/models),
  [language hints and within-sentence multilingual speech](https://soniox.com/docs/stt/concepts/language-hints).
- AssemblyAI: [streaming multilingual transcription](https://www.assemblyai.com/docs/streaming/multilingual-transcription).
- Deepgram: [code-switching](https://developers.deepgram.com/docs/multilingual-code-switching),
  [Flux languages and hints](https://developers.deepgram.com/docs/flux/language-prompting).
- ElevenLabs: [models](https://elevenlabs.io/docs/overview/models),
  [transcription and cleanup options](https://elevenlabs.io/docs/overview/capabilities/speech-to-text),
  [vendor realtime demonstration](https://www.youtube.com/watch?v=_AZ7ptRuzs8).
- Mistral: [Voxtral realtime model card](https://huggingface.co/mistralai/Voxtral-Mini-4B-Realtime-2602).

There is no verified universal accuracy winner here. For example,
[AssemblyAI publishes code-switching benchmarks](https://www.assemblyai.com/benchmarks),
but those are vendor-run, cover particular language pairs and model versions,
and do not establish performance on hesitant, non-native learner speech.
Do not compare batch accuracy or partial-transcript latency as if they were
end-to-end conversational performance.

### Minimal evaluation before committing to a provider

Compare Soniox and AssemblyAI on the same small set of consented human recordings:
English-only, target-only, between-sentence switches, short switches inside a
sentence, and hesitant learner speech with deliberate grammatical mistakes.
Include silence, pauses, and background noise. Synthetic speech is useful for
plumbing checks, not sufficient for evaluating learner accents.

Record:

- Whether target-language words survive instead of being translated, dropped, or
  replaced by English soundalikes.
- Whether grammatical mistakes and self-corrections remain in the transcript.
- Recognition errors around switch boundaries; use character-level scoring where
  word segmentation makes WER misleading.
- Time from the end of speech to a usable final transcript, premature turn endings,
  and full-loop time to the first audible tutor response.
- Actual billable session usage, not only nominal per-minute rates.

Use a small offline check for transcript assembly and conversation state; run live
provider evaluations explicitly, not on every ordinary test run. No paid
transcription evaluations have been run yet.

## Text-to-speech and language pool

Provisional TTS candidate: ElevenLabs Flash v2.5. Its
[documentation](https://elevenlabs.io/docs/overview/capabilities/text-to-speech)
lists 32 languages and positions it for low-latency synthesis. Language coverage
alone does not verify mixed-language pronunciation or accent quality in a chosen
voice; those require listening tests.

Proposed first target-language pool:

- Spanish, French, German, Italian, Portuguese
- Dutch, Hindi, Japanese, Russian

These are candidates, not a claim of tested support. They fit Deepgram Flux's
published pool as well as the documented ElevenLabs Flash language list, leaving
us a practical comparison option. English remains available within every session.
Broader coverage, including Mandarin and Korean, is possible with other shortlisted
STT models but should not be advertised before end-to-end evaluation.

Expose a language only after confirming STT support for English + that language,
TTS voice/pronunciation quality in both languages, and acceptable tutoring output.
Store this as a small curated list with provider codes and a tested voice/locale;
no dynamic provider-discovery system is needed.

Do not require `<en>` tags or Polly SSML in the tutoring output. First test whether
the chosen multilingual voice handles mixed text directly. If explicit language
segmentation is needed, make that a TTS decision rather than assuming every STT
provider emits matching language spans.

A transcript-only tutor cannot assess pronunciation reliably. Pronunciation
scoring is out of scope without an audio-aware assessment path.

## Before implementation

The first interface is settled: a terminal push-to-talk test harness. Confirm
STT/TTS providers through the small bilingual evaluation above, then define
implementation milestones and Cursor cloud-agent setup separately.
Do not add product UI, deployment infrastructure, permanent cloud-agent
credentials, or a provider framework for this test harness.
