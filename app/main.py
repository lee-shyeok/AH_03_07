from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

import app.services.content_advertisement_filter  # noqa: F401 — NFR-COMPLI-003 pre_save signal 등록
import app.services.knowledge_source_validator  # noqa: F401 — NFR-SAFE-002 pre_save signal 등록
from app.apis.v1 import v1_routers
from app.apis.v1.health_guide_routers import health_guide_router
from app.core.db.databases import initialize_tortoise
from app.core.rate_limit.middleware import RateLimitMiddleware

app = FastAPI(
    default_response_class=ORJSONResponse, docs_url="/api/docs", redoc_url="/api/redoc", openapi_url="/api/openapi.json"
)
initialize_tortoise(app)
app.add_middleware(RateLimitMiddleware)

app.include_router(health_guide_router, prefix="/api/v1")  # NFR-PERF-003: GET /{id} 캐시 포함
app.include_router(v1_routers)
