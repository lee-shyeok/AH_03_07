from __future__ import annotations

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app
from app.models.chat_session import ChatSession
from app.models.users import User, UserMode

BASE_URL = "http://test"
ENDPOINT = "/api/v1/chat/sessions"


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "Password123!",
            "name": "챗봇테스터",
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


class TestChatSessionsApis(TestCase):
    async def test_create_session_authenticated_returns_201(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sess1@example.com", "01011110001")
            resp = await client.post(ENDPOINT, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert isinstance(data["session_id"], int)

    async def test_create_session_unauthenticated_returns_401(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.post(ENDPOINT)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_general_mode_user_creates_general_session(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sess2@example.com", "01011110002")
            resp = await client.post(ENDPOINT, headers={"Authorization": f"Bearer {token}"})
        session_id = resp.json()["session_id"]
        session = await ChatSession.get(id=session_id)
        assert session.mode == "GENERAL"

    async def test_autoimmune_mode_user_creates_autoimmune_session(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sess3@example.com", "01011110003")
            await User.filter(email="sess3@example.com").update(mode=UserMode.AUTOIMMUNE)
            resp = await client.post(ENDPOINT, headers={"Authorization": f"Bearer {token}"})
        session_id = resp.json()["session_id"]
        session = await ChatSession.get(id=session_id)
        assert session.mode == "AUTOIMMUNE"
