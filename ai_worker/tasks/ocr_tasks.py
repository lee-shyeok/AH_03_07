import asyncio
import base64
import json
import uuid
import zoneinfo
from datetime import datetime
from pathlib import Path

import httpx
from tortoise import Tortoise

from ai_worker.core.celery_app import celery_app
from ai_worker.core.config import Config as WorkerConfig
from ai_worker.core.logger import setup_logger
from app.models.medical_documents import MedicalDocument, OcrJob, OcrJobStatus

logger = setup_logger("ai_worker.ocr")

_cfg = WorkerConfig()
_TZ = zoneinfo.ZoneInfo("Asia/Seoul")

_TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.mysql",
            "dialect": "asyncmy",
            "credentials": {
                "host": _cfg.DB_HOST,
                "port": _cfg.DB_PORT,
                "user": _cfg.DB_USER,
                "password": _cfg.DB_PASSWORD,
                "database": _cfg.DB_NAME,
                "connect_timeout": _cfg.DB_CONNECT_TIMEOUT,
                "maxsize": _cfg.DB_CONNECTION_POOL_MAXSIZE,
            },
        },
    },
    "apps": {
        "models": {
            "models": ["app.models.medical_documents", "app.models.users"],
        },
    },
    "timezone": "Asia/Seoul",
}

_MIME_TO_FORMAT: dict[str, str] = {
    "image/jpeg": "jpeg",
    "image/jpg": "jpeg",
    "image/png": "png",
    "image/tiff": "tiff",
    "application/pdf": "pdf",
}

_EXT_TO_FORMAT: dict[str, str] = {
    "jpg": "jpeg",
    "jpeg": "jpeg",
    "png": "png",
    "tif": "tiff",
    "tiff": "tiff",
    "pdf": "pdf",
}


@celery_app.task(
    bind=True,
    queue="ocr_queue",
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
)
def process_ocr_task(self, document_id: int) -> None:  # noqa: ANN001
    asyncio.run(_process_ocr_async(document_id))


async def _process_ocr_async(document_id: int) -> None:
    await Tortoise.init(config=_TORTOISE_ORM)
    ocr_job = None
    try:
        doc = await MedicalDocument.get_or_none(id=document_id)
        if doc is None:
            raise ValueError(f"MedicalDocument {document_id} not found")

        ocr_job = await OcrJob.filter(document_id=document_id).order_by("-created_at").first()
        if ocr_job is None:
            ocr_job = await OcrJob.create(
                document_id=document_id,
                user_id=doc.user_id,
                status=OcrJobStatus.pending,
            )

        ocr_job.status = OcrJobStatus.processing
        ocr_job.started_at = datetime.now(_TZ)
        ocr_job.error_message = None
        await ocr_job.save(update_fields=["status", "started_at", "error_message"])
        logger.info(f'{{"event": "ocr_task_start", "document_id": {document_id}, "job_id": {ocr_job.id}}}')

        image_bytes = Path(doc.file_path).read_bytes()

        ocr_format = _MIME_TO_FORMAT.get(
            (doc.mime_type or "").lower(),
            _EXT_TO_FORMAT.get(Path(doc.stored_filename).suffix.lower().lstrip("."), "jpeg"),
        )

        raw_text, confidence_score, field_confidences_json, _ = await _call_clova_ocr(
            image_bytes, ocr_format, doc.stored_filename
        )
        structured_data_json = await _structure_with_llm(raw_text) or "[]"

        ocr_job.status = OcrJobStatus.completed
        ocr_job.completed_at = datetime.now(_TZ)
        ocr_job.raw_text = raw_text
        ocr_job.confidence_score = confidence_score
        ocr_job.field_confidences = field_confidences_json
        ocr_job.structured_data = structured_data_json
        await ocr_job.save(
            update_fields=["status", "completed_at", "raw_text", "confidence_score", "field_confidences", "structured_data"]
        )
        logger.info(f'{{"event": "ocr_task_done", "document_id": {document_id}, "job_id": {ocr_job.id}}}')

    except Exception as exc:
        if ocr_job is not None:
            ocr_job.status = OcrJobStatus.failed
            ocr_job.error_message = str(exc)[:500]
            await ocr_job.save(update_fields=["status", "error_message"])
        logger.error(f'{{"event": "ocr_task_failed", "document_id": {document_id}, "error": "{exc}"}}')
        raise
    finally:
        await Tortoise.close_connections()


async def _structure_with_llm(raw_text: str) -> str | None:
    if not _cfg.OPENAI_API_KEY:
        return None
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=_cfg.OPENAI_API_KEY)
    prompt = f"""다음 처방전 OCR 텍스트에서 약품 정보를 추출해서 JSON 배열로 반환해주세요.

처방전 텍스트:
{raw_text}

JSON 형식:
[
  {{
    "drug_name_user_input": "약 이름",
    "dosage": "용량 (예: 500mg)",
    "frequency": "복용 횟수 (예: 1일 3회)",
    "duration_days": 기간_일수_정수,
    "drug_category": "분류"
  }}
]

JSON 배열만 반환하세요 (다른 설명 없이!)."""

    try:
        response = await client.chat.completions.create(
            model=_cfg.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        json.loads(content)  # validate
        return content
    except Exception as exc:
        logger.warning(f'{{"event": "llm_structure_failed", "error": "{exc}"}}')
        return None


async def _call_clova_ocr(
    image_bytes: bytes,
    ocr_format: str,
    filename: str,
) -> tuple[str, float | None, str, str]:
    if not _cfg.CLOVA_OCR_API_URL or not _cfg.CLOVA_OCR_SECRET_KEY:
        raise RuntimeError("CLOVA_OCR_API_URL 또는 CLOVA_OCR_SECRET_KEY 환경변수가 설정되지 않았습니다.")

    payload = {
        "version": "V2",
        "requestId": str(uuid.uuid4()),
        "timestamp": 0,
        "lang": "ko",
        "images": [
            {
                "format": ocr_format,
                "data": base64.b64encode(image_bytes).decode("utf-8"),
                "name": filename,
            }
        ],
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            _cfg.CLOVA_OCR_API_URL,
            json=payload,
            headers={"X-OCR-SECRET": _cfg.CLOVA_OCR_SECRET_KEY},
        )
        resp.raise_for_status()
        data = resp.json()

    images = data.get("images", [])
    if not images:
        raise RuntimeError("CLOVA OCR 응답에 images 필드가 없습니다.")

    image_result = images[0]
    infer_result = image_result.get("inferResult", "FAILURE")
    if infer_result != "SUCCESS":
        raise RuntimeError(f"CLOVA OCR 처리 실패: {image_result.get('message', infer_result)}")

    fields = image_result.get("fields", [])

    raw_text = "\n".join(f["inferText"] for f in fields if f.get("inferText"))
    confidences = [f["inferConfidence"] for f in fields if "inferConfidence" in f]
    confidence_score = sum(confidences) / len(confidences) if confidences else None
    field_confidences_json = json.dumps(
        [{"text": f.get("inferText", ""), "confidence": f.get("inferConfidence")} for f in fields],
        ensure_ascii=False,
    )
    structured_data_json = json.dumps(
        [
            {
                "text": f.get("inferText", ""),
                "confidence": f.get("inferConfidence"),
                "type": f.get("type"),
                "line_break": f.get("lineBreak", False),
            }
            for f in fields
        ],
        ensure_ascii=False,
    )

    return raw_text, confidence_score, field_confidences_json, structured_data_json
