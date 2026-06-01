from __future__ import annotations

from enum import StrEnum

from tortoise import fields, models


class MedicalScheduleType(StrEnum):
    BLOOD_TEST = "BLOOD_TEST"
    URINE_TEST = "URINE_TEST"
    EYE_EXAM = "EYE_EXAM"
    APPOINTMENT = "APPOINTMENT"
    INJECTION = "INJECTION"


class MedicalSchedule(models.Model):
    """REQ-AUTO-004 — 자가면역 관리 의료 일정 (검사·진료·주사)."""

    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="medical_schedules", on_delete=fields.CASCADE)
    schedule_type = fields.CharEnumField(enum_type=MedicalScheduleType, max_length=16)
    title = fields.CharField(max_length=200, null=True)
    scheduled_date = fields.DateField()
    reminder_days_before = fields.IntField(default=1)
    note = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    deleted_at = fields.DatetimeField(null=True)

    class Meta:
        table = "medical_schedules"
