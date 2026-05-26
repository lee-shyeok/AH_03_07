from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
import logging

load_dotenv('envs/.local.env')
logging.basicConfig(level=logging.DEBUG)

from routers import auth, social_auth, users, medical_documents, medical_records, guides, chats, notifications, dashboard, consent_mode_disease, clinical, extra, guide_v2, postmvp
from database import engine
from extra_models import Base as ExtraBase
from models import Base as UserBase
from ocr_models import Base as OcrBase
from medical_record_models import Base as MedicalRecordBase
from guide_models import Base as GuideBase
from chat_models import Base as ChatBase
from notification_models import Base as NotificationBase
from consent_mode_disease_models import Base as ConsentModeBase
from clinical_models import Base as ClinicalBase
from guide_v2_models import Base as GuideV2Base
from postmvp_models import Base as PostMvpBase
from routers.ocr import router as ocr_router

PostMvpBase.metadata.create_all(bind=engine)
GuideV2Base.metadata.create_all(bind=engine)
ConsentModeBase.metadata.create_all(bind=engine)
ClinicalBase.metadata.create_all(bind=engine)
UserBase.metadata.create_all(bind=engine)
OcrBase.metadata.create_all(bind=engine)
MedicalRecordBase.metadata.create_all(bind=engine)
GuideBase.metadata.create_all(bind=engine)
ChatBase.metadata.create_all(bind=engine)
NotificationBase.metadata.create_all(bind=engine)
ExtraBase.metadata.create_all(bind=engine)

app = FastAPI(root_path="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        err = {}
        for k, v in error.items():
            if k == 'ctx':
                err[k] = {ck: str(cv) for ck, cv in v.items()}
            elif isinstance(v, (str, int, float, bool)):
                err[k] = v
            elif isinstance(v, list):
                err[k] = [str(i) for i in v]
            else:
                err[k] = str(v)
        errors.append(err)
    return JSONResponse(status_code=422, content={"detail": errors})


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    import traceback
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": "데이터베이스 오류가 발생했습니다."})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, StarletteHTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    import traceback
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": "서버 오류가 발생했습니다."})


app.include_router(auth.router, prefix="/v1/auth", tags=["auth"])
app.include_router(social_auth.router, prefix="/v1/auth", tags=["social-auth"])
app.include_router(users.router, prefix="/v1/users", tags=["users"])
app.include_router(medical_documents.router, prefix="/v1", tags=["medical-documents"])
app.include_router(medical_records.router, prefix="/v1", tags=["medical-records"])
app.include_router(guides.router, prefix="/v1", tags=["guides"])
app.include_router(chats.router, prefix="/v1", tags=["chat"])
app.include_router(notifications.router, prefix="/v1", tags=["notifications"])
app.include_router(dashboard.router, prefix="/v1", tags=["dashboard"])
app.include_router(consent_mode_disease.router, prefix="/v1", tags=["consent-mode-disease"])
app.include_router(clinical.router, prefix="/v1", tags=["clinical"])
app.include_router(extra.router, prefix="/v1", tags=["extra"])
app.include_router(guide_v2.router, prefix="/v1", tags=["guide-v2"])
app.include_router(postmvp.router, prefix="/v1", tags=["post-mvp"])
app.include_router(ocr_router, prefix="/v1")