from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

BASE_URL = "http://test"
LOG_DATE = "2026-05-27"
LOG_DATA = {
    "pain_vas": 5,
    "fatigue": 6,
    "morning_stiffness_min": 30,
    "joint_swelling_areas": ["LEFT_KNEE", "RIGHT_WRIST"],
    "daily_difficulty": 4,
    "note": "오늘 컨디션 보통",
}


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    signup_data = {
        "email": email,
        "password": "Password123!",
        "name": "활성도테스터",
        "gender": "FEMALE",
        "birth_date": "1992-06-15",
        "phone_number": phone,
    }
    await client.post("/api/v1/auth/signup", json=signup_data)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    return resp.json()["access_token"]


class TestActivityLogApis(TestCase):
    async def test_upsert_creates_log(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "actv_create@example.com", "01055550001")
            resp = await client.put(
                f"/api/v1/activity-logs/{LOG_DATE}",
                json=LOG_DATA,
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["log_date"] == LOG_DATE
        assert resp.json()["pain_vas"] == 5
        assert resp.json()["joint_swelling_areas"] == ["LEFT_KNEE", "RIGHT_WRIST"]

    async def test_upsert_twice_same_date_updates_not_duplicates(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "actv_upsert@example.com", "01055550002")
            headers = {"Authorization": f"Bearer {token}"}
            first = await client.put(f"/api/v1/activity-logs/{LOG_DATE}", json=LOG_DATA, headers=headers)
            second_data = {**LOG_DATA, "pain_vas": 8, "note": "저녁에 악화"}
            second = await client.put(f"/api/v1/activity-logs/{LOG_DATE}", json=second_data, headers=headers)
            list_resp = await client.get("/api/v1/activity-logs", headers=headers)
        assert first.json()["id"] == second.json()["id"]
        assert second.json()["pain_vas"] == 8
        assert second.json()["note"] == "저녁에 악화"
        assert len(list_resp.json()) == 1

    async def test_list_activity_logs(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "actv_list@example.com", "01055550003")
            headers = {"Authorization": f"Bearer {token}"}
            await client.put("/api/v1/activity-logs/2026-05-25", json=LOG_DATA, headers=headers)
            await client.put("/api/v1/activity-logs/2026-05-26", json=LOG_DATA, headers=headers)
            resp = await client.get("/api/v1/activity-logs", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()) == 2
        assert resp.json()[0]["log_date"] == "2026-05-26"  # 내림차순

    async def test_get_activity_log_by_date(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "actv_get@example.com", "01055550004")
            headers = {"Authorization": f"Bearer {token}"}
            await client.put(f"/api/v1/activity-logs/{LOG_DATE}", json=LOG_DATA, headers=headers)
            resp = await client.get(f"/api/v1/activity-logs/{LOG_DATE}", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["log_date"] == LOG_DATE
        assert resp.json()["fatigue"] == 6

    async def test_get_activity_log_not_found(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "actv_notfound@example.com", "01055550005")
            resp = await client.get(
                "/api/v1/activity-logs/2000-01-01",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_upsert_pain_vas_out_of_range_returns_422(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "actv_invalid@example.com", "01055550006")
            invalid_data = {**LOG_DATA, "pain_vas": 11}
            resp = await client.put(
                f"/api/v1/activity-logs/{LOG_DATE}",
                json=invalid_data,
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_list_activity_logs_unauthorized(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get("/api/v1/activity-logs")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
