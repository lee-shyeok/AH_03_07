from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

BASE_URL = "http://test"


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    signup_data = {
        "email": email,
        "password": "Password123!",
        "name": "약물테스터",
        "gender": "MALE",
        "birth_date": "1980-07-20",
        "phone_number": phone,
    }
    await client.post("/api/v1/auth/signup", json=signup_data)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    return resp.json()["access_token"]


class TestMedicationApis(TestCase):
    async def test_create_medication(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "med_create@example.com", "01044440001")
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.post(
                "/api/v1/medications",
                json={"drug_name_user_input": "메토트렉세이트"},
                headers=headers,
            )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["drug_name_user_input"] == "메토트렉세이트"

    async def test_list_medications(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "med_list@example.com", "01044440002")
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(
                "/api/v1/medications",
                json={"drug_name_user_input": "하이드록시클로로퀸"},
                headers=headers,
            )
            resp = await client.get("/api/v1/medications", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["total"] == 1

    async def test_list_medications_unauthorized(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get("/api/v1/medications")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
