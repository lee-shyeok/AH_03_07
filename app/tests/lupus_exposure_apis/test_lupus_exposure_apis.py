from datetime import date, timedelta

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app
from app.models.lupus_skin_log import LupusSkinLog, LupusSkinSymptomType
from app.models.users import User

BASE_URL = "http://test"
ENDPOINT = "/api/v1/lupus-exposure-triggers"


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "Password123!",
            "name": "루푸스테스터",
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


async def _register_sle_disease(client: AsyncClient, headers: dict) -> None:
    await client.post(
        "/api/v1/diseases",
        json={"diseases": [{"disease_code": "SLE"}]},
        headers=headers,
    )


async def _upsert_activity_log(client: AsyncClient, headers: dict, log_date: str, **fields) -> None:
    body = {
        "pain_vas": 3,
        "fatigue": 3,
        "daily_difficulty": 3,
        **fields,
    }
    await client.put(f"/api/v1/activity-logs/{log_date}", json=body, headers=headers)


async def _create_skin_log(email: str, symptom_type: LupusSkinSymptomType = LupusSkinSymptomType.RASH) -> None:
    user = await User.get(email=email)
    await LupusSkinLog.create(user=user, symptom_type=symptom_type, log_date=date.today())


class TestLupusExposureApis(TestCase):
    async def test_unauthenticated_returns_401(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get(ENDPOINT)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_not_sle_patient_returns_applicable_false(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sle_none@example.com", "01091000001")
            resp = await client.get(ENDPOINT, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["applicable"] is False
        assert data["triggers"] == []

    async def test_only_sle_registered_returns_disease_registered_with_uv_guide(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sle_only@example.com", "01091000002")
            headers = {"Authorization": f"Bearer {token}"}
            await _register_sle_disease(client, headers)
            resp = await client.get(ENDPOINT, headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["applicable"] is True
        codes = [t["code"] for t in data["triggers"]]
        assert codes == ["DISEASE_REGISTERED"]
        trigger = data["triggers"][0]
        assert "UV_PROTECTION_GUIDE" in trigger["exposure_targets"]

    async def test_skin_symptom_logged_triggers(self):
        email = "sle_skin@example.com"
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, email, "01091000003")
            headers = {"Authorization": f"Bearer {token}"}
            await _register_sle_disease(client, headers)
        await _create_skin_log(email, LupusSkinSymptomType.RASH)
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get(ENDPOINT, headers={"Authorization": f"Bearer {token}"})
        codes = [t["code"] for t in resp.json()["triggers"]]
        assert "SKIN_SYMPTOM_LOGGED" in codes

    async def test_fatigue_consecutive_3days_triggers(self):
        today = date.today()
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sle_fatigue@example.com", "01091000004")
            headers = {"Authorization": f"Bearer {token}"}
            await _register_sle_disease(client, headers)
            for i in range(3):
                log_date = (today - timedelta(days=i)).isoformat()
                await _upsert_activity_log(client, headers, log_date, fatigue=7)
            resp = await client.get(ENDPOINT, headers=headers)
        codes = [t["code"] for t in resp.json()["triggers"]]
        assert "FATIGUE_CONSECUTIVE_HIGH" in codes

    async def test_fatigue_not_consecutive_does_not_trigger(self):
        today = date.today()
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sle_fatigue_gap@example.com", "01091000005")
            headers = {"Authorization": f"Bearer {token}"}
            await _register_sle_disease(client, headers)
            for days_ago in [0, 2, 3]:
                log_date = (today - timedelta(days=days_ago)).isoformat()
                await _upsert_activity_log(client, headers, log_date, fatigue=7)
            resp = await client.get(ENDPOINT, headers=headers)
        codes = [t["code"] for t in resp.json()["triggers"]]
        assert "FATIGUE_CONSECUTIVE_HIGH" not in codes

    async def test_sle_medication_triggers(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sle_med@example.com", "01091000006")
            headers = {"Authorization": f"Bearer {token}"}
            await _register_sle_disease(client, headers)
            await client.post(
                "/api/v1/user-medications",
                json={"medications": [{"name": "프레드니솔론", "drug_class": "STEROID", "is_injection": False}]},
                headers=headers,
            )
            resp = await client.get(ENDPOINT, headers=headers)
        data = resp.json()
        codes = [t["code"] for t in data["triggers"]]
        assert "SLE_MEDICATION_REGISTERED" in codes
        trigger = next(t for t in data["triggers"] if t["code"] == "SLE_MEDICATION_REGISTERED")
        assert "프레드니솔론" in trigger["context"]["medication_names"]

    async def test_antimalarial_adds_ophthalmology_screening_target(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sle_hcq@example.com", "01091000007")
            headers = {"Authorization": f"Bearer {token}"}
            await _register_sle_disease(client, headers)
            await client.post(
                "/api/v1/user-medications",
                json={
                    "medications": [{"name": "하이드록시클로로퀸", "drug_class": "ANTIMALARIAL", "is_injection": False}]
                },
                headers=headers,
            )
            resp = await client.get(ENDPOINT, headers=headers)
        data = resp.json()
        trigger = next(t for t in data["triggers"] if t["code"] == "SLE_MEDICATION_REGISTERED")
        assert "OPHTHALMOLOGY_SCREENING_PROMPT" in trigger["exposure_targets"]

    async def test_injection_triggers(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sle_injection@example.com", "01091000008")
            headers = {"Authorization": f"Bearer {token}"}
            await _register_sle_disease(client, headers)
            await client.post(
                "/api/v1/user-medications",
                json={"medications": [{"name": "벨리무맙", "drug_class": "BIOLOGIC", "is_injection": True}]},
                headers=headers,
            )
            resp = await client.get(ENDPOINT, headers=headers)
        codes = [t["code"] for t in resp.json()["triggers"]]
        assert "INJECTION_REGISTERED" in codes

    async def test_symptom_escalation_triggers(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "sle_redflag@example.com", "01091000009")
            headers = {"Authorization": f"Bearer {token}"}
            await _register_sle_disease(client, headers)
            await client.post(
                "/api/v1/symptom-checks",
                json={"checked_symptoms": ["DYSPNEA"]},
                headers=headers,
            )
            resp = await client.get(ENDPOINT, headers=headers)
        codes = [t["code"] for t in resp.json()["triggers"]]
        assert "SYMPTOM_ESCALATION" in codes

    async def test_multiple_triggers_all_present(self):
        email = "sle_all@example.com"
        today = date.today()
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, email, "01091000010")
            headers = {"Authorization": f"Bearer {token}"}
            await _register_sle_disease(client, headers)
            for i in range(3):
                await _upsert_activity_log(client, headers, (today - timedelta(days=i)).isoformat(), fatigue=8)
            await client.post(
                "/api/v1/user-medications",
                json={
                    "medications": [
                        {"name": "하이드록시클로로퀸", "drug_class": "ANTIMALARIAL", "is_injection": False},
                        {"name": "벨리무맙", "drug_class": "BIOLOGIC", "is_injection": True},
                    ]
                },
                headers=headers,
            )
            await client.post(
                "/api/v1/symptom-checks",
                json={"checked_symptoms": ["DYSPNEA"]},
                headers=headers,
            )
        await _create_skin_log(email, LupusSkinSymptomType.ORAL_ULCER)
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get(ENDPOINT, headers={"Authorization": f"Bearer {token}"})
        codes = [t["code"] for t in resp.json()["triggers"]]
        assert "DISEASE_REGISTERED" in codes
        assert "SKIN_SYMPTOM_LOGGED" in codes
        assert "FATIGUE_CONSECUTIVE_HIGH" in codes
        assert "SLE_MEDICATION_REGISTERED" in codes
        assert "INJECTION_REGISTERED" in codes
        assert "SYMPTOM_ESCALATION" in codes

    async def test_response_labels_have_no_forbidden_terms(self):
        email = "sle_safety@example.com"
        today = date.today()
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, email, "01091000011")
            headers = {"Authorization": f"Bearer {token}"}
            await _register_sle_disease(client, headers)
            for i in range(3):
                await _upsert_activity_log(
                    client, headers, (today - timedelta(days=i)).isoformat(), fatigue=9, pain_vas=9
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
        await _create_skin_log(email, LupusSkinSymptomType.HAIR_LOSS)
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get(ENDPOINT, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == status.HTTP_200_OK
        body_text = resp.text
        for forbidden in ["악화", "진단", "약 조절", "처방"]:
            assert forbidden not in body_text, f"금지 표현 '{forbidden}' 응답에서 발견됨"
