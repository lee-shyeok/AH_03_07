import os

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse, Response
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

import app.services.chat_guardrail_enhanced  # noqa: F401 — REQ-CHAT-004 pre_save signal 등록
import app.services.content_advertisement_filter  # noqa: F401 — NFR-COMPLI-003 pre_save signal 등록
import app.services.knowledge_source_validator  # noqa: F401 — NFR-SAFE-002 pre_save signal 등록
from app.apis.v1 import v1_routers
from app.apis.v1.health_guide_routers import health_guide_router
from app.core.db.databases import initialize_tortoise
from app.core.latency.middleware import LatencyMiddleware
from app.core.rate_limit.middleware import RateLimitMiddleware

app = FastAPI(
    default_response_class=ORJSONResponse, docs_url="/api/docs", redoc_url="/api/redoc", openapi_url="/api/openapi.json"
)
initialize_tortoise(app)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(LatencyMiddleware)  # NFR-PERF-001: latency 측정

# static 파일 서빙 추가
_STATIC_ROOT = os.environ.get("STATIC_ROOT", "static")
os.makedirs(f"{_STATIC_ROOT}/cards", exist_ok=True)
os.makedirs(f"{_STATIC_ROOT}/audio", exist_ok=True)
app.mount("/static", StaticFiles(directory=_STATIC_ROOT), name="static")


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(health_guide_router, prefix="/api/v1")  # NFR-PERF-003: GET /{id} 캐시 포함
app.include_router(v1_routers)
