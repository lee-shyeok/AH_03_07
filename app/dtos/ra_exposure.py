from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel


class RATriggerCode(StrEnum):
    DISEASE_REGISTERED = "DISEASE_REGISTERED"
    MORNING_STIFFNESS_HIGH = "MORNING_STIFFNESS_HIGH"
    FATIGUE_CONSECUTIVE_HIGH = "FATIGUE_CONSECUTIVE_HIGH"
    JOINT_SWELLING_CHANGED = "JOINT_SWELLING_CHANGED"
    RA_MEDICATION_REGISTERED = "RA_MEDICATION_REGISTERED"
    INJECTION_REGISTERED = "INJECTION_REGISTERED"
    SYMPTOM_ESCALATION = "SYMPTOM_ESCALATION"


class ExposureTarget(StrEnum):
    RA_DASHBOARD_SECTION = "RA_DASHBOARD_SECTION"
    RA_GENERAL_GUIDES = "RA_GENERAL_GUIDES"
    JOINT_PROTECTION_GUIDE = "JOINT_PROTECTION_GUIDE"
    DAILY_MANAGEMENT_GUIDE = "DAILY_MANAGEMENT_GUIDE"
    ACTIVITY_ADJUSTMENT_GUIDE = "ACTIVITY_ADJUSTMENT_GUIDE"
    SWELLING_TREND_SUMMARY = "SWELLING_TREND_SUMMARY"
    MEDICATION_SAFETY_CARD = "MEDICATION_SAFETY_CARD"
    EXTERNAL_DIET_LINK = "EXTERNAL_DIET_LINK"
    INJECTION_SCHEDULE_PROMPT = "INJECTION_SCHEDULE_PROMPT"
    HIGH_RISK_GATE = "HIGH_RISK_GATE"


class TriggerContext(BaseModel):
    value: int | str | None = None
    log_date: date | None = None
    medication_names: list[str] | None = None


class RATrigger(BaseModel):
    code: RATriggerCode
    label: str
    exposure_targets: list[ExposureTarget]
    context: TriggerContext | None = None


class RAExposureResponse(BaseModel):
    applicable: bool
    triggers: list[RATrigger]
    evaluated_at: datetime
