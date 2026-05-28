"""
Post-MVP 라우터

엔드포인트:
  POST/GET  /v1/health-metrics              건강수치
  GET       /v1/pharmacies/nearby           주변 약국 조회
  POST/GET  /v1/diary/symptom-logs          증상 일기
  POST      /v1/diary/medication-logs       복약 체크
  GET       /v1/diary/pdf                   진료용 PDF
  GET       /v1/general/schedule            통합 캘린더
  POST      /v1/contents/card-news          카드뉴스 생성
  POST      /v1/contents/tts               TTS 생성
  GET       /v1/contents                    콘텐츠 이력
  POST      /v1/games/scores               게임 점수
  GET       /v1/games/badges               뱃지·포인트
  GET       /v1/admin/safety-filter-logs   안전 필터 로그
"""

import json
import os
from datetime import date, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from postmvp_models import (
    ContentConversion,
    ContentStatusEnum,
    ContentTypeEnum,
    DiaryMedicationLog,
    DiarySymptomLog,
    GameScore,
    HealthMetric,
    SafetyFilterLog,
    UserBadge,
    UserPoints,
)
from postmvp_schemas import (
    BADGE_THRESHOLDS,
    POINTS_PER_SCORE,
    BadgeInfo,
    CardNewsCreateRequest,
    ContentConversionResponse,
    DiaryMedicationLogCreate,
    DiaryMedicationLogResponse,
    DiarySymptomLogCreate,
    DiarySymptomLogResponse,
    GameScoreCreate,
    GameScoreResponse,
    HealthMetricCreate,
    HealthMetricResponse,
    SafetyFilterLogResponse,
    ScheduleResponse,
    TTSCreateRequest,
    UserBadgesResponse,
)
from security import get_current_user_id

router = APIRouter()

MAX_HEALTH_METRICS = 5000
MAX_PAGE_SIZE = 50

# 관리자 user_id 목록 (환경변수로 관리)
_ADMIN_IDS_RAW = os.getenv("ADMIN_USER_IDS", "")
ADMIN_USER_IDS: set = {int(x.strip()) for x in _ADMIN_IDS_RAW.split(",") if x.strip().isdigit()}


def _require_admin(user_id: int) -> None:
    if not ADMIN_USER_IDS or user_id not in ADMIN_USER_IDS:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")


# ══════════════════════════════════════════════════════════
# 건강수치
# ══════════════════════════════════════════════════════════


@router.post(
    "/health-metrics",
    response_model=HealthMetricResponse,
    status_code=201,
    summary="API-건강수치-001: 건강 수치 수동 입력",
)
def create_health_metric(
    data: HealthMetricCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    혈압·혈당 등 건강 수치를 수동 입력합니다.
    자동 판정·정상/비정상 분류 X — 사용자 기록값 그대로 저장.
    """
    count = db.query(HealthMetric).filter(HealthMetric.user_id == user_id).count()
    if count >= MAX_HEALTH_METRICS:
        raise HTTPException(status_code=400, detail=f"건강 수치는 최대 {MAX_HEALTH_METRICS}개까지 기록할 수 있습니다.")

    metric = HealthMetric(
        user_id=user_id,
        metric_type=data.metric_type,
        user_recorded_value=data.user_recorded_value,
        unit=data.unit,
        measured_at=data.measured_at,
        memo=data.memo,
    )
    db.add(metric)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="건강 수치 저장에 실패했습니다.")
    db.refresh(metric)
    return metric


@router.get(
    "/health-metrics", response_model=list[HealthMetricResponse], summary="API-건강수치-002: 건강 수치 그래프 데이터"
)
def list_health_metrics(
    metric_type: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(30, ge=1, le=MAX_PAGE_SIZE),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    q = db.query(HealthMetric).filter(HealthMetric.user_id == user_id)
    if metric_type:
        q = q.filter(HealthMetric.metric_type == metric_type)
    if date_from:
        q = q.filter(HealthMetric.measured_at >= date_from)
    if date_to:
        q = q.filter(HealthMetric.measured_at <= date_to)
    return q.order_by(HealthMetric.measured_at.asc()).offset((page - 1) * size).limit(size).all()


# ══════════════════════════════════════════════════════════
# 주변 약국 조회 (외부 API 연동)
# ══════════════════════════════════════════════════════════


@router.get("/pharmacies/nearby", summary="API-약국-001: 주변 약국 정보 조회")
def get_nearby_pharmacies(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius: int = Query(1000, ge=100, le=5000),  # 미터 단위, 최대 5km
    open_now: bool = Query(False),
    user_id: int = Depends(get_current_user_id),
):
    """
    주변 약국 정보를 반환합니다.
    약국 추천·알선·광고 순위 X, 특정 약국 지정·재고 보장 X.
    현재는 외부 API 미연동 상태로 빈 목록 반환.
    """
    # TODO: 공공데이터 포털 또는 카카오 로컬 API 연동
    return {
        "pharmacies": [],
        "total": 0,
        "notice": "주변 약국 정보는 참고용입니다. 재고 및 운영 여부는 직접 확인하세요.",
    }


# ══════════════════════════════════════════════════════════
# 일반 모드 증상 일기
# ══════════════════════════════════════════════════════════


@router.post(
    "/diary/symptom-logs",
    response_model=DiarySymptomLogResponse,
    status_code=201,
    summary="API-일반-일기-001: 증상 일기 작성",
)
def create_diary_symptom_log(
    data: DiarySymptomLogCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    일반 모드 증상 일기. 복약 기록과 완전 분리.
    일자당 1건 upsert.
    """
    existing = (
        db.query(DiarySymptomLog)
        .filter(
            DiarySymptomLog.user_id == user_id,
            DiarySymptomLog.log_date == data.log_date,
        )
        .first()
    )

    body_parts_json = json.dumps(data.body_parts, ensure_ascii=False) if data.body_parts is not None else None

    if existing:
        if data.overall_condition is not None:
            existing.overall_condition = data.overall_condition
        if body_parts_json is not None:
            existing.body_parts = body_parts_json
        if data.feeling is not None:
            existing.feeling = data.feeling
        if data.memo is not None:
            existing.memo = data.memo
        log = existing
    else:
        log = DiarySymptomLog(
            user_id=user_id,
            log_date=data.log_date,
            overall_condition=data.overall_condition,
            body_parts=body_parts_json,
            feeling=data.feeling,
            memo=data.memo,
        )
        db.add(log)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="증상 일기 저장에 실패했습니다.")
    db.refresh(log)
    return DiarySymptomLogResponse.from_orm(log)


@router.get(
    "/diary/symptom-logs", response_model=list[DiarySymptomLogResponse], summary="API-일반-일기-002: 증상 일기 조회"
)
def list_diary_symptom_logs(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=MAX_PAGE_SIZE),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """날짜순 원본 나열. 앱 분석·통계 X. 복약 기록과 완전 분리."""
    q = db.query(DiarySymptomLog).filter(DiarySymptomLog.user_id == user_id)
    if date_from:
        q = q.filter(DiarySymptomLog.log_date >= date_from)
    if date_to:
        q = q.filter(DiarySymptomLog.log_date <= date_to)
    logs = q.order_by(DiarySymptomLog.log_date.asc()).offset((page - 1) * size).limit(size).all()
    return [DiarySymptomLogResponse.from_orm(l) for l in logs]


# ══════════════════════════════════════════════════════════
# 일반 모드 복약 체크
# ══════════════════════════════════════════════════════════


@router.post(
    "/diary/medication-logs",
    response_model=DiaryMedicationLogResponse,
    status_code=201,
    summary="API-일반-일기-003: 복약 체크",
)
def create_diary_medication_log(
    data: DiaryMedicationLogCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    증상 기록과 완전 분리. 약효 평가 차단.
    medication_id 소유권 확인.
    """
    # medication_id 소유권 검증
    from clinical_models import UserMedication

    med = (
        db.query(UserMedication)
        .filter(
            UserMedication.id == data.medication_id,
            UserMedication.user_id == user_id,
            UserMedication.deleted_at.is_(None),
        )
        .first()
    )
    if not med:
        raise HTTPException(status_code=404, detail="약품을 찾을 수 없습니다.")

    log = DiaryMedicationLog(
        user_id=user_id,
        medication_id=data.medication_id,
        log_date=data.log_date,
        time_slot=data.time_slot,
        taken=data.taken,
    )
    db.add(log)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="복약 체크 저장에 실패했습니다.")
    db.refresh(log)
    return log


# ══════════════════════════════════════════════════════════
# 진료용 PDF
# ══════════════════════════════════════════════════════════


@router.get("/diary/pdf", summary="API-일반-일기-004: 진료용 PDF 출력")
def get_diary_pdf(
    date_from: date = Query(...),
    date_to: date = Query(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    증상·복약 두 섹션 완전 분리. 앱 요약·해석 X.
    현재는 텍스트 기반 간단 PDF 생성 (reportlab 미설치 시 텍스트 반환).
    """
    if date_to < date_from:
        raise HTTPException(status_code=400, detail="종료일은 시작일 이후여야 합니다.")

    # 증상 일기 조회
    symptom_logs = (
        db.query(DiarySymptomLog)
        .filter(
            DiarySymptomLog.user_id == user_id,
            DiarySymptomLog.log_date >= date_from,
            DiarySymptomLog.log_date <= date_to,
        )
        .order_by(DiarySymptomLog.log_date.asc())
        .all()
    )

    # 복약 체크 조회
    med_logs = (
        db.query(DiaryMedicationLog)
        .filter(
            DiaryMedicationLog.user_id == user_id,
            DiaryMedicationLog.log_date >= date_from,
            DiaryMedicationLog.log_date <= date_to,
        )
        .order_by(DiaryMedicationLog.log_date.asc())
        .all()
    )

    # 텍스트 기반 PDF 내용 생성 (두 섹션 완전 분리)
    lines = [
        f"진료용 건강 기록 ({date_from} ~ {date_to})",
        "본 기록은 참고용이며 의료진의 판단을 대체하지 않습니다.",
        "",
        "=== 증상 일기 (복약 정보 미포함) ===",
    ]
    for log in symptom_logs:
        lines.append(
            f"{log.log_date} | 컨디션: {log.overall_condition or '-'} "
            f"| 감정: {log.feeling or '-'} | 메모: {log.memo or '-'}"
        )

    lines += ["", "=== 복약 기록 (증상 정보 미포함) ==="]
    for log in med_logs:
        lines.append(
            f"{log.log_date} | 약품ID: {log.medication_id} "
            f"| 시간대: {log.time_slot or '-'} | 복용: {'O' if log.taken else 'X'}"
        )

    content = "\n".join(lines).encode("utf-8")
    return StreamingResponse(
        iter([content]),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=diary_{date_from}_{date_to}.txt"},
    )


# ══════════════════════════════════════════════════════════
# 통합 캘린더
# ══════════════════════════════════════════════════════════


@router.get("/general/schedule", response_model=ScheduleResponse, summary="API-일정-001: 통합 캘린더 뷰")
def get_general_schedule(
    date_from: date = Query(...),
    date_to: date = Query(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    복약·처방 종료·진료 일정을 통합 조회합니다.
    재처방 안내·병원 추천·의료 판단 X.
    """
    if date_to < date_from:
        raise HTTPException(status_code=400, detail="종료일은 시작일 이후여야 합니다.")

    from clinical_models import CareSchedule
    from notification_models import MedicationReminder

    # 복약 알림 일정
    reminders = (
        db.query(MedicationReminder)
        .filter(
            MedicationReminder.user_id == user_id,
            MedicationReminder.is_active == True,
            MedicationReminder.deleted_at.is_(None),
            MedicationReminder.start_date <= date_to,
        )
        .all()
    )

    med_items = []
    for r in reminders:
        if r.end_date and r.end_date < date_from:
            continue
        try:
            times = json.loads(r.remind_times)
        except (json.JSONDecodeError, TypeError, ValueError):
            times = []
        med_items.append(
            {
                "id": r.id,
                "drug_name": r.drug_name,
                "start_date": str(r.start_date),
                "end_date": str(r.end_date) if r.end_date else None,
                "remind_times": times if isinstance(times, list) else [],
            }
        )

    # 처방 종료 예정일 — 복약 알림의 end_date 기준
    prescriptions_end = [
        {
            "id": r.id,
            "drug_name": r.drug_name,
            "end_date": str(r.end_date),
        }
        for r in reminders
        if r.end_date and date_from <= r.end_date <= date_to
    ]

    # 진료·검사 일정
    care_items = (
        db.query(CareSchedule)
        .filter(
            CareSchedule.user_id == user_id,
            CareSchedule.deleted_at.is_(None),
            CareSchedule.scheduled_date >= date_from,
            CareSchedule.scheduled_date <= date_to,
        )
        .order_by(CareSchedule.scheduled_date.asc())
        .all()
    )

    return ScheduleResponse(
        medications=med_items,
        prescriptions_end=prescriptions_end,
        care_schedules=[
            {
                "id": c.id,
                "schedule_type": c.schedule_type.value,
                "title": c.title,
                "scheduled_date": str(c.scheduled_date),
                "reminder_days_before": c.reminder_days_before,
            }
            for c in care_items
        ],
    )


# ══════════════════════════════════════════════════════════
# 콘텐츠 변환
# ══════════════════════════════════════════════════════════


def _run_content_generation(content_id: int) -> None:
    """백그라운드 콘텐츠 생성 (카드뉴스/TTS)."""
    from database import SessionLocal

    db = SessionLocal()
    try:
        content = db.query(ContentConversion).filter(ContentConversion.id == content_id).first()
        if not content:
            return
        content.status = ContentStatusEnum.processing
        db.commit()

        # TODO: 실제 카드뉴스/TTS 엔진 연동
        # 현재는 미연동 상태 — 완료 처리
        content.status = ContentStatusEnum.failed
        content.error_message = "콘텐츠 생성 엔진이 아직 연동되지 않았습니다."
        db.commit()
    finally:
        db.close()


def _get_source_content(source_type: str, source_id: int, user_id: int, db: Session) -> str:
    """소스 콘텐츠 조회 및 소유권 검증."""
    if source_type == "guide":
        from guide_models import Guide

        guide = (
            db.query(Guide)
            .filter(
                Guide.id == source_id,
                Guide.user_id == user_id,
                Guide.deleted_at.is_(None),
            )
            .first()
        )
        if not guide:
            raise HTTPException(status_code=404, detail="안내문을 찾을 수 없습니다.")
        return guide.medication_guide or ""
    elif source_type == "report":
        from guide_v2_models import Report, ReportStatusEnum

        report = (
            db.query(Report)
            .filter(
                Report.id == source_id,
                Report.user_id == user_id,
            )
            .first()
        )
        if not report:
            raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다.")
        if report.status != ReportStatusEnum.completed:
            raise HTTPException(status_code=400, detail="완료된 리포트만 변환할 수 있습니다.")
        return report.content or ""
    raise HTTPException(status_code=400, detail="지원하지 않는 소스 유형입니다.")


@router.post(
    "/contents/card-news",
    response_model=ContentConversionResponse,
    status_code=202,
    summary="API-콘텐츠-001: 카드뉴스 생성",
)
def create_card_news(
    data: CardNewsCreateRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    # 소스 소유권 검증
    _get_source_content(data.source_type.value, data.source_id, user_id, db)

    content = ContentConversion(
        user_id=user_id,
        content_type=ContentTypeEnum.card_news,
        source_type=data.source_type,
        source_id=data.source_id,
    )
    db.add(content)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="카드뉴스 생성 요청에 실패했습니다.")
    db.refresh(content)
    background_tasks.add_task(_run_content_generation, content.id)
    return content


@router.post(
    "/contents/tts", response_model=ContentConversionResponse, status_code=202, summary="API-콘텐츠-002: TTS 음성 변환"
)
def create_tts(
    data: TTSCreateRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    _get_source_content(data.source_type.value, data.source_id, user_id, db)

    content = ContentConversion(
        user_id=user_id,
        content_type=ContentTypeEnum.tts,
        source_type=data.source_type,
        source_id=data.source_id,
        voice_type=data.voice_type,
    )
    db.add(content)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="TTS 생성 요청에 실패했습니다.")
    db.refresh(content)
    background_tasks.add_task(_run_content_generation, content.id)
    return content


@router.get("/contents", response_model=list[ContentConversionResponse], summary="API-콘텐츠-003: 변환 내역 조회")
def list_contents(
    content_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=MAX_PAGE_SIZE),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    q = db.query(ContentConversion).filter(ContentConversion.user_id == user_id)
    if content_type:
        q = q.filter(ContentConversion.content_type == content_type)
    return q.order_by(ContentConversion.created_at.desc()).offset((page - 1) * size).limit(size).all()


# ══════════════════════════════════════════════════════════
# 게임
# ══════════════════════════════════════════════════════════


def _get_or_create_user_points(user_id: int, db: Session) -> UserPoints:
    points = db.query(UserPoints).filter(UserPoints.user_id == user_id).first()
    if not points:
        points = UserPoints(user_id=user_id, total_points=0)
        db.add(points)
        db.commit()
        db.refresh(points)
    return points


def _award_badges(user_id: int, total_points: int, db: Session) -> None:
    """포인트 임계값에 따라 뱃지 자동 지급."""
    existing_types = {b.badge_type for b in db.query(UserBadge).filter(UserBadge.user_id == user_id).all()}
    for threshold, (badge_type, badge_name) in BADGE_THRESHOLDS.items():
        if total_points >= threshold and badge_type not in existing_types:
            db.add(
                UserBadge(
                    user_id=user_id,
                    badge_type=badge_type,
                    badge_name=badge_name,
                )
            )


@router.post("/games/scores", response_model=GameScoreResponse, status_code=201, summary="API-게임-001: 게임 점수 기록")
def record_game_score(
    data: GameScoreCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    points = POINTS_PER_SCORE.get(data.game_type.value, 5)

    game_score = GameScore(
        user_id=user_id,
        game_type=data.game_type,
        score=data.score,
        points_earned=points,
    )
    db.add(game_score)

    # 포인트 누적
    user_points = _get_or_create_user_points(user_id, db)
    user_points.total_points += points

    # 뱃지 지급
    _award_badges(user_id, user_points.total_points, db)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="점수 저장에 실패했습니다.")
    db.refresh(game_score)
    return game_score


@router.get("/games/badges", response_model=UserBadgesResponse, summary="API-게임-002: 뱃지·포인트 조회")
def get_badges(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user_points = _get_or_create_user_points(user_id, db)
    badges = db.query(UserBadge).filter(UserBadge.user_id == user_id).order_by(UserBadge.earned_at.asc()).all()
    return UserBadgesResponse(
        total_points=user_points.total_points,
        badges=[BadgeInfo.model_validate(b) for b in badges],
    )


# ══════════════════════════════════════════════════════════
# 관리자 안전 필터 로그
# ══════════════════════════════════════════════════════════


@router.get(
    "/admin/safety-filter-logs",
    response_model=list[SafetyFilterLogResponse],
    summary="API-관리자-001: 안전 필터 차단 이력 조회",
)
def list_safety_filter_logs(
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    blocked_reason: str | None = Query(None, max_length=200),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """관리자 전용. ADMIN_USER_IDS 환경변수에 등록된 user_id만 접근 가능."""
    _require_admin(user_id)

    q = db.query(SafetyFilterLog)
    if date_from:
        q = q.filter(SafetyFilterLog.created_at >= date_from)
    if date_to:
        q = q.filter(SafetyFilterLog.created_at <= date_to)
    if blocked_reason:
        q = q.filter(SafetyFilterLog.blocked_reason.ilike(f"%{blocked_reason}%"))

    return q.order_by(SafetyFilterLog.created_at.desc()).offset((page - 1) * size).limit(size).all()
