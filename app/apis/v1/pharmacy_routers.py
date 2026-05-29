from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.dependencies.security import get_request_user
from app.dtos.pharmacies import (
    PharmacyCreateRequest,
    PharmacyListResponse,
    PharmacyResponse,
)
from app.models.users import User
from app.services.pharmacies import PharmacyService

pharmacy_router = APIRouter(prefix="/pharmacies", tags=["pharmacies"])


@pharmacy_router.get("", response_model=PharmacyListResponse)
async def get_all_pharmacies(
    user: Annotated[User, Depends(get_request_user)],
):
    """모든 약국 조회"""
    service = PharmacyService()
    return await service.get_all_pharmacies()


@pharmacy_router.get("/nearby", response_model=PharmacyListResponse)
async def search_nearby(
    latitude: Annotated[Decimal, Query(...)],
    longitude: Annotated[Decimal, Query(...)],
    radius_km: Annotated[float, Query()] = 5.0,
    user: User = Depends(get_request_user),
):
    """위치 기반 약국 검색"""
    service = PharmacyService()
    return await service.search_nearby(latitude, longitude, radius_km)


@pharmacy_router.post("", response_model=PharmacyResponse, status_code=status.HTTP_201_CREATED)
async def create_pharmacy(
    data: PharmacyCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
):
    """약국 등록 (테스트용/관리자)"""
    service = PharmacyService()
    return await service.create_pharmacy(data)
