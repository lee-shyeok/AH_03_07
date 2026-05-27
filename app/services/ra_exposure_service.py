from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from app.core import config
from app.dtos.ra_exposure import (
    ExposureTarget,
    RAExposureResponse,
    RATrigger,
    RATriggerCode,
    TriggerContext,
)
from app.models.disease_activity_log import DiseaseActivityLog
from app.models.symptom_check_log import SymptomCheckLog
from app.models.user_disease import DiseaseCode, UserDisease
from app.models.user_medication import DrugClass, UserMedication
from app.models.users import User

RA_DRUG_CLASSES = {DrugClass.STEROID, DrugClass.IMMUNOSUPPRESSANT, DrugClass.ANTIMALARIAL, DrugClass.BIOLOGIC}

LABELS = {
    RATriggerCode.DISEASE_REGISTERED: "RA 질환이 등록되었습니다",
    RATriggerCode.MORNING_STIFFNESS_HIGH: "아침 강직 시간이 30분 이상으로 기록되었습니다",
    RATriggerCode.FATIGUE_CONSECUTIVE_HIGH: "피로도 7 이상이 3일 연속 기록되었습니다",
    RATriggerCode.JOINT_SWELLING_CHANGED: "관절 부종 부위 변화가 기록되었습니다",
    RATriggerCode.RA_MEDICATION_REGISTERED: "RA 관련 약물이 등록되었습니다",
    RATriggerCode.INJECTION_REGISTERED: "주사제 약물이 등록되었습니다",
    RATriggerCode.SYMPTOM_ESCALATION: "증상 변화 의심 신호가 감지되었습니다",
}

TRIGGER_TARGETS = {
    RATriggerCode.DISEASE_REGISTERED: [
        ExposureTarget.RA_DASHBOARD_SECTION,
        ExposureTarget.RA_GENERAL_GUIDES,
    ],
    RATriggerCode.MORNING_STIFFNESS_HIGH: [
        ExposureTarget.JOINT_PROTECTION_GUIDE,
        ExposureTarget.DAILY_MANAGEMENT_GUIDE,
    ],
    RATriggerCode.FATIGUE_CONSECUTIVE_HIGH: [
        ExposureTarget.ACTIVITY_ADJUSTMENT_GUIDE,
    ],
    RATriggerCode.JOINT_SWELLING_CHANGED: [
        ExposureTarget.SWELLING_TREND_SUMMARY,
    ],
    RATriggerCode.RA_MEDICATION_REGISTERED: [
        ExposureTarget.MEDICATION_SAFETY_CARD,
        ExposureTarget.EXTERNAL_DIET_LINK,
    ],
    RATriggerCode.INJECTION_REGISTERED: [
        ExposureTarget.INJECTION_SCHEDULE_PROMPT,
    ],
    RATriggerCode.SYMPTOM_ESCALATION: [
        ExposureTarget.HIGH_RISK_GATE,
    ],
}


class RAExposureService:
    async def evaluate(self, user: User) -> RAExposureResponse:
        if not await self._has_ra_disease(user):
            return RAExposureResponse(
                applicable=False,
                triggers=[],
                evaluated_at=datetime.now(config.TIMEZONE),
            )

        today = date.today()
        start = today - timedelta(days=7)

        logs = await self._get_recent_activity_logs(user, start)
        checks = await self._get_recent_symptom_checks(user, start)
        meds = await self._get_active_medications(user)

        triggers: list[RATrigger] = [self._make_trigger(RATriggerCode.DISEASE_REGISTERED)]

        if t := self._eval_morning_stiffness(logs):
            triggers.append(t)
        if t := self._eval_fatigue_consecutive(logs):
            triggers.append(t)
        if t := self._eval_joint_swelling(logs):
            triggers.append(t)
        if t := self._eval_ra_medication(meds):
            triggers.append(t)
        if t := self._eval_injection(meds):
            triggers.append(t)
        if t := self._eval_symptom_escalation(logs, checks):
            triggers.append(t)

        return RAExposureResponse(
            applicable=True,
            triggers=triggers,
            evaluated_at=datetime.now(config.TIMEZONE),
        )

    # ── 데이터 조회 ───────────────────────────────────────────────

    async def _has_ra_disease(self, user: User) -> bool:
        return await UserDisease.filter(user=user, disease_code=DiseaseCode.RA, deleted_at=None).exists()

    async def _get_recent_activity_logs(self, user: User, start: date) -> list[DiseaseActivityLog]:
        return await DiseaseActivityLog.filter(
            user=user,
            log_date__gte=start,
        ).order_by("-log_date")

    async def _get_recent_symptom_checks(self, user: User, start: date) -> list[SymptomCheckLog]:
        return await SymptomCheckLog.filter(
            user=user,
            created_at__gte=datetime.combine(start, datetime.min.time()),
        ).order_by("-created_at")

    async def _get_active_medications(self, user: User) -> list[UserMedication]:
        return await UserMedication.filter(user=user, deleted_at=None)

    # ── 트리거 평가 ───────────────────────────────────────────────

    def _eval_morning_stiffness(self, logs: list[DiseaseActivityLog]) -> RATrigger | None:
        for log in logs:
            if log.morning_stiffness_min is not None and log.morning_stiffness_min >= 30:
                return self._make_trigger(
                    RATriggerCode.MORNING_STIFFNESS_HIGH,
                    TriggerContext(value=log.morning_stiffness_min, log_date=log.log_date),
                )
        return None

    def _eval_fatigue_consecutive(self, logs: list[DiseaseActivityLog]) -> RATrigger | None:
        recent = logs[:3]
        if len(recent) < 3:
            return None
        if not all(log.fatigue >= 7 for log in recent):
            return None
        dates = [log.log_date for log in recent]
        if not all((dates[i] - dates[i + 1]).days == 1 for i in range(2)):
            return None
        return self._make_trigger(RATriggerCode.FATIGUE_CONSECUTIVE_HIGH)

    def _eval_joint_swelling(self, logs: list[DiseaseActivityLog]) -> RATrigger | None:
        if len(logs) < 2:
            return None

        def _areas(log: DiseaseActivityLog) -> set:
            raw = log.joint_swelling_areas
            if not raw:
                return set()
            if isinstance(raw, list):
                return set(raw)
            try:
                return set(json.loads(raw))
            except (ValueError, TypeError):
                return set()

        if _areas(logs[0]) != _areas(logs[1]):
            return self._make_trigger(RATriggerCode.JOINT_SWELLING_CHANGED)
        return None

    def _eval_ra_medication(self, meds: list[UserMedication]) -> RATrigger | None:
        ra_meds = [m for m in meds if m.drug_class in RA_DRUG_CLASSES]
        if not ra_meds:
            return None
        return self._make_trigger(
            RATriggerCode.RA_MEDICATION_REGISTERED,
            TriggerContext(medication_names=[m.name for m in ra_meds]),
        )

    def _eval_injection(self, meds: list[UserMedication]) -> RATrigger | None:
        if any(m.is_injection for m in meds):
            return self._make_trigger(RATriggerCode.INJECTION_REGISTERED)
        return None

    def _eval_symptom_escalation(
        self,
        logs: list[DiseaseActivityLog],
        checks: list[SymptomCheckLog],
    ) -> RATrigger | None:
        if any(c.red_flag_triggered for c in checks):
            return self._make_trigger(RATriggerCode.SYMPTOM_ESCALATION)
        if any(log.pain_vas >= 8 or log.daily_difficulty >= 8 for log in logs):
            return self._make_trigger(RATriggerCode.SYMPTOM_ESCALATION)
        return None

    # ── 헬퍼 ─────────────────────────────────────────────────────

    def _make_trigger(self, code: RATriggerCode, context: TriggerContext | None = None) -> RATrigger:
        return RATrigger(
            code=code,
            label=LABELS[code],
            exposure_targets=TRIGGER_TARGETS[code],
            context=context,
        )
