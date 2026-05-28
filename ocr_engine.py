"""
OCR 엔진 — GPT-4o mini Vision API 기반
- 이미지(JPG/PNG): base64 인코딩 후 Vision API 전송
- PDF: 첫 페이지를 이미지로 변환 후 전송 (pdf2image + poppler 필요)

[수정 #3] OPENAI_API_KEY 누락 시 Mock 자동 전환 제거
  → 운영환경에서 키 빠짐 → Mock 데이터 DB 저장 사고 방지
  → 키 없으면 즉시 RuntimeError (서버 시작 시 또는 첫 호출 시 명확히 실패)
"""
import base64
import io
import json
import os
import urllib.request
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError

from dotenv import load_dotenv

load_dotenv()

LOW_CONFIDENCE_THRESHOLD = 0.75  # 이 미만이면 프론트에서 노란색 하이라이트

# [수정 #3] 키 없으면 즉시 에러 — Mock 자동 전환 없음
_OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# 지원 확장자 → MIME 타입
_MIME_MAP: dict[str, str] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}

# ── 문서 유형별 추출 프롬프트 ─────────────────────────────

_PROMPTS: dict[str, str] = {
    "prescription": """\
이 이미지는 병원 처방전입니다. 아래 항목을 JSON으로 추출하세요.
반드시 아래 형식만 출력하고 다른 텍스트는 절대 출력하지 마세요.

{
  "hospital_name": "병원명 또는 null",
  "doctor_name": "의사명 또는 null",
  "visit_date": "YYYY-MM-DD 또는 null",
  "diagnosis": "진단명 또는 null",
  "medications": [
    {
      "drug_name": "약품명",
      "dosage": "1회 복용량 (예: 1정)",
      "frequency": "복용 횟수 (예: 1일 3회)",
      "duration_days": 숫자_또는_null,
      "timing": "복용 시점 또는 null"
    }
  ],
  "next_visit_date": "YYYY-MM-DD 또는 null",
  "_confidences": {
    "hospital_name": 0.0~1.0,
    "doctor_name": 0.0~1.0,
    "visit_date": 0.0~1.0,
    "diagnosis": 0.0~1.0,
    "medications": 0.0~1.0,
    "next_visit_date": 0.0~1.0
  }
}
""",
    "medical_record": """\
이 이미지는 진료기록부 또는 진료확인서입니다. 아래 항목을 JSON으로 추출하세요.
반드시 아래 형식만 출력하고 다른 텍스트는 절대 출력하지 마세요.

{
  "hospital_name": "병원명 또는 null",
  "doctor_name": "의사명 또는 null",
  "visit_date": "YYYY-MM-DD 또는 null",
  "diagnosis": "진단명 또는 null",
  "treatment_summary": "진료 내용 요약 또는 null",
  "next_visit_date": "YYYY-MM-DD 또는 null",
  "_confidences": {
    "hospital_name": 0.0~1.0,
    "doctor_name": 0.0~1.0,
    "visit_date": 0.0~1.0,
    "diagnosis": 0.0~1.0,
    "treatment_summary": 0.0~1.0,
    "next_visit_date": 0.0~1.0
  }
}
""",
    "pill_bag": """\
이 이미지는 약봉투입니다. 아래 항목을 JSON으로 추출하세요.
반드시 아래 형식만 출력하고 다른 텍스트는 절대 출력하지 마세요.

{
  "pharmacy_name": "약국명 또는 null",
  "pharmacist_name": "약사명 또는 null",
  "dispensed_date": "YYYY-MM-DD 또는 null",
  "patient_name": "환자명 또는 null",
  "medications": [
    {
      "drug_name": "약품명",
      "dosage": "1회 복용량",
      "frequency": "복용 횟수",
      "duration_days": 숫자_또는_null,
      "timing": "복용 시점 또는 null",
      "caution": "주의사항 또는 null"
    }
  ],
  "_confidences": {
    "pharmacy_name": 0.0~1.0,
    "dispensed_date": 0.0~1.0,
    "patient_name": 0.0~1.0,
    "medications": 0.0~1.0
  }
}
""",
    "lab_result": """\
이 이미지는 검사결과지입니다. 아래 항목을 JSON으로 추출하세요.
반드시 아래 형식만 출력하고 다른 텍스트는 절대 출력하지 마세요.

{
  "hospital_name": "병원명 또는 null",
  "test_date": "YYYY-MM-DD 또는 null",
  "patient_name": "환자명 또는 null",
  "tests": [
    {
      "test_name": "검사항목명",
      "value": "측정값 (문자열)",
      "unit": "단위 또는 null",
      "reference_range": "참고범위 (예: 70-100) 또는 null"
    }
  ],
  "_confidences": {
    "hospital_name": 0.0~1.0,
    "test_date": 0.0~1.0,
    "patient_name": 0.0~1.0,
    "tests": 0.0~1.0
  }
}
""",
    "health_checkup": """\
이 이미지는 건강검진 결과지입니다. 아래 항목을 JSON으로 추출하세요.
반드시 아래 형식만 출력하고 다른 텍스트는 절대 출력하지 마세요.

{
  "institution_name": "검진기관명 또는 null",
  "checkup_date": "YYYY-MM-DD 또는 null",
  "patient_name": "수검자명 또는 null",
  "height_cm": 숫자_또는_null,
  "weight_kg": 숫자_또는_null,
  "bmi": 숫자_또는_null,
  "blood_pressure": "수축기/이완기 (예: 120/80) 또는 null",
  "fasting_glucose": 숫자_또는_null,
  "total_cholesterol": 숫자_또는_null,
  "overall_opinion": "종합 소견 또는 null",
  "_confidences": {
    "institution_name": 0.0~1.0,
    "checkup_date": 0.0~1.0,
    "patient_name": 0.0~1.0,
    "overall_opinion": 0.0~1.0
  }
}
""",
    "other": """\
이 이미지는 의료 관련 문서입니다. 텍스트를 최대한 추출하고 아래 형식으로 출력하세요.
반드시 아래 형식만 출력하고 다른 텍스트는 절대 출력하지 마세요.

{
  "raw_text": "전체 텍스트 내용",
  "summary": "문서 내용 요약 (2~3줄)",
  "_confidences": {
    "raw_text": 0.0~1.0,
    "summary": 0.0~1.0
  }
}
""",
}


# ── 파일 → base64 변환 ────────────────────────────────────

def _file_to_base64(file_path: str) -> tuple[str, str]:
    """
    파일을 base64로 변환. (base64_str, mime_type) 반환.
    PDF는 첫 페이지를 PNG로 변환.
    [수정 #4] 매직바이트로 실제 파일 형식 검증 (Content-Type 헤더 신뢰 금지)
    """
    path = Path(file_path)
    with open(file_path, "rb") as f:
        header = f.read(8)

    # 매직바이트 검증
    if header[:4] == b"\x89PNG":
        mime_type = "image/png"
    elif header[:3] in (b"\xff\xd8\xff",):
        mime_type = "image/jpeg"
    elif header[:4] == b"%PDF":
        # PDF → 첫 페이지 PNG 변환
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(file_path, first_page=1, last_page=1, dpi=200)
            buf = io.BytesIO()
            images[0].save(buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode("utf-8"), "image/png"
        except ImportError:
            raise RuntimeError(
                "PDF 처리를 위해 pdf2image와 poppler가 필요합니다.\n"
                "pip install pdf2image  /  apt install poppler-utils"
            )
    else:
        raise ValueError(f"지원하지 않는 파일 형식입니다. (매직바이트: {header[:4].hex()})")

    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8"), mime_type


# ── OpenAI Vision API 호출 ────────────────────────────────

def _call_openai_vision(image_b64: str, mime_type: str, prompt: str) -> str:
    """
    GPT-4o mini Vision API 호출.
    [수정 #8] HTTPError / URLError / 타임아웃 모두 명시적으로 처리
    """
    body = json.dumps({
        "model": "gpt-4o-mini",
        "max_tokens": 1500,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_b64}",
                            "detail": "high",
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_OPENAI_API_KEY}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        if e.code == 401:
            raise RuntimeError("OpenAI API 인증 실패: API 키를 확인해주세요.")
        if e.code == 429:
            raise RuntimeError("OpenAI API 요청 한도 초과: 잠시 후 다시 시도해주세요.")
        raise RuntimeError(f"OpenAI API 오류 (HTTP {e.code}): {error_body[:200]}")
    except URLError as e:
        raise RuntimeError(f"OpenAI API 연결 실패: {e.reason}")
    except TimeoutError:
        raise RuntimeError("OpenAI API 응답 시간 초과 (60초)")

    return result["choices"][0]["message"]["content"].strip()


# ── GPT 응답 파싱 ─────────────────────────────────────────

def _parse_response(raw_response: str) -> tuple[dict[str, Any], dict[str, Any], float]:
    """
    GPT 응답에서 JSON 파싱.
    [수정 #11] JSONDecodeError 발생 시 명확한 예외 메시지로 변환
    Returns: (structured_data, field_confidences, overall_score)
    """
    text = raw_response.strip()

    # ```json ... ``` 코드 펜스 제거
    if text.startswith("```"):
        lines = text.splitlines()
        # 첫 줄(```json 또는 ```) 제거, 마지막 ``` 제거
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        text = "\n".join(inner).strip()

    try:
        data: dict[str, Any] = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"OCR 엔진 응답이 유효한 JSON이 아닙니다: {e}") from e

    # _confidences 분리
    raw_confidences: dict[str, float] = data.pop("_confidences", {})

    # field_confidences 구조로 변환
    field_confidences: dict[str, Any] = {}
    for key, val in raw_confidences.items():
        try:
            conf = float(val)
        except (TypeError, ValueError):
            conf = 0.5
        conf = max(0.0, min(1.0, conf))  # 0~1 범위 강제
        field_confidences[key] = {
            "value": str(data.get(key)) if data.get(key) is not None else None,
            "confidence": conf,
            "low_confidence": conf < LOW_CONFIDENCE_THRESHOLD,
        }

    overall = (
        sum(float(v) for v in raw_confidences.values()) / len(raw_confidences)
        if raw_confidences else 0.5
    )

    return data, field_confidences, round(max(0.0, min(1.0, overall)), 3)


# ── 메인 진입점 ───────────────────────────────────────────

def run_ocr(file_path: str, document_type: str) -> tuple[str, dict, dict, float]:
    """
    OCR 실행.
    [수정 #3] API 키 없으면 즉시 RuntimeError (Mock 자동 전환 없음)
    Returns: (raw_text, structured_data, field_confidences, overall_confidence)
    """
    if not _OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY 환경변수가 설정되지 않았습니다. "
            ".env 파일에 OPENAI_API_KEY를 추가해주세요."
        )

    prompt = _PROMPTS.get(document_type, _PROMPTS["other"])
    image_b64, mime_type = _file_to_base64(file_path)
    raw_response = _call_openai_vision(image_b64, mime_type, prompt)
    structured_data, field_confidences, overall = _parse_response(raw_response)

    return raw_response, structured_data, field_confidences, overall


# ── Mock (테스트 전용 — 직접 호출만 허용) ────────────────
# 운영 코드에서 import하여 사용 금지. 테스트 코드에서만 패치용으로 사용.

def _mock_result_for_test(document_type: str) -> tuple[str, dict, dict, float]:
    raw = f"[MOCK OCR] document_type={document_type}"
    if document_type == "prescription":
        data = {
            "hospital_name": "서울대학교병원",
            "doctor_name": "홍길동",
            "visit_date": "2025-01-15",
            "diagnosis": "고혈압",
            "medications": [
                {"drug_name": "암로디핀정 5mg", "dosage": "1정",
                 "frequency": "1일 1회", "duration_days": 30, "timing": "아침 식후"},
            ],
            "next_visit_date": None,
        }
        confs = {
            "hospital_name":   {"value": "서울대학교병원", "confidence": 0.97, "low_confidence": False},
            "doctor_name":     {"value": "홍길동",         "confidence": 0.92, "low_confidence": False},
            "visit_date":      {"value": "2025-01-15",     "confidence": 0.99, "low_confidence": False},
            "diagnosis":       {"value": "고혈압",          "confidence": 0.88, "low_confidence": False},
            "medications":     {"value": None,             "confidence": 0.85, "low_confidence": False},
            "next_visit_date": {"value": None,             "confidence": 0.70, "low_confidence": True},
        }
        return raw, data, confs, 0.90
    data = {"raw_text": raw, "summary": f"{document_type} Mock 결과입니다."}
    confs = {
        "raw_text": {"value": raw,  "confidence": 0.70, "low_confidence": True},
        "summary":  {"value": None, "confidence": 0.70, "low_confidence": True},
    }
    return raw, data, confs, 0.70
