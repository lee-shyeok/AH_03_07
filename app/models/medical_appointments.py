import uuid

from tortoise import fields, models


class MedicalAppointment(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    user = fields.ForeignKeyField("models.User", related_name="appointments", on_delete=fields.CASCADE)
    appointment_date = fields.DatetimeField()
    hospital_name = fields.CharField(max_length=200)
    doctor_name = fields.CharField(max_length=100, null=True)
    purpose = fields.CharField(max_length=200, null=True)
    notes = fields.TextField(null=True)
    notification_enabled = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "medical_appointments"
