import uuid
from enum import StrEnum
from tortoise import fields, models

class Gender(StrEnum):
    MALE = "MALE"
    FEMALE = "FEMALE"

class UserMode(StrEnum):
    GENERAL = "GENERAL"  # 일반 모드
    AUTOIMMUNE = "AUTOIMMUNE"  # 자가면역 모드

class User(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    email = fields.CharField(max_length=40)
    hashed_password = fields.CharField(max_length=128)
    name = fields.CharField(max_length=20)
    gender = fields.CharEnumField(enum_type=Gender)
    birthday = fields.DateField()
    phone_number = fields.CharField(max_length=11)
    mode = fields.CharEnumField(enum_type=UserMode, max_length=20, default=UserMode.GENERAL)
    is_active = fields.BooleanField(default=True)
    is_admin = fields.BooleanField(default=False)
    last_login = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "users"
