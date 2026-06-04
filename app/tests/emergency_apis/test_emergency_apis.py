from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

BASE_URL = "http://test"


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    signup_data = {
        "email": email,
        "password": "Password123!",
        "name": "응급테스터",
        "gender": "MALE",
        "birth_date": "1990-01-01",
        "phone_number": phone,
    }
    await client.post("/api/v1/auth/signup", json=signup_data)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    token = resp.json()["access_token"]
    await client.post(
        "/api/v1/users/me/consents",
        json={"consent_type": "MEDICAL_DATA", "agreed": True, "version": "1.0"},
        headers={"Authorization": f"Bearer {token}"},
    )
    return token


class TestEmergencyCardGet(TestCase):
    """GET /api/v1/emergency/card"""

    async def test_get_card_returns_404_when_not_exists(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "emrg_get_empty@example.com", "01011110101")
            resp = await client.get(
                "/api/v1/emergency/card",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_card_requires_auth(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get("/api/v1/emergency/card")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_card_returns_200_after_put(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "emrg_get_ok@example.com", "01011110102")
            headers = {"Authorization": f"Bearer {token}"}
            await client.put(
                "/api/v1/emergency/card",
                json={"blood_type": "A+", "allergies": "페니실린"},
                headers=headers,
            )
            resp = await client.get("/api/v1/emergency/card", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["blood_type"] == "A+"
        assert body["allergies"] == "페니실린"


class TestEmergencyCardPut(TestCase):
    """PUT /api/v1/emergency/card"""

    async def test_put_card_creates_and_returns_200(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "emrg_put_create@example.com", "01011110103")
            resp = await client.put(
                "/api/v1/emergency/card",
                json={
                    "blood_type": "O-",
                    "allergies": "아스피린",
                    "chronic_conditions": "루푸스",
                    "siren_mode": "NORMAL",
                },
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["blood_type"] == "O-"
        assert body["chronic_conditions"] == "루푸스"
        assert "id" in body

    async def test_put_card_updates_existing(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "emrg_put_update@example.com", "01011110104")
            headers = {"Authorization": f"Bearer {token}"}
            await client.put(
                "/api/v1/emergency/card",
                json={"blood_type": "B+"},
                headers=headers,
            )
            resp = await client.put(
                "/api/v1/emergency/card",
                json={"blood_type": "AB+", "allergies": "해산물"},
                headers=headers,
            )
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["blood_type"] == "AB+"
        assert body["allergies"] == "해산물"

    async def test_put_card_requires_auth(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.put("/api/v1/emergency/card", json={"blood_type": "A+"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestSOSTrigger(TestCase):
    """POST /api/v1/emergency/trigger"""

    async def test_trigger_without_card_returns_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sos_no_card@example.com", "01011110105")
            resp = await client.post(
                "/api/v1/emergency/trigger",
                json={"latitude": 37.5665, "longitude": 126.9780},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_trigger_with_no_guardians_returns_200_notified_0(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sos_no_guardian@example.com", "01011110106")
            headers = {"Authorization": f"Bearer {token}"}
            await client.put(
                "/api/v1/emergency/card",
                json={"blood_type": "A+", "allergies": "없음"},
                headers=headers,
            )
            resp = await client.post(
                "/api/v1/emergency/trigger",
                json={"latitude": 37.5665, "longitude": 126.9780},
                headers=headers,
            )
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["status"] == "sent"
        assert body["notified_count"] == 0
        assert body["latitude"] == 37.5665
        assert body["longitude"] == 126.9780

    async def test_trigger_with_guardian_returns_notified_1(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sos_with_guardian@example.com", "01011110107")
            headers = {"Authorization": f"Bearer {token}"}
            await client.put(
                "/api/v1/emergency/card",
                json={"blood_type": "B-"},
                headers=headers,
            )
            await client.post(
                "/api/v1/guardians",
                json={"name": "보호자1", "phone_number": "01099991001", "relationship": "부모"},
                headers=headers,
            )
            resp = await client.post(
                "/api/v1/emergency/trigger",
                json={"latitude": 35.1796, "longitude": 129.0756},
                headers=headers,
            )
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["status"] == "sent"
        assert body["notified_count"] == 1

    async def test_trigger_requires_auth(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.post(
                "/api/v1/emergency/trigger",
                json={"latitude": 37.5665, "longitude": 126.9780},
            )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
