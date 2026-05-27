from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.dependencies.security import get_request_user
from app.dtos.pre_consultation_report import PreConsultationReportRequest
from app.models.users import User
from app.services.pre_consultation_report_service import PreConsultationReportService

pre_consultation_report_router = APIRouter(
    prefix="/pre-consultation-reports",
    tags=["pre-consultation-reports"],
)


@pre_consultation_report_router.post(
    "/pdf",
    status_code=status.HTTP_200_OK,
    responses={200: {"content": {"application/pdf": {}}}},
)
async def generate_pre_consultation_report_pdf(
    body: PreConsultationReportRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[PreConsultationReportService, Depends(PreConsultationReportService)],
) -> Response:
    pdf_bytes = await service.generate_pdf(user, body)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="pre_consultation_report.pdf"'},
    )
