from __future__ import annotations

from datetime import date, datetime, timedelta

from app.core import config
from app.dtos.lupus_exposure import (
    LupusExposureResponse,
    LupusExposureTarget,
    LupusTrigger,
    LupusTriggerCode,
    TriggerContext,
)
from app.models.disease_activity_log import DiseaseActivityLog
from app.models.lupus_skin_log import LupusSkinLog
from app.models.symptom_check_log import SymptomCheckLog
from app.models.user_disease import DiseaseCode, UserDisease
from app.models.user_medication import DrugClass, UserMedication
from app.models.users import User

SLE_DRUG_CLASSES = {DrugClass.STEROID, DrugClass.IMMUNOSUPPRESSANT, DrugClass.ANTIMALARIAL}

LABELS = {
    LupusTriggerCode.DISEASE_REGISTERED: "루푸스(SLE) 질환이 등록되었습니다",
    LupusTriggerCode.SKIN_SYMPTOM_LOGGED: "SLE 관련 피부 증상이 기록되었습니다",
    LupusTriggerCode.FATIGUE_CONSECUTIVE_HIGH: "피로도 7 이상이 3일 연속 기록되었습니다",
    LupusTriggerCode.SLE_MEDICATION_REGISTERED: "SLE 관련 약물이 등록되었습니다",
    LupusTriggerCode.INJECTION_REGISTERED: "주사제 약물이 등록되었습니다",
    LupusTriggerCode.SYMPTOM_ESCALATION: "증상 변화 의심 신호가 감지되었습니다",
}

TRIGGER_TARGETS: dict[LupusTriggerCode, list[LupusExposureTarget]] = {
    LupusTriggerCode.DISEASE_REGISTERED: [
        LupusExposureTarget.LUPUS_DASHBOARD_SECTION,
        LupusExposureTarget.LUPUS_GENERAL_GUIDES,
        LupusExposureTarget.UV_PROTECTION_GUIDE,
    ],
    LupusTriggerCode.SKIN_SYMPTOM_LOGGED: [
        LupusExposureTarget.SKIN_SYMPTOM_GUIDE,
        LupusExposureTarget.SKIN_TREND_SUMMARY,
    ],
    LupusTriggerCode.FATIGUE_CONSECUTIVE_HIGH: [
        LupusExposureTarget.ACTIVITY_ADJUSTMENT_GUIDE,
    ],
    LupusTriggerCode.SLE_MEDICATION_REGISTERED: [
        LupusExposureTarget.MEDICATION_SAFETY_CARD,
        LupusExposureTarget.EXTERNAL_DIET_LINK,
    ],
    LupusTriggerCode.INJECTION_REGISTERED: [
        LupusExposureTarget.INJECTION_SCHEDULE_PROMPT,
    ],
    LupusTriggerCode.SYMPTOM_ESCALATION: [
        LupusExposureTarget.HIGH_RISK_GATE,
    ],
}


class LupusExposureService:
    async def evaluate(self, user: User) -> LupusExposureResponse:
        if not await self._has_sle_disease(user):
            return LupusExposureResponse(
                applicable=False,
                triggers=[],
                evaluated_at=datetime.now(config.TIMEZONE),
            )

        today = date.today()
        start = today - timedelta(days=7)

        logs = await self._get_recent_activity_logs(user, start)
        checks = await self._get_recent_symptom_checks(user, start)
        meds = await self._get_active_medications(user)

        triggers: list[LupusTrigger] = [self._make_trigger(LupusTriggerCode.DISEASE_REGISTERED)]

        if t := await self._eval_skin_symptom(user, start):
            triggers.append(t)
        if t := self._eval_fatigue_consecutive(logs):
            triggers.append(t)
        if t := self._eval_sle_medication(meds):
            triggers.append(t)
        if t := self._eval_injection(meds):
            triggers.append(t)
        if t := self._eval_symptom_escalation(logs, checks):
            triggers.append(t)

        return LupusExposureResponse(
            applicable=True,
            triggers=triggers,
            evaluated_at=datetime.now(config.TIMEZONE),
        )

    # ── 데이터 조회 ───────────────────────────────────────────────

    async def _has_sle_disease(self, user: User) -> bool:
        return await UserDisease.filter(user=user, disease_code=DiseaseCode.SLE, deleted_at=None).exists()

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

    async def _eval_skin_symptom(self, user: User, start: date) -> LupusTrigger | None:
        has_log = await LupusSkinLog.filter(user=user, deleted_at=None, log_date__gte=start).exists()
        if has_log:
            return self._make_trigger(LupusTriggerCode.SKIN_SYMPTOM_LOGGED)
        return None

    def _eval_fatigue_consecutive(self, logs: list[DiseaseActivityLog]) -> LupusTrigger | None:
        recent = logs[:3]
        if len(recent) < 3:
            return None
        if not all(log.fatigue >= 7 for log in recent):
            return None
        dates = [log.log_date for log in recent]
        if not all((dates[i] - dates[i + 1]).days == 1 for i in range(2)):
            return None
        return self._make_trigger(LupusTriggerCode.FATIGUE_CONSECUTIVE_HIGH)

    def _eval_sle_medication(self, meds: list[UserMedication]) -> LupusTrigger | None:
        sle_meds = [m for m in meds if m.drug_class in SLE_DRUG_CLASSES]
        if not sle_meds:
            return None
        targets = list(TRIGGER_TARGETS[LupusTriggerCode.SLE_MEDICATION_REGISTERED])
        if any(m.drug_class == DrugClass.ANTIMALARIAL for m in sle_meds):
            targets.append(LupusExposureTarget.OPHTHALMOLOGY_SCREENING_PROMPT)
        return LupusTrigger(
            code=LupusTriggerCode.SLE_MEDICATION_REGISTERED,
            label=LABELS[LupusTriggerCode.SLE_MEDICATION_REGISTERED],
            exposure_targets=targets,
            context=TriggerContext(medication_names=[m.name for m in sle_meds]),
        )

    def _eval_injection(self, meds: list[UserMedication]) -> LupusTrigger | None:
        if any(m.is_injection for m in meds):
            return self._make_trigger(LupusTriggerCode.INJECTION_REGISTERED)
        return None

    def _eval_symptom_escalation(
        self,
        logs: list[DiseaseActivityLog],
        checks: list[SymptomCheckLog],
    ) -> LupusTrigger | None:
        if any(c.red_flag_triggered for c in checks):
            return self._make_trigger(LupusTriggerCode.SYMPTOM_ESCALATION)
        if any(log.pain_vas >= 8 or log.daily_difficulty >= 8 for log in logs):
            return self._make_trigger(LupusTriggerCode.SYMPTOM_ESCALATION)
        return None

    # ── 헬퍼 ─────────────────────────────────────────────────────

    def _make_trigger(self, code: LupusTriggerCode, context: TriggerContext | None = None) -> LupusTrigger:
        return LupusTrigger(
            code=code,
            label=LABELS[code],
            exposure_targets=TRIGGER_TARGETS[code],
            context=context,
        )
