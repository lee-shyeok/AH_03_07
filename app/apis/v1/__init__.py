from fastapi import APIRouter

from app.apis.v1.activity_alert_routers import activity_alert_router
from app.apis.v1.activity_log_routers import activity_log_router
from app.apis.v1.admin_routers import admin_router
from app.apis.v1.auth_routers import auth_router
from app.apis.v1.auto_guide_router import auto_guide_router, guide_generation_job_router
from app.apis.v1.autoimmune_care_routers import (
    medication_card_router,
    pregnancy_safety_router,
    vaccine_prevention_router,
)
from app.apis.v1.autoimmune_profile_routers import autoimmune_profile_router
from app.apis.v1.care_routers import care_router
from app.apis.v1.chat_routers import chat_router
from app.apis.v1.chat_stream_routers import chat_stream_router
from app.apis.v1.content_conversion_routers import content_router
from app.apis.v1.dashboard_routers import dashboard_router
from app.apis.v1.diary_log_routers import diary_log_router
from app.apis.v1.diet_info_routers import diet_info_router
from app.apis.v1.disease_routers import disease_router
from app.apis.v1.emergency_card_routers import emergency_card_router
from app.apis.v1.health_guide_routers import health_guide_router
from app.apis.v1.health_metric_routers import health_metric_router
from app.apis.v1.knowledge_routers import knowledge_router
from app.apis.v1.lab_result_routers import lab_result_router
from app.apis.v1.lupus_exposure_routers import lupus_exposure_router
from app.apis.v1.lupus_skin_routers import lupus_skin_router
from app.apis.v1.medical_schedule_routers import medical_schedule_router
from app.apis.v1.medication_routers import medication_router
from app.apis.v1.mode_routers import mode_router
from app.apis.v1.notification_routers import notification_router
from app.apis.v1.pharmacy_routers import pharmacy_router
from app.apis.v1.pill_recognition_routers import pill_router
from app.apis.v1.pre_consultation_report_routers import pre_consultation_report_router
from app.apis.v1.ra_exposure_routers import ra_exposure_router
from app.apis.v1.risk_flag_routers import risk_flag_router
from app.apis.v1.risk_profile_routers import risk_profile_router
from app.apis.v1.symptom_check_routers import symptom_check_router
from app.apis.v1.user_consent_routers import user_consent_router
from app.apis.v1.user_medication_routers import user_medication_router
from app.apis.v1.user_routers import user_router

v1_routers = APIRouter(prefix="/api/v1")
v1_routers.include_router(admin_router)
v1_routers.include_router(auth_router)
v1_routers.include_router(user_consent_router)
v1_routers.include_router(user_router)
v1_routers.include_router(mode_router)
v1_routers.include_router(risk_flag_router)
v1_routers.include_router(risk_profile_router)
v1_routers.include_router(autoimmune_profile_router)
v1_routers.include_router(dashboard_router)
v1_routers.include_router(knowledge_router)
v1_routers.include_router(chat_router)
v1_routers.include_router(content_router)
v1_routers.include_router(chat_stream_router)
v1_routers.include_router(auto_guide_router)
v1_routers.include_router(guide_generation_job_router)
v1_routers.include_router(care_router)
v1_routers.include_router(diary_log_router)
v1_routers.include_router(diet_info_router)
v1_routers.include_router(disease_router)
v1_routers.include_router(emergency_card_router)
v1_routers.include_router(health_metric_router)
v1_routers.include_router(medication_router)
v1_routers.include_router(user_medication_router)
v1_routers.include_router(activity_log_router)
v1_routers.include_router(activity_alert_router)
v1_routers.include_router(symptom_check_router)
v1_routers.include_router(medical_schedule_router)
v1_routers.include_router(notification_router)
v1_routers.include_router(pharmacy_router)
v1_routers.include_router(lab_result_router)
v1_routers.include_router(medication_card_router)
v1_routers.include_router(pregnancy_safety_router)
v1_routers.include_router(vaccine_prevention_router)
v1_routers.include_router(lupus_exposure_router)
v1_routers.include_router(lupus_skin_router)
v1_routers.include_router(pre_consultation_report_router)
v1_routers.include_router(ra_exposure_router)
v1_routers.include_router(pill_router)
v1_routers.include_router(health_guide_router)
