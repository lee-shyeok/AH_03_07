"""
약품 기준정보 + 활성도 임계 알림 + 피드백 + 보호자 공유 라우터

엔드포인트:
  GET    /v1/drug-references                    약품 기준정보 검색
  GET    /v1/activity-logs/thresholds           활성도 임계 알림 조회
  PUT    /v1/activity-logs/thresholds           활성도 임계 알림 설정
  POST   /v1/feedback                           피드백 제출
  POST   /v1/guardians/shares                   보호자 공유 링크 생성
  GET    /v1/guardians/shares                   보호자 공유 목록
  DELETE /v1/guardians/shares/{id}             보호자 공유 철회
  GET    /v1/guardians/view/{token}             보호자 의료정보 열람
"""
import json
import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from extra_models import (
    ActivityThreshold,
    DrugReference,
    Feedback,
    GuardianShare,
)
from extra_schemas import (
    VALID_METRIC_TYPES,
    ActivityThresholdResponse,
    ActivityThresholdUpsert,
    DrugReferenceResponse,
    FeedbackCreate,
    FeedbackResponse,
    GuardianShareCreate,
    GuardianShareResponse,
    GuardianViewResponse,
)
from security import get_current_user_id

router = APIRouter()

MAX_THRESHOLDS_PER_USER = len(VALID_METRIC_TYPES)  # metric_type당 1개
MAX_GUARDIAN_SHARES = 3  # 최대 보호자 3명


# ══════════════════════════════════════════════════════════
# 약품 기준정보 조회 (API-약품-007)
# ══════════════════════════════════════════════════════════

@router.get(
    "/drug-references",
    response_model=list[DrugReferenceResponse],
    summary="API-약품-007: 약품 기준정보 검색",
)
def search_drug_references(
    query: str = Query(..., min_length=1, max_length=100),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    약품명으로 기준정보를 검색합니다.
    약품 추천 X — 사용자 입력 약품 확인·일반 정보 조회 용도.
    출처: 식약처 의약품안전나라
    """
    results = db.query(DrugReference).filter(
        DrugReference.drug_name.ilike(f"%{query}%")
    ).offset((page - 1) * size).limit(size).all()
    return results


# ══════════════════════════════════════════════════════════
# 활성도 임계 알림 (API-활성도-003/004)
# ══════════════════════════════════════════════════════════

@router.get(
    "/activity-logs/thresholds",
    response_model=list[ActivityThresholdResponse],
    summary="API-활성도-003: 활성도 알림 기준값 조회",
)
def get_thresholds(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    사용자가 직접 설정한 활성도 알림 기준값을 반환합니다.
    앱 자동 판정 X — 의료법 §27 회피.
    """
    return db.query(ActivityThreshold).filter(
        ActivityThreshold.user_id == user_id,
    ).order_by(ActivityThreshold.metric_type).all()


@router.put(
    "/activity-logs/thresholds",
    response_model=ActivityThresholdResponse,
    summary="API-활성도-004: 활성도 알림 기준값 설정·수정",
)
def upsert_threshold(
    data: ActivityThresholdUpsert,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """metric_type당 1개. 이미 있으면 업데이트."""
    existing = db.query(ActivityThreshold).filter(
        ActivityThreshold.user_id == user_id,
        ActivityThreshold.metric_type == data.metric_type,
    ).first()

    if existing:
        existing.threshold_value = data.threshold_value
        existing.custom_message = data.custom_message
        existing.is_active = data.is_active
        threshold = existing
    else:
        threshold = ActivityThreshold(
            user_id=user_id,
            metric_type=data.metric_type,
            threshold_value=data.threshold_value,
            custom_message=data.custom_message,
            is_active=data.is_active,
        )
        db.add(threshold)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="기준값 저장에 실패했습니다.")
    db.refresh(threshold)
    return threshold


# ══════════════════════════════════════════════════════════
# 피드백 (API-피드백-001)
# ══════════════════════════════════════════════════════════

@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    status_code=201,
    summary="API-피드백-001: 구조화 피드백 제출",
)
def create_feedback(
    data: FeedbackCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    피드백 제출. 개인정보보호법 §28-2: 가명처리 후 모델 개선 활용.
    target_id가 있으면 소유권 확인 없이 저장 (가명처리 특성상 허용).
    """
    feedback = Feedback(
        user_id=user_id,
        target_type=data.target_type,
        target_id=data.target_id,
        score=data.score,
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


# ══════════════════════════════════════════════════════════
# 보호자 공유 (API-보호자-001~004)
# ══════════════════════════════════════════════════════════

def _get_share_or_404(share_id: int, user_id: int, db: Session) -> GuardianShare:
    share = db.query(GuardianShare).filter(
        GuardianShare.id == share_id,
        GuardianShare.user_id == user_id,
    ).first()
    if not share:
        raise HTTPException(status_code=404, detail="보호자 공유를 찾을 수 없습니다.")
    return share


@router.post(
    "/guardians/shares",
    response_model=GuardianShareResponse,
    status_code=201,
    summary="API-보호자-001: 보호자 공유 링크 생성",
)
def create_guardian_share(
    data: GuardianShareCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    보호자 공유 링크를 생성합니다.
    만 14세 미만은 법정대리인 동의 필수 (프론트에서 처리).
    보안 링크 토큰은 64바이트 URL-safe 난수로 생성.
    """
    # 활성 공유 최대 3개 제한
    active_count = db.query(GuardianShare).filter(
        GuardianShare.user_id == user_id,
        GuardianShare.is_revoked == False,
    ).count()
    if active_count >= MAX_GUARDIAN_SHARES:
        raise HTTPException(
            status_code=400,
            detail=f"보호자 공유는 최대 {MAX_GUARDIAN_SHARES}명까지 가능합니다."
        )

    # 암호학적으로 안전한 토큰 생성
    token = secrets.token_urlsafe(64)

    share = GuardianShare(
        user_id=user_id,
        guardian_name=data.guardian_name,
        guardian_contact=data.guardian_contact,
        share_categories=json.dumps(data.share_categories, ensure_ascii=False),
        secure_link_token=token,
        expires_at=data.expires_at,
    )
    db.add(share)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="보호자 공유 생성에 실패했습니다.")
    db.refresh(share)
    return GuardianShareResponse.from_orm(share)


@router.get(
    "/guardians/shares",
    response_model=list[GuardianShareResponse],
    summary="API-보호자-002: 보호자 공유 목록",
)
def list_guardian_shares(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    shares = db.query(GuardianShare).filter(
        GuardianShare.user_id == user_id,
    ).order_by(GuardianShare.created_at.desc()).all()
    return [GuardianShareResponse.from_orm(s) for s in shares]


@router.delete(
    "/guardians/shares/{share_id}",
    status_code=204,
    summary="API-보호자-003: 보호자 공유 철회",
)
def revoke_guardian_share(
    share_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """즉시 링크 무효화."""
    share = _get_share_or_404(share_id, user_id, db)
    share.is_revoked = True
    share.revoked_at = datetime.now(UTC)
    db.commit()


@router.get(
    "/guardians/view/{token}",
    response_model=GuardianViewResponse,
    summary="API-보호자-004: 보호자 의료정보 열람",
)
def view_guardian_share(
    token: str,
    db: Session = Depends(get_db),
):
    """
    보호자가 보안 링크 토큰으로 의료정보를 열람합니다.
    - 별도 인증 없이 토큰만으로 접근 (토큰이 인증 수단)
    - 만료·철회 여부 확인
    - 접근 로그 기록
    """
    # 토큰 길이 검증 (과도하게 긴 입력 차단)
    if len(token) > 200:
        raise HTTPException(status_code=404, detail="유효하지 않은 링크입니다.")

    share = db.query(GuardianShare).filter(
        GuardianShare.secure_link_token == token,
    ).first()

    if not share:
        raise HTTPException(status_code=404, detail="유효하지 않은 링크입니다.")

    # 철회 여부 확인
    if share.is_revoked:
        raise HTTPException(status_code=410, detail="철회된 공유 링크입니다.")

    # 만료 여부 확인
    now = datetime.now(UTC)
    expires = share.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    if now > expires:
        raise HTTPException(status_code=410, detail="만료된 공유 링크입니다.")

    # 접근 로그 기록
    share.last_accessed_at = now
    share.access_count += 1
    db.commit()

    # 공유 카테고리에 따라 데이터 조회
    try:
        categories = json.loads(share.share_categories)
    except (json.JSONDecodeError, TypeError, ValueError):
        categories = []

    content = _build_shared_content(share.user_id, categories, db)

    return GuardianViewResponse(
        guardian_name=share.guardian_name,
        share_categories=categories,
        content=content,
        expires_at=share.expires_at,
    )


def _build_shared_content(user_id: int, categories: list, db: Session) -> dict:
    """공유 카테고리에 따라 데이터를 조회하여 반환."""
    from guide_models import Guide, GuideStatusEnum
    from medical_record_models import MedicalRecord

    content = {}

    if "medical_records" in categories:
        records = db.query(MedicalRecord).filter(
            MedicalRecord.user_id == user_id,
            MedicalRecord.deleted_at.is_(None),
        ).order_by(MedicalRecord.visit_date.desc()).limit(10).all()
        content["medical_records"] = [
            {
                "visit_date": str(r.visit_date),
                "hospital_name": r.hospital_name,
                "diagnosis": r.diagnosis,
            }
            for r in records
        ]

    if "guides" in categories:
        guides = db.query(Guide).filter(
            Guide.user_id == user_id,
            Guide.deleted_at.is_(None),
            Guide.status == GuideStatusEnum.active,
        ).order_by(Guide.created_at.desc()).limit(5).all()
        content["guides"] = [
            {
                "medication_guide": g.medication_guide,
                "precautions": g.precautions,
                "disclaimer": g.disclaimer,
            }
            for g in guides
        ]

    return content
