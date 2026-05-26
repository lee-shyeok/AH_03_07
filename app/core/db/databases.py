from fastapi import FastAPI
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

from app.core import config

TORTOISE_APP_MODELS = [
    "aerich.models",
    "app.models.users",
    "app.models.user_consents",
    "app.models.diary_symptom_logs",
    "app.models.diary_medication_logs",
    "app.models.emergency_cards",
    "app.models.health_metrics",
    "app.models.notification_settings",
    "app.models.notifications",
    "app.models.medical_documents",
    "app.models.prescriptions",
    "app.models.medications",
    "app.models.prompts",
    "app.models.health_guides",
    "app.models.feedback_logs",
    "app.models.accessibility_settings",
    "app.models.pharmacies",
    "app.models.medical_appointments",
    "app.models.favorite_places",
    "app.models.guardians",
    "app.models.share_links",
    "app.models.share_logs",
    "app.models.content_conversions",
    "app.models.pill_recognitions",
    "app.models.audit_logs",
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
