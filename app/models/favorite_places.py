import uuid
from enum import StrEnum

from tortoise import fields, models


class PlaceType(StrEnum):
    HOSPITAL = "HOSPITAL"
    PHARMACY = "PHARMACY"


class FavoritePlace(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    user = fields.ForeignKeyField("models.User", related_name="favorite_places", on_delete=fields.CASCADE)
    place_type = fields.CharEnumField(enum_type=PlaceType, max_length=20)
    name = fields.CharField(max_length=200)
    address = fields.CharField(max_length=500, null=True)
    phone = fields.CharField(max_length=20, null=True)
    memo = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "favorite_places"
