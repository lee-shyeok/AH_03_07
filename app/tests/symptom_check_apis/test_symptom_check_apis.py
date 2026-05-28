from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app
from app.models.audit_log import AuditLog

BASE_URL = "http://test"


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    signup_data = {
        "email": email,
        "password": "Password123!",
        "name": "증상테스터",
        "gender": "MALE",
        "birth_date": "1978-11-05",
        "phone_number": phone,
    }
    await client.post("/api/v1/auth/signup", json=signup_data)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    return resp.json()["access_token"]


class TestSymptomCheckApis(TestCase):
    async def test_non_red_flag_symptom_no_trigger(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "symp_safe@example.com", "01066660001")
            resp = await client.post(
                "/api/v1/symptom-checks",
                json={"checked_symptoms": ["FEVER", "MOUTH_SORES"]},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["red_flag_triggered"] is False
        assert resp.json()["red_flag_symptoms"] == []

    async def test_red_flag_symptom_triggers_flag_and_audit_log(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "symp_redflag@example.com", "01066660002")
            before = await AuditLog.filter(action="SYMP_RED_FLAG").count()
            resp = await client.post(
                "/api/v1/symptom-checks",
                json={"checked_symptoms": ["FEVER", "DYSPNEA"]},
                headers={"Authorization": f"Bearer {token}"},
            )
            after = await AuditLog.filter(action="SYMP_RED_FLAG").count()
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["red_flag_triggered"] is True
        assert "DYSPNEA" in resp.json()["red_flag_symptoms"]
        assert after == before + 1

    async def test_multiple_red_flags_all_included(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "symp_multiflag@example.com", "01066660003")
            resp = await client.post(
                "/api/v1/symptom-checks",
                json={"checked_symptoms": ["DYSPNEA", "JAUNDICE", "FEVER"]},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.json()["red_flag_triggered"] is True
        red_flags = set(resp.json()["red_flag_symptoms"])
        assert "DYSPNEA" in red_flags
        assert "JAUNDICE" in red_flags
        assert "FEVER" not in red_flags

    async def test_empty_symptoms_allowed(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "symp_empty@example.com", "01066660004")
            resp = await client.post(
                "/api/v1/symptom-checks",
                json={"checked_symptoms": []},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["red_flag_triggered"] is False
        assert resp.json()["checked_symptoms"] == []

    async def test_list_symptom_checks(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "symp_list@example.com", "01066660005")
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(
                "/api/v1/symptom-checks",
                json={"checked_symptoms": ["FEVER"]},
                headers=headers,
            )
            await client.post(
                "/api/v1/symptom-checks",
                json={"checked_symptoms": ["DYSPNEA"]},
                headers=headers,
            )
            resp = await client.get("/api/v1/symptom-checks", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()) == 2
        assert resp.json()[0]["red_flag_triggered"] is True  # 최신순 — DYSPNEA
        assert resp.json()[1]["red_flag_triggered"] is False  # FEVER

    async def test_list_symptom_checks_unauthorized(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get("/api/v1/symptom-checks")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
