from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel


class LupusTriggerCode(StrEnum):
    DISEASE_REGISTERED = "DISEASE_REGISTERED"
    SKIN_SYMPTOM_LOGGED = "SKIN_SYMPTOM_LOGGED"
    FATIGUE_CONSECUTIVE_HIGH = "FATIGUE_CONSECUTIVE_HIGH"
    SLE_MEDICATION_REGISTERED = "SLE_MEDICATION_REGISTERED"
    INJECTION_REGISTERED = "INJECTION_REGISTERED"
    SYMPTOM_ESCALATION = "SYMPTOM_ESCALATION"


class LupusExposureTarget(StrEnum):
    LUPUS_DASHBOARD_SECTION = "LUPUS_DASHBOARD_SECTION"
    LUPUS_GENERAL_GUIDES = "LUPUS_GENERAL_GUIDES"
    UV_PROTECTION_GUIDE = "UV_PROTECTION_GUIDE"
    SKIN_SYMPTOM_GUIDE = "SKIN_SYMPTOM_GUIDE"
    SKIN_TREND_SUMMARY = "SKIN_TREND_SUMMARY"
    ACTIVITY_ADJUSTMENT_GUIDE = "ACTIVITY_ADJUSTMENT_GUIDE"
    MEDICATION_SAFETY_CARD = "MEDICATION_SAFETY_CARD"
    EXTERNAL_DIET_LINK = "EXTERNAL_DIET_LINK"
    OPHTHALMOLOGY_SCREENING_PROMPT = "OPHTHALMOLOGY_SCREENING_PROMPT"
    INJECTION_SCHEDULE_PROMPT = "INJECTION_SCHEDULE_PROMPT"
    HIGH_RISK_GATE = "HIGH_RISK_GATE"


class TriggerContext(BaseModel):
    value: int | str | None = None
    log_date: date | None = None
    medication_names: list[str] | None = None


class LupusTrigger(BaseModel):
    code: LupusTriggerCode
    label: str
    exposure_targets: list[LupusExposureTarget]
    context: TriggerContext | None = None


class LupusExposureResponse(BaseModel):
    applicable: bool
    triggers: list[LupusTrigger]
    evaluated_at: datetime
