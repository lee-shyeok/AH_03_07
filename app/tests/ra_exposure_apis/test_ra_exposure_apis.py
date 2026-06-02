from datetime import date, timedelta

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

BASE_URL = "http://test"
ENDPOINT = "/api/v1/ra-exposure-triggers"


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "Password123!",
            "name": "RA테스터",
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


async def _register_ra_disease(client: AsyncClient, headers: dict) -> None:
    await client.post(
        "/api/v1/diseases",
        json={"diseases": [{"disease_code": "RA"}]},
        headers=headers,
    )


async def _upsert_activity_log(client: AsyncClient, headers: dict, log_date: str, **fields) -> None:
    body = {
        "log_date": log_date,
        "pain_vas": 3,
        "fatigue": 3,
        "daily_difficulty": 3,
        **fields,
    }
    await client.post("/api/v1/activity-logs", json=body, headers=headers)


class TestRAExposureApis(TestCase):
    async def test_not_ra_patient_returns_applicable_false(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "ra_none@example.com", "01090000001")
            resp = await client.get(ENDPOINT, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["applicable"] is False
        assert data["triggers"] == []

    async def test_only_ra_registered_returns_disease_registered_only(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "ra_only@example.com", "01090000002")
            headers = {"Authorization": f"Bearer {token}"}
            await _register_ra_disease(client, headers)
            resp = await client.get(ENDPOINT, headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["applicable"] is True
        codes = [t["code"] for t in data["triggers"]]
        assert codes == ["DISEASE_REGISTERED"]

    async def test_morning_stiffness_30min_triggers(self):
        today = date.today().isoformat()
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "ra_stiff@example.com", "01090000003")
            headers = {"Authorization": f"Bearer {token}"}
            await _register_ra_disease(client, headers)
            await _upsert_activity_log(client, headers, today, morning_stiffness_minutes=30)
            resp = await client.get(ENDPOINT, headers=headers)
        data = resp.json()
        codes = [t["code"] for t in data["triggers"]]
        assert "MORNING_STIFFNESS_HIGH" in codes
        trigger = next(t for t in data["triggers"] if t["code"] == "MORNING_STIFFNESS_HIGH")
        assert trigger["context"]["value"] == 30

    async def test_fatigue_consecutive_3days_triggers(self):
        today = date.today()
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "ra_fatigue@example.com", "01090000004")
            headers = {"Authorization": f"Bearer {token}"}
            await _register_ra_disease(client, headers)
            for i in range(3):
                log_date = (today - timedelta(days=i)).isoformat()
                await _upsert_activity_log(client, headers, log_date, fatigue=7)
            resp = await client.get(ENDPOINT, headers=headers)
        codes = [t["code"] for t in resp.json()["triggers"]]
        assert "FATIGUE_CONSECUTIVE_HIGH" in codes

    async def test_fatigue_not_consecutive_does_not_trigger(self):
        today = date.today()
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "ra_fatigue_gap@example.com", "01090000005")
            headers = {"Authorization": f"Bearer {token}"}
            await _register_ra_disease(client, headers)
            # 5/25, 5/26, 5/28 — 날짜 불연속
            for days_ago in [0, 2, 3]:
                log_date = (today - timedelta(days=days_ago)).isoformat()
                await _upsert_activity_log(client, headers, log_date, fatigue=7)
            resp = await client.get(ENDPOINT, headers=headers)
        codes = [t["code"] for t in resp.json()["triggers"]]
        assert "FATIGUE_CONSECUTIVE_HIGH" not in codes

    async def test_joint_swelling_change_triggers(self):
        today = date.today()
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "ra_swelling@example.com", "01090000006")
            headers = {"Authorization": f"Bearer {token}"}
            await _register_ra_disease(client, headers)
            await _upsert_activity_log(
                client,
                headers,
                (today - timedelta(days=1)).isoformat(),
                joint_swelling_areas=["LEFT_KNEE"],
            )
            await _upsert_activity_log(
                client,
                headers,
                today.isoformat(),
                joint_swelling_areas=["RIGHT_WRIST"],
            )
            resp = await client.get(ENDPOINT, headers=headers)
        codes = [t["code"] for t in resp.json()["triggers"]]
        assert "JOINT_SWELLING_CHANGED" in codes

    async def test_ra_medication_triggers(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "ra_med@example.com", "01090000007")
            headers = {"Authorization": f"Bearer {token}"}
            await _register_ra_disease(client, headers)
            await client.post(
                "/api/v1/user-medications",
                json={
                    "medications": [
                        {"name": "메토트렉세이트", "drug_class": "IMMUNOSUPPRESSANT", "is_injection": False}
                    ]
                },
                headers=headers,
            )
            resp = await client.get(ENDPOINT, headers=headers)
        data = resp.json()
        codes = [t["code"] for t in data["triggers"]]
        assert "RA_MEDICATION_REGISTERED" in codes
        trigger = next(t for t in data["triggers"] if t["code"] == "RA_MEDICATION_REGISTERED")
        assert "메토트렉세이트" in trigger["context"]["medication_names"]

    async def test_injection_triggers(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "ra_injection@example.com", "01090000008")
            headers = {"Authorization": f"Bearer {token}"}
            await _register_ra_disease(client, headers)
            await client.post(
                "/api/v1/user-medications",
                json={"medications": [{"name": "아달리무맙", "drug_class": "BIOLOGIC", "is_injection": True}]},
                headers=headers,
            )
            resp = await client.get(ENDPOINT, headers=headers)
        codes = [t["code"] for t in resp.json()["triggers"]]
        assert "INJECTION_REGISTERED" in codes

    async def test_red_flag_symptom_triggers_escalation(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "ra_redflag@example.com", "01090000009")
            headers = {"Authorization": f"Bearer {token}"}
            await _register_ra_disease(client, headers)
            await client.post(
                "/api/v1/symptom-checks",
                json={"checked_symptoms": ["DYSPNEA"]},
                headers=headers,
            )
            resp = await client.get(ENDPOINT, headers=headers)
        codes = [t["code"] for t in resp.json()["triggers"]]
        assert "SYMPTOM_ESCALATION" in codes

    async def test_unauthenticated_returns_401(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get(ENDPOINT)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_response_labels_have_no_forbidden_terms(self):
        today = date.today()
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "ra_safety@example.com", "01090000010")
            headers = {"Authorization": f"Bearer {token}"}
            await _register_ra_disease(client, headers)
            await _upsert_activity_log(client, headers, today.isoformat(), morning_stiffness_minutes=45, pain_vas=9)
            for i in range(3):
                await _upsert_activity_log(
                    client,
                    headers,
                    (today - timedelta(days=i)).isoformat(),
                    fatigue=8,
                )
            await client.post(
                "/api/v1/user-medications",
                json={"medications": [{"name": "프레드니솔론", "drug_class": "STEROID", "is_injection": True}]},
                headers=headers,
            )
            await client.post(
                "/api/v1/symptom-checks",
                json={"checked_symptoms": ["DYSPNEA"]},
                headers=headers,
            )
            resp = await client.get(ENDPOINT, headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        body_text = resp.text
        for forbidden in ["악화", "진단", "약 조절", "처방"]:
            assert forbidden not in body_text, f"금지 표현 '{forbidden}' 응답에서 발견됨"
