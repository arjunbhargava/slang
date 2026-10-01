import pytest
from fastapi.testclient import TestClient

from slang.config import WebConfig
from slang.web.app import COOKIE_NAME, create_app

TOKEN = "t" * 32


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(WebConfig(access_token=TOKEN)), base_url="https://testserver")


def test_healthz_is_public(client):
    assert client.get("/healthz").json() == {"ok": True}


def test_index_requires_token(client):
    assert client.get("/").status_code == 401
    assert client.get("/", params={"token": "wrong"}).status_code == 401


def test_token_moves_to_cookie_and_leaves_url(client):
    response = client.get("/", params={"token": TOKEN}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie and "Secure" in cookie and "SameSite=strict" in cookie
    assert client.cookies.get(COOKIE_NAME) == TOKEN
    page = client.get("/")
    assert page.status_code == 200
    assert "slang" in page.text
