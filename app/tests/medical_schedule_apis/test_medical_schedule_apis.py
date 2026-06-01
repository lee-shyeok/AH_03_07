from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

BASE_URL = "http://test"
SCHEDULES_EP = "/api/v1/care-schedules"


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    signup_data = {
        "email": email,
        "password": "Password123!",
        "name": "일정테스터",
        "gender": "FEMALE",
        "birth_date": "1990-01-01",
        "phone_number": phone,
    }
    await client.post("/api/v1/auth/signup", json=signup_data)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    return resp.json()["access_token"]


SCHEDULE_DATA = {
    "schedule_type": "BLOOD_TEST",
    "title": "3개월 정기 혈액검사",
    "scheduled_date": "2026-08-01",
    "reminder_days_before": 2,
    "note": "공복 채혈",
}


class TestCareScheduleApis(TestCase):
    async def test_create_schedule_returns_201(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sched_create@example.com", "01011110001")
            resp = await client.post(SCHEDULES_EP, json=SCHEDULE_DATA, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == status.HTTP_201_CREATED
        body = resp.json()
        assert body["schedule_type"] == "BLOOD_TEST"
        assert body["title"] == "3개월 정기 혈액검사"
        assert body["scheduled_date"] == "2026-08-01"
        assert body["reminder_days_before"] == 2
        assert body["note"] == "공복 채혈"

    async def test_list_schedules_returns_all(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sched_list@example.com", "01011110002")
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(SCHEDULES_EP, json=SCHEDULE_DATA, headers=headers)
            await client.post(
                SCHEDULES_EP,
                json={
                    **SCHEDULE_DATA,
                    "schedule_type": "APPOINTMENT",
                    "scheduled_date": "2026-08-15",
                    "title": "외래 진료",
                },
                headers=headers,
            )
            resp = await client.get(SCHEDULES_EP, headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()) == 2

    async def test_list_schedules_filter_by_type(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sched_filter@example.com", "01011110003")
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(SCHEDULES_EP, json=SCHEDULE_DATA, headers=headers)
            await client.post(
                SCHEDULES_EP,
                json={
                    **SCHEDULE_DATA,
                    "schedule_type": "APPOINTMENT",
                    "scheduled_date": "2026-08-15",
                    "title": "외래 진료",
                },
                headers=headers,
            )
            resp = await client.get(f"{SCHEDULES_EP}?type=BLOOD_TEST", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data) == 1
        assert data[0]["schedule_type"] == "BLOOD_TEST"

    async def test_list_schedules_filter_by_date_range(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sched_daterange@example.com", "01011110010")
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(SCHEDULES_EP, json={**SCHEDULE_DATA, "scheduled_date": "2026-07-01"}, headers=headers)
            await client.post(SCHEDULES_EP, json={**SCHEDULE_DATA, "scheduled_date": "2026-08-15"}, headers=headers)
            await client.post(SCHEDULES_EP, json={**SCHEDULE_DATA, "scheduled_date": "2026-09-30"}, headers=headers)
            resp = await client.get(f"{SCHEDULES_EP}?from=2026-08-01&to=2026-09-01", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        dates = [item["scheduled_date"] for item in resp.json()]
        assert "2026-08-15" in dates
        assert "2026-07-01" not in dates
        assert "2026-09-30" not in dates

    async def test_put_schedule_replaces_all_fields(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sched_put@example.com", "01011110004")
            headers = {"Authorization": f"Bearer {token}"}
            created = await client.post(SCHEDULES_EP, json=SCHEDULE_DATA, headers=headers)
            schedule_id = created.json()["id"]
            resp = await client.put(
                f"{SCHEDULES_EP}/{schedule_id}",
                json={
                    "schedule_type": "EYE_EXAM",
                    "title": "안과 검진 수정",
                    "scheduled_date": "2026-09-01",
                    "reminder_days_before": 3,
                    "note": "수정된 메모",
                },
                headers=headers,
            )
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["schedule_type"] == "EYE_EXAM"
        assert body["title"] == "안과 검진 수정"
        assert body["scheduled_date"] == "2026-09-01"
        assert body["reminder_days_before"] == 3
        assert body["note"] == "수정된 메모"

    async def test_delete_removes_from_list(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sched_delete@example.com", "01011110005")
            headers = {"Authorization": f"Bearer {token}"}
            created = await client.post(SCHEDULES_EP, json=SCHEDULE_DATA, headers=headers)
            schedule_id = created.json()["id"]
            del_resp = await client.delete(f"{SCHEDULES_EP}/{schedule_id}", headers=headers)
            list_resp = await client.get(SCHEDULES_EP, headers=headers)
        assert del_resp.status_code == status.HTTP_204_NO_CONTENT
        assert list_resp.json() == []

    async def test_put_other_user_schedule_returns_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token_a = await _signup_and_login(client, "sched_owner@example.com", "01011110006")
            token_b = await _signup_and_login(client, "sched_other@example.com", "01011110007")
            created = await client.post(
                SCHEDULES_EP, json=SCHEDULE_DATA, headers={"Authorization": f"Bearer {token_a}"}
            )
            schedule_id = created.json()["id"]
            resp = await client.put(
                f"{SCHEDULES_EP}/{schedule_id}",
                json={**SCHEDULE_DATA, "title": "탈취 시도"},
                headers={"Authorization": f"Bearer {token_b}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_other_user_schedule_returns_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token_a = await _signup_and_login(client, "sched_owner2@example.com", "01011110008")
            token_b = await _signup_and_login(client, "sched_other2@example.com", "01011110009")
            created = await client.post(
                SCHEDULES_EP, json=SCHEDULE_DATA, headers={"Authorization": f"Bearer {token_a}"}
            )
            schedule_id = created.json()["id"]
            resp = await client.delete(f"{SCHEDULES_EP}/{schedule_id}", headers={"Authorization": f"Bearer {token_b}"})
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_unauthenticated_returns_401(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get(SCHEDULES_EP)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_missing_title_returns_422(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sched_notitle@example.com", "01011110011")
            resp = await client.post(
                SCHEDULES_EP,
                json={"schedule_type": "BLOOD_TEST", "scheduled_date": "2026-08-01"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
