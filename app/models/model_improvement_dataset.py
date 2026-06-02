import uuid

from tortoise import fields, models


class ModelImprovementDataset(models.Model):
    """REQ-FEED-002 — 주 1회 집계 결과 (가명처리 후 모델 개선 데이터셋).

    개인정보보호법 §28-2 가명처리 절차 적용.
    MODEL_IMPROVEMENT 동의자 데이터만 포함.
    """

    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    # 집계 기간 식별자 (예: "2026-W22")
    dataset_version = fields.CharField(max_length=20, unique=True)
    week_start = fields.DatetimeField()
    week_end = fields.DatetimeField()

    # 집계 항목별 건수
    low_rated_guide_count = fields.IntField(default=0)
    high_ocr_correction_count = fields.IntField(default=0)
    thumbs_down_chat_count = fields.IntField(default=0)
    total_records = fields.IntField(default=0)

    # 동의 및 가명처리 메타
    consent_only = fields.BooleanField(default=True)
    pseudonymized_at = fields.DatetimeField()
    # 가명처리 수준 기술 (예: "user_id=sha256, drug_name=masked")
    pseudonymization_level = fields.CharField(max_length=200)

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "model_improvement_datasets"
