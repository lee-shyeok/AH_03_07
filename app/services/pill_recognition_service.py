from __future__ import annotations

import base64
import json
import logging

from fastapi import HTTPException, UploadFile, status
from openai import AsyncOpenAI

from app.core import config
from app.dtos.pill_recognition import (
    PillCandidate,
    PillRecognitionHistoryItem,
    PillRecognizeResponse,
)
from app.models.pill_recognition import PillRecognition
from app.models.users import User

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

logger = logging.getLogger(__name__)


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

    async def _call_vision_api(self, image_bytes: bytes, filename: str) -> list[PillCandidate]:
        ext = filename.rsplit(".", 1)[-1].lower()
        mime = "image/png" if ext == "png" else "image/jpeg"
        b64 = base64.b64encode(image_bytes).decode()

        client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a medical pill recognition assistant. "
                        "Analyze the image and identify any pills, tablets, or capsules visible. "
                        "Even if you cannot identify the exact medication, describe what you see based on shape, color, and any markings. "
                        "Return ONLY a JSON array — no markdown, no extra text. "
                        "Each element must have: "
                        "'drug_name' (약품명 또는 특징 설명, 한국어 우선) "
                        "and 'confidence' (float 0.0–1.0). "
                        "Always return at least one candidate if any pill is visible."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{b64}"},
                        },
                        {"type": "text", "text": "이미지의 약품을 인식하고 JSON 배열로만 반환해주세요."},
                    ],
                },
            ],
            max_tokens=512,
            temperature=0,
        )

        raw = (response.choices[0].message.content or "").strip()
        print(f"OpenAI 응답: {raw}")
        # strip markdown code fences if model wraps output
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        try:
            data = json.loads(raw)
            return [PillCandidate(drug_name=item["drug_name"], confidence=float(item["confidence"])) for item in data]
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning("Vision API 응답 파싱 실패: %s — raw: %s", e, raw[:200])
            return []

    async def recognize(self, user: User, file: UploadFile) -> PillRecognizeResponse:
        image_bytes = await self._validate_file(file)

        # TODO: S3 업로드 연동 시 실제 URL로 교체
        image_url = f"uploads/{user.id}/pills/{file.filename}"

        candidates = await self._call_vision_api(image_bytes, file.filename or "image.jpg")

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

    async def confirm(self, user: User, recognition_id: int, selected_drug_name: str) -> PillRecognitionHistoryItem:
        recognition = await PillRecognition.get_or_none(id=recognition_id, user=user)
        if recognition is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "NOT_FOUND", "message": "인식 기록을 찾을 수 없습니다."},
            )
        recognition.selected_drug_name = selected_drug_name
        recognition.user_confirmed = True
        await recognition.save()
        return PillRecognitionHistoryItem(
            id=recognition.id,
            image_url=recognition.image_url,
            candidates=[PillCandidate(**c) for c in (recognition.candidates or [])],
            selected_drug_name=recognition.selected_drug_name,
            user_confirmed=recognition.user_confirmed,
            created_at=recognition.created_at,
        )

    async def get_recognitions(self, user: User, page: int, size: int) -> list[PillRecognitionHistoryItem]:
        records = await PillRecognition.filter(user=user).order_by("-created_at").offset((page - 1) * size).limit(size)
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
