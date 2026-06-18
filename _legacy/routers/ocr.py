import uuid
from datetime import datetime

from fastapi import APIRouter, File, HTTPException, UploadFile

from utils.clova_ocr import recognize_image

router = APIRouter(prefix="/v1", tags=["OCR"])

# 임시 저장소 (추후 DB 모델로 교체)
documents = {}
ocr_jobs = {}

# 지원 document_type
ALLOWED_TYPES = ["prescription", "medical_record", "pill_bag", "lab_result", "health_checkup", "other"]


# ── 1. 의료문서 업로드 ─────────────────────────────────────
@router.post("/medical-documents", status_code=201)
async def upload_medical_document(file: UploadFile = File(...), document_type: str = "other"):
    if document_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "UNSUPPORTED_DOCUMENT_TYPE",
                "message": "지원하지 않는 문서 유형입니다.",
                "details": {"allowed": ALLOWED_TYPES},
            },
        )

    document_id = str(uuid.uuid4())
    image_bytes = await file.read()

    documents[document_id] = {
        "id": document_id,
        "document_type": document_type,
        "upload_status": "uploaded",
        "uploaded_at": datetime.utcnow().isoformat(),
        "image_bytes": image_bytes,
        "filename": file.filename,
        "user_confirmed": False,
        "structured_data": None,
    }

    return {
        "document_id": document_id,
        "document_type": document_type,
        "upload_status": "uploaded",
        "uploaded_at": documents[document_id]["uploaded_at"],
    }


# ── 2. OCR 처리 시작 ───────────────────────────────────────
@router.post("/medical-documents/{document_id}/ocr-jobs", status_code=202)
async def start_ocr_job(document_id: str):
    if document_id not in documents:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "문서를 찾을 수 없습니다."})

    job_id = str(uuid.uuid4())
    ocr_jobs[job_id] = {
        "job_id": job_id,
        "document_id": document_id,
        "status": "pending",
        "structured_data": None,
        "confidence_score": None,
        "error_message": None,
    }

    # 비동기 OCR 처리
    try:
        image_bytes = documents[document_id]["image_bytes"]
        filename = documents[document_id]["filename"]
        fmt = filename.split(".")[-1].lower() if filename else "jpg"

        text = await recognize_image(image_bytes, format=fmt)

        ocr_jobs[job_id]["status"] = "completed"
        ocr_jobs[job_id]["structured_data"] = {"raw_text": text}
        ocr_jobs[job_id]["confidence_score"] = 0.9
    except Exception as e:
        ocr_jobs[job_id]["status"] = "failed"
        ocr_jobs[job_id]["error_message"] = str(e)

    return {"job_id": job_id, "status": "pending"}


# ── 3. OCR 결과 조회 ───────────────────────────────────────
@router.get("/ocr-jobs/{job_id}")
async def get_ocr_job(job_id: str):
    if job_id not in ocr_jobs:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "OCR 작업을 찾을 수 없습니다."})

    job = ocr_jobs[job_id]
    return {
        "job_id": job["job_id"],
        "document_id": job["document_id"],
        "status": job["status"],
        "structured_data": job["structured_data"],
        "confidence_score": job["confidence_score"],
        "error_message": job["error_message"],
        "user_confirmed": False,
    }


# ── 4. 사용자 확정 ─────────────────────────────────────────
@router.put("/medical-documents/{document_id}/confirm")
async def confirm_ocr_result(document_id: str, body: dict):
    if document_id not in documents:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "문서를 찾을 수 없습니다."})

    documents[document_id]["user_confirmed"] = True
    documents[document_id]["structured_data"] = body.get("structured_data")
    documents[document_id]["confirmed_at"] = datetime.utcnow().isoformat()

    return {"document_id": document_id, "user_confirmed": True, "confirmed_at": documents[document_id]["confirmed_at"]}
