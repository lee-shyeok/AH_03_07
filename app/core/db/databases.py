from fastapi import FastAPI
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

from app.core import config

TORTOISE_APP_MODELS = [
    "aerich.models",
    "app.models.users",
    "app.models.knowledge",
    "app.models.health_guide",
    "app.models.user_disease",
    "app.models.audit_log",
    "app.models.user_risk_profile",
    "app.models.user_medication",
    "app.models.disease_activity_log",
    "app.models.symptom_check_log",
    "app.models.activity_alert_setting",
    "app.models.medical_schedule",
    "app.models.lab_result",
    "app.models.lupus_skin_log",
    "app.models.chat_session",
    "app.models.chat_message",
    "app.models.chat_feedback",
    "app.models.user_consents",
    "app.models.accessibility_settings",
    "app.models.diary_medication_logs",
    "app.models.diary_symptom_logs",
    "app.models.emergency_cards",
    "app.models.health_metrics",
    "app.models.feedback_logs",
    "app.models.notifications",
    "app.models.notification_settings",
    "app.models.pharmacies",
    "app.models.favorite_places",
    "app.models.medical_appointments",
    "app.models.guardians",
    "app.models.share_links",
    "app.models.share_logs",
    "app.models.prompts",
    "app.models.health_guides",
    "app.models.prescriptions",
    "app.models.medications",
    "app.models.risk_flag",
    "app.models.autoimmune_profile",
    "app.models.auto_guide",
    "app.models.guide_generation_job",
    "app.models.pre_consultation_report",
    "app.models.report_share",
    "app.models.safety_filter_log",
]

TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.mysql",
            "dialect": "asyncmy",
            "credentials": {
                "host": config.DB_HOST,
                "port": config.DB_PORT,
                "user": config.DB_USER,
                "password": config.DB_PASSWORD,
                "database": config.DB_NAME,
                "connect_timeout": config.DB_CONNECT_TIMEOUT,
                "maxsize": config.DB_CONNECTION_POOL_MAXSIZE,
            },
        },
    },
    "apps": {
        "models": {
            "models": TORTOISE_APP_MODELS,
        },
    },
    "timezone": "Asia/Seoul",
}


def initialize_tortoise(app: FastAPI) -> None:
    Tortoise.init_models(TORTOISE_APP_MODELS, "models")
    register_tortoise(app, config=TORTOISE_ORM)
