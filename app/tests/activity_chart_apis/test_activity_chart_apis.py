from datetime import date, timedelta

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

BASE_URL = "http://test"
LOG_DATA = {"pain_vas": 6, "fatigue": 5, "daily_difficulty": 4}


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    signup_data = {
        "email": email,
        "password": "Password123!",
        "name": "차트테스터",
        "gender": "MALE",
        "birth_date": "1985-04-01",
        "phone_number": phone,
    }
    await client.post("/api/v1/auth/signup", json=signup_data)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    return resp.json()["access_token"]


class TestActivityChartApis(TestCase):
    async def test_chart_with_data_returns_series_and_stats(self):
        today = date.today()
        date_1 = (today - timedelta(days=2)).isoformat()
        date_2 = (today - timedelta(days=1)).isoformat()
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "chart_data@example.com", "01077770001")
            headers = {"Authorization": f"Bearer {token}"}
            await client.put(f"/api/v1/activity-logs/{date_1}", json={**LOG_DATA, "pain_vas": 4}, headers=headers)
            await client.put(f"/api/v1/activity-logs/{date_2}", json={**LOG_DATA, "pain_vas": 8}, headers=headers)
            resp = await client.get("/api/v1/activity-logs/chart?period=1w", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["period"] == "1w"
        assert len(body["series"]) == 2
        assert body["series"][0]["log_date"] <= body["series"][1]["log_date"]
        assert body["pain_stats"]["max"] == 8
        assert body["pain_stats"]["min"] == 4
        assert body["pain_stats"]["avg"] == 6.0

    async def test_chart_no_data_returns_empty_series_and_null_stats(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "chart_empty@example.com", "01077770002")
            resp = await client.get(
                "/api/v1/activity-logs/chart?period=1w",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["series"] == []
        assert body["pain_stats"] == {"avg": None, "max": None, "min": None}
        assert body["fatigue_stats"] == {"avg": None, "max": None, "min": None}

    async def test_chart_invalid_period_returns_422(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "chart_invalid@example.com", "01077770003")
            resp = await client.get(
                "/api/v1/activity-logs/chart?period=bad",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_chart_default_period_is_week(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "chart_default@example.com", "01077770004")
            resp = await client.get(
                "/api/v1/activity-logs/chart",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["period"] == "1w"

    async def test_chart_unauthorized(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get("/api/v1/activity-logs/chart")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
