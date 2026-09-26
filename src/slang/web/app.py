"""Temporary web harness: push-to-talk page + backend holding provider keys.

Served publicly through a Cloudflare quick tunnel, so every route except
`/healthz` requires the per-run access token. The token arrives once as
`?token=`, is moved into an HttpOnly cookie, and is stripped from the URL.
"""

from __future__ import annotations

import secrets
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse

from slang.config import WebConfig, load_web_config

COOKIE_NAME = "slang_token"
STATIC_DIR = Path(__file__).parent / "static"


def _token_matches(candidate: str | None, expected: str) -> bool:
    return candidate is not None and secrets.compare_digest(candidate, expected)


def is_authorized(connection: Request | WebSocket, config: WebConfig) -> bool:
    return _token_matches(connection.cookies.get(COOKIE_NAME), config.access_token)


def create_app(config: WebConfig) -> FastAPI:
    app = FastAPI(title="slang", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.config = config

    @app.get("/healthz")
    async def healthz() -> JSONResponse:
        return JSONResponse({"ok": True})

    @app.get("/", response_model=None)
    async def index(request: Request, token: str | None = None) -> HTMLResponse | RedirectResponse:
        if token is not None:
            if not _token_matches(token, config.access_token):
                return PlainTextResponse("Unauthorized", status_code=401)
            response = RedirectResponse("/", status_code=303)
            response.set_cookie(
                COOKIE_NAME,
                token,
                httponly=True,
                secure=True,
                samesite="strict",
                max_age=12 * 3600,
            )
            return response
        if not is_authorized(request, config):
            return PlainTextResponse("Unauthorized", status_code=401)
        return HTMLResponse(
            (STATIC_DIR / "index.html").read_text(encoding="utf-8"),
            headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"},
        )

    return app


def create_app_from_env() -> FastAPI:
    return create_app(load_web_config())
