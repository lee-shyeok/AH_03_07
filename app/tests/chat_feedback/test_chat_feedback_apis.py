from __future__ import annotations

from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app
from app.models.chat_feedback import ChatFeedback

BASE_URL = "http://test"
SESSIONS_EP = "/api/v1/chat/sessions"
FEEDBACK_EP = "/api/v1/chat/messages/{message_id}/feedback"
RAG_PATCH = "app.services.chat_rag_service.ChatRAGService.generate_response"

_NORMAL_RAG = {
    "answer": "루푸스 관련 정보입니다.",
    "is_general_info": False,
    "sources": [{"title": "EULAR 2022", "url": None, "snippet": "관련 내용"}],
}


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


async def _create_session_and_message(client: AsyncClient, headers: dict) -> int:
    session_resp = await client.post(SESSIONS_EP, headers=headers)
    session_id = session_resp.json()["session_id"]
    with patch(RAG_PATCH, new_callable=AsyncMock, return_value=_NORMAL_RAG):
        msg_resp = await client.post(
            f"{SESSIONS_EP}/{session_id}/messages",
            json={"content": "루푸스가 뭔가요?"},
            headers=headers,
        )
    return msg_resp.json()["message_id"]


class TestChatFeedbackApis(TestCase):
    async def test_feedback_positive(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "fb1@example.com", "01044440001")
            headers = {"Authorization": f"Bearer {token}"}
            message_id = await _create_session_and_message(client, headers)
            resp = await client.post(
                FEEDBACK_EP.format(message_id=message_id),
                json={"score": 1},
                headers=headers,
            )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["message_id"] == message_id
        assert data["score"] == 1
        assert "recorded_at" in data

    async def test_feedback_negative(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "fb2@example.com", "01044440002")
            headers = {"Authorization": f"Bearer {token}"}
            message_id = await _create_session_and_message(client, headers)
            resp = await client.post(
                FEEDBACK_EP.format(message_id=message_id),
                json={"score": -1},
                headers=headers,
            )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["score"] == -1

    async def test_feedback_invalid_score_returns_422(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "fb3@example.com", "01044440003")
            headers = {"Authorization": f"Bearer {token}"}
            message_id = await _create_session_and_message(client, headers)
            resp = await client.post(
                FEEDBACK_EP.format(message_id=message_id),
                json={"score": 5},
                headers=headers,
            )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_feedback_upsert_updates_existing(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "fb4@example.com", "01044440004")
            headers = {"Authorization": f"Bearer {token}"}
            message_id = await _create_session_and_message(client, headers)
            await client.post(
                FEEDBACK_EP.format(message_id=message_id),
                json={"score": 1},
                headers=headers,
            )
            await client.post(
                FEEDBACK_EP.format(message_id=message_id),
                json={"score": -1},
                headers=headers,
            )
        count = await ChatFeedback.filter(message_id=message_id).count()
        latest = await ChatFeedback.get(message_id=message_id)
        assert count == 1
        assert latest.score == -1

    async def test_feedback_other_users_message_returns_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token_a = await _signup_and_login(client, "fb5a@example.com", "01044440005")
            token_b = await _signup_and_login(client, "fb5b@example.com", "01044440006")
            message_id = await _create_session_and_message(client, {"Authorization": f"Bearer {token_a}"})
            resp = await client.post(
                FEEDBACK_EP.format(message_id=message_id),
                json={"score": 1},
                headers={"Authorization": f"Bearer {token_b}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_feedback_unauthenticated_returns_401(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.post(
                FEEDBACK_EP.format(message_id=1),
                json={"score": 1},
            )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
