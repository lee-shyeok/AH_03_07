"""
챗봇 엔진 — GPT-4o mini 기반
- httpx AsyncClient로 진짜 SSE 스트리밍
- 가드레일 (응급/자살/진단/처방 요청 차단)
- 사용자 프로필 + 최근 30일 가이드 시스템 프롬프트 포함
"""
import json
import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv

load_dotenv()

_OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# 가드레일 키워드
_EMERGENCY_KEYWORDS = [
    "가슴 통증", "흉통", "호흡 곤란", "호흡곤란", "숨쉬기 힘들", "숨이 안쉬",
    "심장마비", "뇌졸중", "의식 잃", "응급", "쓰러질 것 같", "쓰러졌",
]
_SUICIDE_KEYWORDS = ["자살", "자해", "죽고 싶", "죽고싶", "살기 싫", "살기싫"]
_DIAGNOSIS_KEYWORDS = ["진단해줘", "진단해 줘", "내 병이 뭐야", "병명이 뭐야", "무슨 병이야"]
_PRESCRIPTION_KEYWORDS = ["처방해줘", "처방해 줘", "약 써줘", "약 처방", "약을 처방"]

_EMERGENCY_RESPONSE = (
    "⚠️ 응급 증상이 의심됩니다. 즉시 119에 신고하거나 가까운 응급실로 가세요. "
    "본 서비스는 응급 상황에 대응할 수 없습니다."
)
_SUICIDE_RESPONSE = (
    "힘드신 상황이시군요. 자살예방상담전화 1393(24시간 무료)으로 연락하시면 "
    "전문 상담사와 이야기 나눌 수 있습니다. 혼자 감당하지 않으셔도 됩니다."
)
_DIAGNOSIS_RESPONSE = (
    "진단은 의사만이 할 수 있습니다. 증상이 걱정되신다면 가까운 의원이나 "
    "병원을 방문하여 전문의 진료를 받아보시길 권장합니다."
)
_PRESCRIPTION_RESPONSE = (
    "약 처방은 의사와 약사만이 할 수 있습니다. "
    "복약 관련 궁금한 점은 담당 약사에게 문의해주세요."
)

_SYSTEM_PROMPT_TEMPLATE = """\
당신은 의료 정보를 친절하고 쉽게 안내하는 헬스케어 도우미입니다.

[절대 규칙]
1. 진단, 처방, 의료 행위를 직접 수행하거나 대체하지 않습니다.
2. 모든 답변은 참고용이며 반드시 의사/약사 상담을 권고합니다.
3. 확실하지 않은 정보는 추측하지 않습니다.
4. 응급 증상 언급 시 즉시 119 신고를 안내합니다.
5. 자살/자해 관련 내용은 자살예방상담전화(1393)를 안내합니다.

[사용자 프로필]
- 만성질환: {chronic_diseases}
- 알레르기: {allergy_info}

[최근 가이드 요약]
{recent_guides}

위 정보를 참고하여 사용자에게 맞춤형 건강 정보를 안내하세요.
"""


def _check_guardrail(content: str) -> str | None:
    """
    가드레일 체크. 차단 응답 문자열 반환, 통과 시 None.
    응급 > 자살 > 진단 > 처방 순 우선순위.
    """
    for kw in _EMERGENCY_KEYWORDS:
        if kw in content:
            return _EMERGENCY_RESPONSE
    for kw in _SUICIDE_KEYWORDS:
        if kw in content:
            return _SUICIDE_RESPONSE
    for kw in _DIAGNOSIS_KEYWORDS:
        if kw in content:
            return _DIAGNOSIS_RESPONSE
    for kw in _PRESCRIPTION_KEYWORDS:
        if kw in content:
            return _PRESCRIPTION_RESPONSE
    return None


def build_system_prompt(
    chronic_diseases: str,
    allergy_info: str,
    recent_guides: list[dict[str, str]],
) -> str:
    if recent_guides:
        guide_lines = [
            f"- [{g.get('visit_date', '')}] {g.get('diagnosis', '')}: "
            f"{g.get('medication_guide', '')[:100]}"
            for g in recent_guides[:3]
        ]
        guides_str = "\n".join(guide_lines)
    else:
        guides_str = "없음"

    return _SYSTEM_PROMPT_TEMPLATE.format(
        chronic_diseases=chronic_diseases or "없음",
        allergy_info=allergy_info or "없음",
        recent_guides=guides_str,
    )


def build_messages(
    system_prompt: str,
    history: list[dict[str, str]],
    user_message: str,
) -> list[dict[str, str]]:
    """최근 20개 메시지(10턴) + 현재 메시지."""
    recent = history[-20:] if len(history) > 20 else history
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(recent)
    messages.append({"role": "user", "content": user_message})
    return messages


async def stream_chat_response(
    messages: list[dict[str, str]],
) -> AsyncGenerator[str, None]:
    """
    [수정 1] httpx AsyncClient로 진짜 비동기 SSE 스트리밍.
    블로킹 I/O 제거 → event loop 차단 없음.
    """
    if not _OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

    try:
        import httpx
    except ImportError:
        raise RuntimeError("httpx 패키지가 필요합니다. requirements.txt에 httpx를 추가해주세요.")

    body = {
        "model": "gpt-4o-mini",
        "max_tokens": 1000,
        "temperature": 0.7,
        "stream": True,
        "messages": messages,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            async with client.stream(
                "POST",
                "https://api.openai.com/v1/chat/completions",
                json=body,
                headers={
                    "Authorization": f"Bearer {_OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
            ) as resp:
                if resp.status_code == 401:
                    raise RuntimeError("OpenAI API 인증 실패: API 키를 확인해주세요.")
                if resp.status_code == 429:
                    raise RuntimeError("OpenAI API 요청 한도 초과. 잠시 후 다시 시도해주세요.")
                if resp.status_code != 200:
                    raise RuntimeError(f"OpenAI API 오류 (HTTP {resp.status_code})")

                async for line in resp.aiter_lines():
                    line = line.strip()
                    if not line or line == "data: [DONE]":
                        continue
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            delta = data["choices"][0]["delta"]
                            if "content" in delta:
                                yield delta["content"]
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

        except httpx.TimeoutException:
            raise RuntimeError("OpenAI API 응답 시간 초과 (60초)")
        except httpx.ConnectError:
            raise RuntimeError("OpenAI API 연결 실패")
