from datetime import date, timedelta

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

BASE_URL = "http://test"
LOG_DATA_BASE = {"pain_vas": 3, "fatigue": 3, "daily_difficulty": 3}
SETTING_DATA = {
    "pain_threshold": 7,
    "pain_consecutive_days": 2,
    "morning_stiffness_threshold": 60,
    "fatigue_threshold": 7,
    "alert_message": "담당 의료진 상담을 권고합니다",
    "is_enabled": True,
}


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    signup_data = {
        "email": email,
        "password": "Password123!",
        "name": "알림테스터",
        "gender": "FEMALE",
        "birth_date": "1990-09-09",
        "phone_number": phone,
    }
    await client.post("/api/v1/auth/signup", json=signup_data)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    return resp.json()["access_token"]


async def _put_log(client: AsyncClient, headers: dict, days_ago: int, data: dict) -> None:
    log_date = (date.today() - timedelta(days=days_ago)).isoformat()
    await client.put(f"/api/v1/activity-logs/{log_date}", json=data, headers=headers)


class TestAlertSettingApis(TestCase):
    async def test_upsert_creates_setting(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "alert_create@example.com", "01088880001")
            resp = await client.put(
                "/api/v1/activity-alerts/setting",
                json=SETTING_DATA,
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["pain_threshold"] == 7
        assert resp.json()["alert_message"] == "담당 의료진 상담을 권고합니다"

    async def test_upsert_twice_updates_same_record(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "alert_update@example.com", "01088880002")
            headers = {"Authorization": f"Bearer {token}"}
            first = await client.put("/api/v1/activity-alerts/setting", json=SETTING_DATA, headers=headers)
            second_data = {**SETTING_DATA, "fatigue_threshold": 8, "is_enabled": False}
            second = await client.put("/api/v1/activity-alerts/setting", json=second_data, headers=headers)
        assert first.json()["id"] == second.json()["id"]
        assert second.json()["fatigue_threshold"] == 8
        assert second.json()["is_enabled"] is False

    async def test_get_setting(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "alert_get@example.com", "01088880003")
            headers = {"Authorization": f"Bearer {token}"}
            await client.put("/api/v1/activity-alerts/setting", json=SETTING_DATA, headers=headers)
            resp = await client.get("/api/v1/activity-alerts/setting", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["pain_consecutive_days"] == 2

    async def test_get_setting_not_found(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "alert_notfound@example.com", "01088880004")
            resp = await client.get(
                "/api/v1/activity-alerts/setting",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_upsert_pain_threshold_out_of_range_returns_422(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "alert_invalid@example.com", "01088880005")
            invalid = {**SETTING_DATA, "pain_threshold": 11}
            resp = await client.put(
                "/api/v1/activity-alerts/setting",
                json=invalid,
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAlertStatusApis(TestCase):
    async def test_status_no_setting_returns_not_triggered(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "status_nosetting@example.com", "01088880006")
            resp = await client.get(
                "/api/v1/activity-alerts/status",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["triggered"] is False
        assert resp.json()["is_enabled"] is False

    async def test_status_fatigue_exceeded_triggers(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "status_fatigue@example.com", "01088880007")
            headers = {"Authorization": f"Bearer {token}"}
            setting = {"fatigue_threshold": 7, "alert_message": "기록한 수치를 의료진과 공유하세요", "is_enabled": True}
            await client.put("/api/v1/activity-alerts/setting", json=setting, headers=headers)
            await _put_log(client, headers, 0, {**LOG_DATA_BASE, "fatigue": 8})
            resp = await client.get("/api/v1/activity-alerts/status", headers=headers)
        assert resp.json()["triggered"] is True
        assert "FATIGUE" in resp.json()["triggered_criteria"]
        assert resp.json()["alert_message"] is not None
        assert resp.json()["disclaimer"] is not None

    async def test_status_fatigue_not_exceeded_not_triggered(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "status_ok@example.com", "01088880008")
            headers = {"Authorization": f"Bearer {token}"}
            setting = {"fatigue_threshold": 7, "alert_message": "메시지", "is_enabled": True}
            await client.put("/api/v1/activity-alerts/setting", json=setting, headers=headers)
            await _put_log(client, headers, 0, {**LOG_DATA_BASE, "fatigue": 5})
            resp = await client.get("/api/v1/activity-alerts/status", headers=headers)
        assert resp.json()["triggered"] is False
        assert resp.json()["alert_message"] is None
        assert resp.json()["disclaimer"] is None

    async def test_status_is_enabled_false_not_triggered(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "status_disabled@example.com", "01088880009")
            headers = {"Authorization": f"Bearer {token}"}
            setting = {"fatigue_threshold": 1, "alert_message": "메시지", "is_enabled": False}
            await client.put("/api/v1/activity-alerts/setting", json=setting, headers=headers)
            await _put_log(client, headers, 0, {**LOG_DATA_BASE, "fatigue": 9})
            resp = await client.get("/api/v1/activity-alerts/status", headers=headers)
        assert resp.json()["triggered"] is False
        assert resp.json()["is_enabled"] is False

    async def test_status_pain_consecutive_days_triggered(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "status_pain_consec@example.com", "01088880010")
            headers = {"Authorization": f"Bearer {token}"}
            setting = {"pain_threshold": 7, "pain_consecutive_days": 2, "alert_message": "메시지", "is_enabled": True}
            await client.put("/api/v1/activity-alerts/setting", json=setting, headers=headers)
            await _put_log(client, headers, 1, {**LOG_DATA_BASE, "pain_vas": 8})
            await _put_log(client, headers, 0, {**LOG_DATA_BASE, "pain_vas": 9})
            resp = await client.get("/api/v1/activity-alerts/status", headers=headers)
        assert resp.json()["triggered"] is True
        assert "PAIN" in resp.json()["triggered_criteria"]

    async def test_status_pain_consecutive_days_gap_not_triggered(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "status_pain_gap@example.com", "01088880011")
            headers = {"Authorization": f"Bearer {token}"}
            setting = {"pain_threshold": 7, "pain_consecutive_days": 2, "alert_message": "메시지", "is_enabled": True}
            await client.put("/api/v1/activity-alerts/setting", json=setting, headers=headers)
            await _put_log(client, headers, 1, {**LOG_DATA_BASE, "pain_vas": 3})  # 미달
            await _put_log(client, headers, 0, {**LOG_DATA_BASE, "pain_vas": 9})
            resp = await client.get("/api/v1/activity-alerts/status", headers=headers)
        assert resp.json()["triggered"] is False

    async def test_get_templates_returns_three(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "alert_templates@example.com", "01088880012")
            resp = await client.get(
                "/api/v1/activity-alerts/templates",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()["templates"]) == 3
