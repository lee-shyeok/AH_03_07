from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.consent import require_consent
from app.dependencies.security import get_request_user
from app.dtos.prescriptions import (
    PrescriptionConfirmRequest,
    PrescriptionCreateRequest,
    PrescriptionListResponse,
    PrescriptionResponse,
)
from app.models.user_consents import ConsentType
from app.models.users import User
from app.services.prescriptions import PrescriptionService

prescription_router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])


@prescription_router.get(
    "",
    response_model=PrescriptionListResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_consent(ConsentType.MEDICAL_DATA))],
)
async def get_my_prescriptions(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[PrescriptionService, Depends(PrescriptionService)],
) -> Response:
    """내 처방전 목록 조회"""
    result = await service.get_my_prescriptions(user_id=user.id)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_200_OK)


@prescription_router.post(
    "",
    response_model=PrescriptionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_consent(ConsentType.MEDICAL_DATA))],
)
async def upload_prescription(
    request: PrescriptionCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[PrescriptionService, Depends(PrescriptionService)],
) -> Response:
    """처방전 업로드 + OCR 추출 (OpenAI Vision 사용!)"""
    result = await service.upload_and_extract(user_id=user.id, data=request)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_201_CREATED)


@prescription_router.patch(
    "/{prescription_id}/confirm",
    response_model=PrescriptionResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_consent(ConsentType.MEDICAL_DATA))],
)
async def confirm_prescription(
    prescription_id: int,
    request: PrescriptionConfirmRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[PrescriptionService, Depends(PrescriptionService)],
) -> Response:
    """처방전 사용자 확인 (OCR 결과 수정)"""
    result = await service.confirm_prescription(
        user_id=user.id,
        prescription_id=prescription_id,
        data=request,
    )
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_200_OK)
