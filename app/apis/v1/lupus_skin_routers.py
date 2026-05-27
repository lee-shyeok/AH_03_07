from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import ORJSONResponse

from app.dependencies.security import get_request_user
from app.dtos.lupus_skin import LupusSkinLogCreateRequest, LupusSkinLogResponse, LupusSkinLogUpdateRequest
from app.models.users import User
from app.services.lupus_skin_service import LupusSkinLogService

lupus_skin_router = APIRouter(prefix="/lupus-skin-logs", tags=["lupus-skin-logs"])


@lupus_skin_router.post("", response_model=LupusSkinLogResponse, status_code=status.HTTP_201_CREATED)
async def create_lupus_skin_log(
    body: LupusSkinLogCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[LupusSkinLogService, Depends(LupusSkinLogService)],
) -> ORJSONResponse:
    log = await service.create_log(user=user, data=body)
    return ORJSONResponse(
        LupusSkinLogResponse.model_validate(log).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@lupus_skin_router.get("", response_model=list[LupusSkinLogResponse], status_code=status.HTTP_200_OK)
async def list_lupus_skin_logs(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[LupusSkinLogService, Depends(LupusSkinLogService)],
) -> ORJSONResponse:
    logs = await service.list_logs(user=user)
    return ORJSONResponse(
        [LupusSkinLogResponse.model_validate(log).model_dump() for log in logs],
        status_code=status.HTTP_200_OK,
    )


@lupus_skin_router.get("/{log_id}", response_model=LupusSkinLogResponse, status_code=status.HTTP_200_OK)
async def get_lupus_skin_log(
    log_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[LupusSkinLogService, Depends(LupusSkinLogService)],
) -> ORJSONResponse:
    log = await service.get_log(user=user, log_id=log_id)
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lupus skin log not found.")
    return ORJSONResponse(
        LupusSkinLogResponse.model_validate(log).model_dump(),
        status_code=status.HTTP_200_OK,
    )


@lupus_skin_router.patch("/{log_id}", response_model=LupusSkinLogResponse, status_code=status.HTTP_200_OK)
async def update_lupus_skin_log(
    log_id: int,
    body: LupusSkinLogUpdateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[LupusSkinLogService, Depends(LupusSkinLogService)],
) -> ORJSONResponse:
    log = await service.update_log(user=user, log_id=log_id, data=body)
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lupus skin log not found.")
    return ORJSONResponse(
        LupusSkinLogResponse.model_validate(log).model_dump(),
        status_code=status.HTTP_200_OK,
    )


@lupus_skin_router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lupus_skin_log(
    log_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[LupusSkinLogService, Depends(LupusSkinLogService)],
) -> Response:
    deleted = await service.delete_log(user=user, log_id=log_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lupus skin log not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
