import io
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response
from fastapi.responses import StreamingResponse

from app.dependencies.consent import require_consent
from app.dependencies.security import get_request_user
from app.dtos.diary_logs import (
    MedicationLogCreateRequest,
    MedicationLogListResponse,
    MedicationLogResponse,
    SymptomLogCreateRequest,
    SymptomLogListResponse,
    SymptomLogResponse,
)
from app.models.user_consents import ConsentType
from app.models.users import User
from app.services.diary_logs import DiaryLogService

diary_log_router = APIRouter(prefix="/diary", tags=["diary-logs"])

# ========== 증상 기록 API ==========


@diary_log_router.get(
    "/symptom-logs",
    response_model=SymptomLogListResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_consent(ConsentType.MEDICAL_DATA))],
)
async def get_my_symptom_logs(
    user: Annotated[User, Depends(get_request_user)],
    diary_service: Annotated[DiaryLogService, Depends(DiaryLogService)],
) -> Response:
    """내 증상 기록 조회"""
    result = await diary_service.get_symptom_logs(user_id=user.id)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_200_OK)


@diary_log_router.post(
    "/symptom-logs",
    response_model=SymptomLogResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_consent(ConsentType.MEDICAL_DATA))],
)
async def create_symptom_log(
    request: SymptomLogCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    diary_service: Annotated[DiaryLogService, Depends(DiaryLogService)],
) -> Response:
    """증상 기록 생성"""
    result = await diary_service.create_symptom_log(user_id=user.id, data=request)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_201_CREATED)


# ========== 복약 기록 API ==========


@diary_log_router.get(
    "/medication-logs",
    response_model=MedicationLogListResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_consent(ConsentType.MEDICAL_DATA))],
)
async def get_my_medication_logs(
    user: Annotated[User, Depends(get_request_user)],
    diary_service: Annotated[DiaryLogService, Depends(DiaryLogService)],
) -> Response:
    """내 복약 기록 조회"""
    result = await diary_service.get_medication_logs(user_id=user.id)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_200_OK)


@diary_log_router.post(
    "/medication-logs",
    response_model=MedicationLogResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_consent(ConsentType.MEDICAL_DATA))],
)
async def create_medication_log(
    request: MedicationLogCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    diary_service: Annotated[DiaryLogService, Depends(DiaryLogService)],
) -> Response:
    """복약 기록 생성"""
    result = await diary_service.create_medication_log(user_id=user.id, data=request)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_201_CREATED)


# ========== PDF 출력 ==========


@diary_log_router.get(
    "/pdf",
    status_code=status.HTTP_200_OK,
    response_class=StreamingResponse,
    dependencies=[Depends(require_consent(ConsentType.MEDICAL_DATA))],
)
async def get_diary_pdf(
    user: Annotated[User, Depends(get_request_user)],
    diary_service: Annotated[DiaryLogService, Depends(DiaryLogService)],
) -> StreamingResponse:
    """일기 PDF 출력 — 증상·복약 별도 섹션 (REQ-DIARY-001)"""
    pdf_bytes = await diary_service.generate_pdf_bytes(user.id)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=diary.pdf"},
    )
