from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app
from app.models.audit_log import AuditLog

BASE_URL = "http://test"

SIGNUP_DATA = {
    "email": "modeuser@example.com",
    "password": "Password123!",
    "name": "모드테스터",
    "gender": "FEMALE",
    "birth_date": "1990-01-01",
    "phone_number": "01011112222",
}


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    data = {**SIGNUP_DATA, "email": email, "phone_number": phone}
    await client.post("/api/v1/auth/signup", json=data)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    return resp.json()["access_token"]


class TestModeApis(TestCase):
    async def test_get_mode_returns_general_by_default(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "mode_get@example.com", "01011110001")
            resp = await client.get("/api/v1/users/me/mode", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["mode"] == "GENERAL"

    async def test_update_mode_general_to_autoimmune_creates_audit_log(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "mode_switch@example.com", "01011110002")
            resp = await client.patch(
                "/api/v1/users/me/mode",
                json={"mode": "AUTOIMMUNE"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["mode"] == "AUTOIMMUNE"
        log_count = await AuditLog.filter(action="MODE_SWITCH").count()
        assert log_count >= 1

    async def test_update_mode_same_value_no_audit_log(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "mode_noop@example.com", "01011110003")
            before = await AuditLog.filter(action="MODE_SWITCH").count()
            await client.patch(
                "/api/v1/users/me/mode",
                json={"mode": "GENERAL"},
                headers={"Authorization": f"Bearer {token}"},
            )
            after = await AuditLog.filter(action="MODE_SWITCH").count()
        assert before == after

    async def test_get_mode_unauthorized(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get("/api/v1/users/me/mode")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
