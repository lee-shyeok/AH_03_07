from datetime import date, datetime

from pydantic import BaseModel, field_validator

from consent_mode_disease_models import ConsentTypeEnum, UserModeEnum

# ── 동의 이력 ─────────────────────────────────────────────

class ConsentUpsertRequest(BaseModel):
    consent_type: ConsentTypeEnum
    agreed: bool
    version: str = "1.0"

    @field_validator("version")
    @classmethod
    def version_valid(cls, v):
        if not v.strip():
            raise ValueError("버전을 입력해주세요.")
        if len(v) > 20:
            raise ValueError("버전은 20자 이하여야 합니다.")
        return v.strip()


class ConsentResponse(BaseModel):
    id: int
    consent_type: ConsentTypeEnum
    agreed: bool
    version: str
    agreed_at: datetime | None = None
    revoked_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── 모드 관리 ─────────────────────────────────────────────

class UserModeUpdate(BaseModel):
    mode: UserModeEnum


class UserModeResponse(BaseModel):
    mode: UserModeEnum
    selected_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── 질환 관리 ─────────────────────────────────────────────

class UserDiseaseCreate(BaseModel):
    disease_name: str
    disease_code: str | None = None
    diagnosis_date: date | None = None
    memo: str | None = None

    @field_validator("disease_name")
    @classmethod
    def disease_name_valid(cls, v):
        stripped = v.strip()
        if not stripped:
            raise ValueError("질환명을 입력해주세요.")
        if len(stripped) > 200:
            raise ValueError("질환명은 200자 이하여야 합니다.")
        return stripped

    @field_validator("disease_code")
    @classmethod
    def disease_code_valid(cls, v):
        if v is not None:
            stripped = v.strip()
            if len(stripped) > 50:
                raise ValueError("질환 코드는 50자 이하여야 합니다.")
            return stripped if stripped else None
        return v

    @field_validator("diagnosis_date")
    @classmethod
    def diagnosis_date_not_future(cls, v):
        if v is not None and v > date.today():
            raise ValueError("진단일은 오늘 이후 날짜를 입력할 수 없습니다.")
        return v

    @field_validator("memo")
    @classmethod
    def memo_length(cls, v):
        if v and len(v) > 1000:
            raise ValueError("메모는 1000자 이하여야 합니다.")
        return v


class UserDiseaseUpdate(BaseModel):
    disease_name: str | None = None
    disease_code: str | None = None
    diagnosis_date: date | None = None
    memo: str | None = None

    @field_validator("disease_name")
    @classmethod
    def disease_name_valid(cls, v):
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("질환명을 입력해주세요.")
            if len(stripped) > 200:
                raise ValueError("질환명은 200자 이하여야 합니다.")
            return stripped
        return v

    @field_validator("disease_code")
    @classmethod
    def disease_code_valid(cls, v):
        if v is not None:
            stripped = v.strip()
            if len(stripped) > 50:
                raise ValueError("질환 코드는 50자 이하여야 합니다.")
            return stripped if stripped else None
        return v

    @field_validator("diagnosis_date")
    @classmethod
    def diagnosis_date_not_future(cls, v):
        if v is not None and v > date.today():
            raise ValueError("진단일은 오늘 이후 날짜를 입력할 수 없습니다.")
        return v

    @field_validator("memo")
    @classmethod
    def memo_length(cls, v):
        if v and len(v) > 1000:
            raise ValueError("메모는 1000자 이하여야 합니다.")
        return v


class UserDiseaseResponse(BaseModel):
    id: int
    disease_name: str
    disease_code: str | None = None
    diagnosis_date: date | None = None
    memo: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
