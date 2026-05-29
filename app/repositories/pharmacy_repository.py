from decimal import Decimal
from uuid import UUID

from app.models.pharmacies import Pharmacy


class PharmacyRepository:
    """약국 DB 쿼리"""

    @staticmethod
    async def get_all() -> list[Pharmacy]:
        """모든 약국 조회"""
        return await Pharmacy.all()

    @staticmethod
    async def get_by_id(pharmacy_id: UUID) -> Pharmacy | None:
        """특정 약국 조회"""
        return await Pharmacy.filter(id=pharmacy_id).first()

    @staticmethod
    async def create(**kwargs) -> Pharmacy:
        """약국 생성 (공공데이터 import용)"""
        return await Pharmacy.create(**kwargs)

    @staticmethod
    async def search_nearby(latitude: Decimal, longitude: Decimal, radius_km: float = 5.0) -> list[Pharmacy]:
        """위치 기반 약국 검색 (간단판: 모든 약국 반환)"""
        return await Pharmacy.all()
