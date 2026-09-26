# Provider research: current APIs and model IDs

Verified on 2026-09-26 against the live official documentation linked in each
section (fetched directly, not from search snippets). Recheck before shipping;
several providers renamed or re-versioned models during 2026.

"README conflict" rows note where this contradicts or refines `README.md`.

## 1. Soniox real-time STT

Docs: [models](https://soniox.com/docs/stt/models),
[WebSocket API](https://soniox.com/docs/stt/api-reference/websocket-api),
[real-time transcription / audio formats](https://soniox.com/docs/stt/rt/real-time-transcription),
[manual finalization](https://soniox.com/docs/stt/rt/manual-finalization),
[keepalive](https://soniox.com/docs/stt/rt/connection-keepalive),
[language hints](https://soniox.com/docs/stt/concepts/language-hints),
[language restrictions](https://soniox.com/docs/stt/concepts/language-restrictions),
[language identification](https://soniox.com/docs/stt/concepts/language-identification),
[supported languages](https://soniox.com/docs/stt/concepts/supported-languages),
[temporary API keys](https://soniox.com/docs/guides/temporary-api-keys),
[pricing](https://soniox.com/pricing).

| Item | Verified value |
|---|---|
| Real-time model | `stt-rt-v5` (released 2026-06-16, Active). `stt-rt-v4` is now an alias to v5. README is correct. |
| Endpoint | `wss://stt-rt.soniox.com/transcribe-websocket` |
| Auth | `api_key` field inside the first (config) JSON text message, not a header. Accepts a long-lived key or a temporary key. REST calls use `Authorization: Bearer <SONIOX_API_KEY>`. |
| Config message (required) | `api_key`, `model`, `audio_format`. For raw audio also `sample_rate` and `num_channels` (errors if missing). |
| Config message (optional) | `language_hints` (array of ISO codes), `language_hints_strict` (bool), `enable_language_identification` (bool), `enable_endpoint_detection` (bool), `max_endpoint_delay_ms` (500-3000), `endpoint_sensitivity` (-1..1, v5 only), `endpoint_latency_adjustment_level` (0-3, v5 only), `context` (`general`, `text`, `terms`, `translation_terms`), `enable_speaker_diarization`, `translation`, `client_reference_id`. |
| Raw PCM | `"audio_format": "pcm_s16le", "sample_rate": 16000, "num_channels": 1`. Audio sent as binary frames (base64 text frames also accepted). Max 300 min per stream. |
| Language hints | `"language_hints": ["en", "es"]` biases, does not restrict. `language_hints_strict: true` restricts best-effort; docs say it is most robust with one language and multi-language strict mode degrades on accents. For a bilingual learner, use hints without strict. All 9 README pool languages are listed (`es fr de it pt nl hi ja ru`). |
| Final vs non-final | Each token has `is_final`. Non-final tokens may change and are resent every response (replace, do not append). Final tokens are sent once and never change. Response also has `final_audio_proc_ms`, `total_audio_proc_ms`. |
| Manual stop / flush | Send text `{"type": "finalize"}`. All audio so far is finalized and a marker token `{"text": "<fin>", "is_final": true}` is emitted. Docs: send about 200 ms of silence after speech before `finalize`; do not call it more than every few seconds. |
| End stream | Send an empty WebSocket frame. Server returns remaining tokens then `{"tokens": [], ..., "finished": true}` and closes. |
| Keepalive | `{"type": "keepalive"}` at least every 20 s when no audio is sent, or the connection may close. |
| Per-token language | Set `enable_language_identification: true`; each token gets `language`. Labels favour sentence-level coherence: a single embedded foreign word (for example "amigo" in an English sentence) is labelled with the surrounding language. Real-time labels may be revised. |
| Errors | JSON with `error_code`, `error_type` (branch on this), `error_message`, `request_id`, then close. |
| Temporary keys | `POST https://api.soniox.com/v1/auth/temporary-api-key` with `Authorization: Bearer <key>`, body `{"usage_type": "transcribe_websocket", "expires_in_seconds": 60, "single_use": true, "max_session_duration_seconds": N}`. Only needed if the browser connects to Soniox directly. |
| Pricing unit | Tokens. Real-time: $2.00 / 1M input audio tokens, $4.00 / 1M input and output text tokens (~$0.12 per hour). Billed for full stream duration, including idle time on an open stream. |

## 2. AssemblyAI streaming STT

Docs: [model selection](https://www.assemblyai.com/docs/streaming/select-the-speech-model),
[multilingual transcription](https://www.assemblyai.com/docs/streaming/multilingual-transcription),
[Streaming WebSocket API spec](https://www.assemblyai.com/docs/streaming/api-spec/streaming-websocket),
[message sequence](https://www.assemblyai.com/docs/streaming/message-sequence),
[turn detection](https://www.assemblyai.com/docs/streaming/turn-detection),
[temporary tokens](https://www.assemblyai.com/docs/streaming/authenticate-with-a-temporary-token),
[billing](https://www.assemblyai.com/docs/billing-and-pricing),
[models / pricing table](https://www.assemblyai.com/docs/getting-started/models),
[pricing page](https://www.assemblyai.com/pricing).

| Item | Verified value |
|---|---|
| Code-switching model | `universal-3-6-pro` (Universal-3.6 Pro Streaming). This is the default and the only streaming model with native mid-sentence code-switching, 32 languages. README is correct. |
| Other models | `universal-3-5-pro` (previous flagship, same features, 19 languages). `universal-streaming-multilingual` (en/es/de/fr/pt/it only, switches per turn, not mid-sentence). `universal-streaming-english`. |
| Endpoint | `wss://streaming.assemblyai.com/v3/ws` (also `streaming.us.` and `streaming.eu.`). v2 `wss://api.assemblyai.com/v2/realtime/ws` is inactive. |
| Auth | Header `Authorization: <API key>` with no `Bearer` prefix. Browsers use `?token=` from `GET https://streaming.assemblyai.com/v3/token?expires_in_seconds=60` (optional `max_session_duration_seconds`). |
| Query params | `speech_model=universal-3-6-pro`, `sample_rate=16000` (8000-96000), `encoding=pcm_s16le` (default; also `pcm_mulaw`, `opus`, `ogg_opus`, `aac`), `language_codes` (list, for example `["en","es"]`; biases per token, still code-switches), `language_detection=true` (adds `language_code` and `language_confidence` to Turn), `keyterms_prompt`, `agent_context`, `max_turn_silence`, `min_turn_silence`, `vad_threshold`, `include_partial_turns`, `inactivity_timeout` (5-3600 s). |
| Param caveat | Unknown or misspelled query params are silently ignored. Check `Begin.configuration.model` matches the requested model. |
| Audio | Binary frames of raw PCM, about 50 ms each (1600 bytes at 16 kHz mono s16le). |
| Server messages | `Begin` (`id`, `expires_at`, `configuration`), `SpeechStarted` (U3.6 Pro only), `Turn` (`turn_order`, `transcript`, `end_of_turn`, `turn_is_formatted`, `words[]` with `word_is_final`, `utterance`), `SpeakerRevision`, `Heartbeat`, `Termination` (`audio_duration_seconds`, `session_duration_seconds`), `Error`. |
| Client messages | `ForceEndpoint`, `Terminate`, `UpdateConfiguration` (can change `language_codes` mid-session, effective next turn), `KeepAlive` (only needed with `inactivity_timeout`). |
| Manual stop | Send `{"type": "ForceEndpoint"}`: the server immediately emits the final `Turn` (`end_of_turn: true`). Then `{"type": "Terminate"}` and keep reading until `Termination`; closing early discards the last transcript. |
| Turn assembly | Each `Turn` replaces the previous one for the same `turn_order`. A turn is complete when `end_of_turn` and `turn_is_formatted` are both true. U3.6 Pro endpoints on semantic pauses, so one push-to-talk recording can contain several turns; concatenate all completed turns. |
| Formatting | README conflict: `format_turns` applies only to Universal-Streaming models. On U3.6 Pro the final turn is always formatted (punctuation, casing, numbers and entities in written form) and there is no documented switch to disable it. Disfluencies and filler words are kept. Keep `filter_profanity` and `redact_pii` off. Whether the formatting fixes learner grammar is untested. |
| Pricing unit | Per hour of WebSocket session duration (idle time billed). Docs list Universal-3.5 Pro Streaming at $0.45/hr and Universal-Streaming at $0.15/hr. No U3.6 Pro rate is published, and the pricing page still names the model `u3-rt-pro`, so it is out of date. Confirm the price in the dashboard. |

## 3. ElevenLabs TTS

Docs: [models](https://elevenlabs.io/docs/overview/models),
[TTS capability](https://elevenlabs.io/docs/overview/capabilities/text-to-speech),
[stream endpoint](https://elevenlabs.io/docs/api-reference/text-to-speech/stream),
[WebSocket stream-input](https://elevenlabs.io/docs/api-reference/text-to-speech/v-1-text-to-speech-voice-id-stream-input),
[authentication](https://elevenlabs.io/docs/api-reference/authentication),
[API keys](https://elevenlabs.io/docs/overview/administration/workspaces/api-keys),
[help: language and accent](https://elevenlabs.io/docs/help-center/product/core-capabilities/text-to-speech/how-do-i-select-the-language-and-accent),
[help: default voices](https://elevenlabs.io/docs/help-center/product/voices/my-voices/what-are-default-voices).

| Item | Verified value |
|---|---|
| Model ID | `eleven_flash_v2_5` (~75 ms model latency, 40,000 char request limit). `eleven_turbo_v2_5` is superseded. The API default is `eleven_multilingual_v2`, so always send `model_id`. |
| HTTP stream | `POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream?output_format=mp3_44100_128`, JSON body `{"text", "model_id", "language_code"?, "voice_settings"?, "apply_text_normalization"?}`. `output_format` is a query parameter. |
| WebSocket | `wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input?model_id=...&output_format=...`. Docs say HTTP has lower latency when the whole text is available up front, which is the case here (LLM reply complete, or sentence by sentence). |
| Auth | Header `xi-api-key: <key>`. The WebSocket also accepts `authorization` or `single_use_token` query params. |
| `output_format` | `mp3_22050_32`, `mp3_24000_48`, `mp3_44100_32/64/96/128/192` (192 needs Creator+), `pcm_8000`...`pcm_48000` (44.1 kHz needs Pro+), `ulaw_8000`, `alaw_8000`, `opus_48000_*`. Default `mp3_44100_128`. For iOS Safari use MP3. |
| `language_code` | ISO 639-1. "Used to enforce a language for the model and text normalization"; ignored if the model doesn't support it; not supported on `multilingual_v2`. Help center: useful for short or ambiguous text such as numbers. Flash v2.5 text normalization is off by default (turning it on is Enterprise-only). |
| Mixed-language text | No official statement that Flash v2.5 handles intra-request code-switching. The help center says language is auto-detected from the text, advises against mixing languages in one website prompt, and says accent comes from the voice. `language_code` forces one language per request. README conflict (refinement): testing mixed text directly is still the first step, but the documented fallback is to split by language and send one request per segment with its own `language_code`. |
| Languages (32) | en, ja, zh, de, hi, fr, ko, pt, it, es, id, nl, tr, fil, pl, sv, bg, ro, ar, cs, el, fi, hr, ms, sk, da, ta, uk, ru, hu, no, vi. README pool is fully covered. |
| Key scoping | Keys are restricted by default: pick the allowed endpoints (enable only Text to Speech), and optionally set a credit quota and an IP allowlist. User keys can expire; service-account keys don't. Keys leaked to public GitHub repos are auto-disabled. |
| Default voice | README conflict: the Default (premade) voices expire on 2026-12-31 and are only available to accounts created before March 2026. The docs' `JBFqnCBsd6RMkjVDRZzb` (George) and `pNInz6obpgDQGcFmaJgB` (Adam) are Default voices. Pick a Voice Library voice per target language (the help center recommends a voice native to that language and accent) and store its `voice_id` in the curated language list. |

## 4. LLMs

Docs: [Anthropic models overview](https://platform.claude.com/docs/en/about-claude/models/overview),
[Anthropic API overview](https://platform.claude.com/docs/en/api/overview),
[Claude Sonnet 5](https://platform.claude.com/docs/en/models/sonnet-5/overview),
[effort](https://platform.claude.com/docs/en/build-with-claude/effort),
[thinking](https://platform.claude.com/docs/en/build-with-claude/thinking),
[deprecations](https://platform.claude.com/docs/en/about-claude/model-deprecations),
[Claude in Amazon Bedrock](https://platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock),
[Claude on Bedrock (legacy Converse)](https://platform.claude.com/docs/en/build-with-claude/claude-on-amazon-bedrock-legacy),
[OpenAI models](https://developers.openai.com/api/docs/models),
[GPT-6 Sol](https://developers.openai.com/api/docs/models/gpt-6-sol),
[GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna),
[OpenAI migrate to Responses](https://developers.openai.com/api/docs/guides/migrate-to-responses),
[AWS Bedrock API keys](https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys-use.html),
[AWS Claude Sonnet 5 model card](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-anthropic-claude-sonnet-5.html),
[botocore changelog](https://github.com/boto/botocore/blob/develop/CHANGELOG.rst).

### Anthropic (Messages API)

| Item | Verified value |
|---|---|
| Endpoint | `POST https://api.anthropic.com/v1/messages`, header `anthropic-version: 2023-06-01`. |
| Auth | `Authorization: Bearer <ANTHROPIC_API_KEY>` is now primary; `x-api-key` is documented as a still-supported legacy fallback. |
| Fast tutor model | `claude-sonnet-5` ("best combination of speed and intelligence", latency "Fast", $2/$10 per MTok). Adaptive thinking is on by default: for low latency send `thinking: {"type": "disabled"}` or `output_config: {"effort": "low"}`. Non-default `temperature`/`top_p`/`top_k` return 400. |
| Fastest | `claude-haiku-4-5` (`claude-haiku-4-5-20251001`), $1/$5, but retirement is "not sooner than October 15, 2026", so not a good default. |
| Other current | `claude-opus-5-5`, `claude-fable-5-1` (slower, costlier). |

### OpenAI

| Item | Verified value |
|---|---|
| API | Responses API (`POST https://api.openai.com/v1/responses`) is "recommended for all new projects"; Chat Completions "remains supported". |
| Auth | `Authorization: Bearer <OPENAI_API_KEY>` |
| Fast tutor model | `gpt-6-sol` ($2/$10, marked "Fast") or `gpt-6-luna` ($0.10/$0.50, cheapest). Both accept `reasoning.effort` `none|low|medium|high|xhigh|max`, default `medium`. Use `none` or `low` for conversational latency. Flagship `gpt-6-astra` is costlier and slower. |

### Bedrock (Converse)

| Item | Verified value |
|---|---|
| Endpoint | `POST https://bedrock-runtime.{region}.amazonaws.com/model/{modelId}/converse` (boto3 `bedrock-runtime` `converse` / `converse_stream`). |
| Auth | `AWS_BEARER_TOKEN_BEDROCK` env var, or header `Authorization: Bearer <key>`. Bedrock API keys can't be used with `InvokeModelWithBidirectionalStream`, Agents, or Data Automation. |
| Inference profile | `us.anthropic.claude-sonnet-5` (also `eu.`, `au.`, `global.anthropic.claude-sonnet-5`). On `bedrock-runtime` the bare `anthropic.claude-sonnet-5` is not supported on demand; a geo or global profile is required. The AWS docs example uses `us.anthropic.claude-sonnet-4-6`, which also works. |
| Thinking via Converse | Sonnet 5 thinks by default; pass `additionalModelRequestFields={"thinking": {"type": "disabled"}}` for latency. The AWS card documents `thinking.type: disabled`; the Converse passthrough field is the standard Converse mechanism but has not been tested here. |
| boto3 version | Bearer token from env var added in botocore/boto3 **1.39.0**; bearer-auth scoping bug fixed in **1.39.12**. Require `boto3>=1.39.12`. Latest on 2026-09-26: 1.43.103. |
| README conflict (refinement) | Anthropic's docs now label Bedrock `InvokeModel`/`Converse` as the "legacy" integration and document a new Messages-API endpoint (`https://bedrock-mantle.{region}.api.aws/anthropic/v1/messages`). AWS's own Sonnet 5 card still lists Converse on `bedrock-runtime` and recommends `bedrock-runtime` for new apps, so Converse is still valid. The one change: the model ID must be a profile ID, not a bare model ID. |

## 5. Browser (iOS Safari)

Docs: [MDN BCD AudioWorklet](https://github.com/mdn/browser-compat-data/blob/main/api/AudioWorklet.json),
[MDN BCD AudioContext](https://github.com/mdn/browser-compat-data/blob/main/api/AudioContext.json),
[MDN AudioContext()](https://developer.mozilla.org/en-US/docs/Web/API/AudioContext/AudioContext),
[MDN getUserMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia),
[MDN autoplay guide](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Autoplay),
[WebKit iOS media policies](https://webkit.org/blog/6784/new-video-policies-for-ios/),
[WebKit autoplay policy](https://webkit.org/blog/7734/auto-play-policy-changes-for-macos/),
[WebKit MediaStreamAudioSourceNode.cpp](https://github.com/WebKit/WebKit/blob/main/Source/WebCore/Modules/webaudio/MediaStreamAudioSourceNode.cpp),
[WebKit bug 251091](https://bugs.webkit.org/show_bug.cgi?id=251091).

| Item | Finding |
|---|---|
| AudioWorklet | Safari 14.1+ (iOS mirrors desktop Safari, so iOS 14.5+). |
| getUserMedia | Secure context only (HTTPS or `localhost`), or `navigator.mediaDevices` is undefined. Top-level document only unless an iframe is granted the `microphone` Permissions Policy. The user must grant permission. Call it from the tap handler. |
| AudioContext | Unprefixed since Safari 14.1. BCD note: new contexts start suspended until `resume()` is called from a user action such as `click`. |
| `sampleRate: 16000` | The constructor option is supported since Safari 14.1 and throws `NotSupportedError` if the rate is unsupported. WebKit's `MediaStreamAudioSourceNode` resamples the mic to the context rate. Resampling and AudioWorklet-with-getUserMedia bugs (WebKit 219201, 251091) have been fixed, but third-party reports still describe Safari ignoring the requested rate. Treat 16 kHz as a request, not a guarantee: read `audioContext.sampleRate` and downsample to 16 kHz in the worklet if it differs. |
| Playback / autoplay | iOS requires a user gesture (`touchend`/`click`/`keydown` handler, not an async callback) to start audible `<audio>` playback; `play()` returns a promise that rejects with `NotAllowedError`. Permission is granted per element, so create one `<audio>` element (or the shared `AudioContext`), unlock it during the first tap, then reuse it by changing `src` or decoding into the unlocked context. Tutor audio arrives after an async delay, so it can't rely on a fresh gesture. |

## 6. Cloudflare quick tunnels

Docs: [Quick Tunnels (TryCloudflare)](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/),
[Tunnels FAQ](https://developers.cloudflare.com/cloudflare-one/faq/cloudflare-tunnels-faq/),
[cloudflared issue 1652](https://github.com/cloudflare/cloudflared/issues/1652).

| Item | Finding |
|---|---|
| Command | `cloudflared tunnel --url http://localhost:8080` gives a random `*.trycloudflare.com` HTTPS URL (so getUserMedia works on iOS). Doesn't work if `~/.cloudflared/config.yaml` exists. |
| WebSocket | FAQ: "Cloudflare Tunnel has full support for Websockets." Open issue 1652 (2026-05) reports `Upgrade: websocket` sometimes dropped (close code 1006), with `--protocol=http2` as a partial workaround. |
| Limits | Hard limit of 200 in-flight concurrent requests (HTTP 429 beyond that). No Server-Sent Events. |
| Uptime / use | "Intended for testing and development only." No SLA or uptime guarantee; Cloudflare uses free tunnels to test new features. For production, create a named, remotely managed tunnel. |

## Recommendations

- Soniox (first choice): `wss://stt-rt.soniox.com/transcribe-websocket`. Config `{"api_key", "model": "stt-rt-v5", "audio_format": "pcm_s16le", "sample_rate": 16000, "num_channels": 1, "language_hints": ["en", "<target>"], "enable_language_identification": true}`. Leave endpoint detection and strict hints off. On stop: send ~200 ms of zero samples, then `{"type": "finalize"}`, wait for `<fin>`, then send an empty frame and wait for `finished`. Open one stream per turn, since idle time is billed.
- AssemblyAI (comparison): `wss://streaming.assemblyai.com/v3/ws?speech_model=universal-3-6-pro&sample_rate=16000&encoding=pcm_s16le&language_codes=["en","<target>"]&language_detection=true` with header `Authorization: <key>`. On stop: `ForceEndpoint`, collect all completed turns, `Terminate`, read until `Termination`. Final turns are always formatted, so measure whether this hides learner errors.
- ElevenLabs: `POST /v1/text-to-speech/{voice_id}/stream?output_format=mp3_44100_128` (or `mp3_22050_32` on slow links), `model_id: "eleven_flash_v2_5"`, `xi-api-key` from a key restricted to Text to Speech. Omit `language_code` for mixed text first; fall back to per-language segments with `language_code`. Choose a native Voice Library voice per target language, not a Default voice.
- Anthropic: `claude-sonnet-5` with `thinking: {"type": "disabled"}` (or effort `low`), `Authorization: Bearer`.
- OpenAI: Responses API, `gpt-6-sol` (or `gpt-6-luna` for cost) with `reasoning: {"effort": "none"}` or `"low"`.
- Bedrock: Converse on `bedrock-runtime`, `modelId="us.anthropic.claude-sonnet-5"` (or `global.`), `AWS_REGION=us-east-1`, `boto3>=1.39.12`, `AWS_BEARER_TOKEN_BEDROCK`.
- Browser: HTTPS origin; on the first tap create and `resume()` one `AudioContext` and unlock one `<audio>` element; request `sampleRate: 16000` but resample in the AudioWorklet whenever `audioContext.sampleRate !== 16000`.
- Tunnel: fine for phone testing over WebSocket (no SSE, 200 in-flight limit, no SLA). If WebSocket upgrades fail, retry with `--protocol=http2`.
- README cleanups: note the formatting caveat for U3.6 Pro, the Default-voice expiry, the Bedrock profile-ID requirement, and that the first interface is now a mobile web page rather than the terminal harness described in "First version".
