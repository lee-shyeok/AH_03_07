from __future__ import annotations

from enum import StrEnum

from tortoise import fields, models

from app.models.user_disease import DiseaseCode


class DietCategory(StrEnum):
    RECOMMEND = "RECOMMEND"
    AVOID = "AVOID"


class FoodCategory(StrEnum):
    MEAT = "MEAT"
    FISH = "FISH"
    VEGETABLE = "VEGETABLE"
    FRUIT = "FRUIT"
    GRAIN = "GRAIN"
    DAIRY = "DAIRY"
    OTHER = "OTHER"


class DietInfo(models.Model):
    id = fields.BigIntField(primary_key=True)
    disease_code = fields.CharEnumField(enum_type=DiseaseCode, max_length=20)
    category = fields.CharEnumField(enum_type=DietCategory, max_length=10)
    food_category = fields.CharField(max_length=30, null=True)
    food_name = fields.CharField(max_length=100)
    reason = fields.TextField()
    terms = fields.JSONField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "diet_infos"
