from __future__ import annotations

from datetime import datetime

from app.core import config
from app.highrisk_gate.schema import HighRiskGateInput
from app.highrisk_gate.service import evaluate_highrisk_gate
from app.models.risk_flag import RiskFlag, RiskFlagSourceType, RiskFlagStatus
from app.models.users import User


class RiskFlagService:
    def _build_message(self, label: str) -> str:
        return f"{label} — 의료진 확인이 필요한 위험 신호입니다. 담당 의료진 상담을 권고합니다."

    async def create_from_symptom_check(
        self,
        user: User,
        symptom_codes: list[str],
        source_id: int,
    ) -> list[RiskFlag]:
        gate_input = HighRiskGateInput(
            user_id=user.id,
            checked_symptom_codes=symptom_codes,
            self_report_codes=[],
            pregnancy_status_codes=[],
            lab_threshold_exceeded=False,
        )
        result = evaluate_highrisk_gate(gate_input)

        created: list[RiskFlag] = []
        for item in result.matched_items:
            already_active = await RiskFlag.filter(
                user=user,
                source_type=RiskFlagSourceType.SYMPTOM_CHECK,
                flag_code=item.code,
                status=RiskFlagStatus.ACTIVE,
            ).exists()
            if already_active:
                continue
            flag = await RiskFlag.create(
                user=user,
                source_type=RiskFlagSourceType.SYMPTOM_CHECK,
                source_id=source_id,
                flag_code=item.code,
                flag_label=item.label,
                category=item.category,
                message=self._build_message(item.label),
                red_flag=item.red_flag,
                consultation_recommended=True,
                status=RiskFlagStatus.ACTIVE,
            )
            created.append(flag)
        return created

    async def list_flags(
        self,
        user: User,
        status: RiskFlagStatus | None = None,
        source_type: RiskFlagSourceType | None = None,
    ) -> list[RiskFlag]:
        query = RiskFlag.filter(user=user)
        if status is not None:
            query = query.filter(status=status)
        if source_type is not None:
            query = query.filter(source_type=source_type)
        return await query.order_by("-created_at")

    async def get_flag(self, user: User, flag_id: int) -> RiskFlag | None:
        return await RiskFlag.filter(id=flag_id, user=user).first()

    async def update_status(
        self,
        user: User,
        flag_id: int,
        status: RiskFlagStatus,
    ) -> RiskFlag | None:
        flag = await self.get_flag(user, flag_id)
        if flag is None:
            return None
        flag.status = status
        flag.updated_at = datetime.now(config.TIMEZONE)
        await flag.save(update_fields=["status", "updated_at"])
        return flag
