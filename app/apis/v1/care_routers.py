from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies.security import get_request_user
from app.dtos.care import (
    GuardianCreateRequest,
    GuardianListResponse,
    GuardianResponse,
    ShareLinkCreateRequest,
    ShareLinkListResponse,
    ShareLinkResponse,
)
from app.models.users import User
from app.services.care import CareService

care_router = APIRouter(prefix="/care", tags=["care"])


@care_router.post("/guardians", response_model=GuardianResponse, status_code=status.HTTP_201_CREATED)
async def create_guardian(
    data: GuardianCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
):
    """보호자 등록"""
    service = CareService()
    return await service.create_guardian(user.id, data)


@care_router.get("/guardians", response_model=GuardianListResponse)
async def get_my_guardians(
    user: Annotated[User, Depends(get_request_user)],
):
    """내 보호자 목록"""
    service = CareService()
    return await service.get_my_guardians(user.id)


@care_router.post("/share-links", response_model=ShareLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_share_link(
    data: ShareLinkCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
):
    """공유 링크 생성"""
    service = CareService()
    return await service.create_share_link(user.id, data)


@care_router.get("/share-links", response_model=ShareLinkListResponse)
async def get_my_share_links(
    user: Annotated[User, Depends(get_request_user)],
):
    """내 공유 링크 목록"""
    service = CareService()
    return await service.get_my_share_links(user.id)


@care_router.delete("/share-links/{link_id}", response_model=ShareLinkResponse)
async def revoke_share_link(
    link_id: UUID,
    user: Annotated[User, Depends(get_request_user)],
):
    """공유 링크 철회"""
    service = CareService()
    return await service.revoke_share_link(link_id)
