from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app
from app.models.users import User, UserMode

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


class TestChatMessagesApis(TestCase):
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

    async def test_normal_message_returns_answer(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "msg1@example.com", "01022220001")
            headers = {"Authorization": f"Bearer {token}"}
            session_id = await _create_session(client, headers)
            with patch(RAG_PATCH, new_callable=AsyncMock, return_value=_NORMAL_RAG):
                resp = await client.post(
                    f"{SESSIONS_EP}/{session_id}/messages",
                    json={"content": "루푸스가 뭔가요?"},
                    headers=headers,
                )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["content"] == "루푸스 관련 정보입니다."
        assert data["blocked_by_filter"] is False
        assert len(data["rag_sources"]) == 1

    async def test_intent_blocked_returns_refusal(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "msg2@example.com", "01022220002")
            headers = {"Authorization": f"Bearer {token}"}
            session_id = await _create_session(client, headers)
            resp = await client.post(
                f"{SESSIONS_EP}/{session_id}/messages",
                json={"content": "진단해줘"},
                headers=headers,
            )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["blocked_by_filter"] is True
        assert data["block_reason"] == "INTENT_BLOCKED"

    async def test_safety_filter_blocks_dangerous_answer(self):
        dangerous_rag = {**_NORMAL_RAG, "answer": "제가 처방해드릴게요"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "msg3@example.com", "01022220003")
            headers = {"Authorization": f"Bearer {token}"}
            session_id = await _create_session(client, headers)
            with patch(RAG_PATCH, new_callable=AsyncMock, return_value=dangerous_rag):
                resp = await client.post(
                    f"{SESSIONS_EP}/{session_id}/messages",
                    json={"content": "약 정보 알려줘"},
                    headers=headers,
                )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["blocked_by_filter"] is True
        assert data["block_reason"] == "SAFETY_FILTER"

    async def test_autoimmune_no_sources_gets_general_label(self):
        no_source_rag = {"answer": "일반 정보입니다.", "is_general_info": True, "sources": []}
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "msg4@example.com", "01022220004")
            headers = {"Authorization": f"Bearer {token}"}
            await User.filter(email="msg4@example.com").update(mode=UserMode.AUTOIMMUNE)
            session_id = await _create_session(client, headers)
            with patch(RAG_PATCH, new_callable=AsyncMock, return_value=no_source_rag):
                resp = await client.post(
                    f"{SESSIONS_EP}/{session_id}/messages",
                    json={"content": "관절통이 있어요"},
                    headers=headers,
                )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["content"].startswith("[일반 정보]")

    async def test_other_users_session_returns_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token_a = await _signup_and_login(client, "msg5a@example.com", "01022220005")
            token_b = await _signup_and_login(client, "msg5b@example.com", "01022220006")
            session_id = await _create_session(client, {"Authorization": f"Bearer {token_a}"})
            resp = await client.post(
                f"{SESSIONS_EP}/{session_id}/messages",
                json={"content": "안녕하세요"},
                headers={"Authorization": f"Bearer {token_b}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_unauthenticated_returns_401(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.post(
                f"{SESSIONS_EP}/1/messages",
                json={"content": "안녕하세요"},
            )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
