from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

BASE_URL = "http://test"
LOG_EP = "/api/v1/activity-logs"
LOG_DATA = {
    "log_date": "2026-05-27",
    "pain_vas": 5,
    "fatigue": 6,
    "morning_stiffness_minutes": 30,
    "joint_swelling_areas": ["LEFT_KNEE", "RIGHT_WRIST"],
    "daily_difficulty": 4,
    "free_memo": "오늘 컨디션 보통",
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
            resp = await client.post(
                LOG_EP,
                json=LOG_DATA,
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["log_date"] == "2026-05-27"
        assert body["pain_vas"] == 5
        assert body["morning_stiffness_minutes"] == 30
        assert body["joint_swelling_areas"] == ["LEFT_KNEE", "RIGHT_WRIST"]
        assert body["free_memo"] == "오늘 컨디션 보통"

    async def test_upsert_twice_same_date_updates_not_duplicates(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "actv_upsert@example.com", "01055550002")
            headers = {"Authorization": f"Bearer {token}"}
            first = await client.post(LOG_EP, json=LOG_DATA, headers=headers)
            second_data = {**LOG_DATA, "pain_vas": 8, "free_memo": "저녁에 악화"}
            second = await client.post(LOG_EP, json=second_data, headers=headers)
            list_resp = await client.get(LOG_EP, headers=headers)
        assert first.json()["id"] == second.json()["id"]
        assert second.json()["pain_vas"] == 8
        assert second.json()["free_memo"] == "저녁에 악화"
        assert len(list_resp.json()) == 1

    async def test_list_activity_logs_ordered_desc(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "actv_list@example.com", "01055550003")
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(LOG_EP, json={**LOG_DATA, "log_date": "2026-05-25"}, headers=headers)
            await client.post(LOG_EP, json={**LOG_DATA, "log_date": "2026-05-26"}, headers=headers)
            resp = await client.get(LOG_EP, headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()) == 2
        assert resp.json()[0]["log_date"] == "2026-05-26"  # 내림차순

    async def test_list_filter_by_date_range(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "actv_daterange@example.com", "01055550007")
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(LOG_EP, json={**LOG_DATA, "log_date": "2026-04-01"}, headers=headers)
            await client.post(LOG_EP, json={**LOG_DATA, "log_date": "2026-05-15"}, headers=headers)
            await client.post(LOG_EP, json={**LOG_DATA, "log_date": "2026-07-01"}, headers=headers)
            resp = await client.get(f"{LOG_EP}?from=2026-05-01&to=2026-06-01", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        dates = [r["log_date"] for r in resp.json()]
        assert "2026-05-15" in dates
        assert "2026-04-01" not in dates
        assert "2026-07-01" not in dates

    async def test_get_activity_log_by_date(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "actv_get@example.com", "01055550004")
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(LOG_EP, json=LOG_DATA, headers=headers)
            resp = await client.get(f"{LOG_EP}/2026-05-27", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["log_date"] == "2026-05-27"
        assert resp.json()["fatigue"] == 6

    async def test_get_activity_log_not_found(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "actv_notfound@example.com", "01055550005")
            resp = await client.get(
                f"{LOG_EP}/2000-01-01",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_upsert_pain_vas_out_of_range_returns_422(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "actv_invalid@example.com", "01055550006")
            resp = await client.post(
                LOG_EP,
                json={**LOG_DATA, "pain_vas": 11},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_list_activity_logs_unauthorized(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get(LOG_EP)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
