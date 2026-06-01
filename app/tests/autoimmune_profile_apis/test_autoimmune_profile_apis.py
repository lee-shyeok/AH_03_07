from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

BASE_URL = "http://test"
PROFILE_URL = "/api/v1/autoimmune/profile"


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    signup_data = {
        "email": email,
        "password": "Password123!",
        "name": "자가면역테스터",
        "gender": "FEMALE",
        "birth_date": "1990-05-15",
        "phone_number": phone,
    }
    await client.post("/api/v1/auth/signup", json=signup_data)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    return resp.json()["access_token"]


class TestAutoimmuneProfileApis(TestCase):
    async def test_get_returns_defaults_when_no_profile(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "ai_get_default@example.com", "01066660010")
            resp = await client.get(PROFILE_URL, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["risk_factors"] == {}
        assert body["pregnancy_status"] == "none"
        assert body["vaccination_history"] == []

    async def test_put_then_get_reflects_update(self):
        payload = {
            "risk_factors": {
                "age": 35,
                "organ_function": "normal",
                "infection_history": ["TB 2020"],
                "drug_allergies": ["penicillin"],
                "comorbidities": ["hypertension"],
            },
            "pregnancy_status": "none",
            "vaccination_history": [{"vaccine": "flu", "date": "2025-10-01"}],
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "ai_put_get@example.com", "01066660011")
            headers = {"Authorization": f"Bearer {token}"}
            put_resp = await client.put(PROFILE_URL, json=payload, headers=headers)
            assert put_resp.status_code == status.HTTP_200_OK

            get_resp = await client.get(PROFILE_URL, headers=headers)
        assert get_resp.status_code == status.HTTP_200_OK
        body = get_resp.json()
        assert body["risk_factors"]["age"] == 35
        assert body["risk_factors"]["infection_history"] == ["TB 2020"]
        assert body["vaccination_history"][0]["vaccine"] == "flu"

    async def test_put_pregnant_includes_advisory(self):
        payload = {
            "risk_factors": {},
            "pregnancy_status": "pregnant",
            "vaccination_history": [],
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "ai_pregnant@example.com", "01066660012")
            resp = await client.put(PROFILE_URL, json=payload, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["pregnancy_status"] == "pregnant"
        assert body["advisory_message"] == "담당 류마티스내과 및 산부인과 상담이 필요합니다."

    async def test_put_planning_includes_advisory(self):
        payload = {
            "risk_factors": {},
            "pregnancy_status": "planning",
            "vaccination_history": [],
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "ai_planning@example.com", "01066660013")
            resp = await client.put(PROFILE_URL, json=payload, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["advisory_message"] == "담당 류마티스내과 및 산부인과 상담이 필요합니다."

    async def test_put_none_status_no_advisory(self):
        payload = {
            "risk_factors": {},
            "pregnancy_status": "none",
            "vaccination_history": [],
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "ai_none_status@example.com", "01066660014")
            resp = await client.put(PROFILE_URL, json=payload, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["advisory_message"] is None

    async def test_unauthenticated_get_returns_401(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get(PROFILE_URL)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_unauthenticated_put_returns_401(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.put(
                PROFILE_URL, json={"risk_factors": {}, "pregnancy_status": "none", "vaccination_history": []}
            )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
