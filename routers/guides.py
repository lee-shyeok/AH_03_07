"""
가이드 라우터  REQ-GUIDE-001 ~ REQ-GUIDE-006

엔드포인트:
  POST   /v1/guides                       가이드 생성
  GET    /v1/guides                       목록 조회
  GET    /v1/guides/{guide_id}            상세 조회
  POST   /v1/guides/{guide_id}/regenerate 재생성
  POST   /v1/guides/{guide_id}/feedback   피드백 등록/수정
  GET    /v1/guides/{guide_id}/feedback   피드백 조회
"""

from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db, redis_client
from guide_engine import DISCLAIMER, generate_guide
from guide_models import Guide, GuideFeedback, GuideStatusEnum
from guide_schemas import (
    GuideBrief,
    GuideCreateRequest,
    GuideDetail,
    GuideFeedbackRequest,
    GuideFeedbackResponse,
    GuideListResponse,
    GuideRegenerateRequest,
)
from medical_record_models import MedicalRecord, Medication
from models import User
from security import get_current_user_id

router = APIRouter()

MAX_PAGE_SIZE = 50
REGEN_DAILY_LIMIT = 5
_REGEN_LIMIT_KEY = "guide:regen:{user_id}:{date}"


# ── 헬퍼 ──────────────────────────────────────────────────


def _get_guide_or_404(guide_id: int, user_id: int, db: Session) -> Guide:
    guide = (
        db.query(Guide)
        .filter(
            Guide.id == guide_id,
            Guide.user_id == user_id,
            Guide.deleted_at.is_(None),
        )
        .first()
    )
    if not guide:
        raise HTTPException(status_code=404, detail="가이드를 찾을 수 없습니다.")
    return guide


def _get_record_or_404(record_id: int, user_id: int, db: Session) -> MedicalRecord:
    record = (
        db.query(MedicalRecord)
        .filter(
            MedicalRecord.id == record_id,
            MedicalRecord.user_id == user_id,
            MedicalRecord.deleted_at.is_(None),
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="진료 기록을 찾을 수 없습니다.")
    return record


def _build_brief(guide: Guide, diagnosis: str) -> GuideBrief:
    # 가이드 요약: medication_guide 앞 100자
    summary = ""
    if guide.medication_guide:
        summary = guide.medication_guide[:100]
    elif guide.lifestyle_guide:
        summary = guide.lifestyle_guide[:100]
    return GuideBrief(
        id=guide.id,
        record_id=guide.record_id,
        diagnosis=diagnosis,
        summary=summary,
        status=guide.status.value,
        version=guide.version,
        created_at=guide.created_at,
    )


def _build_detail(guide: Guide, diagnosis: str) -> GuideDetail:
    return GuideDetail(
        id=guide.id,
        record_id=guide.record_id,
        diagnosis=diagnosis,
        status=guide.status.value,
        version=guide.version,
        medication_guide=guide.medication_guide,
        lifestyle_guide=guide.lifestyle_guide,
        precautions=guide.precautions,
        recommended_checkups=guide.recommended_checkups,
        disclaimer=guide.disclaimer,
        regeneration_reason=guide.regeneration_reason,
        created_at=guide.created_at,
        updated_at=guide.updated_at,
    )


def _check_regen_limit(user_id: int) -> None:
    """재생성 일일 횟수 제한 확인 (5회/일)."""
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    key = _REGEN_LIMIT_KEY.format(user_id=user_id, date=today)

    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, 86400)  # 24시간 TTL
    results = pipe.execute()
    count = results[0]

    if count > REGEN_DAILY_LIMIT:
        raise HTTPException(status_code=429, detail=f"가이드 재생성은 하루 {REGEN_DAILY_LIMIT}회까지 가능합니다.")


def _run_guide_generation(
    guide_id: int,
    record_id: int,
    user_id: int,
) -> None:
    """백그라운드 가이드 생성 함수."""
    from database import SessionLocal

    db = SessionLocal()
    try:
        guide = db.query(Guide).filter(Guide.id == guide_id).first()
        if not guide:
            return

        record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
        user = db.query(User).filter(User.id == user_id).first()
        medications = db.query(Medication).filter(Medication.record_id == record_id).all()

        if not record or not user:
            guide.status = GuideStatusEnum.archived
            db.commit()
            return

        try:
            result = generate_guide(
                visit_date=str(record.visit_date),
                hospital_name=record.hospital_name or "",
                diagnosis=record.diagnosis,
                medications=medications,
                memo=record.memo or "",
                chronic_diseases=user.chronic_diseases or "",
                allergy_info=user.allergy_info or "",
            )
            guide.medication_guide = result["medication_guide"]
            guide.lifestyle_guide = result["lifestyle_guide"]
            guide.precautions = result["precautions"]
            guide.recommended_checkups = result["recommended_checkups"]
            guide.status = GuideStatusEnum.active

            # 진료기록에 가이드 생성 완료 표시
            record.has_guide = True
            record.guide_needs_update = False

        except Exception:
            # 생성 실패 시 가이드 삭제 처리
            guide.deleted_at = datetime.now(UTC)

        db.commit()
    finally:
        db.close()


# ── 1. 가이드 생성 ────────────────────────────────────────


@router.post(
    "/guides",
    response_model=GuideDetail,
    status_code=202,
    summary="REQ-GUIDE-001: 가이드 생성",
)
def create_guide(
    data: GuideCreateRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """진료기록 기반 가이드를 백그라운드에서 생성합니다."""
    record = _get_record_or_404(data.record_id, user_id, db)

    # 이미 active 가이드가 있으면 중복 생성 방지
    existing = (
        db.query(Guide)
        .filter(
            Guide.record_id == data.record_id,
            Guide.user_id == user_id,
            Guide.status == GuideStatusEnum.active,
            Guide.deleted_at.is_(None),
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="이미 생성된 가이드가 있습니다. 재생성을 이용해주세요.")

    guide = Guide(
        user_id=user_id,
        record_id=data.record_id,
        status=GuideStatusEnum.needs_update,  # 생성 완료 전 임시 상태
        disclaimer=DISCLAIMER,
        version=1,
    )
    db.add(guide)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="가이드 생성 요청에 실패했습니다.")
    db.refresh(guide)

    background_tasks.add_task(_run_guide_generation, guide.id, data.record_id, user_id)

    return _build_detail(guide, record.diagnosis)


# ── 2. 목록 조회 ──────────────────────────────────────────


@router.get(
    "/guides",
    response_model=GuideListResponse,
    summary="REQ-GUIDE-003: 가이드 목록 조회",
)
def list_guides(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=MAX_PAGE_SIZE),
    order: str = Query("latest", pattern="^(latest|visit_date)$"),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    # archived 가이드는 목록에서 제외 (active, needs_update만 노출)
    query = db.query(Guide).filter(
        Guide.user_id == user_id,
        Guide.deleted_at.is_(None),
        Guide.status != GuideStatusEnum.archived,
    )

    if order == "visit_date":
        # 진료일자 기준 정렬 — record join 필요
        query = query.join(MedicalRecord, Guide.record_id == MedicalRecord.id).order_by(
            MedicalRecord.visit_date.desc(), Guide.id.desc()
        )
    else:
        query = query.order_by(Guide.created_at.desc(), Guide.id.desc())

    total = query.count()
    guides = query.offset((page - 1) * size).limit(size).all()

    # 진단명 일괄 조회 (N+1 방지)
    record_ids = [g.record_id for g in guides]
    records_map = {}
    if record_ids:
        records = (
            db.query(MedicalRecord)
            .filter(
                MedicalRecord.id.in_(record_ids),
                MedicalRecord.deleted_at.is_(None),
            )
            .all()
        )
        records_map = {r.id: r.diagnosis for r in records}

    items = [_build_brief(g, records_map.get(g.record_id, "알 수 없음")) for g in guides]

    return GuideListResponse(items=items, total=total, page=page, size=size)


# ── 3. 상세 조회 ──────────────────────────────────────────


@router.get(
    "/guides/{guide_id}",
    response_model=GuideDetail,
    summary="REQ-GUIDE-004: 가이드 상세 조회",
)
def get_guide(
    guide_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    guide = _get_guide_or_404(guide_id, user_id, db)
    record = db.query(MedicalRecord).filter(MedicalRecord.id == guide.record_id).first()
    diagnosis = record.diagnosis if record else "알 수 없음"
    return _build_detail(guide, diagnosis)


# ── 4. 가이드 재생성 ──────────────────────────────────────


@router.post(
    "/guides/{guide_id}/regenerate",
    response_model=GuideDetail,
    status_code=202,
    summary="REQ-GUIDE-005: 가이드 재생성",
)
def regenerate_guide(
    guide_id: int,
    data: GuideRegenerateRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """기존 가이드를 archived로 전환 후 새 가이드를 생성합니다."""
    # 일일 재생성 횟수 제한 확인
    _check_regen_limit(user_id)

    old_guide = _get_guide_or_404(guide_id, user_id, db)
    record = _get_record_or_404(old_guide.record_id, user_id, db)

    # 기존 가이드 archived 처리
    old_guide.status = GuideStatusEnum.archived

    # 새 가이드 생성
    new_guide = Guide(
        user_id=user_id,
        record_id=old_guide.record_id,
        status=GuideStatusEnum.needs_update,
        disclaimer=DISCLAIMER,
        regeneration_reason=data.reason,
        version=old_guide.version + 1,
    )
    db.add(new_guide)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="가이드 재생성 요청에 실패했습니다.")
    db.refresh(new_guide)

    background_tasks.add_task(_run_guide_generation, new_guide.id, old_guide.record_id, user_id)

    return _build_detail(new_guide, record.diagnosis)


# ── 5. 피드백 등록/수정 ───────────────────────────────────


@router.post(
    "/guides/{guide_id}/feedback",
    response_model=GuideFeedbackResponse,
    summary="REQ-GUIDE-006: 가이드 피드백 등록/수정",
)
def upsert_feedback(
    guide_id: int,
    data: GuideFeedbackRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """피드백이 없으면 생성, 있으면 수정합니다."""
    _get_guide_or_404(guide_id, user_id, db)

    feedback = (
        db.query(GuideFeedback)
        .filter(
            GuideFeedback.guide_id == guide_id,
            GuideFeedback.user_id == user_id,
        )
        .first()
    )

    if feedback:
        # 기존 피드백 수정
        feedback.accuracy = data.accuracy
        feedback.clarity = data.clarity
        feedback.usefulness = data.usefulness
        feedback.comment = data.comment
    else:
        # 새 피드백 등록
        feedback = GuideFeedback(
            guide_id=guide_id,
            user_id=user_id,
            accuracy=data.accuracy,
            clarity=data.clarity,
            usefulness=data.usefulness,
            comment=data.comment,
        )
        db.add(feedback)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="피드백 저장에 실패했습니다.")
    db.refresh(feedback)
    return feedback


# ── 6. 피드백 조회 ────────────────────────────────────────


@router.get(
    "/guides/{guide_id}/feedback",
    response_model=GuideFeedbackResponse,
    summary="REQ-GUIDE-006: 내 피드백 조회",
)
def get_feedback(
    guide_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    _get_guide_or_404(guide_id, user_id, db)

    feedback = (
        db.query(GuideFeedback)
        .filter(
            GuideFeedback.guide_id == guide_id,
            GuideFeedback.user_id == user_id,
        )
        .first()
    )
    if not feedback:
        raise HTTPException(status_code=404, detail="등록된 피드백이 없습니다.")
    return feedback
