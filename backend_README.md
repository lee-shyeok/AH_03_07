# 🏥 AI 헬스케어 앱 - FastAPI 백엔드
**AI-HealthCare-03 | 7조 | 이승혁 담당**

---

## 📱 구현 화면

### 🌟 온보딩 / 시작
| 기능 | 설명 |
|------|------|
| 스플래시 | 앱 로고 및 토큰 유효성 검사 |
| 온보딩 | 3페이지 앱 소개 슬라이드 |
| 사용자 타입 선택 | 일반 환자 / 자가면역환자 선택 |

### 🔐 인증
| 기능 | 설명 |
|------|------|
| 회원가입 | 이메일 인증 기반 회원가입 |
| 로그인 | JWT 토큰 기반 로그인 |
| 구글 로그인 | Google OAuth 2.0 소셜 로그인 ✅ NEW |
| 네이버 로그인 | 네이버 OAuth 소셜 로그인 ✅ NEW |
| 로그아웃 | 토큰 삭제 및 로그인 화면 이동 |

### 🏠 메인
| 기능 | 설명 |
|------|------|
| 대시보드 | 오늘의 복약, 최근 진료기록, 안내문 요약 |
| 검색 | 최근 검색어, 인기 검색어, 카테고리별 탐색 |
| AI 건강 챗봇 | 건강 관련 질문 챗봇 |
| 챗봇 대화 내역 | 세션별 대화 내역 조회 |

### 📋 진료기록
| 기능 | 설명 |
|------|------|
| 진료기록 목록 | 전체 진료기록 조회 |
| 진료기록 상세 | 진료기록 상세 조회 |
| 진료기록 직접 입력 | 병원명, 진단명, 메모 직접 입력 |
| 진료기록 수정 | 기존 진료기록 수정 |
| 진료기록 삭제 | 진료기록 삭제 |

### 📄 OCR
| 기능 | 설명 |
|------|------|
| 의료문서 업로드 | 이미지/PDF 업로드 |
| OCR 결과 검토 | OCR 결과 수정 및 확정 |
| OCR 처리 내역 | 업로드한 의료문서 목록 조회 |

### 📖 안내문
| 기능 | 설명 |
|------|------|
| 안내문 목록 | 전체 안내문 조회 |
| 안내문 상세 | 복약/생활습관/주의사항/권장검사 |
| 안내문 재생성 | 최신 진료기록 기반 재생성 |
| 안내문 평가 | 별점 + 코멘트 피드백 |

### 🔔 알림
| 기능 | 설명 |
|------|------|
| 알림 목록 | 전체 알림 조회 및 읽음 처리 |
| 복약 알림 설정 | 약품별 알림 시각/요일/채널 설정 |
| 알림 ON/OFF | 알림 유형별 / 채널별 활성화 설정 |

### 👤 마이페이지
| 기능 | 설명 |
|------|------|
| 내 정보 조회 | 프로필 정보 조회 (일반/자가면역 모드) |
| 프로필 수정 | 이름, 키/몸무게 수정 |
| 휴대폰 번호 수정 | 휴대폰 번호 변경 |
| 비밀번호 변경 | 현재/새 비밀번호 변경 |
| 만성질환 / 알레르기 | 칩 형태 다중 입력 및 저장 |
| 회원탈퇴 | 비밀번호 확인 후 계정 삭제 |

---

## 🗂 파일 구조

```
lib/
├── main.dart                        # 앱 진입점, SecureTokenStorage
├── splash_screen.dart               # 스플래시 + 토큰 유효성 검사
├── onboarding_page.dart             # 온보딩 3페이지
├── user_type_page.dart              # 사용자 타입 선택
├── login_page.dart                  # 로그인 (구글/네이버 소셜 로그인 포함)
├── signup_page.dart                 # 회원가입
├── home_page.dart                   # 바텀 네비게이션 (홈/기록/안내문/알림/마이)
├── dashboard_page.dart              # 홈 대시보드
├── search_page.dart                 # 검색
├── medical_records_page.dart        # 진료기록 목록/상세/입력/수정
├── guides_page.dart                 # 안내문 목록/상세/재생성/평가
├── notifications_page.dart          # 알림 목록
├── notification_settings_page.dart  # 복약 알림 설정 (약품별)
├── notification_toggle_page.dart    # 알림 ON/OFF 설정
├── ocr_history_page.dart            # OCR 처리 내역
├── chat_page.dart                   # 챗봇 + 대화 내역
├── my_page.dart                     # 마이페이지
├── user_edit_page.dart              # 내 정보 수정 + 회원탈퇴
├── chip_section.dart                # 만성질환/알레르기 입력 컴포넌트
├── pill_page.dart                   # 약품 이미지 인식 (Post-MVP)
├── contents_page.dart               # 콘텐츠 변환 내역 (Post-MVP)
└── services/
    ├── auth_service.dart            # 로그인/로그아웃/토큰 갱신
    ├── ocr_service.dart             # OCR 업로드/결과 조회
    ├── user_service.dart            # 유저 정보 조회/수정/탈퇴
    ├── notification_service.dart    # 알림 설정 조회/저장
    ├── google_auth_service.dart     # 구글 소셜 로그인 ✅ NEW
    └── naver_auth_service.dart      # 네이버 소셜 로그인 ✅ NEW
```

---

## 🛠 기술 스택

```
Flutter (Dart)
├── http: ^1.2.0              # API 통신
├── flutter_secure_storage    # JWT 토큰 저장 (웹: IndexedDB)
├── image_picker: ^1.0.7      # 이미지 선택
├── http_parser: ^4.0.0       # 파일 업로드
├── intl                      # 날짜 포맷
├── flutter_localizations     # 한국어 로케일
├── google_sign_in: ^6.2.2    # 구글 소셜 로그인 ✅ NEW
└── webview_flutter: ^4.13.0  # 네이버 로그인 웹뷰 ✅ NEW

FastAPI (Python)
├── fastapi                   # 웹 프레임워크
├── sqlalchemy                # ORM
├── pymysql                   # MySQL 드라이버
├── redis                     # 토큰 저장소
├── httpx                     # 소셜 로그인 HTTP 클라이언트 ✅ NEW
├── python-jose               # JWT 토큰
└── passlib                   # 비밀번호 해싱
```

---

## 🚀 실행 방법

### 1. 환경변수 설정
`envs/.local.env` 파일에 아래 내용 추가:
```
GOOGLE_WEB_CLIENT_ID=...
GOOGLE_ANDROID_CLIENT_ID=...
GOOGLE_IOS_CLIENT_ID=...
NAVER_CLIENT_ID=...
NAVER_CLIENT_SECRET=...
```

### 2. 백엔드 서버 실행
```bash
cd PythonProject
docker compose up -d --build
```

### 3. Flutter 실행
```bash
cd flutter_application_1
flutter pub get
flutter run
```

### 4. 브랜치
```
백엔드: feature/이승혁-frontend
Flutter: feature/이승혁-flutter
```

---

## 📡 API 연동

| 항목 | 내용 |
|------|------|
| Base URL | `http://localhost/api` |
| 인증 방식 | Bearer JWT Token |
| Access Token | 30분 |
| Refresh Token | 14일 |
| 백엔드 | FastAPI + MySQL + Redis |

### 주요 엔드포인트
| 기능 | 메서드 | 경로 |
|------|--------|------|
| 로그인 | POST | `/v1/auth/login` |
| 로그아웃 | POST | `/v1/auth/logout` |
| 토큰 갱신 | POST | `/v1/auth/refresh` |
| 구글 소셜 로그인 | POST | `/v1/auth/google` ✅ NEW |
| 네이버 소셜 로그인 | POST | `/v1/auth/naver` ✅ NEW |
| 내 정보 | GET/PATCH | `/v1/users/me` |
| 진료기록 | GET/POST/PATCH/DELETE | `/v1/medical-records` |
| OCR 업로드 | POST | `/v1/medical-documents` |
| 안내문 | GET | `/v1/guides` |
| 알림 | GET | `/v1/notifications` |
| 알림 설정 | GET/POST | `/v1/notifications/settings` |
| 대시보드 | GET | `/v1/dashboard` |
| 챗봇 세션 | GET/POST | `/v1/chat/sessions` |

---

## 🔐 소셜 로그인 설정

### 구글 로그인
- Google Cloud Console에서 OAuth 2.0 클라이언트 ID 발급
- 웹 / Android / iOS 클라이언트 ID 각각 발급 필요
- People API 활성화 필요

### 네이버 로그인
- Naver Developers에서 앱 등록 및 Client ID/Secret 발급
- 현재 개발 상태 (배포 시 심사 필요)
- 웹 환경에서는 임시 구현 (모바일 앱 빌드 시 정식 구현 예정)

### DB 변경사항
```sql
-- users 테이블에 소셜 로그인 컬럼 추가
ALTER TABLE users 
ADD COLUMN social_provider VARCHAR(20) NULL,
ADD COLUMN social_id VARCHAR(200) NULL;
```

---

## ⚠️ 주의사항

- 민감 의료정보 처리 시 면책문구 포함
- 의료 진단/처방 관련 표현 사용 금지 (의료법 §27)
- API 호출은 서비스 레이어로 분리
- 컴포넌트는 PascalCase, 함수는 camelCase
- 소셜 로그인 키는 절대 코드에 하드코딩 금지 (`.env` 파일 사용)
