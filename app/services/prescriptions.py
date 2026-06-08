from datetime import date, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from openai import OpenAI

from app.core import config
from app.dtos.prescriptions import (
    PrescriptionConfirmRequest,
    PrescriptionCreateRequest,
    PrescriptionListResponse,
    PrescriptionResponse,
)
from app.models.notifications import NotificationType
from app.models.prescriptions import OCRStatus
from app.repositories.medication_repository import MedicationRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.prescription_repository import PrescriptionRepository


class PrescriptionService:
    """처방전 OCR 비즈니스 로직"""

    def __init__(self):
        self.repo = PrescriptionRepository()
        self.med_repo = MedicationRepository()
        self.noti_repo = NotificationRepository()
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)

    @staticmethod
    def adjust_to_weekday(target_date: date) -> date:
        while target_date.weekday() >= 5:
            target_date = target_date - timedelta(days=1)
        return target_date

    async def calculate_progress(self, prescription) -> dict:
        if not prescription.prescription_date:
            return {}

        medications = await self.med_repo.get_by_prescription(prescription.id)
        max_days = 0
        for med in medications:
            if med.duration_days and med.duration_days > max_days:
                max_days = med.duration_days

        if max_days == 0:
            return {}

        start = prescription.prescription_date
        end = start + timedelta(days=max_days)
        today = date.today()

        elapsed = (today - start).days
        progress = min(100, max(0, int(elapsed / max_days * 100)))
        remaining = max(0, (end - today).days)

        return {
            "end_date": end,
            "progress_percentage": progress,
            "days_remaining": remaining,
            "is_near_end": progress >= 80,
        }

    async def build_response(self, prescription) -> PrescriptionResponse:
        progress_info = await self.calculate_progress(prescription)
        response = PrescriptionResponse.model_validate(prescription)
        for key, value in progress_info.items():
            setattr(response, key, value)
        return response

    async def get_my_prescriptions(self, user_id: UUID) -> PrescriptionListResponse:
        prescriptions = await self.repo.get_user_prescriptions(user_id)
        responses = []
        for p in prescriptions:
            responses.append(await self.build_response(p))
        return PrescriptionListResponse(prescriptions=responses, total=len(responses))

    async def upload_and_extract(self, user_id: UUID, data: PrescriptionCreateRequest) -> PrescriptionResponse:
        prescription = await self.repo.create_prescription(
            user_id=user_id,
            image_s3_url=data.image_s3_url,
            document_id=data.document_id,
        )

        try:
            prescription.ocr_status = OCRStatus.PROCESSING
            await prescription.save()

            response = self.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "이 처방전 이미지에서 텍스트를 추출해주세요. 의약품명, 용량, 복용법, 병원명을 포함해주세요.",
                            },
                            {"type": "image_url", "image_url": {"url": data.image_s3_url}},
                        ],
                    }
                ],
                max_tokens=1000,
            )

            extracted_text = response.choices[0].message.content
            await self.repo.update_ocr_result(
                prescription_id=prescription.id,
                diagnosis_text=extracted_text,
                status=OCRStatus.COMPLETED,
            )
            prescription = await self.repo.get_by_id(prescription.id)

        except Exception as e:
            await self.repo.update_ocr_result(
                prescription_id=prescription.id,
                diagnosis_text=f"OCR 실패: {str(e)}",
                status=OCRStatus.FAILED,
            )
            prescription = await self.repo.get_by_id(prescription.id)

        return await self.build_response(prescription)

    async def confirm_prescription(
        self, user_id: UUID, prescription_id: UUID, data: PrescriptionConfirmRequest
    ) -> PrescriptionResponse:
        prescription = await self.repo.get_by_id(prescription_id)

        if not prescription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="처방전을 찾을 수 없습니다.")

        if prescription.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="권한이 없습니다.")

        updated = await self.repo.confirm_prescription(
            prescription_id=prescription_id,
            prescription_date=data.prescription_date,
            hospital_name=data.hospital_name,
            diagnosis_text=data.diagnosis_text,
        )

        try:
            medications = await self.med_repo.get_by_prescription(prescription_id)
            max_days = 0
            for med in medications:
                if med.duration_days and med.duration_days > max_days:
                    max_days = med.duration_days

            if max_days > 0:
                start_date = data.prescription_date or date.today()
                end_date = self.adjust_to_weekday(start_date + timedelta(days=max_days))

                first_alert = self.adjust_to_weekday(start_date + timedelta(days=int(max_days * 0.8)))
                await self.noti_repo.create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.MEDICATION,
                    title="복약 종료일이 다가옵니다",
                    content="복약 종료일이 다가옵니다. 다음 진료 일정을 확인하세요.",
                    scheduled_at=datetime.combine(first_alert, datetime.min.time()),
                )

                second_alert = self.adjust_to_weekday(end_date - timedelta(days=3))
                await self.noti_repo.create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.MEDICATION,
                    title="복약 종료일 3일 전",
                    content="복약 종료일이 3일 남았습니다. 다음 진료 일정을 확인하세요.",
                    scheduled_at=datetime.combine(second_alert, datetime.min.time()),
                )
        except Exception as noti_err:
            print(f"NOTI-007 알림 예약 실패: {noti_err}")

        return await self.build_response(updated)
