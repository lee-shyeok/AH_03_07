from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


from app.core import config
from app.dtos.pre_consultation_report import PreConsultationReportRequest
from app.models.disease_activity_log import DiseaseActivityLog
from app.models.lab_result import LabResult
from app.models.medical_schedule import MedicalSchedule
from app.models.symptom_check_log import SymptomCheckLog
from app.models.user_medication import UserMedication
from app.models.users import User

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


class PreConsultationReportService:
    def __init__(self) -> None:
        self._env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=select_autoescape(["html"]),
        )

    async def generate_pdf(self, user: User, request: PreConsultationReportRequest) -> bytes:
        context = await self._aggregate_data(user, request)
        return self._render_pdf(context)

    async def _aggregate_data(self, user: User, request: PreConsultationReportRequest) -> dict:
        end_date = date.today()
        start_date = end_date - timedelta(days=request.period_days)

        return {
            "user_name": user.name,
            "generated_at": datetime.now(config.TIMEZONE),
            "period_start": start_date,
            "period_end": end_date,
            "medications": await self._get_medications(user),
            "activity_logs": await self._get_activity_logs(user, start_date, end_date),
            "symptom_checks": await self._get_symptom_checks(user, start_date, end_date),
            "lab_results": await self._get_lab_results(user, start_date, end_date),
            "medical_schedules": await self._get_medical_schedules(user, start_date),
            "questions": request.questions or [],
        }

    async def _get_medications(self, user: User) -> list[UserMedication]:
        return await UserMedication.filter(user=user, deleted_at=None).order_by("name")

    async def _get_activity_logs(self, user: User, start_date: date, end_date: date) -> list[DiseaseActivityLog]:
        return await DiseaseActivityLog.filter(
            user=user,
            log_date__gte=start_date,
            log_date__lte=end_date,
        ).order_by("-log_date")

    async def _get_symptom_checks(self, user: User, start_date: date, end_date: date) -> list[SymptomCheckLog]:
        return await SymptomCheckLog.filter(
            user=user,
            created_at__gte=datetime.combine(start_date, datetime.min.time()),
            created_at__lte=datetime.combine(end_date, datetime.max.time()),
        ).order_by("-created_at")

    async def _get_lab_results(self, user: User, start_date: date, end_date: date) -> list[LabResult]:
        return await LabResult.filter(
            user=user,
            deleted_at=None,
            test_date__gte=start_date,
            test_date__lte=end_date,
        ).order_by("-test_date")

    async def _get_medical_schedules(self, user: User, start_date: date) -> list[MedicalSchedule]:
        return await MedicalSchedule.filter(
            user=user,
            deleted_at=None,
            scheduled_date__gte=start_date,
        ).order_by("scheduled_date")

    def _render_pdf(self, context: dict) -> bytes:
        template = self._env.get_template("pre_consultation_report.html")
        html_str = template.render(**context)
        stylesheets = [str(TEMPLATE_DIR / "pre_consultation_report.css")]
        from weasyprint import HTML
        return HTML(string=html_str, base_url=str(TEMPLATE_DIR)).write_pdf(
            stylesheets=stylesheets,
        )
