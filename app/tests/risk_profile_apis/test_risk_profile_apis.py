from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

BASE_URL = "http://test"


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    signup_data = {
        "email": email,
        "password": "Password123!",
        "name": "프로필테스터",
        "gender": "FEMALE",
        "birth_date": "1988-03-10",
        "phone_number": phone,
    }
    await client.post("/api/v1/auth/signup", json=signup_data)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    return resp.json()["access_token"]


PROFILE_DATA = {
    "pregnancy_status": "NONE",
    "renal_impairment": False,
    "hepatic_impairment": True,
    "infection_history": "결핵 이력 있음",
    "drug_allergy": "페니실린",
    "comorbidities": "고혈압",
}


class TestRiskProfileApis(TestCase):
    async def test_get_risk_profile_not_found(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "rp_notfound@example.com", "01033330001")
            resp = await client.get(
                "/api/v1/users/me/risk-profile",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_upsert_creates_profile(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "rp_create@example.com", "01033330002")
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.put("/api/v1/users/me/risk-profile", json=PROFILE_DATA, headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["hepatic_impairment"] is True
        assert resp.json()["drug_allergy"] == "페니실린"

    async def test_upsert_twice_updates_same_record(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "rp_update@example.com", "01033330003")
            headers = {"Authorization": f"Bearer {token}"}
            first = await client.put("/api/v1/users/me/risk-profile", json=PROFILE_DATA, headers=headers)
            second_data = {**PROFILE_DATA, "drug_allergy": "설파제", "renal_impairment": True}
            second = await client.put("/api/v1/users/me/risk-profile", json=second_data, headers=headers)
        assert first.json()["id"] == second.json()["id"]
        assert second.json()["drug_allergy"] == "설파제"
        assert second.json()["renal_impairment"] is True

    async def test_get_risk_profile_after_upsert(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "rp_get@example.com", "01033330004")
            headers = {"Authorization": f"Bearer {token}"}
            await client.put("/api/v1/users/me/risk-profile", json=PROFILE_DATA, headers=headers)
            resp = await client.get("/api/v1/users/me/risk-profile", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["comorbidities"] == "고혈압"

    async def test_get_risk_profile_unauthorized(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get("/api/v1/users/me/risk-profile")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
