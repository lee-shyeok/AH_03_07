from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class GateStatus(str, Enum):
    PASS = "PASS"
    LOCKED = "LOCKED"


class HighRiskGateInput(BaseModel):
    user_id: int
    checked_symptom_codes: list[str] = []
    self_report_codes: list[str] = []
    pregnancy_status_codes: list[str] = []
    lab_threshold_exceeded: bool = False


class MatchedItem(BaseModel):
    code: str
    label: str
    category: str
    red_flag: bool


class HighRiskGateResult(BaseModel):
    status: GateStatus
    matched_items: list[MatchedItem]
    trigger_emergency_modal: bool
    message: str
    disclaimer: str
    evaluated_at: datetime
