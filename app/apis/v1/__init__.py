from fastapi import APIRouter

from app.apis.v1.activity_alert_routers import activity_alert_router
from app.apis.v1.activity_log_routers import activity_log_router
from app.apis.v1.auth_routers import auth_router
from app.apis.v1.auto_guide_router import auto_guide_router
from app.apis.v1.chat_routers import chat_router
from app.apis.v1.disease_routers import disease_router
from app.apis.v1.knowledge_routers import knowledge_router
from app.apis.v1.lab_result_routers import lab_result_router
from app.apis.v1.medical_schedule_routers import medical_schedule_router
from app.apis.v1.medication_routers import medication_router
from app.apis.v1.mode_routers import mode_router
from app.apis.v1.risk_profile_routers import risk_profile_router
from app.apis.v1.symptom_check_routers import symptom_check_router
from app.apis.v1.user_routers import user_router

v1_routers = APIRouter(prefix="/api/v1")
v1_routers.include_router(auth_router)
v1_routers.include_router(user_router)
v1_routers.include_router(mode_router)
v1_routers.include_router(risk_profile_router)
v1_routers.include_router(knowledge_router)
v1_routers.include_router(chat_router)
v1_routers.include_router(auto_guide_router)
v1_routers.include_router(disease_router)
v1_routers.include_router(medication_router)
v1_routers.include_router(activity_log_router)
v1_routers.include_router(activity_alert_router)
v1_routers.include_router(symptom_check_router)
v1_routers.include_router(medical_schedule_router)
v1_routers.include_router(lab_result_router)
