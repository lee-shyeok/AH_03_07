from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app

BASE_URL = "http://test"
PDF_ENDPOINT = "/api/v1/pre-consultation-reports/pdf"


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    signup_data = {
        "email": email,
        "password": "Password123!",
        "name": "리포트테스터",
        "gender": "FEMALE",
        "birth_date": "1988-11-11",
        "phone_number": phone,
    }
    await client.post("/api/v1/auth/signup", json=signup_data)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    return resp.json()["access_token"]


class TestPreConsultationReportApis(TestCase):
    async def test_generates_pdf_200(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "report_basic@example.com", "01055550001")
            resp = await client.post(
                PDF_ENDPOINT,
                json={},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:4] == b"%PDF"
        assert len(resp.content) > 0

    async def test_questions_included_no_error(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "report_questions@example.com", "01055550002")
            resp = await client.post(
                PDF_ENDPOINT,
                json={"questions": ["현재 약 조절이 필요할까요?", "다음 검사는 언제 받아야 하나요?"]},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.content[:4] == b"%PDF"

    async def test_period_days_boundary_valid(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "report_period@example.com", "01055550003")
            headers = {"Authorization": f"Bearer {token}"}
            resp_min = await client.post(PDF_ENDPOINT, json={"period_days": 1}, headers=headers)
            resp_max = await client.post(PDF_ENDPOINT, json={"period_days": 90}, headers=headers)
        assert resp_min.status_code == status.HTTP_200_OK
        assert resp_max.status_code == status.HTTP_200_OK

    async def test_period_days_out_of_range_returns_422(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "report_invalid@example.com", "01055550004")
            headers = {"Authorization": f"Bearer {token}"}
            resp_zero = await client.post(PDF_ENDPOINT, json={"period_days": 0}, headers=headers)
            resp_over = await client.post(PDF_ENDPOINT, json={"period_days": 200}, headers=headers)
        assert resp_zero.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert resp_over.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_with_medication_data_returns_pdf(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "report_meddata@example.com", "01055550005")
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(
                "/api/v1/medications",
                json={
                    "medications": [{"name": "히드록시클로로퀸", "drug_class": "ANTIMALARIAL", "is_injection": False}]
                },
                headers=headers,
            )
            resp = await client.post(PDF_ENDPOINT, json={}, headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.content[:4] == b"%PDF"
        assert len(resp.content) > 1000

    async def test_cross_user_isolation(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token_a = await _signup_and_login(client, "report_owner@example.com", "01055550006")
            token_b = await _signup_and_login(client, "report_other@example.com", "01055550007")
            await client.post(
                "/api/v1/medications",
                json={
                    "medications": [
                        {"name": "비밀약물XYZ", "drug_class": "STEROID", "is_injection": False},
                        {"name": "비밀약물ABC", "drug_class": "BIOLOGIC", "is_injection": True},
                        {"name": "비밀약물DEF", "drug_class": "NSAID", "is_injection": False},
                    ]
                },
                headers={"Authorization": f"Bearer {token_a}"},
            )
            resp_a = await client.post(PDF_ENDPOINT, json={}, headers={"Authorization": f"Bearer {token_a}"})
            resp_b = await client.post(PDF_ENDPOINT, json={}, headers={"Authorization": f"Bearer {token_b}"})
        assert resp_b.status_code == status.HTTP_200_OK
        assert resp_b.content[:4] == b"%PDF"
        # 사용자 A는 약물 3건이 있으므로 PDF가 B보다 커야 함 — B에 A 데이터가 섞이지 않음을 확인
        assert len(resp_b.content) < len(resp_a.content)

    async def test_unauthenticated_returns_401(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.post(PDF_ENDPOINT, json={})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
