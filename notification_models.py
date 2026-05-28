import enum

from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from database import Base


class NotificationTypeEnum(str, enum.Enum):
    medication = "medication"  # 복약 알림
    guide = "guide"  # 가이드 확인 알림
    marketing = "marketing"  # 마케팅 알림


class NotificationChannelEnum(str, enum.Enum):
    app = "app"  # 앱 내 알림
    email = "email"  # 이메일
    kakao = "kakao"  # 카카오 알림톡


class MedicationReminder(Base):
    """복약 알림 설정 (REQ-NOTI-001)"""

    __tablename__ = "medication_reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=True)  # 연결된 약품 (선택)

    # 약품명 (medication_id가 없어도 직접 입력 가능)
    drug_name = Column(String(200), nullable=False)

    # 알림 시각 목록 (JSON 배열: ["08:00", "12:00", "18:00"])
    remind_times = Column(Text, nullable=False)

    # 복용 기간
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    # 요일 선택 (JSON 배열: ["mon", "tue", "wed", "thu", "fri", "sat", "sun"])
    weekdays = Column(Text, nullable=False)

    # 알림 채널 (JSON 배열: ["app", "email", "kakao"])
    channels = Column(Text, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)

    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class Notification(Base):
    """발송된 알림 (REQ-NOTI-004)"""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    notification_type = Column(Enum(NotificationTypeEnum), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)

    # 백링크 (클릭 시 이동할 경로)
    backlink = Column(String(500), nullable=True)

    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class NotificationSetting(Base):
    """알림 ON/OFF 설정 (REQ-NOTI-006) — 유저당 1개"""

    __tablename__ = "notification_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    # 유형별 ON/OFF
    medication_enabled = Column(Boolean, default=True, nullable=False)
    guide_enabled = Column(Boolean, default=True, nullable=False)
    marketing_enabled = Column(Boolean, default=False, nullable=False)

    # 채널별 ON/OFF
    app_enabled = Column(Boolean, default=True, nullable=False)
    email_enabled = Column(Boolean, default=True, nullable=False)
    kakao_enabled = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
