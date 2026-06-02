from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.main import app
from app.services.diary_logs import DiaryLogService

BASE_URL = "http://test"
DIARY_PDF_URL = "/api/v1/diary/pdf"
FAKE_PDF = b"%PDF-1.4 fake-diary"


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "Password123!",
            "name": "다이어리테스터",
            "gender": "FEMALE",
            "birth_date": "1990-01-01",
            "phone_number": phone,
        },
    )
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    token = resp.json()["access_token"]
    await client.post(
        "/api/v1/users/me/consents",
        json={"consent_type": "MEDICAL_DATA", "agreed": True, "version": "1.0"},
        headers={"Authorization": f"Bearer {token}"},
    )
    return token


def _patch_pdf(return_value=FAKE_PDF, side_effect=None):
    return patch.object(
        DiaryLogService,
        "generate_pdf_bytes",
        AsyncMock(return_value=return_value, side_effect=side_effect),
    )


class TestDiaryPdfApi(TestCase):
    async def test_200_returns_pdf_content_type(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "diary_pdf_ok@example.com", "01099990001")
            with _patch_pdf():
                resp = await client.get(DIARY_PDF_URL, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content == FAKE_PDF

    async def test_200_content_disposition_attachment(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "diary_pdf_cd@example.com", "01099990002")
            with _patch_pdf():
                resp = await client.get(DIARY_PDF_URL, headers={"Authorization": f"Bearer {token}"})
        assert "attachment" in resp.headers.get("content-disposition", "")
        assert "diary.pdf" in resp.headers.get("content-disposition", "")

    async def test_401_without_auth(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.get(DIARY_PDF_URL)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
