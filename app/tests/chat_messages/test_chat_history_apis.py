from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

BASE_URL = "http://test"
SESSIONS_EP = "/api/v1/chat/sessions"
RAG_PATCH = "app.services.chat_rag_service.ChatRAGService.generate_response"
MODERATION_PATCH = "app.services.chat_guardrail_enhanced.AsyncOpenAI"


def _make_moderation_mock() -> AsyncMock:
    """Moderation API 응답 Mock — flagged=False (통과)."""
    client = AsyncMock()
    client.moderations.create = AsyncMock(
        return_value=SimpleNamespace(results=[SimpleNamespace(flagged=False, categories=SimpleNamespace())])
    )
    return client


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


async def _create_session(client: AsyncClient, headers: dict) -> int:
    resp = await client.post(SESSIONS_EP, headers=headers)
    return resp.json()["session_id"]


async def _send_message(
    client: AsyncClient,
    session_id: int,
    content: str,
    headers: dict,
    mock_rag: dict | None = None,
) -> None:
    if mock_rag:
        with patch(RAG_PATCH, new_callable=AsyncMock, return_value=mock_rag):
            await client.post(
                f"{SESSIONS_EP}/{session_id}/messages",
                json={"content": content},
                headers=headers,
            )
    else:
        await client.post(
            f"{SESSIONS_EP}/{session_id}/messages",
            json={"content": content},
            headers=headers,
        )


class TestChatHistoryApis(TestCase):
    def setUp(self) -> None:
        super().setUp()
        try:
            self._mod_patcher = patch(MODERATION_PATCH, return_value=_make_moderation_mock())
            self._mod_patcher.start()
        except (ModuleNotFoundError, AttributeError):
            self._mod_patcher = None

    def tearDown(self) -> None:
        if self._mod_patcher:
            self._mod_patcher.stop()
        super().tearDown()

    async def test_list_messages_returns_chronological(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "hist1@example.com", "01033330001")
            headers = {"Authorization": f"Bearer {token}"}
            session_id = await _create_session(client, headers)
            await _send_message(client, session_id, "첫 번째 질문", headers, _NORMAL_RAG)
            await _send_message(client, session_id, "두 번째 질문", headers, _NORMAL_RAG)
            resp = await client.get(f"{SESSIONS_EP}/{session_id}/messages", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["total"] == 4  # USER + ASSISTANT 각 2개
        assert len(data["messages"]) == 4
        assert data["messages"][0]["role"] == "user"  # field_serializer → 소문자 직렬화
        assert data["messages"][0]["content"] == "첫 번째 질문"

    async def test_list_messages_empty_session(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "hist2@example.com", "01033330002")
            headers = {"Authorization": f"Bearer {token}"}
            session_id = await _create_session(client, headers)
            resp = await client.get(f"{SESSIONS_EP}/{session_id}/messages", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["messages"] == []
        assert data["total"] == 0

    async def test_list_messages_includes_blocked(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "hist3@example.com", "01033330003")
            headers = {"Authorization": f"Bearer {token}"}
            session_id = await _create_session(client, headers)
            await _send_message(client, session_id, "진단해줘", headers)
            resp = await client.get(f"{SESSIONS_EP}/{session_id}/messages", headers=headers)
        data = resp.json()
        blocked = [m for m in data["messages"] if m["blocked_by_filter"] is True]
        assert len(blocked) >= 1

    async def test_list_messages_pagination(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "hist4@example.com", "01033330004")
            headers = {"Authorization": f"Bearer {token}"}
            session_id = await _create_session(client, headers)
            await _send_message(client, session_id, "질문1", headers, _NORMAL_RAG)
            await _send_message(client, session_id, "질문2", headers, _NORMAL_RAG)
            resp = await client.get(f"{SESSIONS_EP}/{session_id}/messages?page=1&size=1", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data["messages"]) == 1
        assert data["total"] == 4  # USER + ASSISTANT 각 2개
        assert data["size"] == 1

    async def test_list_other_users_session_returns_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token_a = await _signup_and_login(client, "hist5a@example.com", "01033330005")
            token_b = await _signup_and_login(client, "hist5b@example.com", "01033330006")
            session_id = await _create_session(client, {"Authorization": f"Bearer {token_a}"})
            resp = await client.get(
                f"{SESSIONS_EP}/{session_id}/messages",
                headers={"Authorization": f"Bearer {token_b}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_list_unauthenticated_returns_401(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get(f"{SESSIONS_EP}/1/messages")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
