from enum import StrEnum

from tortoise import fields, models


class Gender(StrEnum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class UserMode(StrEnum):
    GENERAL = "GENERAL"
    AUTOIMMUNE = "AUTOIMMUNE"


class User(models.Model):
    id = fields.BigIntField(primary_key=True)
    email = fields.CharField(max_length=40)
    hashed_password = fields.CharField(max_length=128)
    name = fields.CharField(max_length=20)
    gender = fields.CharEnumField(enum_type=Gender)
    birthday = fields.DateField()
    phone_number = fields.CharField(max_length=11)
    mode = fields.CharEnumField(enum_type=UserMode, default=UserMode.GENERAL, max_length=16)
    is_active = fields.BooleanField(default=True)
    is_admin = fields.BooleanField(default=False)
    last_login = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "users"
