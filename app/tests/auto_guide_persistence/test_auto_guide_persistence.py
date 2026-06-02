from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient
from tortoise.contrib.test import TestCase

from app.apis.v1.auto_guide_router import _run_generation_job
from app.auto_guide.schema import OrchestratorResult, OrchestratorStatus, TriggerCheckResult, TriggerStatus
from app.guide_generator.schema import GuideStatus, HealthGuideOutput, SourceItem
from app.main import app
from app.models.auto_guide import AutoGuide
from app.models.guide_generation_job import GuideGenerationJob, GuideGenerationJobStatus
from app.models.users import User

BASE_URL = "http://test"

_FAKE_SOURCE = SourceItem(
    title="류마티스관절염 진료지침",
    section="약물 치료",
    page=42,
    organization="대한류마티스학회",
    published_year=2023,
    score=0.91,
)


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> None:
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


def _make_guide_output(user_id: int) -> HealthGuideOutput:
    return HealthGuideOutput(
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


def _make_result(
    user_id: int,
    status: OrchestratorStatus,
    *,
    trigger_emergency_modal: bool = False,
    missing_conditions: list[str] | None = None,
) -> OrchestratorResult:
    guide = None
    trigger_check = None
    if status == OrchestratorStatus.GENERATED:
        guide = _make_guide_output(user_id)
    if status == OrchestratorStatus.TRIGGER_NOT_MET:
        trigger_check = TriggerCheckResult(
            status=TriggerStatus.NOT_MET,
            missing_conditions=missing_conditions or [],
        )
    return OrchestratorResult(
        user_id=user_id,
        orchestrator_status=status,
        guide=guide,
        trigger_check=trigger_check,
        trigger_emergency_modal=trigger_emergency_modal,
        evaluated_at=datetime.now(UTC),
    )


async def _create_user(email: str, phone: str) -> int:
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        await _signup_and_login(client, email, phone)
    user = await User.get(email=email)
    return user.id


async def _create_job(user_id: int) -> GuideGenerationJob:
    return await GuideGenerationJob.create(
        user_id=user_id,
        status=GuideGenerationJobStatus.PENDING,
        trigger_type="manual",
    )


class TestRunGenerationJob(TestCase):
    async def test_generated_completes_and_saves_auto_guide(self):
        """GENERATED → status=COMPLETED, guide_id 채워짐, AutoGuide 1건(필드 일치)."""
        user_id = await _create_user("job_gen@example.com", "01097000001")
        job = await _create_job(user_id)
        result = _make_result(user_id, OrchestratorStatus.GENERATED)

        with patch("app.apis.v1.auto_guide_router.orchestrate", AsyncMock(return_value=result)):
            await _run_generation_job(job.id)

        job = await GuideGenerationJob.get(id=job.id)
        assert job.status == GuideGenerationJobStatus.COMPLETED
        assert job.guide_id is not None

        saved = await AutoGuide.filter(user_id=user_id).all()
        assert len(saved) == 1
        assert saved[0].id == job.guide_id
        assert saved[0].medication_general == result.guide.medication_general
        assert saved[0].disclaimer == result.guide.disclaimer

    async def test_blocked_high_risk_sets_blocked_and_no_auto_guide(self):
        """BLOCKED_HIGH_RISK → status=BLOCKED, blocked_reason='HIGH_RISK_GATE_BLOCKED', AutoGuide 0건."""
        user_id = await _create_user("job_blocked@example.com", "01097000002")
        job = await _create_job(user_id)
        result = _make_result(user_id, OrchestratorStatus.BLOCKED_HIGH_RISK)

        with patch("app.apis.v1.auto_guide_router.orchestrate", AsyncMock(return_value=result)):
            await _run_generation_job(job.id)

        job = await GuideGenerationJob.get(id=job.id)
        assert job.status == GuideGenerationJobStatus.BLOCKED
        assert job.blocked_reason == "HIGH_RISK_GATE_BLOCKED"
        assert await AutoGuide.filter(user_id=user_id).count() == 0

    async def test_trigger_not_met_sets_failed_with_message(self):
        """TRIGGER_NOT_MET → status=FAILED, error_message에 'TRIGGER_NOT_MET'과 조건 포함, AutoGuide 0건."""
        user_id = await _create_user("job_notmet@example.com", "01097000003")
        job = await _create_job(user_id)
        result = _make_result(
            user_id,
            OrchestratorStatus.TRIGGER_NOT_MET,
            missing_conditions=["자가면역 모드"],
        )

        with patch("app.apis.v1.auto_guide_router.orchestrate", AsyncMock(return_value=result)):
            await _run_generation_job(job.id)

        job = await GuideGenerationJob.get(id=job.id)
        assert job.status == GuideGenerationJobStatus.FAILED
        assert "TRIGGER_NOT_MET" in job.error_message
        assert "자가면역 모드" in job.error_message
        assert await AutoGuide.filter(user_id=user_id).count() == 0

    async def test_generation_failed_sets_failed_with_message(self):
        """GENERATION_FAILED → status=FAILED, error_message=='GENERATION_FAILED'."""
        user_id = await _create_user("job_genfail@example.com", "01097000004")
        job = await _create_job(user_id)
        result = _make_result(user_id, OrchestratorStatus.GENERATION_FAILED)

        with patch("app.apis.v1.auto_guide_router.orchestrate", AsyncMock(return_value=result)):
            await _run_generation_job(job.id)

        job = await GuideGenerationJob.get(id=job.id)
        assert job.status == GuideGenerationJobStatus.FAILED
        assert job.error_message == "GENERATION_FAILED"

    async def test_trigger_emergency_modal_propagated(self):
        """trigger_emergency_modal=True이면 job에 그대로 기록된다."""
        user_id = await _create_user("job_emerg@example.com", "01097000005")
        job = await _create_job(user_id)
        result = _make_result(user_id, OrchestratorStatus.GENERATED, trigger_emergency_modal=True)

        with patch("app.apis.v1.auto_guide_router.orchestrate", AsyncMock(return_value=result)):
            await _run_generation_job(job.id)

        job = await GuideGenerationJob.get(id=job.id)
        assert job.trigger_emergency_modal is True

    async def test_orchestrate_exception_sets_failed_internal_error(self):
        """orchestrate가 예외를 raise하면 status=FAILED, error_message='internal error'."""
        user_id = await _create_user("job_exc@example.com", "01097000006")
        job = await _create_job(user_id)

        with patch(
            "app.apis.v1.auto_guide_router.orchestrate",
            AsyncMock(side_effect=RuntimeError("unexpected")),
        ):
            await _run_generation_job(job.id)

        job = await GuideGenerationJob.get(id=job.id)
        assert job.status == GuideGenerationJobStatus.FAILED
        assert job.error_message == "internal error"
