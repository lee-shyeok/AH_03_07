import base64
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.core.logger import default_logger as logger
from app.dependencies.security import get_request_user
from app.dtos.pre_consultation_report import (
    PreConsultationReportRequest,
    ReportCreatedResponse,
    ReportShareRequest,
    ReportShareResponse,
    ReportStatusResponse,
)
from app.models.pre_consultation_report import PreConsultationReport, ReportStatus
from app.models.users import User
from app.services.pre_consultation_report_service import PreConsultationReportService

pre_consultation_report_router = APIRouter(
    prefix="/reports",
    tags=["reports"],
)


async def _run_report_job(report_id: int, request: PreConsultationReportRequest) -> None:
    report = await PreConsultationReport.get_or_none(id=report_id)
    if report is None:
        logger.error(f"report job: report {report_id} not found")
        return
    try:
        report.status = ReportStatus.PROCESSING
        await report.save()

        user = await report.user
        service = PreConsultationReportService()
        pdf_bytes = await service.generate_pdf(user, request)

        report.pdf = pdf_bytes
        report.status = ReportStatus.COMPLETED
        await report.save()
    except Exception:
        logger.exception(f"report job {report_id} failed")
        report.status = ReportStatus.FAILED
        report.error_message = "internal error during report generation"
        await report.save()


@pre_consultation_report_router.post(
    "/pre-visit",
    response_model=ReportCreatedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_pre_visit_report(
    body: PreConsultationReportRequest,
    background_tasks: BackgroundTasks,
    user: Annotated[User, Depends(get_request_user)],
) -> ReportCreatedResponse:
    report = await PreConsultationReport.create(
        user_id=user.id,
        status=ReportStatus.PENDING,
        visit_date=body.visit_date,
        period_days=body.period_days,
    )
    background_tasks.add_task(_run_report_job, report.id, body)
    return ReportCreatedResponse(report_id=report.id, status=report.status)


@pre_consultation_report_router.get(
    "/{report_id}",
    response_model=ReportStatusResponse,
)
async def get_report(
    report_id: int,
    user: Annotated[User, Depends(get_request_user)],
) -> ReportStatusResponse:
    report = await PreConsultationReport.get_or_none(id=report_id, user_id=user.id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="리포트를 찾을 수 없습니다.",
        )

    pdf_base64 = None
    if report.status == ReportStatus.COMPLETED and report.pdf is not None:
        pdf_base64 = base64.b64encode(report.pdf).decode()

    return ReportStatusResponse(
        id=report.id,
        status=report.status,
        visit_date=report.visit_date,
        created_at=report.created_at,
        pdf_base64=pdf_base64,
    )


@pre_consultation_report_router.post(
    "/{report_id}/share",
    response_model=ReportShareResponse,
    status_code=status.HTTP_201_CREATED,
)
async def share_report(
    report_id: int,
    body: ReportShareRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[PreConsultationReportService, Depends(PreConsultationReportService)],
) -> ReportShareResponse:
    report = await PreConsultationReport.get_or_none(id=report_id, user_id=user.id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="리포트를 찾을 수 없습니다.",
        )
    if report.status != ReportStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="리포트가 아직 완료되지 않았습니다.",
        )

    token = await service.create_share(report, body.recipient_email)
    return ReportShareResponse(secure_link_token=token)
