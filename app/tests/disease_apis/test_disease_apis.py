from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

BASE_URL = "http://test"


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    signup_data = {
        "email": email,
        "password": "Password123!",
        "name": "질환테스터",
        "gender": "MALE",
        "birth_date": "1985-05-15",
        "phone_number": phone,
    }
    await client.post("/api/v1/auth/signup", json=signup_data)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    return resp.json()["access_token"]


class TestDiseaseApis(TestCase):
    async def test_create_diseases_bulk(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "disease_create@example.com", "01022220001")
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.post(
                "/api/v1/diseases",
                json={"diseases": [{"disease_code": "RA"}, {"disease_code": "SLE"}]},
                headers=headers,
            )
        assert resp.status_code == status.HTTP_201_CREATED
        assert len(resp.json()) == 2
        codes = {d["disease_code"] for d in resp.json()}
        assert codes == {"RA", "SLE"}

    async def test_list_diseases_own_and_active_only(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "disease_list@example.com", "01022220002")
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(
                "/api/v1/diseases",
                json={"diseases": [{"disease_code": "RA"}]},
                headers=headers,
            )
            resp = await client.get("/api/v1/diseases", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()) == 1
        assert resp.json()[0]["disease_code"] == "RA"

    async def test_update_disease_note_only(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "disease_update@example.com", "01022220003")
            headers = {"Authorization": f"Bearer {token}"}
            create_resp = await client.post(
                "/api/v1/diseases",
                json={"diseases": [{"disease_code": "SLE", "note": "초기 메모"}]},
                headers=headers,
            )
            disease_id = create_resp.json()[0]["id"]
            patch_resp = await client.patch(
                f"/api/v1/diseases/{disease_id}",
                json={"note": "수정된 메모"},
                headers=headers,
            )
        assert patch_resp.status_code == status.HTTP_200_OK
        assert patch_resp.json()["note"] == "수정된 메모"
        assert patch_resp.json()["disease_code"] == "SLE"

    async def test_delete_disease_soft_delete(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "disease_delete@example.com", "01022220004")
            headers = {"Authorization": f"Bearer {token}"}
            create_resp = await client.post(
                "/api/v1/diseases",
                json={"diseases": [{"disease_code": "RA"}]},
                headers=headers,
            )
            disease_id = create_resp.json()[0]["id"]
            del_resp = await client.delete(f"/api/v1/diseases/{disease_id}", headers=headers)
            list_resp = await client.get("/api/v1/diseases", headers=headers)
        assert del_resp.status_code == status.HTTP_204_NO_CONTENT
        assert all(d["id"] != disease_id for d in list_resp.json())

    async def test_update_other_user_disease_returns_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token_a = await _signup_and_login(client, "disease_owner@example.com", "01022220005")
            token_b = await _signup_and_login(client, "disease_intruder@example.com", "01022220006")
            create_resp = await client.post(
                "/api/v1/diseases",
                json={"diseases": [{"disease_code": "RA"}]},
                headers={"Authorization": f"Bearer {token_a}"},
            )
            disease_id = create_resp.json()[0]["id"]
            resp = await client.patch(
                f"/api/v1/diseases/{disease_id}",
                json={"note": "침입"},
                headers={"Authorization": f"Bearer {token_b}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_other_user_disease_returns_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token_a = await _signup_and_login(client, "disease_owner2@example.com", "01022220007")
            token_b = await _signup_and_login(client, "disease_intruder2@example.com", "01022220008")
            create_resp = await client.post(
                "/api/v1/diseases",
                json={"diseases": [{"disease_code": "SLE"}]},
                headers={"Authorization": f"Bearer {token_a}"},
            )
            disease_id = create_resp.json()[0]["id"]
            resp = await client.delete(
                f"/api/v1/diseases/{disease_id}",
                headers={"Authorization": f"Bearer {token_b}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_list_diseases_unauthorized(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get("/api/v1/diseases")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
