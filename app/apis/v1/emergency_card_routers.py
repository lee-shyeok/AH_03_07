from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.consent import require_consent
from app.dependencies.security import get_request_user
from app.dtos.emergency_cards import EmergencyCardCreateRequest, EmergencyCardResponse
from app.models.user_consents import ConsentType
from app.models.users import User
from app.services.emergency_cards import EmergencyCardService

emergency_card_router = APIRouter(prefix="/emergency-cards", tags=["emergency-cards"])


@emergency_card_router.get(
    "/me",
    response_model=EmergencyCardResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_consent(ConsentType.MEDICAL_DATA))],
)
async def get_my_emergency_card(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[EmergencyCardService, Depends(EmergencyCardService)],
) -> Response:
    """내 응급 카드 조회"""
    result = await service.get_my_card(user_id=user.id)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_200_OK)


@emergency_card_router.post(
    "/me",
    response_model=EmergencyCardResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_consent(ConsentType.MEDICAL_DATA))],
)
async def create_or_update_emergency_card(
    request: EmergencyCardCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[EmergencyCardService, Depends(EmergencyCardService)],
) -> Response:
    """응급 카드 생성/수정"""
    result = await service.create_or_update_card(user_id=user.id, data=request)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_201_CREATED)
