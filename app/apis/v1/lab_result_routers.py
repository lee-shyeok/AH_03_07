from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import ORJSONResponse

from app.dependencies.security import get_request_user
from app.dtos.autoimmune_medical import (
    LabResultCreateRequest,
    LabResultResponse,
    LabResultUpdateRequest,
)
from app.models.users import User
from app.services.autoimmune_medical_service import LabResultService

lab_result_router = APIRouter(prefix="/lab-results", tags=["lab-results"])


@lab_result_router.post("", response_model=LabResultResponse, status_code=status.HTTP_201_CREATED)
async def create_lab_result(
    body: LabResultCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[LabResultService, Depends(LabResultService)],
) -> ORJSONResponse:
    result = await service.create_result(user=user, data=body)
    return ORJSONResponse(
        LabResultResponse.model_validate(result).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@lab_result_router.get("", response_model=list[LabResultResponse], status_code=status.HTTP_200_OK)
async def list_lab_results(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[LabResultService, Depends(LabResultService)],
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
) -> ORJSONResponse:
    results = await service.list_results(user=user, from_date=from_date, to_date=to_date)
    return ORJSONResponse(
        [LabResultResponse.model_validate(r).model_dump() for r in results],
        status_code=status.HTTP_200_OK,
    )


@lab_result_router.patch("/{result_id}", response_model=LabResultResponse, status_code=status.HTTP_200_OK)
async def update_lab_result(
    result_id: int,
    body: LabResultUpdateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[LabResultService, Depends(LabResultService)],
) -> ORJSONResponse:
    result = await service.update_result(user=user, result_id=result_id, data=body)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab result not found.")
    return ORJSONResponse(
        LabResultResponse.model_validate(result).model_dump(),
        status_code=status.HTTP_200_OK,
    )


@lab_result_router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lab_result(
    result_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[LabResultService, Depends(LabResultService)],
) -> Response:
    deleted = await service.delete_result(user=user, result_id=result_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab result not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
