from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.dependencies.security import get_request_user
from app.dtos.care import (
    GuardianCreateRequest,
    GuardianListResponse,
    GuardianResponse,
    GuardianViewResponse,
    ShareLinkCreateRequest,
    ShareLinkListResponse,
    ShareLinkResponse,
)
from app.models.users import User
from app.services.care import CareService

care_router = APIRouter(prefix="/guardians", tags=["guardians"])


@care_router.post("", response_model=GuardianResponse, status_code=status.HTTP_201_CREATED)
async def create_guardian(
    data: GuardianCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
):
    """보호자 등록"""
    service = CareService()
    return await service.create_guardian(user.id, data)


@care_router.get("", response_model=GuardianListResponse)
async def get_my_guardians(
    user: Annotated[User, Depends(get_request_user)],
):
    """내 보호자 목록"""
    service = CareService()
    return await service.get_my_guardians(user.id)


@care_router.post("/shares", response_model=ShareLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_share_link(
    data: ShareLinkCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
):
    """보호자 공유 링크 생성"""
    service = CareService()
    return await service.create_share_link(user.id, data)


@care_router.get("/shares", response_model=ShareLinkListResponse)
async def get_my_share_links(
    user: Annotated[User, Depends(get_request_user)],
):
    """내 보호자 공유 목록"""
    service = CareService()
    return await service.get_my_share_links(user.id)


@care_router.delete("/shares/{id}", response_model=ShareLinkResponse)
async def revoke_share_link(
    id: UUID,
    user: Annotated[User, Depends(get_request_user)],
):
    """보호자 공유 철회"""
    service = CareService()
    return await service.revoke_share_link(id)


@care_router.get("/view/{token}", response_model=GuardianViewResponse)
async def view_share(
    token: str,
    request: Request,
):
    """보호자 본인 인증 후 의료정보 열람 (토큰 기반, 인증 불필요)"""
    service = CareService()
    viewer_ip = request.client.host if request.client else None
    return await service.view_share_link(token, viewer_ip)
