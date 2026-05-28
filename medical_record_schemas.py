from datetime import date, datetime

from pydantic import BaseModel, field_validator

# ── 약품 ─────────────────────────────────────────────────

class MedicationCreate(BaseModel):
    drug_name: str
    dosage: str | None = None
    frequency: str | None = None
    duration_days: int | None = None
    timing: str | None = None

    @field_validator("drug_name")
    @classmethod
    def drug_name_valid(cls, v):
        stripped = v.strip()
        if not stripped:
            raise ValueError("약품명을 입력해주세요.")
        if len(stripped) > 200:
            raise ValueError("약품명은 200자 이하여야 합니다.")
        return stripped

    @field_validator("duration_days")
    @classmethod
    def duration_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("복용 일수는 1 이상이어야 합니다.")
        return v


class MedicationResponse(BaseModel):
    id: int
    drug_name: str
    dosage: str | None = None
    frequency: str | None = None
    duration_days: int | None = None
    timing: str | None = None

    class Config:
        from_attributes = True


# ── 진료기록 생성 ─────────────────────────────────────────

class MedicalRecordCreate(BaseModel):
    visit_date: date
    hospital_name: str | None = None
    diagnosis: str
    medications: list[MedicationCreate] = []
    memo: str | None = None
    document_id: int | None = None

    @field_validator("visit_date")
    @classmethod
    def visit_date_not_future(cls, v):
        from datetime import date as date_type
        if v > date_type.today():
            raise ValueError("진료일자는 오늘 이후 날짜를 입력할 수 없습니다.")
        return v

    @field_validator("diagnosis")
    @classmethod
    def diagnosis_valid(cls, v):
        stripped = v.strip()
        if not stripped:
            raise ValueError("진단명을 입력해주세요.")
        if len(stripped) > 500:
            raise ValueError("진단명은 500자 이하여야 합니다.")
        return stripped

    @field_validator("hospital_name")
    @classmethod
    def hospital_name_valid(cls, v):
        if v is None:
            return None
        stripped = v.strip()
        if not stripped:
            return None
        if len(stripped) > 200:
            raise ValueError("의료기관명은 200자 이하여야 합니다.")
        return stripped

    @field_validator("medications")
    @classmethod
    def medications_valid(cls, v):
        if len(v) > 50:
            raise ValueError("처방 약품은 50개 이하여야 합니다.")
        return v

    @field_validator("memo")
    @classmethod
    def memo_length(cls, v):
        if v and len(v) > 2000:
            raise ValueError("메모는 2000자 이하여야 합니다.")
        return v


# ── 진료기록 수정 ─────────────────────────────────────────

class MedicalRecordUpdate(BaseModel):
    visit_date: date | None = None
    hospital_name: str | None = None
    diagnosis: str | None = None
    medications: list[MedicationCreate] | None = None
    memo: str | None = None

    @field_validator("visit_date")
    @classmethod
    def visit_date_not_future(cls, v):
        from datetime import date as date_type
        if v is not None and v > date_type.today():
            raise ValueError("진료일자는 오늘 이후 날짜를 입력할 수 없습니다.")
        return v

    @field_validator("diagnosis")
    @classmethod
    def diagnosis_valid(cls, v):
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("진단명을 입력해주세요.")
            if len(stripped) > 500:
                raise ValueError("진단명은 500자 이하여야 합니다.")
            return stripped
        return v

    @field_validator("hospital_name")
    @classmethod
    def hospital_name_valid(cls, v):
        if v is None:
            return None
        stripped = v.strip()
        if not stripped:
            return None
        if len(stripped) > 200:
            raise ValueError("의료기관명은 200자 이하여야 합니다.")
        return stripped

    @field_validator("medications")
    @classmethod
    def medications_valid(cls, v):
        if v is not None:
            if len(v) > 50:
                raise ValueError("처방 약품은 50개 이하여야 합니다.")
        return v

    @field_validator("memo")
    @classmethod
    def memo_length(cls, v):
        if v and len(v) > 2000:
            raise ValueError("메모는 2000자 이하여야 합니다.")
        return v


# ── 응답 ─────────────────────────────────────────────────

class MedicalRecordBrief(BaseModel):
    id: int
    visit_date: date
    hospital_name: str | None = None
    diagnosis: str
    medication_count: int
    has_guide: bool
    guide_needs_update: bool
    created_at: datetime


class MedicalRecordDetail(BaseModel):
    id: int
    visit_date: date
    hospital_name: str | None = None
    diagnosis: str
    medications: list[MedicationResponse]
    memo: str | None = None
    document_id: int | None = None
    has_guide: bool
    guide_needs_update: bool
    created_at: datetime
    updated_at: datetime


class MedicalRecordListResponse(BaseModel):
    items: list[MedicalRecordBrief]
    total: int
    page: int
    size: int
