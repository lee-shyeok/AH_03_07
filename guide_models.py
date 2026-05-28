import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from database import Base


class GuideStatusEnum(str, enum.Enum):
    active = "active"  # 최신 가이드
    needs_update = "needs_update"  # 갱신 필요
    archived = "archived"  # 보관됨 (재생성으로 대체된 이전 가이드)


class Guide(Base):
    """가이드"""

    __tablename__ = "guides"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    record_id = Column(Integer, ForeignKey("medical_records.id"), nullable=False, index=True)

    status = Column(Enum(GuideStatusEnum), default=GuideStatusEnum.active, nullable=False)

    # GPT 생성 결과 (JSON 문자열)
    medication_guide = Column(Text, nullable=True)  # 복약 가이드
    lifestyle_guide = Column(Text, nullable=True)  # 생활습관 가이드
    precautions = Column(Text, nullable=True)  # 주의사항 (약물 상호작용 등)
    recommended_checkups = Column(Text, nullable=True)  # 권장 추가 검진

    # 면책 문구 (항상 노출 필수)
    disclaimer = Column(
        Text,
        nullable=False,
        default=(
            "본 가이드는 의료 전문가의 진단을 대체하지 않습니다. "
            "증상이 지속되거나 악화되면 반드시 의사 또는 약사와 상담하세요."
        ),
    )

    # 재생성 관련
    regeneration_reason = Column(String(100), nullable=True)  # 재생성 사유
    version = Column(Integer, default=1, nullable=False)  # 버전 (재생성 시 증가)

    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class GuideFeedback(Base):
    """가이드 평가 피드백"""

    __tablename__ = "guide_feedbacks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    guide_id = Column(Integer, ForeignKey("guides.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    accuracy = Column(Integer, nullable=False)  # 정확성 1~5
    clarity = Column(Integer, nullable=False)  # 이해도 1~5
    usefulness = Column(Integer, nullable=False)  # 유용성 1~5
    comment = Column(String(500), nullable=True)  # 자유 코멘트

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
