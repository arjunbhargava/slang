# AGENTS.md

Design and requirements live in `README.md`; read it before changing behavior.

## Commands

- Setup (idempotent; installs `uv`, `cloudflared`, deps): `bash scripts/install.sh`
- Tests (offline, no keys): `uv run pytest`
- Live provider tests (paid, opt-in): `uv run pytest -m live`
- Lint/format: `uv run ruff check . && uv run ruff format --check .`
- Serve on a public HTTPS URL: `scripts/serve.sh` (run inside tmux). It prints
  `https://<random>.trycloudflare.com/?token=<token>` and writes it to
  `/tmp/slang-url.txt`. That tokenized URL is what the user opens on their phone.

## Rules

- Python 3.12, async interfaces. Shared types are in `slang.domain`,
  `slang.models.base`, `slang.speech.stt`, `slang.speech.tts`, `slang.errors`,
  `slang.config`. Change these only with a clear reason stated in the PR; parallel
  branches depend on them.
- Dependencies are pre-declared in `pyproject.toml`. Prefer them over adding new
  ones; if you must add one, keep the `uv.lock` change in its own commit.
- Never log, print, commit, or return in API responses: API keys, the access
  token, raw audio, or transcript text. Map provider failures to
  `ProviderError` with a learner-safe message. Never fall back to another provider.
- Tests must pass without credentials. Tests that call real providers are marked
  `@pytest.mark.live` and skip cleanly when their key is absent.
- Keys arrive as environment variables from Cursor secrets. Variable names are in
  `slang/config.py`.

## Module ownership (parallel agents)

Each workstream owns its files; do not edit another stream's files.

| Stream | Files |
|---|---|
| Tutoring policy + turn orchestration | `src/slang/tutor.py`, `src/slang/session.py` |
| Anthropic mapping | `src/slang/models/anthropic.py` |
| OpenAI mapping | `src/slang/models/openai.py` |
| Bedrock Converse mapping | `src/slang/models/bedrock.py` |
| Soniox STT | `src/slang/speech/soniox.py` |
| AssemblyAI STT | `src/slang/speech/assemblyai.py` |
| ElevenLabs TTS | `src/slang/speech/elevenlabs.py` |
| STT evaluation | `eval/` |
| Web client + WebSocket protocol | `src/slang/web/` |

Tests go in `tests/test_<module>.py` for the files you own. Provider modules
expose `from_config(config)`; `slang.factory` imports them by provider name, so
no registry edits are needed.
