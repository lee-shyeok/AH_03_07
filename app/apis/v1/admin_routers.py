"""NFR-SAFE-003 — 관리자 안전 필터 로그 조회 엔드포인트."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import ORJSONResponse

from app.dependencies.security import get_request_user
from app.dtos.safety_filter_log import SafetyFilterLogItem, SafetyFilterLogListResponse
from app.models.safety_filter_log import SafetyFilterLog
from app.models.users import User

admin_router = APIRouter(prefix="/admin", tags=["admin"])


async def require_admin(user: Annotated[User, Depends(get_request_user)]) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="관리자 권한이 필요합니다.")
    return user


@admin_router.get(
    "/safety-filter-logs",
    response_model=SafetyFilterLogListResponse,
    status_code=status.HTTP_200_OK,
    summary="안전 필터 차단 로그 목록 조회 (NFR-SAFE-003)",
)
async def list_safety_filter_logs(
    _: Annotated[User, Depends(require_admin)],
    from_dt: Annotated[datetime | None, Query(description="조회 시작 시각 (ISO 8601)")] = None,
    to_dt: Annotated[datetime | None, Query(description="조회 종료 시각 (ISO 8601)")] = None,
    user_id: Annotated[int | None, Query(description="특정 사용자 ID 필터")] = None,
    blocked_reason: Annotated[str | None, Query(description="차단 사유 키워드 필터")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ORJSONResponse:
    qs = SafetyFilterLog.all().order_by("-created_at")

    if from_dt is not None:
        qs = qs.filter(created_at__gte=from_dt)
    if to_dt is not None:
        qs = qs.filter(created_at__lte=to_dt)
    if user_id is not None:
        qs = qs.filter(user_id=user_id)
    if blocked_reason is not None:
        qs = qs.filter(blocked_reason__icontains=blocked_reason)

    total = await qs.count()
    logs = await qs.offset(offset).limit(limit)

    items = [SafetyFilterLogItem.from_orm(log) for log in logs]
    payload = SafetyFilterLogListResponse(total=total, items=items)
    return ORJSONResponse(payload.model_dump(mode="json"), status_code=status.HTTP_200_OK)
