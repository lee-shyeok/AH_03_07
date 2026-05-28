"""
약품 + 복약 + 활성도 + 증상 + 위험신호 + 자가면역 + 검사 라우터

엔드포인트:
  POST/GET/PUT/DELETE  /v1/medications              복용 약품 CRUD
  GET                  /v1/medication-logs           복약 이력 조회
  PUT                  /v1/medication-logs/{id}/check 복약 체크

  POST/GET             /v1/activity-logs             활성도 기록 (upsert)

  POST/GET             /v1/symptom-checks            증상 자가체크

  GET/PATCH            /v1/risk-flags                위험 신호
  GET/PATCH            /v1/risk-flags/{id}

  GET/PUT              /v1/autoimmune/profile        자가면역 프로필
  POST/GET/PUT/DELETE  /v1/care-schedules            진료 일정

  POST/GET             /v1/lab-results               검사 결과
"""
import json
from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from clinical_models import (
    ActivityLog,
    AutoimmuneProfile,
    CareSchedule,
    LabResult,
    MedicationLog,
    RiskFlag,
    RiskFlagStatusEnum,
    SymptomCheck,
    UserMedication,
)
from clinical_schemas import (
    SAFETY_NOTICE_SYMPTOMS,
    ActivityLogResponse,
    ActivityLogUpsert,
    AutoimmuneProfileResponse,
    AutoimmuneProfileUpdate,
    CareScheduleCreate,
    CareScheduleResponse,
    CareScheduleUpdate,
    LabResultCreate,
    LabResultResponse,
    MedicationLogCheckRequest,
    MedicationLogResponse,
    RiskFlagResponse,
    RiskFlagUpdateRequest,
    SymptomCheckCreate,
    SymptomCheckResponse,
    UserMedicationCreate,
    UserMedicationResponse,
    UserMedicationUpdate,
)
from database import get_db
from security import get_current_user_id

router = APIRouter()

MAX_MEDICATIONS = 200
MAX_CARE_SCHEDULES = 200
MAX_LAB_RESULTS = 500
MAX_PAGE_SIZE = 50


# ══════════════════════════════════════════════════════════
# 약품 CRUD
# ══════════════════════════════════════════════════════════

def _get_medication_or_404(mid: int, user_id: int, db: Session) -> UserMedication:
    m = db.query(UserMedication).filter(
        UserMedication.id == mid,
        UserMedication.user_id == user_id,
        UserMedication.deleted_at.is_(None),
    ).first()
    if not m:
        raise HTTPException(status_code=404, detail="약품을 찾을 수 없습니다.")
    return m


@router.post("/medications", response_model=UserMedicationResponse, status_code=201,
             summary="API-약품-001: 복용 약품 등록")
def create_medication(
    data: UserMedicationCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    count = db.query(UserMedication).filter(
        UserMedication.user_id == user_id,
        UserMedication.deleted_at.is_(None),
    ).count()
    if count >= MAX_MEDICATIONS:
        raise HTTPException(status_code=400,
            detail=f"약품은 최대 {MAX_MEDICATIONS}개까지 등록할 수 있습니다.")

    med = UserMedication(
        user_id=user_id,
        drug_name_user_input=data.drug_name_user_input,
        drug_reference_id=data.drug_reference_id,
        dosage=data.dosage,
        frequency=data.frequency,
        duration_days=data.duration_days,
        is_autoimmune_drug=data.is_autoimmune_drug,
        memo=data.memo,
    )
    db.add(med)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="약품 등록에 실패했습니다.")
    db.refresh(med)
    return med


@router.get("/medications", response_model=list[UserMedicationResponse],
            summary="API-약품-002: 내 약품 목록")
def list_medications(
    is_autoimmune: bool | None = Query(None),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    q = db.query(UserMedication).filter(
        UserMedication.user_id == user_id,
        UserMedication.deleted_at.is_(None),
    )
    if is_autoimmune is not None:
        q = q.filter(UserMedication.is_autoimmune_drug == is_autoimmune)
    return q.order_by(UserMedication.created_at.desc()).all()


@router.put("/medications/{med_id}", response_model=UserMedicationResponse,
            summary="API-약품-003: 약품 정보 수정")
def update_medication(
    med_id: int,
    data: UserMedicationUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    med = _get_medication_or_404(med_id, user_id, db)
    if data.drug_name_user_input is not None:
        med.drug_name_user_input = data.drug_name_user_input
    if data.dosage is not None:
        med.dosage = data.dosage
    if data.frequency is not None:
        med.frequency = data.frequency
    if data.duration_days is not None:
        med.duration_days = data.duration_days
    if data.is_autoimmune_drug is not None:
        med.is_autoimmune_drug = data.is_autoimmune_drug
    if data.memo is not None:
        med.memo = data.memo
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="약품 수정에 실패했습니다.")
    db.refresh(med)
    return med


@router.delete("/medications/{med_id}", status_code=204,
               summary="API-약품-004: 약품 삭제")
def delete_medication(
    med_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    med = _get_medication_or_404(med_id, user_id, db)
    med.deleted_at = datetime.now(UTC)
    db.commit()


# ══════════════════════════════════════════════════════════
# 복약 이력
# ══════════════════════════════════════════════════════════

@router.get("/medication-logs", response_model=list[MedicationLogResponse],
            summary="API-복약-001: 복약 이력 조회")
def list_medication_logs(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    q = db.query(MedicationLog).filter(MedicationLog.user_id == user_id)
    if date_from:
        q = q.filter(MedicationLog.scheduled_date >= date_from)
    if date_to:
        q = q.filter(MedicationLog.scheduled_date <= date_to)
    return q.order_by(MedicationLog.scheduled_date.desc()).limit(500).all()


@router.put("/medication-logs/{log_id}/check", response_model=MedicationLogResponse,
            summary="API-복약-002: 복약 체크")
def check_medication_log(
    log_id: int,
    data: MedicationLogCheckRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    log = db.query(MedicationLog).filter(
        MedicationLog.id == log_id,
        MedicationLog.user_id == user_id,
    ).first()
    if not log:
        raise HTTPException(status_code=404, detail="복약 기록을 찾을 수 없습니다.")
    log.taken = data.taken
    log.taken_at = datetime.now(UTC) if data.taken else None
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="복약 체크에 실패했습니다.")
    db.refresh(log)
    return log


# ══════════════════════════════════════════════════════════
# 활성도 일지
# ══════════════════════════════════════════════════════════

@router.post("/activity-logs", response_model=ActivityLogResponse,
             summary="API-활성도-001: 활성도 기록 (upsert)")
def upsert_activity_log(
    data: ActivityLogUpsert,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """일자당 1건. 이미 있으면 업데이트."""
    existing = db.query(ActivityLog).filter(
        ActivityLog.user_id == user_id,
        ActivityLog.log_date == data.log_date,
    ).first()

    areas_json = json.dumps(data.joint_swelling_areas, ensure_ascii=False) \
        if data.joint_swelling_areas is not None else None

    if existing:
        if data.pain_vas is not None:
            existing.pain_vas = data.pain_vas
        if data.fatigue is not None:
            existing.fatigue = data.fatigue
        if data.morning_stiffness_minutes is not None:
            existing.morning_stiffness_minutes = data.morning_stiffness_minutes
        if areas_json is not None:
            existing.joint_swelling_areas = areas_json
        if data.daily_difficulty is not None:
            existing.daily_difficulty = data.daily_difficulty
        if data.free_memo is not None:
            existing.free_memo = data.free_memo
        log = existing
    else:
        log = ActivityLog(
            user_id=user_id,
            log_date=data.log_date,
            pain_vas=data.pain_vas,
            fatigue=data.fatigue,
            morning_stiffness_minutes=data.morning_stiffness_minutes,
            joint_swelling_areas=areas_json,
            daily_difficulty=data.daily_difficulty,
            free_memo=data.free_memo,
        )
        db.add(log)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="활성도 기록에 실패했습니다.")
    db.refresh(log)
    return ActivityLogResponse.from_orm(log)


@router.get("/activity-logs", response_model=list[ActivityLogResponse],
            summary="API-활성도-002: 활성도 기록 조회")
def list_activity_logs(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    q = db.query(ActivityLog).filter(ActivityLog.user_id == user_id)
    if date_from:
        q = q.filter(ActivityLog.log_date >= date_from)
    if date_to:
        q = q.filter(ActivityLog.log_date <= date_to)
    logs = q.order_by(ActivityLog.log_date.asc()).limit(365).all()
    return [ActivityLogResponse.from_orm(l) for l in logs]


# ══════════════════════════════════════════════════════════
# 증상 체크
# ══════════════════════════════════════════════════════════

@router.post("/symptom-checks", response_model=SymptomCheckResponse, status_code=201,
             summary="API-증상-001: 위험 증상 자가체크")
def create_symptom_check(
    data: SymptomCheckCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    # 안전 고지 필요 여부 판단
    safety_required = any(
        s in SAFETY_NOTICE_SYMPTOMS for s in data.checked_symptoms
    )

    check = SymptomCheck(
        user_id=user_id,
        checked_symptoms=json.dumps(data.checked_symptoms, ensure_ascii=False),
        safety_notice_required=safety_required,
    )
    db.add(check)

    # 안전 고지 필요 시 위험 신호 생성
    if safety_required:
        flag = RiskFlag(
            user_id=user_id,
            source_type="symptom_check",
            flag_type="safety_notice",
            message="위험 증상이 체크되었습니다. 의료진 상담을 권고드립니다.",
            consultation_recommended=True,
        )
        db.add(flag)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="증상 체크 저장에 실패했습니다.")
    db.refresh(check)
    return SymptomCheckResponse.from_orm(check)


@router.get("/symptom-checks", response_model=list[SymptomCheckResponse],
            summary="API-증상-002: 증상 체크 이력 조회")
def list_symptom_checks(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=MAX_PAGE_SIZE),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    q = db.query(SymptomCheck).filter(SymptomCheck.user_id == user_id)
    if date_from:
        q = q.filter(SymptomCheck.created_at >= datetime(
            date_from.year, date_from.month, date_from.day))
    if date_to:
        q = q.filter(SymptomCheck.created_at <= datetime(
            date_to.year, date_to.month, date_to.day, 23, 59, 59))
    checks = q.order_by(SymptomCheck.created_at.desc())\
        .offset((page - 1) * size).limit(size).all()
    return [SymptomCheckResponse.from_orm(c) for c in checks]


# ══════════════════════════════════════════════════════════
# 위험 신호
# ══════════════════════════════════════════════════════════

@router.get("/risk-flags", response_model=list[RiskFlagResponse],
            summary="API-위험-001: 위험 신호 목록")
def list_risk_flags(
    status: RiskFlagStatusEnum | None = Query(None),
    source_type: str | None = Query(None, max_length=50),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=MAX_PAGE_SIZE),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    q = db.query(RiskFlag).filter(RiskFlag.user_id == user_id)
    if status:
        q = q.filter(RiskFlag.status == status)
    if source_type:
        q = q.filter(RiskFlag.source_type == source_type)
    return q.order_by(RiskFlag.created_at.desc())\
        .offset((page - 1) * size).limit(size).all()


@router.get("/risk-flags/{flag_id}", response_model=RiskFlagResponse,
            summary="API-위험-002: 위험 신호 상세")
def get_risk_flag(
    flag_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    flag = db.query(RiskFlag).filter(
        RiskFlag.id == flag_id,
        RiskFlag.user_id == user_id,
    ).first()
    if not flag:
        raise HTTPException(status_code=404, detail="위험 신호를 찾을 수 없습니다.")
    return flag


@router.patch("/risk-flags/{flag_id}", response_model=RiskFlagResponse,
              summary="API-위험-003: 위험 신호 처리")
def update_risk_flag(
    flag_id: int,
    data: RiskFlagUpdateRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    flag = db.query(RiskFlag).filter(
        RiskFlag.id == flag_id,
        RiskFlag.user_id == user_id,
    ).first()
    if not flag:
        raise HTTPException(status_code=404, detail="위험 신호를 찾을 수 없습니다.")

    flag.status = data.status
    if data.status == RiskFlagStatusEnum.resolved:
        flag.resolved_at = datetime.now(UTC)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="위험 신호 처리에 실패했습니다.")
    db.refresh(flag)
    return flag


# ══════════════════════════════════════════════════════════
# 자가면역 프로필
# ══════════════════════════════════════════════════════════

def _get_or_create_autoimmune_profile(user_id: int, db: Session) -> AutoimmuneProfile:
    profile = db.query(AutoimmuneProfile).filter(
        AutoimmuneProfile.user_id == user_id
    ).first()
    if not profile:
        profile = AutoimmuneProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("/autoimmune/profile", response_model=AutoimmuneProfileResponse,
            summary="API-자가면역-001: 위험요인 프로필 조회")
def get_autoimmune_profile(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    profile = _get_or_create_autoimmune_profile(user_id, db)
    return AutoimmuneProfileResponse.from_orm(profile)


@router.put("/autoimmune/profile", response_model=AutoimmuneProfileResponse,
            summary="API-자가면역-002: 위험요인 프로필 수정")
def update_autoimmune_profile(
    data: AutoimmuneProfileUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    profile = _get_or_create_autoimmune_profile(user_id, db)

    if data.risk_factors is not None:
        profile.risk_factors = json.dumps(data.risk_factors, ensure_ascii=False)
    if data.pregnancy_status is not None:
        profile.pregnancy_status = data.pregnancy_status
    if data.vaccination_history is not None:
        profile.vaccination_history = json.dumps(data.vaccination_history, ensure_ascii=False)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="프로필 수정에 실패했습니다.")
    db.refresh(profile)
    return AutoimmuneProfileResponse.from_orm(profile)


# ══════════════════════════════════════════════════════════
# 진료 일정
# ══════════════════════════════════════════════════════════

def _get_schedule_or_404(sid: int, user_id: int, db: Session) -> CareSchedule:
    s = db.query(CareSchedule).filter(
        CareSchedule.id == sid,
        CareSchedule.user_id == user_id,
        CareSchedule.deleted_at.is_(None),
    ).first()
    if not s:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다.")
    return s


@router.post("/care-schedules", response_model=CareScheduleResponse, status_code=201,
             summary="API-자가면역-003: 일정 등록")
def create_care_schedule(
    data: CareScheduleCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    count = db.query(CareSchedule).filter(
        CareSchedule.user_id == user_id,
        CareSchedule.deleted_at.is_(None),
    ).count()
    if count >= MAX_CARE_SCHEDULES:
        raise HTTPException(status_code=400,
            detail=f"일정은 최대 {MAX_CARE_SCHEDULES}개까지 등록할 수 있습니다.")

    schedule = CareSchedule(
        user_id=user_id,
        schedule_type=data.schedule_type,
        title=data.title,
        scheduled_date=data.scheduled_date,
        reminder_days_before=data.reminder_days_before,
        memo=data.memo,
    )
    db.add(schedule)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="일정 등록에 실패했습니다.")
    db.refresh(schedule)
    return schedule


@router.get("/care-schedules", response_model=list[CareScheduleResponse],
            summary="API-자가면역-004: 일정 목록 조회")
def list_care_schedules(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    schedule_type: str | None = Query(None),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    q = db.query(CareSchedule).filter(
        CareSchedule.user_id == user_id,
        CareSchedule.deleted_at.is_(None),
    )
    if date_from:
        q = q.filter(CareSchedule.scheduled_date >= date_from)
    if date_to:
        q = q.filter(CareSchedule.scheduled_date <= date_to)
    if schedule_type:
        q = q.filter(CareSchedule.schedule_type == schedule_type)
    return q.order_by(CareSchedule.scheduled_date.asc()).all()


@router.put("/care-schedules/{sid}", response_model=CareScheduleResponse,
            summary="API-자가면역-005: 일정 수정")
def update_care_schedule(
    sid: int,
    data: CareScheduleUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    schedule = _get_schedule_or_404(sid, user_id, db)
    if data.schedule_type is not None:
        schedule.schedule_type = data.schedule_type
    if data.title is not None:
        schedule.title = data.title
    if data.scheduled_date is not None:
        schedule.scheduled_date = data.scheduled_date
    if data.reminder_days_before is not None:
        schedule.reminder_days_before = data.reminder_days_before
    if data.memo is not None:
        schedule.memo = data.memo
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="일정 수정에 실패했습니다.")
    db.refresh(schedule)
    return schedule


@router.delete("/care-schedules/{sid}", status_code=204,
               summary="API-자가면역-006: 일정 삭제")
def delete_care_schedule(
    sid: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    schedule = _get_schedule_or_404(sid, user_id, db)
    schedule.deleted_at = datetime.now(UTC)
    db.commit()


# ══════════════════════════════════════════════════════════
# 검사 결과
# ══════════════════════════════════════════════════════════

@router.post("/lab-results", response_model=LabResultResponse, status_code=201,
             summary="API-검사-001: 검사 결과 기록")
def create_lab_result(
    data: LabResultCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    # document_id 소유권 검증
    if data.document_id is not None:
        from ocr_models import MedicalDocument
        doc = db.query(MedicalDocument).filter(
            MedicalDocument.id == data.document_id,
            MedicalDocument.user_id == user_id,
            MedicalDocument.deleted_at.is_(None),
        ).first()
        if not doc:
            raise HTTPException(status_code=404, detail="연결할 문서를 찾을 수 없습니다.")

    count = db.query(LabResult).filter(
        LabResult.user_id == user_id,
        LabResult.deleted_at.is_(None),
    ).count()
    if count >= MAX_LAB_RESULTS:
        raise HTTPException(status_code=400,
            detail=f"검사 결과는 최대 {MAX_LAB_RESULTS}개까지 등록할 수 있습니다.")

    result = LabResult(
        user_id=user_id,
        document_id=data.document_id,
        test_date=data.test_date,
        test_type=data.test_type,
        user_recorded_value=data.user_recorded_value,
        reference_range=data.reference_range,
        unit=data.unit,
        memo=data.memo,
    )
    db.add(result)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="검사 결과 저장에 실패했습니다.")
    db.refresh(result)
    return result


@router.get("/lab-results", response_model=list[LabResultResponse],
            summary="API-검사-002: 검사 결과 목록")
def list_lab_results(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=MAX_PAGE_SIZE),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    q = db.query(LabResult).filter(
        LabResult.user_id == user_id,
        LabResult.deleted_at.is_(None),
    )
    if date_from:
        q = q.filter(LabResult.test_date >= date_from)
    if date_to:
        q = q.filter(LabResult.test_date <= date_to)
    return q.order_by(LabResult.test_date.desc())\
        .offset((page - 1) * size).limit(size).all()
