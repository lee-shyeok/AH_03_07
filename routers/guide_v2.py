"""
안내문 + 처방전 편의 + 약품 이미지 인식 + 리포트 라우터

엔드포인트:
  POST   /v1/guides/generate                안내문 생성 요청
  GET    /v1/guide-generation-jobs/{id}     생성 작업 상태 조회
  GET    /v1/guides                         안내문 목록 (기존 guides 라우터와 통합)
  GET    /v1/guides/{id}                    안내문 상세
  GET    /v1/guides/{id}/sources            출처 목록
  GET    /v1/guides/{id}/sections           섹션별 조회

  GET    /v1/prescriptions                  처방전 목록
  GET    /v1/prescriptions/{id}             처방전 상세

  POST   /v1/pills/recognize               약품 이미지 인식
  GET    /v1/pills/recognitions            인식 이력 조회

  POST   /v1/reports/pre-visit             리포트 생성
  GET    /v1/reports/{id}                  리포트 조회
  POST   /v1/reports/{id}/share            리포트 공유
"""
import json
import os
import re
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from guide_models import Guide, GuideStatusEnum
from guide_v2_models import (
    GuideGenerationJob,
    GuideJobStatusEnum,
    GuideSection,
    GuideSource,
    PillRecognition,
    Report,
    ReportStatusEnum,
)
from guide_v2_schemas import (
    GuideGenerateRequest,
    GuideGenerationJobResponse,
    GuideSectionResponse,
    GuideSourceResponse,
    PillRecognitionResponse,
    PrescriptionBrief,
    ReportCreateRequest,
    ReportResponse,
    ReportShareResponse,
)
from medical_record_models import MedicalRecord
from ocr_models import DocumentTypeEnum, MedicalDocument
from security import get_current_user_id

router = APIRouter()

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads")) / "pills"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_PILL_MAGIC = {
    b"\x89PNG": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
}
MAX_PILL_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_PAGE_SIZE = 50
REPORT_SHARE_EXPIRE_HOURS = 72


# ── 헬퍼 ──────────────────────────────────────────────────

def _get_guide_or_404(guide_id: int, user_id: int, db: Session) -> Guide:
    guide = db.query(Guide).filter(
        Guide.id == guide_id,
        Guide.user_id == user_id,
        Guide.deleted_at.is_(None),
    ).first()
    if not guide:
        raise HTTPException(status_code=404, detail="안내문을 찾을 수 없습니다.")
    return guide


def _verify_pill_magic(data: bytes) -> str:
    """매직바이트로 실제 이미지 형식 검증."""
    if data[:4] == b"\x89PNG" and data[4:8] == b"\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    raise ValueError("JPG 또는 PNG 파일만 업로드 가능합니다.")


def _sanitize_filename(name: str) -> str:
    name = name.replace("/", "").replace("\\", "").replace("\x00", "")
    name = re.sub(r"[^\w\s\-.]", "", name, flags=re.UNICODE)
    return name.strip(". ")[:255] or "unnamed"


# ── 안내문 생성 작업 ──────────────────────────────────────

def _run_guide_generation_v2(job_id: int, user_id: int) -> None:
    """백그라운드 안내문 생성."""
    from database import SessionLocal
    from guide_engine import DISCLAIMER, generate_guide
    from models import User

    db = SessionLocal()
    try:
        job = db.query(GuideGenerationJob).filter(GuideGenerationJob.id == job_id).first()
        if not job:
            return

        job.status = GuideJobStatusEnum.processing
        job.started_at = datetime.now(UTC)
        db.commit()

        # 최근 진료기록 조회
        records = db.query(MedicalRecord).filter(
            MedicalRecord.user_id == user_id,
            MedicalRecord.deleted_at.is_(None),
        ).order_by(MedicalRecord.visit_date.desc()).limit(1).all()

        if not records:
            job.status = GuideJobStatusEnum.failed
            job.error_message = "진료 기록이 없어 안내문을 생성할 수 없습니다."
            job.completed_at = datetime.now(UTC)
            db.commit()
            return

        record = records[0]
        user = db.query(User).filter(User.id == user_id).first()

        from medical_record_models import Medication
        medications = db.query(Medication).filter(
            Medication.record_id == record.id
        ).all()

        try:
            result = generate_guide(
                visit_date=str(record.visit_date),
                hospital_name=record.hospital_name or "",
                diagnosis=record.diagnosis,
                medications=medications,
                memo=record.memo or "",
                chronic_diseases=user.chronic_diseases if user else "",
                allergy_info=user.allergy_info if user else "",
            )

            # 안내문 생성
            guide = Guide(
                user_id=user_id,
                record_id=record.id,
                status=GuideStatusEnum.active,
                disclaimer=DISCLAIMER,
                medication_guide=result["medication_guide"],
                lifestyle_guide=result["lifestyle_guide"],
                precautions=result["precautions"],
                recommended_checkups=result["recommended_checkups"],
                version=1,
            )
            db.add(guide)
            db.flush()

            # 섹션 저장
            sections = [
                ("medication", "복약 안내", result["medication_guide"], 1),
                ("lifestyle", "생활습관 안내", result["lifestyle_guide"], 2),
                ("caution", "주의사항", result["precautions"], 3),
                ("source_notice", "면책 고지", DISCLAIMER, 99),
            ]
            for stype, stitle, scontent, order in sections:
                if scontent:
                    db.add(GuideSection(
                        guide_id=guide.id,
                        section_type=stype,
                        section_title=stitle,
                        section_content=scontent,
                        display_order=order,
                    ))

            job.status = GuideJobStatusEnum.completed
            job.guide_id = guide.id
            record.has_guide = True
            record.guide_needs_update = False

        except Exception as e:
            job.status = GuideJobStatusEnum.failed
            job.error_message = str(e)[:500]

        job.completed_at = datetime.now(UTC)
        db.commit()
    finally:
        db.close()


@router.post(
    "/guides/generate",
    response_model=GuideGenerationJobResponse,
    status_code=202,
    summary="API-안내문-001: 맞춤 안내문 생성 요청",
)
def generate_guide_request(
    data: GuideGenerateRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    안내문 생성 비동기 작업을 시작합니다.
    안전 필터 통과 후에만 안내문이 생성됩니다.
    """
    # 이미 처리 중인 작업 중복 방지
    existing = db.query(GuideGenerationJob).filter(
        GuideGenerationJob.user_id == user_id,
        GuideGenerationJob.status.in_([
            GuideJobStatusEnum.pending,
            GuideJobStatusEnum.processing,
        ]),
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="이미 처리 중인 안내문 생성 작업이 있습니다.")

    # 활성 위험 신호 확인 (high_risk_gate)
    from clinical_models import RiskFlag, RiskFlagStatusEnum
    active_risk = db.query(RiskFlag).filter(
        RiskFlag.user_id == user_id,
        RiskFlag.status == RiskFlagStatusEnum.active,
    ).first()

    job = GuideGenerationJob(
        user_id=user_id,
        trigger_type=data.trigger_type,
    )
    db.add(job)

    if active_risk:
        job.status = GuideJobStatusEnum.high_risk_gate_blocked
        job.blocked_reason = "HIGH_RISK_GATE_BLOCKED"
        db.commit()
        db.refresh(job)
        return GuideGenerationJobResponse.from_orm(job)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="작업 생성에 실패했습니다.")
    db.refresh(job)

    background_tasks.add_task(_run_guide_generation_v2, job.id, user_id)
    return GuideGenerationJobResponse.from_orm(job)


@router.get(
    "/guide-generation-jobs/{job_id}",
    response_model=GuideGenerationJobResponse,
    summary="API-안내문-002: 안내문 생성 작업 상태 조회",
)
def get_guide_generation_job(
    job_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    job = db.query(GuideGenerationJob).filter(
        GuideGenerationJob.id == job_id,
        GuideGenerationJob.user_id == user_id,
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    return GuideGenerationJobResponse.from_orm(job)


@router.get(
    "/guides/{guide_id}/sources",
    response_model=list[GuideSourceResponse],
    summary="API-안내문-005: 안내문 출처 목록",
)
def get_guide_sources(
    guide_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    _get_guide_or_404(guide_id, user_id, db)
    return db.query(GuideSource).filter(
        GuideSource.guide_id == guide_id,
    ).order_by(GuideSource.citation_order).all()


@router.get(
    "/guides/{guide_id}/sections",
    response_model=list[GuideSectionResponse],
    summary="API-안내문-006: 안내문 섹션별 조회",
)
def get_guide_sections(
    guide_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    _get_guide_or_404(guide_id, user_id, db)
    return db.query(GuideSection).filter(
        GuideSection.guide_id == guide_id,
    ).order_by(GuideSection.display_order).all()


# ── 처방전 편의 API ───────────────────────────────────────

@router.get(
    "/prescriptions",
    response_model=list[PrescriptionBrief],
    summary="API-처방전-001: 처방전 목록 조회",
)
def list_prescriptions(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=MAX_PAGE_SIZE),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """의료문서 중 prescription 타입만 필터링하는 편의 API."""
    docs = db.query(MedicalDocument).filter(
        MedicalDocument.user_id == user_id,
        MedicalDocument.document_type == DocumentTypeEnum.prescription,
        MedicalDocument.deleted_at.is_(None),
    ).order_by(MedicalDocument.created_at.desc())\
     .offset((page - 1) * size).limit(size).all()
    return [PrescriptionBrief.from_orm(d) for d in docs]


@router.get(
    "/prescriptions/{doc_id}",
    response_model=PrescriptionBrief,
    summary="API-처방전-002: 처방전 상세 조회",
)
def get_prescription(
    doc_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    doc = db.query(MedicalDocument).filter(
        MedicalDocument.id == doc_id,
        MedicalDocument.user_id == user_id,
        MedicalDocument.document_type == DocumentTypeEnum.prescription,
        MedicalDocument.deleted_at.is_(None),
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="처방전을 찾을 수 없습니다.")
    return PrescriptionBrief.from_orm(doc)


# ── 약품 이미지 인식 ──────────────────────────────────────

@router.post(
    "/pills/recognize",
    response_model=PillRecognitionResponse,
    summary="API-약품-005: 약품 이미지 인식",
)
async def recognize_pill(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    약품 이미지로 후보 약품을 제시합니다.
    약품 자동 판정·확정·추천 X. 사용자 확정 필수.
    """
    # 스트리밍 방식으로 읽어 크기 초과 즉시 거부
    chunks = []
    total = 0
    async for chunk in file:
        total += len(chunk)
        if total > MAX_PILL_FILE_SIZE:
            raise HTTPException(status_code=400, detail="파일 크기는 5MB를 초과할 수 없습니다.")
        chunks.append(chunk)
    content = b"".join(chunks)

    # 매직바이트 검증
    try:
        _verify_pill_magic(content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 파일 저장 (UUID 기반)
    safe_name = _sanitize_filename(file.filename or "unnamed")
    ext = Path(safe_name).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png"}:
        ext = ""
    stored_filename = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / stored_filename
    dest.write_bytes(content)

    # TODO: 실제 약품 인식 모델 연동 (EfficientNet-B0)
    # 현재는 빈 후보 반환 — 모델 연동 후 교체
    candidates = []

    recognition = PillRecognition(
        user_id=user_id,
        image_path=str(dest),
        stored_filename=stored_filename,
        candidates=json.dumps(candidates, ensure_ascii=False),
    )
    db.add(recognition)
    try:
        db.commit()
    except Exception:
        db.rollback()
        # 저장 실패 시 파일도 삭제
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="약품 인식 저장에 실패했습니다.")
    db.refresh(recognition)
    return PillRecognitionResponse.from_orm(recognition)


@router.get(
    "/pills/recognitions",
    response_model=list[PillRecognitionResponse],
    summary="API-약품-006: 약품 인식 이력 조회",
)
def list_pill_recognitions(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=MAX_PAGE_SIZE),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    recognitions = db.query(PillRecognition).filter(
        PillRecognition.user_id == user_id,
        PillRecognition.deleted_at.is_(None),
    ).order_by(PillRecognition.created_at.desc())\
     .offset((page - 1) * size).limit(size).all()
    return [PillRecognitionResponse.from_orm(r) for r in recognitions]


# ── 리포트 ────────────────────────────────────────────────

def _run_report_generation(report_id: int, user_id: int) -> None:
    """백그라운드 리포트 생성."""
    from database import SessionLocal
    from models import User

    db = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return

        report.status = ReportStatusEnum.processing
        db.commit()

        user = db.query(User).filter(User.id == user_id).first()
        records = db.query(MedicalRecord).filter(
            MedicalRecord.user_id == user_id,
            MedicalRecord.deleted_at.is_(None),
        ).order_by(MedicalRecord.visit_date.desc()).limit(3).all()

        try:
            # 진료 전 요약 생성 (GPT 기반)
            import urllib.request

            from ocr_engine import _OPENAI_API_KEY

            if not _OPENAI_API_KEY:
                raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다.")

            record_summary = "\n".join([
                f"- {r.visit_date} {r.hospital_name or ''}: {r.diagnosis}"
                for r in records
            ]) or "진료 기록 없음"

            prompt = f"""다음 환자 정보를 바탕으로 진료 전 1페이지 요약을 작성해주세요.
진료 예정일: {report.visit_date}
최근 진료 기록:
{record_summary}
만성질환: {user.chronic_diseases if user else '없음'}
알레르기: {user.allergy_info if user else '없음'}

간결하고 의료진이 빠르게 파악할 수 있도록 작성하세요.
본 요약은 참고용이며 의료진의 판단을 대체하지 않습니다."""

            import json as _json
            body = _json.dumps({
                "model": "gpt-4o-mini",
                "max_tokens": 800,
                "messages": [{"role": "user", "content": prompt}],
            }).encode("utf-8")

            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {_OPENAI_API_KEY}",
                },
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = _json.loads(resp.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"].strip()

            report.content = content
            report.status = ReportStatusEnum.completed

        except Exception as e:
            report.status = ReportStatusEnum.failed
            report.error_message = str(e)[:500]

        db.commit()
    finally:
        db.close()


@router.post(
    "/reports/pre-visit",
    response_model=ReportResponse,
    status_code=202,
    summary="API-리포트-001: 진료 전 요약 생성",
)
def create_report(
    data: ReportCreateRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    report = Report(
        user_id=user_id,
        visit_date=data.visit_date,
        status=ReportStatusEnum.pending,
    )
    db.add(report)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="리포트 생성 요청에 실패했습니다.")
    db.refresh(report)

    background_tasks.add_task(_run_report_generation, report.id, user_id)
    return report


@router.get(
    "/reports/{report_id}",
    response_model=ReportResponse,
    summary="API-리포트-002: 리포트 조회",
)
def get_report(
    report_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.user_id == user_id,
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다.")
    return report


@router.post(
    "/reports/{report_id}/share",
    response_model=ReportShareResponse,
    status_code=201,
    summary="API-리포트-003: 리포트 의료진 공유",
)
def share_report(
    report_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """보안 링크 토큰을 생성하여 의료진과 공유합니다."""
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.user_id == user_id,
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다.")

    if report.status != ReportStatusEnum.completed:
        raise HTTPException(status_code=400, detail="완료된 리포트만 공유할 수 있습니다.")

    token = secrets.token_urlsafe(64)
    expires = datetime.now(UTC) + timedelta(hours=REPORT_SHARE_EXPIRE_HOURS)

    report.secure_link_token = token
    report.share_expires_at = expires

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="공유 링크 생성에 실패했습니다.")

    return ReportShareResponse(
        report_id=report.id,
        secure_link_token=token,
        share_expires_at=expires,
    )
