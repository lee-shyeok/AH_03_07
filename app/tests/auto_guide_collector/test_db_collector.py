from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient
from tortoise.contrib.test import TestCase

from app.auto_guide.collector import DbDataSourceCollector
from app.auto_guide.schema import OrchestratorStatus
from app.auto_guide.service import orchestrate
from app.guide_generator.schema import GuideStatus, HealthGuideOutput
from app.main import app
from app.models.disease_activity_log import DiseaseActivityLog
from app.models.lab_result import LabResult
from app.models.medical_schedule import MedicalSchedule, MedicalScheduleType
from app.models.risk_flag import RiskFlag, RiskFlagSourceType, RiskFlagStatus
from app.models.symptom_check_log import SymptomCheckLog
from app.models.user_disease import DiseaseCode, UserDisease
from app.models.user_medication import DrugClass, UserMedication
from app.models.user_risk_profile import PregnancyStatus, UserRiskProfile
from app.models.users import User, UserMode

BASE_URL = "http://test"

FORBIDDEN_SUMMARY_WORDS = [
    "의심",
    "권장",
    "위험합니다",
    "복용하세요",
    "하세요",
    "받으세요",
    "필요합니다",
    "주의하세요",
]


async def _signup_and_login(client: AsyncClient, email: str, phone: str) -> str:
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "Password123!",
            "name": "콜렉터테스터",
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


async def _create_autoimmune_user(email: str, phone: str) -> User:
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        await _signup_and_login(client, email, phone)
    user = await User.get(email=email)
    user.mode = UserMode.AUTOIMMUNE
    await user.save(update_fields=["mode"])
    return user


def _make_guide_output(user_id: int, guide_status: GuideStatus) -> HealthGuideOutput:
    return HealthGuideOutput(
        user_id=user_id,
        status=guide_status,
        medication_general="약물 복용 시 의료진 지시를 따르세요.",
        side_effect_monitoring=["두통이 생기면 의료진에게 알려주세요."],
        lifestyle_info="규칙적인 생활을 유지하세요.",
        symptom_summary="증상 변화를 다음 진료 시 공유하세요.",
        sources=[],
        disclaimer="※ 이 안내문은 의료 진단·처방·치료를 대체하지 않습니다.",
        created_at=datetime.now(UTC),
    )


# ── 실 DB 쿼리 정확성 ──────────────────────────────────────────────


class TestDbDataSourceCollector(TestCase):
    async def test_get_autoimmune_mode_true(self):
        """AUTOIMMUNE 모드 유저 → True 반환."""
        user = await _create_autoimmune_user("col_mode_true@example.com", "01094000001")
        result = await DbDataSourceCollector().get_autoimmune_mode(user.id)
        assert result is True

    async def test_get_autoimmune_mode_false_for_general(self):
        """GENERAL 모드 유저 → False 반환."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            await _signup_and_login(client, "col_mode_false@example.com", "01094000002")
        user = await User.get(email="col_mode_false@example.com")
        result = await DbDataSourceCollector().get_autoimmune_mode(user.id)
        assert result is False

    async def test_get_disease_codes_excludes_soft_deleted(self):
        """UserDisease 시드 → 코드 반환, soft-deleted(deleted_at) 제외."""
        user = await _create_autoimmune_user("col_disease@example.com", "01094000003")
        await UserDisease.create(user_id=user.id, disease_code=DiseaseCode.RA)
        await UserDisease.create(
            user_id=user.id,
            disease_code=DiseaseCode.SLE,
            deleted_at=datetime.now(UTC),
        )
        result = await DbDataSourceCollector().get_disease_codes(user.id)
        assert "RA" in result
        assert "SLE" not in result

    async def test_get_medication_list_excludes_soft_deleted(self):
        """UserMedication 시드 → 목록 반환, soft-deleted 제외."""
        user = await _create_autoimmune_user("col_meds@example.com", "01094000004")
        await UserMedication.create(user_id=user.id, name="메토트렉세이트", drug_class=DrugClass.IMMUNOSUPPRESSANT)
        await UserMedication.create(
            user_id=user.id,
            name="삭제약물",
            drug_class=DrugClass.NSAID,
            deleted_at=datetime.now(UTC),
        )
        result = await DbDataSourceCollector().get_medication_list(user.id)
        assert "메토트렉세이트" in result
        assert "삭제약물" not in result

    async def test_get_activity_score_summary_excludes_old_logs(self):
        """최근 30일 로그 → 평균 포함 문자열, 31일 전 로그 제외."""
        user = await _create_autoimmune_user("col_activity@example.com", "01094000005")
        today = date.today()
        await DiseaseActivityLog.create(
            user_id=user.id,
            log_date=today - timedelta(days=1),
            pain_vas=6,
            fatigue=8,
            daily_difficulty=7,
        )
        # 30일 기준 밖 (제외 대상)
        await DiseaseActivityLog.create(
            user_id=user.id,
            log_date=today - timedelta(days=31),
            pain_vas=0,
            fatigue=0,
            daily_difficulty=0,
        )
        result = await DbDataSourceCollector().get_activity_score_summary(user.id)
        assert result is not None
        assert "6.0" in result  # pain_vas 평균
        assert "8.0" in result  # fatigue 평균
        assert "1일 기록" in result  # 오래된 로그 제외되어 1개만

    async def test_get_risk_symptom_codes_union_of_red_flag_logs(self):
        """red_flag_triggered=True 로그 → 증상 합집합, False 로그 제외."""
        user = await _create_autoimmune_user("col_symp@example.com", "01094000006")
        await SymptomCheckLog.create(
            user_id=user.id,
            checked_symptoms=["DYSPNEA", "FEVER"],
            red_flag_triggered=True,
        )
        await SymptomCheckLog.create(
            user_id=user.id,
            checked_symptoms=["RASH"],
            red_flag_triggered=False,
        )
        result = await DbDataSourceCollector().get_risk_symptom_codes(user.id)
        assert "DYSPNEA" in result
        assert "FEVER" in result
        assert "RASH" not in result

    async def test_get_upcoming_appointments_excludes_past(self):
        """미래 일정 → 포함, 과거 일정 → 제외."""
        user = await _create_autoimmune_user("col_appt@example.com", "01094000007")
        today = date.today()
        await MedicalSchedule.create(
            user_id=user.id,
            schedule_type=MedicalScheduleType.APPOINTMENT,
            scheduled_date=today + timedelta(days=15),
        )
        await MedicalSchedule.create(
            user_id=user.id,
            schedule_type=MedicalScheduleType.BLOOD_TEST,
            scheduled_date=today - timedelta(days=10),
        )
        result = await DbDataSourceCollector().get_upcoming_appointments(user.id)
        assert len(result) == 1
        assert "APPOINTMENT" in result[0]

    async def test_get_self_report_codes_risk_profile_active_only(self):
        """RiskFlag RISK_PROFILE/ACTIVE → flag_code 목록, 다른 source 제외."""
        user = await _create_autoimmune_user("col_self@example.com", "01094000008")
        await RiskFlag.create(
            user_id=user.id,
            source_type=RiskFlagSourceType.RISK_PROFILE,
            flag_code="INFECTION_RISK",
            flag_label="감염 위험",
            category="infection",
            message="감염 이력 — 의료진 확인이 필요합니다.",
            status=RiskFlagStatus.ACTIVE,
        )
        await RiskFlag.create(
            user_id=user.id,
            source_type=RiskFlagSourceType.LAB_RESULT,
            flag_code="LAB_ABNORMAL",
            flag_label="검사 이상",
            category="lab",
            message="검사 이상 — 의료진 확인이 필요합니다.",
            status=RiskFlagStatus.ACTIVE,
        )
        result = await DbDataSourceCollector().get_self_report_codes(user.id)
        assert "INFECTION_RISK" in result
        assert "LAB_ABNORMAL" not in result

    async def test_get_lab_threshold_exceeded_true_when_lab_flag_active(self):
        """RiskFlag LAB_RESULT/ACTIVE 존재 → True."""
        user = await _create_autoimmune_user("col_lab_t@example.com", "01094000009")
        await RiskFlag.create(
            user_id=user.id,
            source_type=RiskFlagSourceType.LAB_RESULT,
            flag_code="LAB_ABNORMAL",
            flag_label="검사 이상",
            category="lab",
            message="검사 이상 — 의료진 확인이 필요합니다.",
            status=RiskFlagStatus.ACTIVE,
        )
        result = await DbDataSourceCollector().get_lab_threshold_exceeded(user.id)
        assert result is True

    async def test_get_lab_threshold_exceeded_false_when_no_lab_flag(self):
        """LAB_RESULT RiskFlag 없음 → False."""
        user = await _create_autoimmune_user("col_lab_f@example.com", "01094000010")
        result = await DbDataSourceCollector().get_lab_threshold_exceeded(user.id)
        assert result is False

    async def test_summaries_factual_only(self):
        """NFR-SAFE-003 — 모든 summary 메서드에 해석·판단·권고 표현 미포함."""
        user = await _create_autoimmune_user("col_safe@example.com", "01094000011")
        today = date.today()
        await UserRiskProfile.create(
            user_id=user.id,
            pregnancy_status=PregnancyStatus.NONE,
            renal_impairment=True,
            hepatic_impairment=False,
            infection_history="결핵 완치 이력",
            drug_allergy="페니실린",
            comorbidities="고혈압",
        )
        await DiseaseActivityLog.create(
            user_id=user.id,
            log_date=today - timedelta(days=1),
            pain_vas=5,
            fatigue=4,
            daily_difficulty=3,
        )
        await LabResult.create(
            user_id=user.id,
            test_date=today - timedelta(days=7),
            test_item="혈색소",
            value="10.5",
            reference_range="12-16",
        )
        collector = DbDataSourceCollector()
        summaries = [
            await collector.get_risk_factor_summary(user.id),
            await collector.get_activity_score_summary(user.id),
            await collector.get_lab_results_summary(user.id),
        ]
        for summary in summaries:
            if summary is None:
                continue
            for word in FORBIDDEN_SUMMARY_WORDS:
                assert word not in summary, f"금지어 '{word}' in: {summary}"


# ── 실 collector 경유 orchestrate 트리거 검증 ──────────────────────


class TestOrchestrateTrigger(TestCase):
    async def test_trigger_met_proceeds_to_generation(self):
        """AUTOIMMUNE + 질환 + 약물(입력 소스) → TRIGGER_NOT_MET 아님."""
        user = await _create_autoimmune_user("orch_met@example.com", "01094000012")
        await UserDisease.create(user_id=user.id, disease_code=DiseaseCode.RA)
        await UserMedication.create(user_id=user.id, name="메토트렉세이트", drug_class=DrugClass.IMMUNOSUPPRESSANT)
        mock_gen = AsyncMock(return_value=_make_guide_output(user.id, GuideStatus.GENERATED))
        with patch("app.auto_guide.service.generate_guide", mock_gen):
            result = await orchestrate(user_id=user.id)
        assert result.orchestrator_status != OrchestratorStatus.TRIGGER_NOT_MET
        mock_gen.assert_called_once()

    async def test_trigger_not_met_no_autoimmune_mode(self):
        """GENERAL 모드 → TRIGGER_NOT_MET, generate_guide 미호출."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            await _signup_and_login(client, "orch_no_mode@example.com", "01094000013")
        user = await User.get(email="orch_no_mode@example.com")
        await UserDisease.create(user_id=user.id, disease_code=DiseaseCode.RA)
        with patch("app.auto_guide.service.generate_guide") as mock_gen:
            result = await orchestrate(user_id=user.id)
        assert result.orchestrator_status == OrchestratorStatus.TRIGGER_NOT_MET
        mock_gen.assert_not_called()

    async def test_trigger_not_met_no_disease(self):
        """질환 미등록 → TRIGGER_NOT_MET."""
        user = await _create_autoimmune_user("orch_no_disease@example.com", "01094000014")
        await UserMedication.create(user_id=user.id, name="메토트렉세이트", drug_class=DrugClass.IMMUNOSUPPRESSANT)
        with patch("app.auto_guide.service.generate_guide") as mock_gen:
            result = await orchestrate(user_id=user.id)
        assert result.orchestrator_status == OrchestratorStatus.TRIGGER_NOT_MET
        mock_gen.assert_not_called()

    async def test_trigger_not_met_no_input_source(self):
        """입력 소스(약물·위험요인·증상) 전무 → TRIGGER_NOT_MET."""
        user = await _create_autoimmune_user("orch_no_input@example.com", "01094000015")
        await UserDisease.create(user_id=user.id, disease_code=DiseaseCode.SLE)
        with patch("app.auto_guide.service.generate_guide") as mock_gen:
            result = await orchestrate(user_id=user.id)
        assert result.orchestrator_status == OrchestratorStatus.TRIGGER_NOT_MET
        mock_gen.assert_not_called()

    async def test_high_risk_gate_blocks_with_dyspnea(self):
        """DYSPNEA 증상 → 게이트 LOCKED, generate_guide에 high_risk_flag=True 전달."""
        user = await _create_autoimmune_user("orch_highrisk@example.com", "01094000016")
        await UserDisease.create(user_id=user.id, disease_code=DiseaseCode.RA)
        await UserMedication.create(user_id=user.id, name="메토트렉세이트", drug_class=DrugClass.IMMUNOSUPPRESSANT)
        # DYSPNEA: gate_rules.json에서 red_flag=True → LOCKED
        await SymptomCheckLog.create(
            user_id=user.id,
            checked_symptoms=["DYSPNEA"],
            red_flag_triggered=True,
        )
        mock_gen = AsyncMock(return_value=_make_guide_output(user.id, GuideStatus.BLOCKED_HIGH_RISK))
        with patch("app.auto_guide.service.generate_guide", mock_gen):
            result = await orchestrate(user_id=user.id)
        assert result.orchestrator_status == OrchestratorStatus.BLOCKED_HIGH_RISK
        called_input = mock_gen.call_args.args[0]
        assert called_input.high_risk_flag is True
