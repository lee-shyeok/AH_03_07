from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import ORJSONResponse

from app.dependencies.security import get_request_user
from app.dtos.autoimmune_profile import MedicationBulkCreateRequest, MedicationResponse, MedicationUpdateRequest
from app.models.users import User
from app.services.autoimmune_profile_service import MedicationService

medication_router = APIRouter(prefix="/medications", tags=["medications"])


@medication_router.post("", response_model=list[MedicationResponse], status_code=status.HTTP_201_CREATED)
async def create_medications(
    body: MedicationBulkCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[MedicationService, Depends(MedicationService)],
) -> ORJSONResponse:
    medications = await service.create_medications(user=user, data=body)
    return ORJSONResponse(
        [MedicationResponse.model_validate(m).model_dump() for m in medications],
        status_code=status.HTTP_201_CREATED,
    )


@medication_router.get("", response_model=list[MedicationResponse], status_code=status.HTTP_200_OK)
async def list_medications(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[MedicationService, Depends(MedicationService)],
) -> ORJSONResponse:
    medications = await service.list_medications(user=user)
    return ORJSONResponse(
        [MedicationResponse.model_validate(m).model_dump() for m in medications],
        status_code=status.HTTP_200_OK,
    )


@medication_router.patch("/{medication_id}", response_model=MedicationResponse, status_code=status.HTTP_200_OK)
async def update_medication(
    medication_id: int,
    body: MedicationUpdateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[MedicationService, Depends(MedicationService)],
) -> ORJSONResponse:
    med = await service.update_medication(user=user, medication_id=medication_id, data=body)
    if med is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found.")
    return ORJSONResponse(MedicationResponse.model_validate(med).model_dump(), status_code=status.HTTP_200_OK)


@medication_router.delete("/{medication_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medication(
    medication_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[MedicationService, Depends(MedicationService)],
) -> Response:
    deleted = await service.delete_medication(user=user, medication_id=medication_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
