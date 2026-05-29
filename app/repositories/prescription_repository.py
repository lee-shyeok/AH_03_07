from uuid import UUID

from app.models.medical_documents import DocumentType, MedicalDocument, UploadStatus

from app.models.prescriptions import OCRStatus, Prescription


class PrescriptionRepository:
    """처방전 + 의료 문서 DB 쿼리"""

    # ========== 의료 문서 ==========

    @staticmethod
    async def create_document(
        user_id: UUID,
        document_type: DocumentType,
        file_s3_url: str,
        original_filename: str,
        mime_type: str | None = None,
    ) -> MedicalDocument:
        """의료 문서 생성"""
        return await MedicalDocument.create(
            user_id=user_id,
            document_type=document_type,
            file_s3_url=file_s3_url,
            original_filename=original_filename,
            mime_type=mime_type,
        )

    @staticmethod
    async def update_document_status(document_id: int, status: UploadStatus) -> MedicalDocument | None:
        """문서 업로드 상태 변경"""
        doc = await MedicalDocument.filter(id=document_id).first()
        if doc:
            doc.upload_status = status
            await doc.save()
        return doc

    # ========== 처방전 ==========

    @staticmethod
    async def get_user_prescriptions(user_id: UUID) -> list[Prescription]:
        """사용자 처방전 목록"""
        return await Prescription.filter(user_id=user_id).order_by("-created_at").all()

    @staticmethod
    async def get_by_id(prescription_id: UUID) -> Prescription | None:
        """처방전 1건 조회"""
        return await Prescription.filter(id=prescription_id).first()

    @staticmethod
    async def create_prescription(
        user_id: UUID,
        image_s3_url: str,
        document_id: int | None = None,
    ) -> Prescription:
        """처방전 생성 (OCR 대기 상태!)"""
        return await Prescription.create(
            user_id=user_id,
            document_id=document_id,
            image_s3_url=image_s3_url,
            ocr_status=OCRStatus.PENDING,
        )

    @staticmethod
    async def update_ocr_result(
        prescription_id: UUID,
        diagnosis_text: str,
        status: OCRStatus = OCRStatus.COMPLETED,
    ) -> Prescription | None:
        """OCR 결과 업데이트"""
        prescription = await Prescription.filter(id=prescription_id).first()
        if prescription:
            prescription.diagnosis_text = diagnosis_text
            prescription.ocr_status = status
            await prescription.save()
        return prescription

    @staticmethod
    async def confirm_prescription(prescription_id: UUID, **kwargs) -> Prescription | None:
        """사용자가 처방전 정보 확인 후 수정"""
        prescription = await Prescription.filter(id=prescription_id).first()
        if prescription:
            prescription.user_confirmed = True
            for key, value in kwargs.items():
                if value is not None:
                    setattr(prescription, key, value)
            await prescription.save()
        return prescription
