from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import ORJSONResponse

from app.dependencies.security import get_request_user
from app.dtos.autoimmune import DiseaseBulkCreateRequest, DiseaseResponse, DiseaseUpdateRequest
from app.models.users import User
from app.services.autoimmune_service import DiseaseService

disease_router = APIRouter(prefix="/diseases", tags=["diseases"])


@disease_router.post("", response_model=list[DiseaseResponse], status_code=status.HTTP_201_CREATED)
async def create_diseases(
    body: DiseaseBulkCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[DiseaseService, Depends(DiseaseService)],
) -> ORJSONResponse:
    diseases = await service.create_diseases(user=user, data=body)
    return ORJSONResponse(
        [DiseaseResponse.model_validate(d).model_dump() for d in diseases],
        status_code=status.HTTP_201_CREATED,
    )


@disease_router.get("", response_model=list[DiseaseResponse], status_code=status.HTTP_200_OK)
async def list_diseases(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[DiseaseService, Depends(DiseaseService)],
) -> ORJSONResponse:
    diseases = await service.list_diseases(user=user)
    return ORJSONResponse(
        [DiseaseResponse.model_validate(d).model_dump() for d in diseases],
        status_code=status.HTTP_200_OK,
    )


@disease_router.patch("/{disease_id}", response_model=DiseaseResponse, status_code=status.HTTP_200_OK)
async def update_disease(
    disease_id: int,
    body: DiseaseUpdateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[DiseaseService, Depends(DiseaseService)],
) -> ORJSONResponse:
    disease = await service.update_disease(user=user, disease_id=disease_id, data=body)
    if disease is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Disease not found.")
    return ORJSONResponse(DiseaseResponse.model_validate(disease).model_dump(), status_code=status.HTTP_200_OK)


@disease_router.delete("/{disease_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_disease(
    disease_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[DiseaseService, Depends(DiseaseService)],
) -> Response:
    deleted = await service.delete_disease(user=user, disease_id=disease_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Disease not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
