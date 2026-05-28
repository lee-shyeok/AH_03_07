from __future__ import annotations

from fastapi import HTTPException, UploadFile, status

from app.dtos.pill_recognition import (
    PillCandidate,
    PillRecognitionHistoryItem,
    PillRecognizeResponse,
)
from app.models.pill_recognition import PillRecognition
from app.models.users import User

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


class PillRecognitionService:
    async def _validate_file(self, file: UploadFile) -> bytes:
        ext = (file.filename or "").rsplit(".", 1)[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "UNSUPPORTED_FILE_TYPE",
                    "message": "JPG, JPEG, PNG 형식만 지원합니다.",
                },
            )
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "FILE_TOO_LARGE", "message": "파일 크기는 5MB 이하여야 합니다."},
            )
        return content

    async def recognize(self, user: User, file: UploadFile) -> PillRecognizeResponse:
        await self._validate_file(file)

        # TODO: S3 업로드 연동 시 실제 URL로 교체
        image_url = f"uploads/{user.id}/pills/{file.filename}"

        # TODO: EfficientNet-B0 ML 모델 Celery 비동기 연동 (REQ-PILL-002, 권순현 담당)
        # 현재는 빈 candidates 반환 (모델 연동 전 placeholder)
        candidates: list[PillCandidate] = []

        recognition = await PillRecognition.create(
            user=user,
            image_url=image_url,
            original_filename=file.filename or "",
            candidates=[c.model_dump() for c in candidates],
            user_confirmed=False,
        )

        return PillRecognizeResponse(
            recognition_id=recognition.id,
            candidates=candidates,
            user_confirm_required=True,
        )

    async def get_recognitions(
        self, user: User, page: int, size: int
    ) -> list[PillRecognitionHistoryItem]:
        records = (
            await PillRecognition.filter(user=user)
            .order_by("-created_at")
            .offset((page - 1) * size)
            .limit(size)
        )
        return [
            PillRecognitionHistoryItem(
                id=r.id,
                image_url=r.image_url,
                candidates=[PillCandidate(**c) for c in (r.candidates or [])],
                selected_drug_name=r.selected_drug_name,
                user_confirmed=r.user_confirmed,
                created_at=r.created_at,
            )
            for r in records
        ]