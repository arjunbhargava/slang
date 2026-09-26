#!/usr/bin/env bash
# Serve the web harness on a temporary public HTTPS URL (Cloudflare quick tunnel).
# Prints the tokenized URL and writes it to $SLANG_URL_FILE. Ctrl-C stops both.
set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"
cd "$(dirname "$0")/.."

PORT="${SLANG_PORT:-8000}"
URL_FILE="${SLANG_URL_FILE:-/tmp/slang-url.txt}"
TUNNEL_LOG="$(mktemp -t slang-tunnel.XXXXXX)"
export SLANG_ACCESS_TOKEN="${SLANG_ACCESS_TOKEN:-$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')}"

cleanup() {
  trap - EXIT INT TERM
  kill "${TUNNEL_PID:-}" "${SERVER_PID:-}" 2>/dev/null || true
  rm -f "$URL_FILE" "$TUNNEL_LOG"
}
trap cleanup EXIT INT TERM

# Access logging is off because the first request carries the token in its query string.
uv run uvicorn --factory slang.web.app:create_app_from_env \
  --host 127.0.0.1 --port "$PORT" --no-access-log &
SERVER_PID=$!

for _ in $(seq 50); do
  curl -fsS "http://127.0.0.1:$PORT/healthz" >/dev/null 2>&1 && break
  kill -0 "$SERVER_PID" 2>/dev/null || { echo "server exited" >&2; exit 1; }
  sleep 0.2
done

cloudflared tunnel --no-autoupdate --url "http://127.0.0.1:$PORT" >"$TUNNEL_LOG" 2>&1 &
TUNNEL_PID=$!

PUBLIC_URL=""
for _ in $(seq 60); do
  PUBLIC_URL="$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$TUNNEL_LOG" | head -1 || true)"
  [ -n "$PUBLIC_URL" ] && break
  kill -0 "$TUNNEL_PID" 2>/dev/null || { cat "$TUNNEL_LOG" >&2; exit 1; }
  sleep 0.5
done
[ -n "$PUBLIC_URL" ] || { echo "tunnel URL not found" >&2; cat "$TUNNEL_LOG" >&2; exit 1; }

echo "$PUBLIC_URL/?token=$SLANG_ACCESS_TOKEN" >"$URL_FILE"
chmod 600 "$URL_FILE"
echo "slang is live: $(cat "$URL_FILE")"

wait -n "$SERVER_PID" "$TUNNEL_PID"
