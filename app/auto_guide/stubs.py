"""REQ-AUTO-005 Phase 3 스텁 구현체.

실제 소스 구현(Phase 4+)이 완료될 때까지 오케스트레이터가 사용하는 기본값 반환 구현체.
"""


class StubDataSourceCollector:
    async def get_autoimmune_mode(self, user_id: int) -> bool:
        return False

    async def get_disease_codes(self, user_id: int) -> list[str]:
        return []

    async def get_risk_factor_summary(self, user_id: int) -> str | None:
        return None

    async def get_medication_list(self, user_id: int) -> list[str]:
        return []

    async def get_activity_score_summary(self, user_id: int) -> str | None:
        return None

    async def get_risk_symptom_codes(self, user_id: int) -> list[str]:
        return []

    async def get_upcoming_appointments(self, user_id: int) -> list[str]:
        return []

    async def get_lab_results_summary(self, user_id: int) -> str | None:
        return None

    async def get_pregnancy_lactation_codes(self, user_id: int) -> list[str]:
        return []

    async def get_vaccine_infection_prevention(self, user_id: int) -> str | None:
        return None

    async def get_checked_symptom_codes(self, user_id: int) -> tuple[list[str], bool]:
        return [], False

    async def get_self_report_codes(self, user_id: int) -> list[str]:
        return []

    async def get_lab_threshold_exceeded(self, user_id: int) -> bool:
        return False
