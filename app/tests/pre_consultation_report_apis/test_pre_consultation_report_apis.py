from datetime import date
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient
from starlette import status
from tortoise.contrib.test import TestCase

from app.apis.v1.pre_consultation_report_routers import _run_report_job
from app.dtos.pre_consultation_report import PreConsultationReportRequest
from app.main import app
from app.models.pre_consultation_report import PreConsultationReport, ReportStatus
from app.models.users import User
from app.services.pre_consultation_report_service import PreConsultationReportService

BASE_URL = "http://test"
PRE_VISIT = "/api/v1/reports/pre-visit"
FAKE_PDF = b"%PDF-1.4 test"


def _report_url(report_id: int) -> str:
    return f"/api/v1/reports/{report_id}"


def _share_url(report_id: int) -> str:
    return f"/api/v1/reports/{report_id}/share"


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


def _patch_pdf(return_value=FAKE_PDF, side_effect=None):
    return patch.object(
        PreConsultationReportService,
        "generate_pdf",
        AsyncMock(return_value=return_value, side_effect=side_effect),
    )


class TestRunReportJob(TestCase):
    async def test_success_sets_completed_and_pdf(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            await _signup_and_login(client, "runner_ok@example.com", "01055550010")
        user = await User.get(email="runner_ok@example.com")
        report = await PreConsultationReport.create(
            user_id=user.id,
            status=ReportStatus.PENDING,
            visit_date=date(2026, 7, 1),
            period_days=30,
        )
        request = PreConsultationReportRequest(visit_date=date(2026, 7, 1))
        with _patch_pdf():
            await _run_report_job(report.id, request)
        refreshed = await PreConsultationReport.get(id=report.id)
        assert refreshed.status == ReportStatus.COMPLETED
        assert refreshed.pdf == FAKE_PDF

    async def test_failure_sets_failed_with_error(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            await _signup_and_login(client, "runner_fail@example.com", "01055550011")
        user = await User.get(email="runner_fail@example.com")
        report = await PreConsultationReport.create(
            user_id=user.id,
            status=ReportStatus.PENDING,
            visit_date=date(2026, 7, 1),
            period_days=30,
        )
        request = PreConsultationReportRequest(visit_date=date(2026, 7, 1))
        with _patch_pdf(side_effect=RuntimeError("boom")):
            await _run_report_job(report.id, request)
        refreshed = await PreConsultationReport.get(id=report.id)
        assert refreshed.status == ReportStatus.FAILED
        assert refreshed.error_message is not None

    async def test_missing_report_returns_silently(self):
        request = PreConsultationReportRequest(visit_date=date(2026, 7, 1))
        # 존재하지 않는 id — 예외 없이 그냥 return 해야 함
        await _run_report_job(99999999, request)


class TestPreConsultationReportApis(TestCase):
    async def test_create_pre_visit_202_then_completed(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "report_create@example.com", "01055550012")
            headers = {"Authorization": f"Bearer {token}"}
            with _patch_pdf():
                resp = await client.post(PRE_VISIT, json={"visit_date": "2026-07-01"}, headers=headers)
            assert resp.status_code == status.HTTP_202_ACCEPTED
            body = resp.json()
            assert body["status"] == ReportStatus.PENDING.value
            report_id = body["report_id"]
            # ASGITransport에서 BackgroundTask가 응답 시점에 실행됨 → 이미 COMPLETED
            resp2 = await client.get(_report_url(report_id), headers=headers)
        assert resp2.status_code == status.HTTP_200_OK
        data = resp2.json()
        assert data["status"] == ReportStatus.COMPLETED.value
        assert data["pdf_base64"] is not None

    async def test_get_other_user_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token_a = await _signup_and_login(client, "report_a@example.com", "01055550013")
            token_b = await _signup_and_login(client, "report_b@example.com", "01055550014")
            with _patch_pdf():
                resp = await client.post(
                    PRE_VISIT,
                    json={"visit_date": "2026-07-01"},
                    headers={"Authorization": f"Bearer {token_a}"},
                )
            report_id = resp.json()["report_id"]
            resp_b = await client.get(
                _report_url(report_id),
                headers={"Authorization": f"Bearer {token_b}"},
            )
        assert resp_b.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_not_found_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "report_missing@example.com", "01055550015")
            resp = await client.get(
                _report_url(99999999),
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_share_201_returns_token(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "report_share@example.com", "01055550016")
            headers = {"Authorization": f"Bearer {token}"}
            with _patch_pdf():
                resp = await client.post(PRE_VISIT, json={"visit_date": "2026-07-01"}, headers=headers)
            report_id = resp.json()["report_id"]
            resp_share = await client.post(
                _share_url(report_id),
                json={"recipient_email": "doctor@example.com"},
                headers=headers,
            )
        assert resp_share.status_code == status.HTTP_201_CREATED
        assert resp_share.json()["secure_link_token"]

    async def test_share_not_completed_409(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "report_notready@example.com", "01055550017")
            user = await User.get(email="report_notready@example.com")
            report = await PreConsultationReport.create(
                user_id=user.id,
                status=ReportStatus.PENDING,
                visit_date=date(2026, 7, 1),
                period_days=30,
            )
            resp = await client.post(
                _share_url(report.id),
                json={"recipient_email": "doctor@example.com"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_409_CONFLICT

    async def test_share_other_user_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token_a = await _signup_and_login(client, "report_owner2@example.com", "01055550018")
            token_b = await _signup_and_login(client, "report_other2@example.com", "01055550019")
            with _patch_pdf():
                resp = await client.post(
                    PRE_VISIT,
                    json={"visit_date": "2026-07-01"},
                    headers={"Authorization": f"Bearer {token_a}"},
                )
            report_id = resp.json()["report_id"]
            resp_b = await client.post(
                _share_url(report_id),
                json={"recipient_email": "doctor@example.com"},
                headers={"Authorization": f"Bearer {token_b}"},
            )
        assert resp_b.status_code == status.HTTP_404_NOT_FOUND

    async def test_unauthenticated_401(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            resp = await client.post(PRE_VISIT, json={"visit_date": "2026-07-01"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_missing_visit_date_422(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "report_novisit@example.com", "01055550020")
            resp = await client.post(PRE_VISIT, json={}, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_period_days_out_of_range_422(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "report_period@example.com", "01055550021")
            resp = await client.post(
                PRE_VISIT,
                json={"visit_date": "2026-07-01", "period_days": 200},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
