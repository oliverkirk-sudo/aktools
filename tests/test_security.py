# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/3/28 13:20
Desc: 请求 token 安全测试
"""
from fastapi.testclient import TestClient

from aktools.config import get_request_security_settings
from aktools.core import api as api_module
from aktools.main import app


class DummyResponse:
    def to_json(self, orient: str = "records", date_format: str = "iso") -> str:
        return '[{"value": 1}]'


def fake_endpoint() -> DummyResponse:
    return DummyResponse()


def create_client(
    monkeypatch: object,
    api_token: str = "",
    trust_proxy_headers: bool = False,
) -> TestClient:
    monkeypatch.setattr(api_module.ak, "test_endpoint", fake_endpoint, raising=False)
    if api_token:
        monkeypatch.setenv("AKTOOLS_API_TOKEN", api_token)
    else:
        monkeypatch.delenv("AKTOOLS_API_TOKEN", raising=False)
    if trust_proxy_headers:
        monkeypatch.setenv("AKTOOLS_TRUST_PROXY_HEADERS", "1")
    else:
        monkeypatch.delenv("AKTOOLS_TRUST_PROXY_HEADERS", raising=False)
    monkeypatch.delenv("AKTOOLS_TOKEN_HEADER", raising=False)
    get_request_security_settings.cache_clear()
    return TestClient(app)


def test_local_request_without_token_is_allowed(monkeypatch: object) -> None:
    client = create_client(monkeypatch=monkeypatch)
    response = client.get("/api/public/test_endpoint")
    assert response.status_code == 200
    assert response.json() == [{"value": 1}]


def test_remote_request_without_token_is_forbidden(monkeypatch: object) -> None:
    client = create_client(monkeypatch=monkeypatch, trust_proxy_headers=True)
    response = client.get(
        "/api/public/test_endpoint",
        headers={"X-Forwarded-For": "8.8.8.8"},
    )
    assert response.status_code == 403
    assert "AKTOOLS_API_TOKEN" in response.json()["detail"]


def test_remote_request_with_custom_header_token_is_allowed(monkeypatch: object) -> None:
    client = create_client(
        monkeypatch=monkeypatch,
        api_token="demo-token",
        trust_proxy_headers=True,
    )
    response = client.get(
        "/api/public/test_endpoint",
        headers={
            "X-Forwarded-For": "8.8.8.8",
            "X-AKTOOLS-TOKEN": "demo-token",
        },
    )
    assert response.status_code == 200
    assert response.json() == [{"value": 1}]


def test_remote_request_with_wrong_token_is_rejected(monkeypatch: object) -> None:
    client = create_client(
        monkeypatch=monkeypatch,
        api_token="demo-token",
        trust_proxy_headers=True,
    )
    response = client.get(
        "/api/public/test_endpoint",
        headers={
            "X-Forwarded-For": "8.8.8.8",
            "X-AKTOOLS-TOKEN": "wrong-token",
        },
    )
    assert response.status_code == 401
    assert "token" in response.json()["detail"]


def test_remote_request_with_query_token_is_allowed(monkeypatch: object) -> None:
    client = create_client(
        monkeypatch=monkeypatch,
        api_token="demo-token",
        trust_proxy_headers=True,
    )
    response = client.get(
        "/api/public/test_endpoint?aktools_token=demo-token",
        headers={"X-Forwarded-For": "8.8.8.8"},
    )
    assert response.status_code == 200
    assert response.json() == [{"value": 1}]
