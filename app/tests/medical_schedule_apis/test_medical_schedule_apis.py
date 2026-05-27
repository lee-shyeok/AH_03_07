from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

BASE_URL = "http://test"


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


SCHEDULE_DATA = {"schedule_type": "BLOOD_TEST", "scheduled_date": "2026-08-01", "note": "공복 채혈"}


class TestMedicalScheduleApis(TestCase):
    async def test_create_schedule_returns_201(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sched_create@example.com", "01011110001")
            resp = await client.post(
                "/api/v1/medical-schedules",
                json=SCHEDULE_DATA,
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["schedule_type"] == "BLOOD_TEST"
        assert resp.json()["scheduled_date"] == "2026-08-01"
        assert resp.json()["note"] == "공복 채혈"

    async def test_list_schedules_returns_all(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sched_list@example.com", "01011110002")
            headers = {"Authorization": f"Bearer {token}"}
            await client.post("/api/v1/medical-schedules", json=SCHEDULE_DATA, headers=headers)
            await client.post(
                "/api/v1/medical-schedules",
                json={**SCHEDULE_DATA, "schedule_type": "APPOINTMENT", "scheduled_date": "2026-08-15"},
                headers=headers,
            )
            resp = await client.get("/api/v1/medical-schedules", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()) == 2

    async def test_list_schedules_filter_by_type(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sched_filter@example.com", "01011110003")
            headers = {"Authorization": f"Bearer {token}"}
            await client.post("/api/v1/medical-schedules", json=SCHEDULE_DATA, headers=headers)
            await client.post(
                "/api/v1/medical-schedules",
                json={**SCHEDULE_DATA, "schedule_type": "APPOINTMENT", "scheduled_date": "2026-08-15"},
                headers=headers,
            )
            resp = await client.get("/api/v1/medical-schedules?schedule_type=BLOOD_TEST", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data) == 1
        assert data[0]["schedule_type"] == "BLOOD_TEST"

    async def test_patch_schedule_updates_only_sent_fields(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sched_patch@example.com", "01011110004")
            headers = {"Authorization": f"Bearer {token}"}
            created = await client.post("/api/v1/medical-schedules", json=SCHEDULE_DATA, headers=headers)
            schedule_id = created.json()["id"]
            resp = await client.patch(
                f"/api/v1/medical-schedules/{schedule_id}",
                json={"note": "수정된 메모"},
                headers=headers,
            )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["note"] == "수정된 메모"
        assert resp.json()["schedule_type"] == "BLOOD_TEST"

    async def test_delete_removes_from_list(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sched_delete@example.com", "01011110005")
            headers = {"Authorization": f"Bearer {token}"}
            created = await client.post("/api/v1/medical-schedules", json=SCHEDULE_DATA, headers=headers)
            schedule_id = created.json()["id"]
            del_resp = await client.delete(f"/api/v1/medical-schedules/{schedule_id}", headers=headers)
            list_resp = await client.get("/api/v1/medical-schedules", headers=headers)
        assert del_resp.status_code == status.HTTP_204_NO_CONTENT
        assert list_resp.json() == []

    async def test_patch_other_user_schedule_returns_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token_a = await _signup_and_login(client, "sched_owner@example.com", "01011110006")
            token_b = await _signup_and_login(client, "sched_other@example.com", "01011110007")
            created = await client.post(
                "/api/v1/medical-schedules",
                json=SCHEDULE_DATA,
                headers={"Authorization": f"Bearer {token_a}"},
            )
            schedule_id = created.json()["id"]
            resp = await client.patch(
                f"/api/v1/medical-schedules/{schedule_id}",
                json={"note": "탈취 시도"},
                headers={"Authorization": f"Bearer {token_b}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_other_user_schedule_returns_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token_a = await _signup_and_login(client, "sched_owner2@example.com", "01011110008")
            token_b = await _signup_and_login(client, "sched_other2@example.com", "01011110009")
            created = await client.post(
                "/api/v1/medical-schedules",
                json=SCHEDULE_DATA,
                headers={"Authorization": f"Bearer {token_a}"},
            )
            schedule_id = created.json()["id"]
            resp = await client.delete(
                f"/api/v1/medical-schedules/{schedule_id}",
                headers={"Authorization": f"Bearer {token_b}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_unauthenticated_returns_401(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get("/api/v1/medical-schedules")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
