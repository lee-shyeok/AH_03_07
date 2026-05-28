"""
알림 라우터  REQ-NOTI-001, REQ-NOTI-004 ~ REQ-NOTI-006
"""
import json
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from notification_models import (
    MedicationReminder,
    Notification,
    NotificationSetting,
)
from notification_schemas import (
    MedicationReminderCreate,
    MedicationReminderListResponse,
    MedicationReminderResponse,
    MedicationReminderUpdate,
    NotificationListResponse,
    NotificationResponse,
    NotificationSettingResponse,
    NotificationSettingUpdate,
)
from security import get_current_user_id

router = APIRouter()

MAX_PAGE_SIZE = 50
MAX_REMINDERS_PER_USER = 50


def _get_reminder_or_404(reminder_id: int, user_id: int, db: Session) -> MedicationReminder:
    reminder = db.query(MedicationReminder).filter(
        MedicationReminder.id == reminder_id,
        MedicationReminder.user_id == user_id,
        MedicationReminder.deleted_at.is_(None),
    ).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="복약 알림을 찾을 수 없습니다.")
    return reminder


def _get_or_create_setting(user_id: int, db: Session) -> NotificationSetting:
    setting = db.query(NotificationSetting).filter(
        NotificationSetting.user_id == user_id
    ).first()
    if not setting:
        setting = NotificationSetting(user_id=user_id)
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting


@router.post(
    "/reminders",
    response_model=MedicationReminderResponse,
    status_code=201,
    summary="REQ-NOTI-001: 복약 알림 생성",
)
def create_reminder(
    data: MedicationReminderCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    count = db.query(MedicationReminder).filter(
        MedicationReminder.user_id == user_id,
        MedicationReminder.deleted_at.is_(None),
    ).count()
    if count >= MAX_REMINDERS_PER_USER:
        raise HTTPException(
            status_code=400,
            detail=f"복약 알림은 최대 {MAX_REMINDERS_PER_USER}개까지 설정할 수 있습니다."
        )

    if data.medication_id is not None:
        from medical_record_models import MedicalRecord, Medication
        med = (
            db.query(Medication)
            .join(MedicalRecord, Medication.record_id == MedicalRecord.id)
            .filter(
                Medication.id == data.medication_id,
                MedicalRecord.user_id == user_id,
                MedicalRecord.deleted_at.is_(None),
            )
            .first()
        )
        if not med:
            raise HTTPException(status_code=404, detail="연결할 약품을 찾을 수 없습니다.")

    reminder = MedicationReminder(
        user_id=user_id,
        medication_id=data.medication_id,
        drug_name=data.drug_name,
        remind_times=json.dumps(data.remind_times, ensure_ascii=False),
        start_date=data.start_date,
        end_date=data.end_date,
        weekdays=json.dumps(data.weekdays, ensure_ascii=False),
        channels=json.dumps(data.channels, ensure_ascii=False),
    )
    db.add(reminder)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="복약 알림 저장에 실패했습니다.")
    db.refresh(reminder)
    return MedicationReminderResponse.from_orm(reminder)


@router.get(
    "/reminders",
    response_model=MedicationReminderListResponse,
    summary="REQ-NOTI-001: 복약 알림 목록 조회",
)
def list_reminders(
    is_active: bool | None = Query(None),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    query = db.query(MedicationReminder).filter(
        MedicationReminder.user_id == user_id,
        MedicationReminder.deleted_at.is_(None),
    )
    if is_active is not None:
        query = query.filter(MedicationReminder.is_active == is_active)

    total = query.count()
    reminders = query.order_by(MedicationReminder.created_at.desc()).all()

    return MedicationReminderListResponse(
        items=[MedicationReminderResponse.from_orm(r) for r in reminders],
        total=total,
    )


@router.patch(
    "/reminders/{reminder_id}",
    response_model=MedicationReminderResponse,
    summary="REQ-NOTI-001: 복약 알림 수정",
)
def update_reminder(
    reminder_id: int,
    data: MedicationReminderUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    reminder = _get_reminder_or_404(reminder_id, user_id, db)

    if data.drug_name is not None:
        reminder.drug_name = data.drug_name
    if data.remind_times is not None:
        reminder.remind_times = json.dumps(data.remind_times, ensure_ascii=False)
    if data.start_date is not None:
        reminder.start_date = data.start_date
    if data.end_date is not None:
        reminder.end_date = data.end_date
    if data.weekdays is not None:
        reminder.weekdays = json.dumps(data.weekdays, ensure_ascii=False)
    if data.channels is not None:
        reminder.channels = json.dumps(data.channels, ensure_ascii=False)
    if data.is_active is not None:
        reminder.is_active = data.is_active

    if reminder.end_date and reminder.end_date < reminder.start_date:
        raise HTTPException(status_code=400, detail="종료일은 시작일 이후여야 합니다.")

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="복약 알림 수정에 실패했습니다.")
    db.refresh(reminder)
    return MedicationReminderResponse.from_orm(reminder)


@router.delete(
    "/reminders/{reminder_id}",
    status_code=204,
    summary="REQ-NOTI-001: 복약 알림 삭제",
)
def delete_reminder(
    reminder_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    reminder = _get_reminder_or_404(reminder_id, user_id, db)
    reminder.deleted_at = datetime.now(UTC)
    reminder.is_active = False
    db.commit()


@router.get(
    "/notifications",
    response_model=NotificationListResponse,
    summary="REQ-NOTI-004: 알림 목록 조회",
)
def list_notifications(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=MAX_PAGE_SIZE),
    tab: str | None = Query("all", pattern="^(all|unread|read)$"),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    query = db.query(Notification).filter(
        Notification.user_id == user_id,
    )
    if tab == "unread":
        query = query.filter(Notification.is_read == False)
    elif tab == "read":
        query = query.filter(Notification.is_read == True)

    total = query.count()

    unread_count = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False,
    ).count()

    notifications = (
        query.order_by(Notification.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        page=page,
        size=size,
        unread_count=unread_count,
    )


@router.patch(
    "/notifications/read-all",
    summary="REQ-NOTI-005: 전체 읽음 처리",
)
def read_all_notifications(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    now = datetime.now(UTC)
    db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False,
    ).update({"is_read": True, "read_at": now}, synchronize_session=False)
    db.commit()
    return {"message": "모든 알림을 읽음 처리했습니다."}


@router.patch(
    "/notifications/{notification_id}/read",
    response_model=NotificationResponse,
    summary="REQ-NOTI-005: 개별 읽음 처리",
)
def read_notification(
    notification_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id,
    ).first()
    if not notification:
        raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다.")

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(UTC)
        db.commit()
        db.refresh(notification)

    return notification


@router.get(
    "/notification-settings",
    response_model=NotificationSettingResponse,
    summary="REQ-NOTI-006: 알림 설정 조회",
)
def get_notification_setting(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return _get_or_create_setting(user_id, db)


@router.patch(
    "/notification-settings",
    response_model=NotificationSettingResponse,
    summary="REQ-NOTI-006: 알림 설정 수정",
)
def update_notification_setting(
    data: NotificationSettingUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    setting = _get_or_create_setting(user_id, db)

    if data.medication_enabled is not None:
        setting.medication_enabled = data.medication_enabled
    if data.guide_enabled is not None:
        setting.guide_enabled = data.guide_enabled
    if data.marketing_enabled is not None:
        setting.marketing_enabled = data.marketing_enabled
    if data.app_enabled is not None:
        setting.app_enabled = data.app_enabled
    if data.email_enabled is not None:
        setting.email_enabled = data.email_enabled
    if data.kakao_enabled is not None:
        setting.kakao_enabled = data.kakao_enabled

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="알림 설정 저장에 실패했습니다.")
    db.refresh(setting)
    return setting
