"""
GPT-4o mini 기반 가이드 생성 엔진
- 진료기록 + 약품 정보 + 사용자 프로필을 컨텍스트로 가이드 생성
- OPENAI_API_KEY 없으면 RuntimeError (Mock 자동 전환 없음)
"""

import json
import os
import urllib.request
from typing import Any
from urllib.error import HTTPError, URLError

from dotenv import load_dotenv

load_dotenv()

_OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

DISCLAIMER = (
    "본 가이드는 의료 전문가의 진단을 대체하지 않습니다. 증상이 지속되거나 악화되면 반드시 의사 또는 약사와 상담하세요."
)

_SYSTEM_PROMPT = """\
당신은 의료 정보를 쉽고 정확하게 안내하는 도우미입니다.
반드시 아래 규칙을 따르세요:
1. 진단·처방·의료 행위를 직접 수행하거나 대체하지 않습니다.
2. 모든 안내는 참고용이며, 반드시 의사/약사 상담을 권고합니다.
3. 불확실한 정보는 추측하지 않고 "의료진 상담 필요"로 표기합니다.
4. 응답은 반드시 JSON 형식만 출력합니다. 다른 텍스트는 절대 출력하지 않습니다.
"""

_USER_PROMPT_TEMPLATE = """\
다음 진료 정보를 바탕으로 환자를 위한 가이드를 JSON 형식으로 작성해주세요.

[진료 정보]
- 진료일자: {visit_date}
- 의료기관: {hospital_name}
- 진단명: {diagnosis}
- 처방 약품: {medications}
- 환자 메모: {memo}

[환자 프로필]
- 만성질환: {chronic_diseases}
- 알레르기: {allergy_info}

아래 JSON 형식만 출력하세요. 다른 텍스트는 절대 출력하지 마세요.

{{
  "medication_guide": "약품별 복용 시점, 방법, 주의사항을 구체적으로 안내 (500자 이내)",
  "lifestyle_guide": "식이, 운동, 수면 관련 생활습관 권장사항 (300자 이내)",
  "precautions": "약물 상호작용, 알레르기 경고, 부작용 주의사항 (300자 이내)",
  "recommended_checkups": "권장 추가 검진 또는 상담 항목 (200자 이내)"
}}
"""


def _call_openai(messages: list, temperature: float = 0.3) -> str:
    """OpenAI Chat API 호출. 실패 시 명확한 예외 발생."""
    if not _OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

    body = json.dumps(
        {
            "model": "gpt-4o-mini",
            "max_tokens": 1500,
            "temperature": temperature,
            "messages": messages,
        }
    ).encode("utf-8")

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
        err = e.read().decode("utf-8", errors="replace")
        if e.code == 401:
            raise RuntimeError("OpenAI API 인증 실패: API 키를 확인해주세요.")
        if e.code == 429:
            raise RuntimeError("OpenAI API 요청 한도 초과. 잠시 후 다시 시도해주세요.")
        raise RuntimeError(f"OpenAI API 오류 (HTTP {e.code}): {err[:200]}")
    except URLError as e:
        raise RuntimeError(f"OpenAI API 연결 실패: {e.reason}")
    except TimeoutError:
        raise RuntimeError("OpenAI API 응답 시간 초과 (60초)")

    return result["choices"][0]["message"]["content"].strip()


def _parse_json_response(raw: str) -> dict[str, Any]:
    """GPT 응답 JSON 파싱. 코드 펜스 제거 후 파싱."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        text = "\n".join(inner).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"GPT 응답이 유효한 JSON이 아닙니다: {e}") from e


def _format_medications(medications: list) -> str:
    """약품 목록을 프롬프트용 문자열로 변환."""
    if not medications:
        return "없음"
    parts = []
    for m in medications:
        parts.append(
            f"{m.drug_name} "
            f"({m.dosage or '용량 미상'}, "
            f"{m.frequency or '횟수 미상'}, "
            f"{m.duration_days or '?'}일, "
            f"{m.timing or '시점 미상'})"
        )
    return " / ".join(parts)


def generate_guide(
    visit_date: str,
    hospital_name: str,
    diagnosis: str,
    medications: list,
    memo: str,
    chronic_diseases: str,
    allergy_info: str,
) -> dict[str, str]:
    """
    가이드 생성 메인 함수.
    Returns: {medication_guide, lifestyle_guide, precautions, recommended_checkups}
    """
    user_prompt = _USER_PROMPT_TEMPLATE.format(
        visit_date=visit_date,
        hospital_name=hospital_name or "미상",
        diagnosis=diagnosis,
        medications=_format_medications(medications),
        memo=memo or "없음",
        chronic_diseases=chronic_diseases or "없음",
        allergy_info=allergy_info or "없음",
    )

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    raw = _call_openai(messages, temperature=0.3)
    data = _parse_json_response(raw)

    # 필수 필드 보정 — GPT가 누락하더라도 빈값으로 처리
    return {
        "medication_guide": str(data.get("medication_guide") or ""),
        "lifestyle_guide": str(data.get("lifestyle_guide") or ""),
        "precautions": str(data.get("precautions") or ""),
        "recommended_checkups": str(data.get("recommended_checkups") or ""),
    }
