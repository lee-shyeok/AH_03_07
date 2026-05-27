from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

BASE_URL = "http://test"


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    signup_data = {
        "email": email,
        "password": "Password123!",
        "name": "약물테스터",
        "gender": "MALE",
        "birth_date": "1980-07-20",
        "phone_number": phone,
    }
    await client.post("/api/v1/auth/signup", json=signup_data)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    return resp.json()["access_token"]


class TestMedicationApis(TestCase):
    async def test_create_medications_bulk(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "med_create@example.com", "01044440001")
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.post(
                "/api/v1/medications",
                json={
                    "medications": [
                        {"name": "메토트렉세이트", "drug_class": "IMMUNOSUPPRESSANT"},
                        {"name": "프레드니솔론", "drug_class": "STEROID", "is_injection": False},
                    ]
                },
                headers=headers,
            )
        assert resp.status_code == status.HTTP_201_CREATED
        assert len(resp.json()) == 2
        names = {m["name"] for m in resp.json()}
        assert names == {"메토트렉세이트", "프레드니솔론"}

    async def test_list_medications_own_and_active_only(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "med_list@example.com", "01044440002")
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(
                "/api/v1/medications",
                json={"medications": [{"name": "하이드록시클로로퀸", "drug_class": "ANTIMALARIAL"}]},
                headers=headers,
            )
            resp = await client.get("/api/v1/medications", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()) == 1
        assert resp.json()[0]["drug_class"] == "ANTIMALARIAL"

    async def test_update_medication(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "med_update@example.com", "01044440003")
            headers = {"Authorization": f"Bearer {token}"}
            create_resp = await client.post(
                "/api/v1/medications",
                json={"medications": [{"name": "인플릭시맙", "drug_class": "BIOLOGIC", "is_injection": True}]},
                headers=headers,
            )
            med_id = create_resp.json()[0]["id"]
            patch_resp = await client.patch(
                f"/api/v1/medications/{med_id}",
                json={"note": "8주 간격 주사"},
                headers=headers,
            )
        assert patch_resp.status_code == status.HTTP_200_OK
        assert patch_resp.json()["note"] == "8주 간격 주사"
        assert patch_resp.json()["name"] == "인플릭시맙"
        assert patch_resp.json()["is_injection"] is True

    async def test_delete_medication_soft_delete(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "med_delete@example.com", "01044440004")
            headers = {"Authorization": f"Bearer {token}"}
            create_resp = await client.post(
                "/api/v1/medications",
                json={"medications": [{"name": "나프록센", "drug_class": "NSAID"}]},
                headers=headers,
            )
            med_id = create_resp.json()[0]["id"]
            del_resp = await client.delete(f"/api/v1/medications/{med_id}", headers=headers)
            list_resp = await client.get("/api/v1/medications", headers=headers)
        assert del_resp.status_code == status.HTTP_204_NO_CONTENT
        assert all(m["id"] != med_id for m in list_resp.json())

    async def test_update_other_user_medication_returns_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token_a = await _signup_and_login(client, "med_owner@example.com", "01044440005")
            token_b = await _signup_and_login(client, "med_intruder@example.com", "01044440006")
            create_resp = await client.post(
                "/api/v1/medications",
                json={"medications": [{"name": "메토트렉세이트", "drug_class": "IMMUNOSUPPRESSANT"}]},
                headers={"Authorization": f"Bearer {token_a}"},
            )
            med_id = create_resp.json()[0]["id"]
            resp = await client.patch(
                f"/api/v1/medications/{med_id}",
                json={"note": "침입"},
                headers={"Authorization": f"Bearer {token_b}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_other_user_medication_returns_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token_a = await _signup_and_login(client, "med_owner2@example.com", "01044440007")
            token_b = await _signup_and_login(client, "med_intruder2@example.com", "01044440008")
            create_resp = await client.post(
                "/api/v1/medications",
                json={"medications": [{"name": "프레드니솔론", "drug_class": "STEROID"}]},
                headers={"Authorization": f"Bearer {token_a}"},
            )
            med_id = create_resp.json()[0]["id"]
            resp = await client.delete(
                f"/api/v1/medications/{med_id}",
                headers={"Authorization": f"Bearer {token_b}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_list_medications_unauthorized(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get("/api/v1/medications")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
