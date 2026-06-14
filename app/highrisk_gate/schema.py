from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class GateStatus(str, Enum):
    PASS = "PASS"
    LOCKED = "LOCKED"


class HighRiskGateInput(BaseModel):
    user_id: int
    checked_symptom_codes: list[str] = []
    checked_symptoms_is_stale: bool = False  # 최신 체크가 STALE_WINDOW 초과 시 True
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
    needs_recheck: bool = False  # stale 소스만으로 LOCKED → 재체크 요청
    message: str
    disclaimer: str
    evaluated_at: datetime
