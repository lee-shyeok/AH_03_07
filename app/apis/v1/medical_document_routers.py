from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query, UploadFile, status
from fastapi.responses import JSONResponse as Response

from app.dependencies.auth import get_current_user
from app.dtos.medical_document import (
    MedicalDocumentListResponse,
    MedicalDocumentResponse,
    MedicalDocumentUploadResponse,
    OcrConfirmRequest,
    OcrConfirmResponse,
    OcrJobResultResponse,
    OcrJobStartResponse,
)
from app.models.users import User
from app.services.medical_document_service import MedicalDocumentService

medical_document_router = APIRouter(prefix="/medical-documents", tags=["medical-documents"])
ocr_job_router = APIRouter(prefix="/ocr-jobs", tags=["ocr-jobs"])


@medical_document_router.post("", status_code=status.HTTP_201_CREATED, response_model=MedicalDocumentUploadResponse)
async def upload_document(
    file: UploadFile,
    document_type: Annotated[str, Form()],
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[MedicalDocumentService, Depends(MedicalDocumentService)],
) -> Response:
    result = await service.upload_document(current_user, file, document_type)
    return Response(content=result.model_dump(mode="json"), status_code=status.HTTP_201_CREATED)


@medical_document_router.get("", status_code=status.HTTP_200_OK, response_model=list[MedicalDocumentListResponse])
async def list_documents(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[MedicalDocumentService, Depends(MedicalDocumentService)],
    document_type: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=50)] = 10,
) -> Response:
    result = await service.list_documents(current_user, document_type, page, size)
    return Response(content=[r.model_dump(mode="json") for r in result], status_code=status.HTTP_200_OK)


@medical_document_router.get("/{document_id}", status_code=status.HTTP_200_OK, response_model=MedicalDocumentResponse)
async def get_document(
    document_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[MedicalDocumentService, Depends(MedicalDocumentService)],
) -> Response:
    result = await service.get_document(current_user, document_id)
    return Response(content=result.model_dump(mode="json"), status_code=status.HTTP_200_OK)


@medical_document_router.post(
    "/{document_id}/ocr-jobs", status_code=status.HTTP_202_ACCEPTED, response_model=OcrJobStartResponse
)
async def start_ocr_job(
    document_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[MedicalDocumentService, Depends(MedicalDocumentService)],
) -> Response:
    result = await service.start_ocr_job(current_user, document_id)
    return Response(content=result.model_dump(mode="json"), status_code=status.HTTP_202_ACCEPTED)


@medical_document_router.put(
    "/{document_id}/confirm", status_code=status.HTTP_200_OK, response_model=OcrConfirmResponse
)
async def confirm_ocr_result(
    document_id: str,
    request: OcrConfirmRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[MedicalDocumentService, Depends(MedicalDocumentService)],
) -> Response:
    result = await service.confirm_ocr_result(
        current_user, document_id, request.structured_data, request.user_confirmed
    )
    return Response(content=result.model_dump(mode="json"), status_code=status.HTTP_200_OK)


@medical_document_router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[MedicalDocumentService, Depends(MedicalDocumentService)],
) -> None:
    await service.delete_document(current_user, document_id)


@ocr_job_router.get("/{job_id}", status_code=status.HTTP_200_OK, response_model=OcrJobResultResponse)
async def get_ocr_result(
    job_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[MedicalDocumentService, Depends(MedicalDocumentService)],
) -> Response:
    result = await service.get_ocr_result(current_user, job_id)
    return Response(content=result.model_dump(mode="json"), status_code=status.HTTP_200_OK)