"""NFR-SEC-004 — Rate Limiting 단위 테스트."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import jwt
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.rate_limit.config import get_tier
from app.core.rate_limit.middleware import RateLimitMiddleware

# ── Tier 분류 ─────────────────────────────────────────────────


def test_tier_chat_sessions_is_llm() -> None:
    assert get_tier("POST", "/api/v1/chat/sessions/1/messages").name == "llm"


def test_tier_guide_generate_is_llm() -> None:
    assert get_tier("POST", "/api/v1/guide/generate").name == "llm"


def test_tier_guide_regenerate_is_llm() -> None:
    assert get_tier("POST", "/api/v1/guide/5/regenerate").name == "llm"


def test_tier_pills_recognize_is_ocr() -> None:
    assert get_tier("POST", "/api/v1/pills/recognize").name == "ocr"


def test_tier_medical_documents_ocr_is_ocr() -> None:
    assert get_tier("POST", "/api/v1/medical-documents/1/ocr-jobs").name == "ocr"


def test_tier_get_method_is_default() -> None:
    assert get_tier("GET", "/api/v1/chat/sessions/1/messages").name == "default"


def test_tier_unknown_path_is_default() -> None:
    assert get_tier("POST", "/api/v1/users/profile").name == "default"


# ── 헬퍼 ──────────────────────────────────────────────────────


def _make_token(user_id: int = 1) -> str:
    return jwt.encode({"user_id": user_id}, "test-secret", algorithm="HS256")


def _make_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)

    @app.get("/api/v1/health")
    async def health():
        return {"ok": True}

    @app.post("/api/v1/chat/sessions/{session_id}/messages")
    async def chat(session_id: int):
        return {"ok": True}

    return app


def _mock_redis(count: int) -> MagicMock:
    pipe = MagicMock()
    pipe.execute = AsyncMock(return_value=[count, True])
    redis_mock = MagicMock()
    redis_mock.pipeline.return_value = pipe
    return redis_mock


# ── 미들웨어 동작 ──────────────────────────────────────────────


async def test_allow_under_limit() -> None:
    app = _make_app()
    with patch("app.core.rate_limit.middleware.get_redis", return_value=_mock_redis(1)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/chat/sessions/1/messages",
                headers={"Authorization": f"Bearer {_make_token()}"},
            )
    assert resp.status_code == 200


async def test_block_over_limit() -> None:
    app = _make_app()
    with patch("app.core.rate_limit.middleware.get_redis", return_value=_mock_redis(31)):  # llm limit=30 초과
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/chat/sessions/1/messages",
                headers={"Authorization": f"Bearer {_make_token()}"},
            )
    assert resp.status_code == 429
    body = resp.json()
    assert body["code"] == "RATE_LIMIT_EXCEEDED"
    assert body["message"] == "요청 횟수가 초과되었습니다."


async def test_allow_unauthenticated() -> None:
    app = _make_app()
    with patch("app.core.rate_limit.middleware.get_redis") as mock_get_redis:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    mock_get_redis.assert_not_called()


async def test_fail_open_on_redis_error() -> None:
    app = _make_app()
    pipe = MagicMock()
    pipe.execute = AsyncMock(side_effect=ConnectionError("redis down"))
    redis_mock = MagicMock()
    redis_mock.pipeline.return_value = pipe
    with patch("app.core.rate_limit.middleware.get_redis", return_value=redis_mock):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/chat/sessions/1/messages",
                headers={"Authorization": f"Bearer {_make_token()}"},
            )
    assert resp.status_code == 200
