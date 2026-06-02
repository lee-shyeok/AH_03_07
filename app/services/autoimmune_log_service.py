from __future__ import annotations

from datetime import date, datetime

from app.core import config
from app.dtos.autoimmune_log import ActivityLogUpsertRequest, SymptomCheckCreateRequest
from app.models.audit_log import AuditLog
from app.models.disease_activity_log import DiseaseActivityLog
from app.models.symptom_check_log import SymptomCheckLog, SymptomCode
from app.models.users import User

# SYMP-002 Red Flag 집합 — 정적 룰 매칭용 (임상 판정 아님)
RED_FLAG_SYMPTOMS: frozenset[SymptomCode] = frozenset(
    {
        SymptomCode.DYSPNEA,
        SymptomCode.ALTERED_CONSCIOUSNESS,
        SymptomCode.JAUNDICE,
        SymptomCode.SEVERE_BLEEDING,
    }
)


class ActivityLogService:
    async def upsert_log(self, user: User, data: ActivityLogUpsertRequest) -> DiseaseActivityLog:
        log = await DiseaseActivityLog.get_or_none(user=user, log_date=data.log_date)
        if log is None:
            return await DiseaseActivityLog.create(
                user=user,
                log_date=data.log_date,
                pain_vas=data.pain_vas,
                fatigue=data.fatigue,
                morning_stiffness_min=data.morning_stiffness_minutes,
                joint_swelling_areas=data.joint_swelling_areas,
                daily_difficulty=data.daily_difficulty,
                note=data.free_memo,
            )
        log.pain_vas = data.pain_vas
        log.fatigue = data.fatigue
        log.morning_stiffness_min = data.morning_stiffness_minutes
        log.joint_swelling_areas = data.joint_swelling_areas
        log.daily_difficulty = data.daily_difficulty
        log.note = data.free_memo
        log.updated_at = datetime.now(config.TIMEZONE)
        await log.save(
            update_fields=[
                "pain_vas",
                "fatigue",
                "morning_stiffness_min",
                "joint_swelling_areas",
                "daily_difficulty",
                "note",
                "updated_at",
            ]
        )
        return log

    async def list_logs(
        self,
        user: User,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[DiseaseActivityLog]:
        qs = DiseaseActivityLog.filter(user=user)
        if from_date is not None:
            qs = qs.filter(log_date__gte=from_date)
        if to_date is not None:
            qs = qs.filter(log_date__lte=to_date)
        return await qs.order_by("-log_date")

    async def get_log_by_date(self, user: User, log_date: date) -> DiseaseActivityLog | None:
        return await DiseaseActivityLog.get_or_none(user=user, log_date=log_date)


class SymptomCheckService:
    async def create_check(
        self, user: User, data: SymptomCheckCreateRequest
    ) -> tuple[SymptomCheckLog, list[SymptomCode]]:
        red_flags = sorted(set(data.checked_symptoms) & RED_FLAG_SYMPTOMS, key=lambda s: s.value)
        log = await SymptomCheckLog.create(
            user=user,
            checked_symptoms=[s.value for s in data.checked_symptoms],
            red_flag_triggered=bool(red_flags),
        )
        if red_flags:
            await AuditLog.create(
                user=user,
                action="SYMP_RED_FLAG",
                detail={"symptoms": [s.value for s in red_flags]},
            )
        return log, red_flags

    async def list_checks(self, user: User) -> list[tuple[SymptomCheckLog, list[SymptomCode]]]:
        logs = await SymptomCheckLog.filter(user=user).order_by("-created_at")
        result = []
        for log in logs:
            checked = {SymptomCode(s) for s in log.checked_symptoms}
            red_flags = sorted(checked & RED_FLAG_SYMPTOMS, key=lambda s: s.value)
            result.append((log, red_flags))
        return result
