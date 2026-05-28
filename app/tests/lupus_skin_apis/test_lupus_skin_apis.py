from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

BASE_URL = "http://test"


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    signup_data = {
        "email": email,
        "password": "Password123!",
        "name": "루푸스테스터",
        "gender": "FEMALE",
        "birth_date": "1995-07-20",
        "phone_number": phone,
    }
    await client.post("/api/v1/auth/signup", json=signup_data)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    return resp.json()["access_token"]


LOG_DATA = {"symptom_type": "RASH", "log_date": "2026-07-01", "note": "뺨 부위 나비 모양 발진"}


class TestLupusSkinLogApis(TestCase):
    async def test_create_log_returns_201(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "lupus_create@example.com", "01044440001")
            resp = await client.post(
                "/api/v1/lupus-skin-logs",
                json=LOG_DATA,
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_201_CREATED
        body = resp.json()
        assert body["symptom_type"] == "RASH"
        assert body["log_date"] == "2026-07-01"
        assert body["note"] == "뺨 부위 나비 모양 발진"
        assert "id" in body

    async def test_list_logs_empty(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "lupus_empty@example.com", "01044440002")
            resp = await client.get(
                "/api/v1/lupus-skin-logs",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == []

    async def test_list_logs_returns_own_latest_first(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "lupus_list@example.com", "01044440003")
            headers = {"Authorization": f"Bearer {token}"}
            await client.post("/api/v1/lupus-skin-logs", json={**LOG_DATA, "log_date": "2026-06-01"}, headers=headers)
            await client.post("/api/v1/lupus-skin-logs", json={**LOG_DATA, "log_date": "2026-07-01"}, headers=headers)
            resp = await client.get("/api/v1/lupus-skin-logs", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        dates = [r["log_date"] for r in resp.json()]
        assert dates == sorted(dates, reverse=True)
        assert len(dates) == 2

    async def test_get_single_log(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "lupus_get@example.com", "01044440004")
            headers = {"Authorization": f"Bearer {token}"}
            created = await client.post("/api/v1/lupus-skin-logs", json=LOG_DATA, headers=headers)
            log_id = created.json()["id"]
            resp = await client.get(f"/api/v1/lupus-skin-logs/{log_id}", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["id"] == log_id

    async def test_get_nonexistent_log_returns_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "lupus_404@example.com", "01044440005")
            resp = await client.get(
                "/api/v1/lupus-skin-logs/99999",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_patch_updates_only_sent_fields(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "lupus_patch@example.com", "01044440006")
            headers = {"Authorization": f"Bearer {token}"}
            created = await client.post("/api/v1/lupus-skin-logs", json=LOG_DATA, headers=headers)
            log_id = created.json()["id"]
            resp = await client.patch(
                f"/api/v1/lupus-skin-logs/{log_id}",
                json={"note": "구강 내 궤양 추가 관찰"},
                headers=headers,
            )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["note"] == "구강 내 궤양 추가 관찰"
        assert resp.json()["symptom_type"] == "RASH"

    async def test_patch_nonexistent_log_returns_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "lupus_patch404@example.com", "01044440007")
            resp = await client.patch(
                "/api/v1/lupus-skin-logs/99999",
                json={"note": "없는 기록"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_soft_deletes_log(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "lupus_delete@example.com", "01044440008")
            headers = {"Authorization": f"Bearer {token}"}
            created = await client.post("/api/v1/lupus-skin-logs", json=LOG_DATA, headers=headers)
            log_id = created.json()["id"]
            del_resp = await client.delete(f"/api/v1/lupus-skin-logs/{log_id}", headers=headers)
            get_resp = await client.get(f"/api/v1/lupus-skin-logs/{log_id}", headers=headers)
            list_resp = await client.get("/api/v1/lupus-skin-logs", headers=headers)
        assert del_resp.status_code == status.HTTP_204_NO_CONTENT
        assert get_resp.status_code == status.HTTP_404_NOT_FOUND
        assert list_resp.json() == []

    async def test_cross_user_isolation(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token_a = await _signup_and_login(client, "lupus_owner@example.com", "01044440009")
            token_b = await _signup_and_login(client, "lupus_other@example.com", "01044440010")
            created = await client.post(
                "/api/v1/lupus-skin-logs",
                json=LOG_DATA,
                headers={"Authorization": f"Bearer {token_a}"},
            )
            log_id = created.json()["id"]
            headers_b = {"Authorization": f"Bearer {token_b}"}
            get_resp = await client.get(f"/api/v1/lupus-skin-logs/{log_id}", headers=headers_b)
            patch_resp = await client.patch(
                f"/api/v1/lupus-skin-logs/{log_id}", json={"note": "침입"}, headers=headers_b
            )
            del_resp = await client.delete(f"/api/v1/lupus-skin-logs/{log_id}", headers=headers_b)
            list_resp = await client.get("/api/v1/lupus-skin-logs", headers=headers_b)
        assert get_resp.status_code == status.HTTP_404_NOT_FOUND
        assert patch_resp.status_code == status.HTTP_404_NOT_FOUND
        assert del_resp.status_code == status.HTTP_404_NOT_FOUND
        assert list_resp.json() == []

    async def test_unauthenticated_returns_401(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get("/api/v1/lupus-skin-logs")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
