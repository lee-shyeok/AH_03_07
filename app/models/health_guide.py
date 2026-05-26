from tortoise import fields
from tortoise.models import Model


class HealthGuide(Model):
    id = fields.IntField(pk=True)
    user_id = fields.IntField()
    status = fields.CharField(max_length=30)
    medication_general = fields.TextField(default="")
    side_effect_monitoring = fields.JSONField(default=list)
    lifestyle_info = fields.TextField(default="")
    symptom_summary = fields.TextField(default="")
    sources = fields.JSONField(default=list)
    disclaimer = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "health_guides"
