from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app
from app.models.chat_session import ChatSession

BASE_URL = "http://test"
SESSIONS_EP = "/api/v1/chat/sessions"
STREAM_EP = "/api/v1/chat/sessions/{session_id}/messages/stream"
STREAM_PATCH = "app.services.chat_stream_service.AsyncOpenAI"


def parse_sse(text: str) -> list[dict]:
    return [
        json.loads(line.strip()[6:])
        for line in text.split("\n")
        if line.strip().startswith("data: ")
    ]


def make_openai_mock(tokens: list[str]) -> AsyncMock:
    async def _gen():
        for t in tokens:
            yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=t))])
        yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=None))])

    client = AsyncMock()
    client.chat.completions.create = AsyncMock(return_value=_gen())
    return client


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "Password123!",
            "name": "테스터",
            "gender": "FEMALE",
            "birth_date": "1990-01-01",
            "phone_number": phone,
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    return resp.json()["access_token"]


class TestChatStreamApis(TestCase):
    async def test_stream_unauthenticated_returns_401(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.post(
                STREAM_EP.format(session_id=1),
                json={"message": "테스트"},
            )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_stream_session_not_found_returns_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "str2@example.com", "01099990002")
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.post(
                STREAM_EP.format(session_id=99999),
                json={"message": "테스트"},
                headers=headers,
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_stream_session_expired_returns_410(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "str1@example.com", "01099990001")
            headers = {"Authorization": f"Bearer {token}"}
            session_resp = await client.post(SESSIONS_EP, headers=headers)
            session_id = session_resp.json()["session_id"]
            # created_at을 31분 전으로 조작 (auto_now_add bypass)
            old_time = datetime.now(tz=UTC) - timedelta(minutes=31)
            await ChatSession.filter(id=session_id).update(created_at=old_time)
            resp = await client.post(
                STREAM_EP.format(session_id=session_id),
                json={"message": "테스트"},
                headers=headers,
            )
        assert resp.status_code == status.HTTP_410_GONE
