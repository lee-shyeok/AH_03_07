from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

BASE_URL = "http://test"
LAB_EP = "/api/v1/lab-results"


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    signup_data = {
        "email": email,
        "password": "Password123!",
        "name": "검사테스터",
        "gender": "MALE",
        "birth_date": "1988-06-15",
        "phone_number": phone,
    }
    await client.post("/api/v1/auth/signup", json=signup_data)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    return resp.json()["access_token"]


LAB_DATA = {
    "test_date": "2026-07-20",
    "test_type": "ESR",
    "user_recorded_value": "45 mm/h",
    "reference_range": "0-20 mm/h",
    "note": "염증 수치 상승",
}


class TestLabResultApis(TestCase):
    async def test_create_lab_result_returns_201_with_spec_fields(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "lab_create@example.com", "01022220001")
            resp = await client.post(LAB_EP, json=LAB_DATA, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == status.HTTP_201_CREATED
        body = resp.json()
        assert body["test_type"] == "ESR"
        assert body["user_recorded_value"] == "45 mm/h"
        assert body["reference_range"] == "0-20 mm/h"
        assert body["note"] == "염증 수치 상승"

    async def test_list_lab_results_ordered_by_test_date_desc(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "lab_list@example.com", "01022220002")
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(LAB_EP, json={**LAB_DATA, "test_date": "2026-06-01"}, headers=headers)
            await client.post(LAB_EP, json={**LAB_DATA, "test_date": "2026-07-20"}, headers=headers)
            resp = await client.get(LAB_EP, headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        dates = [r["test_date"] for r in resp.json()]
        assert dates == sorted(dates, reverse=True)

    async def test_list_filter_by_date_range(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "lab_daterange@example.com", "01022220010")
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(LAB_EP, json={**LAB_DATA, "test_date": "2026-05-01"}, headers=headers)
            await client.post(LAB_EP, json={**LAB_DATA, "test_date": "2026-07-15"}, headers=headers)
            await client.post(LAB_EP, json={**LAB_DATA, "test_date": "2026-09-01"}, headers=headers)
            resp = await client.get(f"{LAB_EP}?from=2026-07-01&to=2026-08-01", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        dates = [r["test_date"] for r in resp.json()]
        assert "2026-07-15" in dates
        assert "2026-05-01" not in dates
        assert "2026-09-01" not in dates

    async def test_patch_updates_only_sent_fields(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "lab_patch@example.com", "01022220003")
            headers = {"Authorization": f"Bearer {token}"}
            created = await client.post(LAB_EP, json=LAB_DATA, headers=headers)
            result_id = created.json()["id"]
            resp = await client.patch(
                f"{LAB_EP}/{result_id}",
                json={"user_recorded_value": "38 mm/h"},
                headers=headers,
            )
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["user_recorded_value"] == "38 mm/h"
        assert body["test_type"] == "ESR"

    async def test_delete_removes_from_list(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "lab_delete@example.com", "01022220004")
            headers = {"Authorization": f"Bearer {token}"}
            created = await client.post(LAB_EP, json=LAB_DATA, headers=headers)
            result_id = created.json()["id"]
            del_resp = await client.delete(f"{LAB_EP}/{result_id}", headers=headers)
            list_resp = await client.get(LAB_EP, headers=headers)
        assert del_resp.status_code == status.HTTP_204_NO_CONTENT
        assert list_resp.json() == []

    async def test_patch_other_user_result_returns_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token_a = await _signup_and_login(client, "lab_owner@example.com", "01022220005")
            token_b = await _signup_and_login(client, "lab_other@example.com", "01022220006")
            created = await client.post(LAB_EP, json=LAB_DATA, headers={"Authorization": f"Bearer {token_a}"})
            result_id = created.json()["id"]
            resp = await client.patch(
                f"{LAB_EP}/{result_id}",
                json={"user_recorded_value": "99 mm/h"},
                headers={"Authorization": f"Bearer {token_b}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_other_user_result_returns_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token_a = await _signup_and_login(client, "lab_owner2@example.com", "01022220007")
            token_b = await _signup_and_login(client, "lab_other2@example.com", "01022220008")
            created = await client.post(LAB_EP, json=LAB_DATA, headers={"Authorization": f"Bearer {token_a}"})
            result_id = created.json()["id"]
            resp = await client.delete(f"{LAB_EP}/{result_id}", headers={"Authorization": f"Bearer {token_b}"})
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_empty_test_type_returns_422(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "lab_invalid@example.com", "01022220009")
            resp = await client.post(
                LAB_EP,
                json={**LAB_DATA, "test_type": ""},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_unauthenticated_returns_401(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get(LAB_EP)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
