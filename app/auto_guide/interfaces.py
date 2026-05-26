"""REQ-AUTO-005 데이터 소스 수집기 프로토콜.

각 소스 구현체는 이 프로토콜을 준수해야 한다.
Phase 3에서는 StubDataSourceCollector만 제공한다.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class DataSourceCollector(Protocol):
    async def get_autoimmune_mode(self, user_id: int) -> bool:
        """자가면역 모드 활성화 여부 (REQ-MODE-001)."""
        ...

    async def get_disease_codes(self, user_id: int) -> list[str]:
        """등록 질환 코드 목록 (REQ-DISE-001)."""
        ...

    async def get_risk_factor_summary(self, user_id: int) -> str | None:
        """위험 요인 요약 (AUTO-001)."""
        ...

    async def get_medication_list(self, user_id: int) -> list[str]:
        """복용 약물 목록 (AUTO-002)."""
        ...

    async def get_activity_score_summary(self, user_id: int) -> str | None:
        """최근 30일 활성도 점수 요약 (ACTV-001)."""
        ...

    async def get_risk_symptom_codes(self, user_id: int) -> list[str]:
        """체크된 위험 증상 코드 (SYMP-001)."""
        ...

    async def get_upcoming_appointments(self, user_id: int) -> list[str]:
        """예정 진료 일정 (AUTO-004)."""
        ...

    async def get_lab_results_summary(self, user_id: int) -> str | None:
        """검사 결과 요약 (LAB-001)."""
        ...

    async def get_pregnancy_lactation_codes(self, user_id: int) -> list[str]:
        """임신·수유 상태 코드 (AUTO-SAFE-001)."""
        ...

    async def get_vaccine_infection_prevention(self, user_id: int) -> str | None:
        """감염·예방접종 정보 (AUTO-PREV-001)."""
        ...

    async def get_checked_symptom_codes(self, user_id: int) -> list[str]:
        """증상 체크 코드 목록 (SYMP-001 → 게이트 입력)."""
        ...

    async def get_self_report_codes(self, user_id: int) -> list[str]:
        """자가 보고 코드 목록 (결핵·간염 이력 등, AUTO-006 SELF_REPORT 채널)."""
        ...

    async def get_lab_threshold_exceeded(self, user_id: int) -> bool:
        """검사 수치 임계값 초과 여부 (AUTO-006 LAB_THRESHOLD 채널)."""
        ...
