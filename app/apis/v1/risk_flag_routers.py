from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import ORJSONResponse

from app.dependencies.security import get_request_user
from app.dtos.risk_flag import RiskFlagItem, RiskFlagStatusUpdateRequest
from app.models.risk_flag import RiskFlagSourceType, RiskFlagStatus
from app.models.users import User
from app.services.risk_flag_service import RiskFlagService

risk_flag_router = APIRouter(prefix="/risk-flags", tags=["risk-flags"])


@risk_flag_router.get("", response_model=list[RiskFlagItem], status_code=status.HTTP_200_OK)
async def list_risk_flags(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[RiskFlagService, Depends(RiskFlagService)],
    flag_status: RiskFlagStatus | None = None,
    source_type: RiskFlagSourceType | None = None,
) -> ORJSONResponse:
    flags = await service.list_flags(user, status=flag_status, source_type=source_type)
    return ORJSONResponse(
        [RiskFlagItem.model_validate(f).model_dump(mode="json") for f in flags],
        status_code=status.HTTP_200_OK,
    )


@risk_flag_router.get("/{flag_id}", response_model=RiskFlagItem, status_code=status.HTTP_200_OK)
async def get_risk_flag(
    flag_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[RiskFlagService, Depends(RiskFlagService)],
) -> ORJSONResponse:
    flag = await service.get_flag(user, flag_id)
    if flag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="플래그를 찾을 수 없습니다")
    return ORJSONResponse(
        RiskFlagItem.model_validate(flag).model_dump(mode="json"),
        status_code=status.HTTP_200_OK,
    )


@risk_flag_router.patch("/{flag_id}", response_model=RiskFlagItem, status_code=status.HTTP_200_OK)
async def update_risk_flag_status(
    flag_id: int,
    body: RiskFlagStatusUpdateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[RiskFlagService, Depends(RiskFlagService)],
) -> ORJSONResponse:
    flag = await service.update_status(user, flag_id, body.status)
    if flag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="플래그를 찾을 수 없습니다")
    return ORJSONResponse(
        RiskFlagItem.model_validate(flag).model_dump(mode="json"),
        status_code=status.HTTP_200_OK,
    )


@risk_flag_router.delete("/{flag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_risk_flag(
    flag_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[RiskFlagService, Depends(RiskFlagService)],
) -> None:
    flag = await service.get_flag(user, flag_id)
    if flag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="플래그를 찾을 수 없습니다")
    if flag.status == RiskFlagStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="ACTIVE 플래그는 삭제할 수 없습니다")
    await service.delete_flag(user, flag_id)
