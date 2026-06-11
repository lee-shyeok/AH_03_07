# 팀 피드백 반영 설계서 — 2026-06-10

## 범위

팀 채팅(명동, 오후 5:45) 요청사항 6개 구현.  
EC2 미배포 상태를 고려해 프론트 단에서 완결되는 변경만 포함.

---

## 1. 홈버튼 버그 수정 (home/page.tsx)

**증상**: 일반 모드 사용자가 홈 이동 시 자가면역 페이지 표시  
**원인**: `getMe()` 응답의 `user_type`이 localStorage 모드를 덮어씀  
- EC2 꺼져 있어 `updateMode()` 저장 실패 → 백엔드는 이전 모드 유지  
- 홈 진입 시 `getMe()` 성공 → 오래된 `user_type`으로 강제 전환

**수정**: `setUserType(u.user_type)` 제거. localStorage 모드를 항상 우선.

```tsx
// before
getMe().then((u) => { setName(u.name); if (u.user_type) setUserType(u.user_type); })
// after
getMe().then((u) => { setName(u.name); }).catch(() => {});
```

---

## 2. 약품목록 모드 구분 (medication/queries.ts + page.tsx + new/page.tsx)

| 모드 | 더미 데이터 | 약물 분류 선택 | DrugClass 배지 |
|------|------------|--------------|---------------|
| 일반 | 타이레놀, 이부프로펜, 아스피린 | 숨김 | 숨김 |
| 자가면역 | 메토트렉세이트, 하이드록시클로로퀸, 엽산 | 표시 | 표시 |

- `queries.ts`: `getMode()` 기반 더미 분기
- `new/page.tsx`: 일반 모드면 약물 분류 섹션 렌더링 제외 (category → drug_class 매핑 불필요)

---

## 3. 약품명 자동완성 (medication/new/page.tsx + schema.ts)

- 약품명 input 입력 시 모드별 약품 목록 드롭다운
- 일반: 타이레놀, 이부프로펜, 아스피린, 세티리진, 오메프라졸 등
- 자가면역: 메토트렉세이트, 하이드록시클로로퀸, 프레드니솔론, 엔브렐, 아자티오프린, 레플루노마이드, 셀레콕시브 등
- 정적 목록 (백엔드 API 연동 구조로 추후 교체 가능)

---

## 4. 복약알림설정 — 실제 약물 연동 + 모드 색상 (notifications/settings/page.tsx)

**현재**: `DRUG = { name: "메토트렉세이트 7.5mg", type: "자가면역" }` 하드코딩  
**변경**:
- `useMedications()` 훅으로 실제 등록 약물 불러오기
- 약이 여러 개면 상단 약물 선택 탭 표시
- **모드 색상**: 일반 → 초록(`#03C85F`), 자가면역 → 보라(`#7C5CCF`)
- 약물 없으면 안내 문구 + `/medication/new` 링크

---

## 5. 마이페이지 — 내 건강 정보에 다이어트/인포 항목 (mypage/page.tsx)

일반 모드 `healthMenus` 맨 아래에 추가:

```tsx
{ href: "/guides", label: "건강 정보 · 다이어트", icon: BookOpen }
```

기존 `/guides` 페이지 활용 (이미 존재).

---

## 6. 알림 디자인 모드 구분 색상

`notifications/settings/page.tsx`의 accent 색상 동적 적용:
- 일반 모드: `#03C85F` (초록)
- 자가면역 모드: `#7C5CCF` (보라)
- 약물 카드 배경, 배지, 저장 버튼 등에 적용

---

## 충돌 위험 평가

| 파일 | 위험도 | 근거 |
|------|--------|------|
| `home/page.tsx` | 🟡 중 | 여러 팀원이 수정한 파일 → 최소 변경 |
| `medication/*` | 🟢 낮음 | 허승혜 담당 REQ-AUTO-002/003 |
| `notifications/settings/page.tsx` | 🟢 낮음 | 허승혜 담당 REQ-NOTI |
| `mypage/page.tsx` | 🟡 중 | 배열 1줄 추가라 충돌 위험 낮음 |

---

## 스킵

- 알림 디자인 전면 리디자인: 색상 구분은 추가하되 레이아웃 대공사는 팀 협의 후
