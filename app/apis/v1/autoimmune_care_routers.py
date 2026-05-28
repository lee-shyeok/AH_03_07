from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse

from app.dependencies.security import get_request_user
from app.dtos.autoimmune_care import (
    MedicationCardListResponse,
    PregnancySafetyResponse,
    VaccinePreventionResponse,
)
from app.models.users import User
from app.services.autoimmune_care_service import (
    MedicationCardService,
    PregnancySafetyService,
    VaccinePreventionService,
)

medication_card_router = APIRouter(prefix="/medication-cards", tags=["medication-cards"])
pregnancy_safety_router = APIRouter(prefix="/pregnancy-safety", tags=["pregnancy-safety"])
vaccine_prevention_router = APIRouter(prefix="/vaccine-prevention-info", tags=["vaccine-prevention-info"])


@medication_card_router.get("", response_model=MedicationCardListResponse)
async def get_medication_cards(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[MedicationCardService, Depends(MedicationCardService)],
) -> ORJSONResponse:
    result = await service.get_cards(user=user)
    return ORJSONResponse(result.model_dump())


@pregnancy_safety_router.get("", response_model=PregnancySafetyResponse)
async def get_pregnancy_safety(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[PregnancySafetyService, Depends(PregnancySafetyService)],
) -> ORJSONResponse:
    result = await service.get_guidance(user=user)
    return ORJSONResponse(result.model_dump())


@vaccine_prevention_router.get("", response_model=VaccinePreventionResponse)
async def get_vaccine_prevention_info(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[VaccinePreventionService, Depends(VaccinePreventionService)],
) -> ORJSONResponse:
    result = service.get_info()
    return ORJSONResponse(result.model_dump())
