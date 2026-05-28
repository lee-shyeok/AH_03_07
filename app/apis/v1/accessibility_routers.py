from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.security import get_request_user
from app.dtos.accessibility_settings import (
    AccessibilitySettingResponse,
    AccessibilitySettingUpdateRequest,
)
from app.models.users import User
from app.services.accessibility_settings import AccessibilityService

accessibility_router = APIRouter(prefix="/accessibility", tags=["accessibility"])


@accessibility_router.get("/me", response_model=AccessibilitySettingResponse)
async def get_my_setting(
    user: Annotated[User, Depends(get_request_user)],
):
    """내 접근성 설정 조회"""
    service = AccessibilityService()
    return await service.get_my_setting(user.id)


@accessibility_router.put("/me", response_model=AccessibilitySettingResponse)
async def update_my_setting(
    data: AccessibilitySettingUpdateRequest,
    user: Annotated[User, Depends(get_request_user)],
):
    """내 접근성 설정 업데이트"""
    service = AccessibilityService()
    return await service.update_my_setting(user.id, data)
