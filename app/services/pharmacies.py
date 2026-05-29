from decimal import Decimal

from app.dtos.pharmacies import (
    PharmacyCreateRequest,
    PharmacyListResponse,
    PharmacyResponse,
)
from app.repositories.pharmacy_repository import PharmacyRepository


class PharmacyService:
    """약국 비즈니스 로직"""

    def __init__(self):
        self.repo = PharmacyRepository()

    async def get_all_pharmacies(self) -> PharmacyListResponse:
        """모든 약국 조회"""
        pharmacies = await self.repo.get_all()
        return PharmacyListResponse(
            pharmacies=[PharmacyResponse.model_validate(p) for p in pharmacies],
            total=len(pharmacies),
        )

    async def search_nearby(
        self, latitude: Decimal, longitude: Decimal, radius_km: float = 5.0
    ) -> PharmacyListResponse:
        """위치 기반 약국 검색"""
        pharmacies = await self.repo.search_nearby(latitude, longitude, radius_km)
        return PharmacyListResponse(
            pharmacies=[PharmacyResponse.model_validate(p) for p in pharmacies],
            total=len(pharmacies),
        )

    async def create_pharmacy(self, data: PharmacyCreateRequest) -> PharmacyResponse:
        """약국 등록 (관리자/공공데이터용)"""
        pharmacy = await self.repo.create(
            name=data.name,
            address=data.address,
            phone=data.phone,
            latitude=data.latitude,
            longitude=data.longitude,
            operating_hours=data.operating_hours,
            is_24h_available=data.is_24h_available,
            is_holiday_available=data.is_holiday_available,
        )
        return PharmacyResponse.model_validate(pharmacy)
