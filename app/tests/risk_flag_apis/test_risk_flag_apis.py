from __future__ import annotations

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

BASE_URL = "http://test"
SYMPTOM_EP = "/api/v1/symptom-checks"
FLAGS_EP = "/api/v1/risk-flags"


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "Password123!",
            "name": "플래그테스터",
            "gender": "FEMALE",
            "birth_date": "1990-01-01",
            "phone_number": phone,
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    return resp.json()["access_token"]


class TestRiskFlagApis(TestCase):
    async def test_unauthenticated_get_returns_401(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get(FLAGS_EP)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_no_flags_returns_empty_list(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "rf_empty@example.com", "01092000001")
            resp = await client.get(FLAGS_EP, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == []

    async def test_symptom_check_with_gate_match_returns_risk_flag_ids(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "rf_create@example.com", "01092000002")
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.post(
                SYMPTOM_EP,
                json={"checked_symptoms": ["DYSPNEA"]},
                headers=headers,
            )
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert "risk_flag_ids" in data
        assert len(data["risk_flag_ids"]) > 0

    async def test_get_flags_after_symptom_check(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "rf_list@example.com", "01092000003")
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(
                SYMPTOM_EP,
                json={"checked_symptoms": ["DYSPNEA"]},
                headers=headers,
            )
            resp = await client.get(FLAGS_EP, headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        flags = resp.json()
        assert len(flags) > 0
        flag = flags[0]
        assert flag["source_type"] == "SYMPTOM_CHECK"
        assert flag["status"] == "ACTIVE"
        assert flag["flag_code"] == "DYSPNEA"

    async def test_list_flags_filter_by_status(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "rf_filter@example.com", "01092000004")
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(
                SYMPTOM_EP,
                json={"checked_symptoms": ["DYSPNEA"]},
                headers=headers,
            )
            active_resp = await client.get(f"{FLAGS_EP}?flag_status=ACTIVE", headers=headers)
            resolved_resp = await client.get(f"{FLAGS_EP}?flag_status=RESOLVED", headers=headers)
        assert len(active_resp.json()) > 0
        assert resolved_resp.json() == []

    async def test_get_flag_detail(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "rf_detail@example.com", "01092000005")
            headers = {"Authorization": f"Bearer {token}"}
            create_resp = await client.post(
                SYMPTOM_EP,
                json={"checked_symptoms": ["DYSPNEA"]},
                headers=headers,
            )
            flag_id = create_resp.json()["risk_flag_ids"][0]
            resp = await client.get(f"{FLAGS_EP}/{flag_id}", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["id"] == flag_id
        assert data["flag_code"] == "DYSPNEA"
        assert data["red_flag"] is True

    async def test_get_nonexistent_flag_returns_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "rf_404@example.com", "01092000006")
            resp = await client.get(f"{FLAGS_EP}/99999", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_patch_flag_status_to_resolved(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "rf_patch@example.com", "01092000007")
            headers = {"Authorization": f"Bearer {token}"}
            create_resp = await client.post(
                SYMPTOM_EP,
                json={"checked_symptoms": ["DYSPNEA"]},
                headers=headers,
            )
            flag_id = create_resp.json()["risk_flag_ids"][0]
            resp = await client.patch(
                f"{FLAGS_EP}/{flag_id}",
                json={"status": "RESOLVED"},
                headers=headers,
            )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["status"] == "RESOLVED"

    async def test_patch_status_active_returns_422(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "rf_422@example.com", "01092000008")
            headers = {"Authorization": f"Bearer {token}"}
            create_resp = await client.post(
                SYMPTOM_EP,
                json={"checked_symptoms": ["DYSPNEA"]},
                headers=headers,
            )
            flag_id = create_resp.json()["risk_flag_ids"][0]
            resp = await client.patch(
                f"{FLAGS_EP}/{flag_id}",
                json={"status": "ACTIVE"},
                headers=headers,
            )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_duplicate_symptom_check_no_duplicate_flag(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "rf_dup@example.com", "01092000009")
            headers = {"Authorization": f"Bearer {token}"}
            resp1 = await client.post(
                SYMPTOM_EP,
                json={"checked_symptoms": ["DYSPNEA"]},
                headers=headers,
            )
            resp2 = await client.post(
                SYMPTOM_EP,
                json={"checked_symptoms": ["DYSPNEA"]},
                headers=headers,
            )
            all_flags = await client.get(FLAGS_EP, headers=headers)
        dyspnea_flags = [f for f in all_flags.json() if f["flag_code"] == "DYSPNEA"]
        assert len(resp1.json()["risk_flag_ids"]) > 0
        assert resp2.json()["risk_flag_ids"] == []
        assert len(dyspnea_flags) == 1

    async def test_non_red_flag_gate_symptom_creates_flag_without_emergency(self):
        """gate에 등록된 non-red-flag 증상(SHINGLES_SUSPECTED)은 risk_flag를 생성하되
        red_flag_symptoms(응급 증상 목록)에는 포함되지 않는다."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "rf_nomatch@example.com", "01092000010")
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.post(
                SYMPTOM_EP,
                json={"checked_symptoms": ["SHINGLES_SUSPECTED"]},
                headers=headers,
            )
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert len(data["risk_flag_ids"]) > 0
        assert "SHINGLES_SUSPECTED" not in data.get("red_flag_symptoms", [])

    async def test_other_users_flag_returns_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token_a = await _signup_and_login(client, "rf_own_a@example.com", "01092000011")
            token_b = await _signup_and_login(client, "rf_own_b@example.com", "01092000012")
            headers_a = {"Authorization": f"Bearer {token_a}"}
            headers_b = {"Authorization": f"Bearer {token_b}"}
            create_resp = await client.post(
                SYMPTOM_EP,
                json={"checked_symptoms": ["DYSPNEA"]},
                headers=headers_a,
            )
            flag_id = create_resp.json()["risk_flag_ids"][0]
            get_resp = await client.get(f"{FLAGS_EP}/{flag_id}", headers=headers_b)
            patch_resp = await client.patch(
                f"{FLAGS_EP}/{flag_id}",
                json={"status": "RESOLVED"},
                headers=headers_b,
            )
        assert get_resp.status_code == status.HTTP_404_NOT_FOUND
        assert patch_resp.status_code == status.HTTP_404_NOT_FOUND
