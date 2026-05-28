"""
동의 이력 + 모드 관리 + 질환 관리 라우터

엔드포인트:
  GET    /v1/users/me/consents           동의 이력 조회
  POST   /v1/users/me/consents           동의 추가·갱신

  GET    /v1/users/me/mode               현재 모드 조회
  PUT    /v1/users/me/mode               모드 전환

  POST   /v1/diseases                    질환 등록
  GET    /v1/diseases                    내 질환 목록
  PUT    /v1/diseases/{id}               질환 수정
  DELETE /v1/diseases/{id}              질환 삭제
"""
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from consent_mode_disease_models import (
    ConsentTypeEnum,
    UserConsent,
    UserDisease,
    UserMode,
    UserModeEnum,
)
from consent_mode_disease_schemas import (
    ConsentResponse,
    ConsentUpsertRequest,
    UserDiseaseCreate,
    UserDiseaseResponse,
    UserDiseaseUpdate,
    UserModeResponse,
    UserModeUpdate,
)
from database import get_db
from security import get_current_user_id

router = APIRouter()

MAX_DISEASES_PER_USER = 100


def _get_disease_or_404(disease_id: int, user_id: int, db: Session) -> UserDisease:
    disease = db.query(UserDisease).filter(
        UserDisease.id == disease_id,
        UserDisease.user_id == user_id,
        UserDisease.deleted_at.is_(None),
    ).first()
    if not disease:
        raise HTTPException(status_code=404, detail="질환 정보를 찾을 수 없습니다.")
    return disease


def _get_or_create_mode(user_id: int, db: Session) -> UserMode:
    mode = db.query(UserMode).filter(UserMode.user_id == user_id).first()
    if not mode:
        mode = UserMode(user_id=user_id, mode=UserModeEnum.general)
        db.add(mode)
        db.commit()
        db.refresh(mode)
    return mode


@router.get("/users/me/consents", response_model=list[ConsentResponse],
            summary="API-사용자-004: 동의 이력 조회")
def get_consents(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return db.query(UserConsent).filter(
        UserConsent.user_id == user_id,
    ).order_by(UserConsent.consent_type, UserConsent.updated_at.desc()).all()


@router.post("/users/me/consents", response_model=ConsentResponse,
             summary="API-사용자-005: 동의 추가·갱신")
def upsert_consent(data: ConsentUpsertRequest,
                   user_id: int = Depends(get_current_user_id),
                   db: Session = Depends(get_db)):
    now = datetime.now(UTC)
    existing = db.query(UserConsent).filter(
        UserConsent.user_id == user_id,
        UserConsent.consent_type == data.consent_type,
    ).order_by(UserConsent.created_at.desc()).first()

    if existing:
        existing.agreed = data.agreed
        existing.version = data.version
        existing.agreed_at = now if data.agreed else existing.agreed_at
        existing.revoked_at = now if not data.agreed else None
        consent = existing
    else:
        consent = UserConsent(
            user_id=user_id,
            consent_type=data.consent_type,
            agreed=data.agreed,
            version=data.version,
            agreed_at=now if data.agreed else None,
            revoked_at=None if data.agreed else now,
        )
        db.add(consent)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="동의 정보 저장에 실패했습니다.")
    db.refresh(consent)
    return consent


@router.get("/users/me/mode", response_model=UserModeResponse,
            summary="API-모드-001: 현재 모드 조회")
def get_mode(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return _get_or_create_mode(user_id, db)


@router.put("/users/me/mode", response_model=UserModeResponse,
            summary="API-모드-002: 모드 전환")
def update_mode(data: UserModeUpdate,
                user_id: int = Depends(get_current_user_id),
                db: Session = Depends(get_db)):
    if data.mode == UserModeEnum.autoimmune:
        consent = db.query(UserConsent).filter(
            UserConsent.user_id == user_id,
            UserConsent.consent_type == ConsentTypeEnum.sensitive_medical,
            UserConsent.agreed == True,
        ).first()
        if not consent:
            raise HTTPException(status_code=403,
                detail="자가면역 모드 사용을 위해 민감 의료정보 처리 동의가 필요합니다.")

    mode = _get_or_create_mode(user_id, db)
    mode.mode = data.mode
    mode.selected_at = datetime.now(UTC)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="모드 변경에 실패했습니다.")
    db.refresh(mode)
    return mode


@router.post("/diseases", response_model=UserDiseaseResponse, status_code=201,
             summary="API-질환-001: 질환 등록")
def create_disease(data: UserDiseaseCreate,
                   user_id: int = Depends(get_current_user_id),
                   db: Session = Depends(get_db)):
    count = db.query(UserDisease).filter(
        UserDisease.user_id == user_id,
        UserDisease.deleted_at.is_(None),
    ).count()
    if count >= MAX_DISEASES_PER_USER:
        raise HTTPException(status_code=400,
            detail=f"질환은 최대 {MAX_DISEASES_PER_USER}개까지 등록할 수 있습니다.")

    disease = UserDisease(
        user_id=user_id,
        disease_name=data.disease_name,
        disease_code=data.disease_code,
        diagnosis_date=data.diagnosis_date,
        memo=data.memo,
    )
    db.add(disease)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="질환 등록에 실패했습니다.")
    db.refresh(disease)
    return disease


@router.get("/diseases", response_model=list[UserDiseaseResponse],
            summary="API-질환-002: 내 질환 목록 조회")
def list_diseases(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return db.query(UserDisease).filter(
        UserDisease.user_id == user_id,
        UserDisease.deleted_at.is_(None),
    ).order_by(UserDisease.created_at.desc()).all()


@router.put("/diseases/{disease_id}", response_model=UserDiseaseResponse,
            summary="API-질환-003: 질환 정보 수정")
def update_disease(disease_id: int, data: UserDiseaseUpdate,
                   user_id: int = Depends(get_current_user_id),
                   db: Session = Depends(get_db)):
    disease = _get_disease_or_404(disease_id, user_id, db)
    if data.disease_name is not None:
        disease.disease_name = data.disease_name
    if data.disease_code is not None:
        disease.disease_code = data.disease_code
    if data.diagnosis_date is not None:
        disease.diagnosis_date = data.diagnosis_date
    if data.memo is not None:
        disease.memo = data.memo
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="질환 정보 수정에 실패했습니다.")
    db.refresh(disease)
    return disease


@router.delete("/diseases/{disease_id}", status_code=204,
               summary="API-질환-004: 질환 삭제")
def delete_disease(disease_id: int,
                   user_id: int = Depends(get_current_user_id),
                   db: Session = Depends(get_db)):
    disease = _get_disease_or_404(disease_id, user_id, db)
    disease.deleted_at = datetime.now(UTC)
    db.commit()
