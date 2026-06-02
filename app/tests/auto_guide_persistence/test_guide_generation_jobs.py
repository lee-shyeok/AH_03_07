from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient
from tortoise.contrib.test import TestCase

from app.auto_guide.schema import OrchestratorResult, OrchestratorStatus
from app.guide_generator.schema import GuideStatus, HealthGuideOutput, SourceItem
from app.main import app
from app.models.auto_guide import AutoGuide, AutoGuideStatus
from app.models.guide_generation_job import GuideGenerationJob, GuideGenerationJobStatus
from app.models.users import User

BASE_URL = "http://test"
GENERATE_EP = "/api/v1/guides/generate"
JOB_EP = "/api/v1/guide-generation-jobs"

_FAKE_SOURCE = SourceItem(
    title="류마티스관절염 진료지침",
    section="약물 치료",
    page=42,
    organization="대한류마티스학회",
    published_year=2023,
    score=0.91,
)


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "Password123!",
            "name": "가이드테스터",
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


def _make_generated_result(user_id: int) -> OrchestratorResult:
    guide = HealthGuideOutput(
        user_id=user_id,
        status=GuideStatus.GENERATED,
        medication_general="약물 복용 시 의료진 지시를 따르세요.",
        side_effect_monitoring=["두통", "구역"],
        lifestyle_info="규칙적인 생활을 유지하세요.",
        symptom_summary="증상 변화를 다음 진료 시 공유하세요.",
        sources=[_FAKE_SOURCE],
        disclaimer="※ 이 안내문은 의료 진단·처방·치료를 대체하지 않습니다.",
        created_at=datetime.now(UTC),
    )
    return OrchestratorResult(
        user_id=user_id,
        orchestrator_status=OrchestratorStatus.GENERATED,
        guide=guide,
        evaluated_at=datetime.now(UTC),
    )


class TestGenerateEndpoint(TestCase):
    async def test_generate_returns_202_and_creates_job(self):
        """POST /generate → 202, status=PENDING, job 행 존재."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "gen_202@example.com", "01098000001")
            user = await User.get(email="gen_202@example.com")
            mock_result = _make_generated_result(user.id)

            with patch("app.apis.v1.auto_guide_router.orchestrate", AsyncMock(return_value=mock_result)):
                resp = await client.post(GENERATE_EP, headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 202
        body = resp.json()
        assert body["status"] == "PENDING"
        job_id = body["job_id"]
        assert job_id is not None
        assert await GuideGenerationJob.filter(id=job_id).exists()


class TestJobStatusEndpoint(TestCase):
    async def test_completed_job_returns_guide_id(self):
        """COMPLETED + guide_id 있는 job → GET 200, guide_id 반환."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "job_completed@example.com", "01098000002")
            user = await User.get(email="job_completed@example.com")

            auto_guide = await AutoGuide.create(
                user_id=user.id,
                status=AutoGuideStatus.GENERATED,
                medication_general="약물 안내",
                side_effect_monitoring=[],
                lifestyle_info="생활 안내",
                symptom_summary="증상 요약",
                sources=[],
                disclaimer="면책 조항",
            )
            job = await GuideGenerationJob.create(
                user_id=user.id,
                status=GuideGenerationJobStatus.COMPLETED,
                trigger_type="manual",
                guide_id=auto_guide.id,
            )

            resp = await client.get(
                f"{JOB_EP}/{job.id}",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "COMPLETED"
        assert body["guide_id"] == auto_guide.id

    async def test_blocked_job_returns_blocked_reason(self):
        """BLOCKED + blocked_reason='HIGH_RISK_GATE_BLOCKED' job → GET, 필드 반환, guide_id None."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "job_blocked@example.com", "01098000003")
            user = await User.get(email="job_blocked@example.com")

            job = await GuideGenerationJob.create(
                user_id=user.id,
                status=GuideGenerationJobStatus.BLOCKED,
                trigger_type="manual",
                blocked_reason="HIGH_RISK_GATE_BLOCKED",
            )

            resp = await client.get(
                f"{JOB_EP}/{job.id}",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "BLOCKED"
        assert body["blocked_reason"] == "HIGH_RISK_GATE_BLOCKED"
        assert body["guide_id"] is None

    async def test_emergency_flag_returned(self):
        """trigger_emergency_modal=True인 job → GET 응답에 True."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "job_emerg@example.com", "01098000004")
            user = await User.get(email="job_emerg@example.com")

            job = await GuideGenerationJob.create(
                user_id=user.id,
                status=GuideGenerationJobStatus.COMPLETED,
                trigger_type="manual",
                trigger_emergency_modal=True,
            )

            resp = await client.get(
                f"{JOB_EP}/{job.id}",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        assert resp.json()["trigger_emergency_modal"] is True

    async def test_other_user_404(self):
        """다른 유저의 job_id로 조회 → 404."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            await _signup_and_login(client, "job_usera@example.com", "01098000005")
            user_a = await User.get(email="job_usera@example.com")
            job = await GuideGenerationJob.create(
                user_id=user_a.id,
                status=GuideGenerationJobStatus.PENDING,
                trigger_type="manual",
            )

            token_b = await _signup_and_login(client, "job_userb@example.com", "01098000006")
            resp = await client.get(
                f"{JOB_EP}/{job.id}",
                headers={"Authorization": f"Bearer {token_b}"},
            )

        assert resp.status_code == 404

    async def test_nonexistent_job_404(self):
        """존재하지 않는 job_id → 404."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            token = await _signup_and_login(client, "job_miss@example.com", "01098000007")

            resp = await client.get(
                f"{JOB_EP}/999999999",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 404
