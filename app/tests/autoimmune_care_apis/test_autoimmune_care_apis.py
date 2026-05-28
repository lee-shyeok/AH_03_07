from urllib.parse import quote

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app
from app.services.autoimmune_care_service import AUTOIMMUNE_NOTES_BY_DRUG_CLASS

BASE_URL = "http://test"


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    signup_data = {
        "email": email,
        "password": "Password123!",
        "name": "케어테스터",
        "gender": "FEMALE",
        "birth_date": "1992-03-15",
        "phone_number": phone,
    }
    await client.post("/api/v1/auth/signup", json=signup_data)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    return resp.json()["access_token"]


class TestMedicationCardApis(TestCase):
    async def test_no_medications_returns_empty_cards(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "card_empty@example.com", "01033330001")
            resp = await client.get(
                "/api/v1/medication-cards",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["cards"] == []

    async def test_cards_contain_user_medication_data(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "card_data@example.com", "01033330002")
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(
                "/api/v1/medications",
                json={
                    "medications": [
                        {
                            "name": "메토트렉세이트",
                            "drug_class": "IMMUNOSUPPRESSANT",
                            "is_injection": False,
                            "note": "주 1회 복용",
                        }
                    ]
                },
                headers=headers,
            )
            resp = await client.get("/api/v1/medication-cards", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        cards = resp.json()["cards"]
        assert len(cards) == 1
        card = cards[0]
        assert card["name"] == "메토트렉세이트"
        assert card["user_note"] == "주 1회 복용"
        assert quote("메토트렉세이트") in card["official_source_url"]
        assert len(card["discontinuation_notice"]) > 0
        assert len(card["consultation_checklist"]) > 0
        assert len(card["reference_sources"]) > 0

    async def test_other_user_medications_not_in_cards(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token_a = await _signup_and_login(client, "card_owner@example.com", "01033330003")
            token_b = await _signup_and_login(client, "card_other@example.com", "01033330004")
            await client.post(
                "/api/v1/medications",
                json={"medications": [{"name": "프레드니솔론", "drug_class": "STEROID", "is_injection": False}]},
                headers={"Authorization": f"Bearer {token_a}"},
            )
            resp = await client.get(
                "/api/v1/medication-cards",
                headers={"Authorization": f"Bearer {token_b}"},
            )
        assert resp.json()["cards"] == []

    async def test_unauthenticated_returns_401(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get("/api/v1/medication-cards")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_medication_card_includes_autoimmune_notes(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "notes_steroid@example.com", "01033330009")
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(
                "/api/v1/medications",
                json={"medications": [{"name": "프레드니솔론", "drug_class": "STEROID", "is_injection": False}]},
                headers=headers,
            )
            resp = await client.get("/api/v1/medication-cards", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        card = resp.json()["cards"][0]
        assert len(card["autoimmune_notes"]) > 0
        assert "스테로이드" in card["autoimmune_notes"][0]

    async def test_autoimmune_notes_match_drug_class(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "notes_match@example.com", "01033330010")
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(
                "/api/v1/medications",
                json={
                    "medications": [
                        {"name": "메토트렉세이트", "drug_class": "IMMUNOSUPPRESSANT", "is_injection": False},
                        {"name": "하이드록시클로로퀸", "drug_class": "ANTIMALARIAL", "is_injection": False},
                        {"name": "아달리무맙", "drug_class": "BIOLOGIC", "is_injection": True},
                        {"name": "이부프로펜", "drug_class": "NSAID", "is_injection": False},
                    ]
                },
                headers=headers,
            )
            resp = await client.get("/api/v1/medication-cards", headers=headers)
        from app.models.user_medication import DrugClass

        cards = resp.json()["cards"]
        for card in cards:
            dc = DrugClass(card["drug_class"])
            expected = AUTOIMMUNE_NOTES_BY_DRUG_CLASS.get(dc, [])
            assert card["autoimmune_notes"] == expected


class TestAutoImmuneNotesSafety(TestCase):
    async def test_autoimmune_notes_have_no_forbidden_terms(self):
        forbidden = ["악화", "진단", "처방", "약 조절", "비대면 진료", "의사 매칭"]
        for dc, notes in AUTOIMMUNE_NOTES_BY_DRUG_CLASS.items():
            for note in notes:
                for term in forbidden:
                    assert term not in note, f"금지 표현 '{term}' 발견 — {dc}: {note!r}"


class TestPregnancySafetyApis(TestCase):
    async def test_pregnant_status_returns_applicable_true(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "preg_yes@example.com", "01033330005")
            headers = {"Authorization": f"Bearer {token}"}
            await client.put(
                "/api/v1/users/me/risk-profile",
                json={"pregnancy_status": "PREGNANT"},
                headers=headers,
            )
            resp = await client.get("/api/v1/pregnancy-safety", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["applicable"] is True
        assert body["pregnancy_status"] == "PREGNANT"
        assert body["consultation_notice"] is not None
        assert body["general_safety_info"] is not None
        assert body["disclaimer"] is not None

    async def test_none_status_returns_applicable_false(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "preg_none@example.com", "01033330006")
            headers = {"Authorization": f"Bearer {token}"}
            await client.put(
                "/api/v1/users/me/risk-profile",
                json={"pregnancy_status": "NONE"},
                headers=headers,
            )
            resp = await client.get("/api/v1/pregnancy-safety", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["applicable"] is False
        assert body["consultation_notice"] is None
        assert body["general_safety_info"] is None
        assert body["disclaimer"] is None

    async def test_no_profile_returns_applicable_false(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "preg_noprofile@example.com", "01033330007")
            resp = await client.get(
                "/api/v1/pregnancy-safety",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["applicable"] is False

    async def test_unauthenticated_returns_401(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get("/api/v1/pregnancy-safety")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestVaccinePreventionApis(TestCase):
    async def test_returns_vaccines_and_disclaimer(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "vaccine_info@example.com", "01033330008")
            resp = await client.get(
                "/api/v1/vaccine-prevention-info",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert len(body["recommended_vaccines"]) > 0
        assert len(body["disclaimer"]) > 0
        assert "의료진" in body["disclaimer"]

    async def test_unauthenticated_returns_401(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get("/api/v1/vaccine-prevention-info")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
