# NFR-SAFE-004 — 제공 금지 기능 차단 정책 설계

**날짜:** 2026-06-02  
**브랜치:** feature/nfr-safe-004  
**담당:** tnsgus375 (권순현)  
**관련 요구사항:** NFR-SAFE-004  
**연계 모듈:** NFR-SAFE-003 (`app/services/nfr_safe_003.py`)

---

## 1. 목적

의료 서비스 앱에서 법령 위반 소지가 있는 8가지 기능을 코드 레벨에서 명문화하고, 사용자 입력(pre-generation)과 AI 응답(post-generation) 양 단계에서 탐지·차단한다.

---

## 2. 법적 근거 및 금지 기능 목록

| # | 카테고리 | 법적 근거 |
|---|---------|----------|
| 1 | 비대면 진료 중개·예약 (`telemedicine_brokerage`) | 의료법 비대면 진료 규정 |
| 2 | 의사 매칭·소개·알선 (`doctor_matching`) | 의료법 제27조 제3항 |
| 3 | 처방전 요청·전송 (`prescription_handling`) | 의료법 |
| 4 | 처방약 추천·약물 변경 지시 (`drug_recommendation`) | 약사법 제24조 |
| 5 | 의료진 판단 개입 (`medical_judgment_interference`) | 의료법 |
| 6 | 응급 자동 신고 (`auto_emergency_report`) | 응급의료법·통신법 |
| 7 | 의료기관 광고·후기·추천 (`medical_institution_advertisement`) | 의료법 제56조 |
| 8 | 의료기관 소개 대가 수수료 (`referral_commission`) | 의료법 제27조 |

---

## 3. 파일 구성

```
app/services/nfr_safe_004.py      # 신규 — 금지 기능 정책 모듈
app/tests/test_nfr_safe_004.py    # 신규 — 단위 테스트
```

### 수정하지 않는 파일

| 파일 | 작성자 | 이유 |
|-----|--------|------|
| `app/services/chat_validation_service.py` | shhur310 | 팀원 작성 파일, 수정 금지 |
| `app/services/chat_message_service.py` | shhur310 | 팀원 작성 파일, 수정 금지 |
| `app/services/nfr_safe_003.py` | tnsgus375 | 재활용만 (import) |
| `app/models/safety_filter_log.py` | tnsgus375 | 재활용만 (테이블 공유) |

---

## 4. 데이터 구조

### 4-1. 룰셋

```python
REFUSAL_MESSAGE = "이 기능은 관련 법령에 따라 제공이 제한됩니다. 담당 의료진과 직접 상담하세요."

_RULESET: dict[str, list[str]] = {
    "telemedicine_brokerage": [
        "비대면 진료 예약", "원격 진료 예약", "화상 진료 연결",
        "비대면 진료 중개", "온라인 진료 예약",
    ],
    "doctor_matching": [
        "의사 매칭", "의사 소개", "의사 연결해", "의사 알선",
        "전문의 매칭", "담당의 연결",
    ],
    "prescription_handling": [
        "처방전 발급", "처방전 보내", "처방전 요청",
        "처방전 전송", "처방전 받아",
    ],
    "drug_recommendation": [
        "처방약 추천", "약 추천해줘", "어떤 약 먹어야",
        "약 변경해줘", "약 바꿔줘", "이 약 대신",
    ],
    "medical_judgment_interference": [
        "의사 판단 무시", "의사 말 무시", "처방 무시해도",
        "의사보다 내가", "의사 의견 틀렸",
    ],
    "auto_emergency_report": [
        "119 자동 신고", "119 자동 발신", "112 자동 신고",
        "자동으로 신고해", "대신 신고해줘",
    ],
    "medical_institution_advertisement": [
        "좋은 병원 추천", "병원 추천해줘", "병원 후기",
        "의원 광고", "병원 광고", "추천 병원",
    ],
    "referral_commission": [
        "소개비", "중개 수수료", "병원 소개 수수료",
        "의료기관 소개비", "진료 중개비",
    ],
}
```

### 4-2. 결과 타입

```python
@dataclass
class ProhibitedFeatureResult:
    is_blocked: bool
    matched_categories: list[str] = field(default_factory=list)
    refusal_message: str = ""
```

### 4-3. DB 저장

기존 `safety_filter_logs` 테이블 재활용. 마이그레이션 없음.

`blocked_reason` 컬럼은 `max_length=100`. 카테고리 전체명을 쉼표 연결하면 최대 185자로 초과하므로, 아래 약어 코드를 사용한다.

| 카테고리 | 약어 코드 |
|---------|---------|
| `telemedicine_brokerage` | `TMB` |
| `doctor_matching` | `DM` |
| `prescription_handling` | `PH` |
| `drug_recommendation` | `DR` |
| `medical_judgment_interference` | `MJI` |
| `auto_emergency_report` | `AER` |
| `medical_institution_advertisement` | `MIA` |
| `referral_commission` | `RC` |

8개 전부 매칭 시: `"TMB,DM,PH,DR,MJI,AER,MIA,RC"` = 28자 (한계 내).

| 컬럼 | NFR-SAFE-004 값 예시 |
|------|---------------------|
| `target_type` | `"CHAT_INPUT"` / `"CHAT_OUTPUT"` / `"GUIDE"` |
| `filter_stage` | `"pre_generation"` / `"post_generation"` |
| `blocked_reason` | `"TMB,DM"` (약어 코드, 쉼표 구분) |

---

## 5. 함수 시그니처 (3-레이어)

```python
# Layer 1: 순수 탐지 (동기)
def apply_nfr_safe_004(text: str) -> ProhibitedFeatureResult: ...

# Layer 2: DB 로깅 (비동기)
async def log_prohibited_block(
    *, user_id, target_type, target_id,
    matched_categories, original_text, filter_stage,
) -> None: ...

# Layer 3: 탐지 + 로깅 통합 (비동기)
async def filter_and_log_004(
    text: str,
    *, user_id=None, target_type, target_id=None, filter_stage,
) -> ProhibitedFeatureResult: ...
```

---

## 6. 테스트 계획 (14개)

| 구분 | 수 | 내용 |
|-----|----|------|
| 패스 케이스 | 2 | 안전 문구, 의료진 상담 권유 |
| 카테고리별 차단 | 8 | 각 카테고리 1개씩 |
| 복수 카테고리 | 1 | 2개 이상 동시 매칭 |
| refusal_message 검증 | 1 | REFUSAL_MESSAGE 상수 일치 |
| filter_and_log_004 통합 | 2 | DB mock, 차단/미차단 |

DB 호출은 `AsyncMock`으로 격리. `pytest-asyncio` 사용.

---

## 7. 구현 순서

1. `feature/nfr-safe-004` 브랜치 생성 (develop 기준)
2. `app/services/nfr_safe_004.py` 구현
3. `app/tests/test_nfr_safe_004.py` 작성
4. `ruff check` + `ruff format` + `pytest` 통과 확인
5. 커밋 + push (PR은 수동 생성)