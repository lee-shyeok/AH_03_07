from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from app.guide_generator.schema import HealthGuideOutput


class OrchestratorStatus(str, Enum):
    GENERATED = "GENERATED"
    BLOCKED_HIGH_RISK = "BLOCKED_HIGH_RISK"
    GENERATION_FAILED = "GENERATION_FAILED"
    TRIGGER_NOT_MET = "TRIGGER_NOT_MET"


class TriggerStatus(str, Enum):
    MET = "MET"
    NOT_MET = "NOT_MET"


class TriggerCheckResult(BaseModel):
    status: TriggerStatus
    missing_conditions: list[str]


class OrchestratorResult(BaseModel):
    user_id: int
    orchestrator_status: OrchestratorStatus
    trigger_emergency_modal: bool = False
    guide: HealthGuideOutput | None = None
    trigger_check: TriggerCheckResult | None = None
    evaluated_at: datetime
