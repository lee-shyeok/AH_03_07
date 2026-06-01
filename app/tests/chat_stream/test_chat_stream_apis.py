from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

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
    return [json.loads(line.strip()[6:]) for line in text.split("\n") if line.strip().startswith("data: ")]


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

    async def test_stream_blocked_intent_guardrail(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "str3@example.com", "01099990003")
            headers = {"Authorization": f"Bearer {token}"}
            session_resp = await client.post(SESSIONS_EP, headers=headers)
            session_id = session_resp.json()["session_id"]
            resp = await client.post(
                STREAM_EP.format(session_id=session_id),
                json={"message": "진단해줘"},
                headers=headers,
            )
        assert resp.status_code == status.HTTP_200_OK
        events = parse_sse(resp.text)
        assert len(events) == 1
        assert events[0]["type"] == "guardrail"
        assert "category" in events[0]
        assert "message" in events[0]

    async def test_stream_normal_message(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "str5@example.com", "01099990005")
            headers = {"Authorization": f"Bearer {token}"}
            session_resp = await client.post(SESSIONS_EP, headers=headers)
            session_id = session_resp.json()["session_id"]
            with patch(STREAM_PATCH, return_value=make_openai_mock(["루푸스는 ", "자가면역 질환입니다."])):
                resp = await client.post(
                    STREAM_EP.format(session_id=session_id),
                    json={"message": "루푸스가 뭔가요?"},
                    headers=headers,
                )
        assert resp.status_code == status.HTTP_200_OK
        events = parse_sse(resp.text)
        token_events = [e for e in events if e["type"] == "token"]
        done_events = [e for e in events if e["type"] == "done"]
        assert len(token_events) == 2
        assert token_events[0]["content"] == "루푸스는 "
        assert token_events[1]["content"] == "자가면역 질환입니다."
        assert len(done_events) == 1
        assert done_events[0]["message_id"] > 0
        assert "created_at" in done_events[0]

    async def test_stream_emergency_event(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "str4@example.com", "01099990004")
            headers = {"Authorization": f"Bearer {token}"}
            session_resp = await client.post(SESSIONS_EP, headers=headers)
            session_id = session_resp.json()["session_id"]
            resp = await client.post(
                STREAM_EP.format(session_id=session_id),
                json={"message": "지금 죽을 것 같아"},
                headers=headers,
            )
        assert resp.status_code == status.HTTP_200_OK
        events = parse_sse(resp.text)
        assert len(events) == 1
        assert events[0]["type"] == "emergency"
        assert "message" in events[0]

    async def test_stream_safety_filter_event(self):
        # "처방해드릴게요" 포함 → FORBIDDEN_TERMS 매칭 → safety_filter 이벤트
        dangerous_tokens = ["제가 ", "처방해드릴게요."]
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "str6@example.com", "01099990006")
            headers = {"Authorization": f"Bearer {token}"}
            session_resp = await client.post(SESSIONS_EP, headers=headers)
            session_id = session_resp.json()["session_id"]
            with patch(STREAM_PATCH, return_value=make_openai_mock(dangerous_tokens)):
                resp = await client.post(
                    STREAM_EP.format(session_id=session_id),
                    json={"message": "약 정보 알려줘"},
                    headers=headers,
                )
        assert resp.status_code == status.HTTP_200_OK
        events = parse_sse(resp.text)
        event_types = [e["type"] for e in events]
        assert "safety_filter" in event_types
        assert "done" in event_types
        # safety_filter가 done보다 먼저 와야 함
        assert event_types.index("safety_filter") < event_types.index("done")
        sf_event = next(e for e in events if e["type"] == "safety_filter")
        assert "message" in sf_event
