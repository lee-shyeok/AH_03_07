from __future__ import annotations

from enum import StrEnum

from tortoise import fields, models


class SymptomCode(StrEnum):
    FEVER = "FEVER"
    PERSISTENT_COUGH = "PERSISTENT_COUGH"
    DYSPNEA = "DYSPNEA"
    SEVERE_ABDOMINAL_PAIN = "SEVERE_ABDOMINAL_PAIN"
    JAUNDICE = "JAUNDICE"
    SEVERE_BLEEDING = "SEVERE_BLEEDING"
    ALTERED_CONSCIOUSNESS = "ALTERED_CONSCIOUSNESS"
    SHINGLES_SUSPECTED = "SHINGLES_SUSPECTED"
    MOUTH_SORES = "MOUTH_SORES"
    BLURRED_VISION = "BLURRED_VISION"


class SymptomCheckLog(models.Model):
    """REQ-SYMP-001 — 위험 증상 자가체크 기록. red_flag_triggered는 SYMP-002 룰 매칭 결과."""

    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="symptom_check_logs", on_delete=fields.CASCADE)
    checked_symptoms = fields.JSONField()
    red_flag_triggered = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "symptom_check_logs"
