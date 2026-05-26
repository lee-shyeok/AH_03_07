from fastapi import APIRouter

from app.apis.v1.accessibility_routers import accessibility_router
from app.apis.v1.auth_routers import auth_router
from app.apis.v1.care_routers import care_router
from app.apis.v1.content_conversion_routers import content_router
from app.apis.v1.diary_log_routers import diary_log_router
from app.apis.v1.emergency_card_routers import emergency_card_router
from app.apis.v1.feedback_routers import feedback_router
from app.apis.v1.health_guide_routers import health_guide_router
from app.apis.v1.health_metric_routers import health_metric_router
from app.apis.v1.medication_routers import medication_router
from app.apis.v1.notification_routers import notification_router
from app.apis.v1.pharmacy_routers import pharmacy_router
from app.apis.v1.prescription_routers import prescription_router
from app.apis.v1.prompt_routers import prompt_router
from app.apis.v1.schedule_routers import schedule_router
from app.apis.v1.user_consent_routers import user_consent_router
from app.apis.v1.user_routers import user_router
from app.apis.v1.pill_recognition_routers import pill_router



v1_routers = APIRouter(prefix="/api/v1")

v1_routers.include_router(accessibility_router)
v1_routers.include_router(auth_router)
v1_routers.include_router(care_router)
v1_routers.include_router(content_router)
v1_routers.include_router(diary_log_router)
v1_routers.include_router(emergency_card_router)
v1_routers.include_router(feedback_router)
v1_routers.include_router(health_guide_router)
v1_routers.include_router(health_metric_router)
v1_routers.include_router(medication_router)
v1_routers.include_router(notification_router)
v1_routers.include_router(pharmacy_router)
v1_routers.include_router(prescription_router)
v1_routers.include_router(prompt_router)
v1_routers.include_router(schedule_router)
v1_routers.include_router(user_consent_router)
v1_routers.include_router(user_router)
v1_routers.include_router(pill_router)

