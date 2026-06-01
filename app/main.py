from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

import app.services.knowledge_source_validator  # noqa: F401 — NFR-SAFE-002 pre_save signal 등록
from app.apis.v1 import v1_routers
from app.core.db.databases import initialize_tortoise

app = FastAPI(
    default_response_class=ORJSONResponse, docs_url="/api/docs", redoc_url="/api/redoc", openapi_url="/api/openapi.json"
)
initialize_tortoise(app)

app.include_router(v1_routers)
