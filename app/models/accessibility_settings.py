import uuid
from enum import StrEnum

from tortoise import fields, models


class FontSize(StrEnum):
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"
    XLARGE = "XLARGE"


class AccessibilitySetting(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    user = fields.OneToOneField("models.User", related_name="accessibility_setting", on_delete=fields.CASCADE)
    font_size = fields.CharEnumField(enum_type=FontSize, max_length=20, default=FontSize.MEDIUM)
    tts_enabled = fields.BooleanField(default=False)
    easy_language = fields.BooleanField(default=False)
    guardian_share_enabled = fields.BooleanField(default=False)
    # NOTI-008: 위치 태깅 동의 (별도 동의, 기본 비활성)
    location_tracking_enabled = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "accessibility_settings"
