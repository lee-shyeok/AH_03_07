# 🏥 AI 헬스케어 앱 - FastAPI 백엔드
**AI-HealthCare-03 | 7조 | 이승혁 담당**

---

## 📡 구현 API

### 🔐 인증
| 기능 | 메서드 | 경로 |
|------|--------|------|
| 회원가입 | POST | `/v1/auth/signup` |
| 이메일 인증코드 발송 | POST | `/v1/auth/email-verify/send` |
| 이메일 인증코드 확인 | POST | `/v1/auth/email-verify/confirm` |
| 로그인 | POST | `/v1/auth/login` |
| 구글 소셜 로그인 | POST | `/v1/auth/google` ✅ NEW |
| 네이버 소셜 로그인 | POST | `/v1/auth/naver` ✅ NEW |
| 토큰 갱신 | POST | `/v1/auth/refresh` |
| 로그아웃 | POST | `/v1/auth/logout` |

### 👤 사용자
| 기능 | 메서드 | 경로 |
|------|--------|------|
| 내 정보 조회 | GET | `/v1/users/me` |
| 내 정보 수정 | PATCH | `/v1/users/me` |
| 회원 탈퇴 | DELETE | `/v1/users/me` |

### 📋 진료기록
| 기능 | 메서드 | 경로 |
|------|--------|------|
| 진료기록 목록 | GET | `/v1/medical-records` |
| 진료기록 등록 | POST | `/v1/medical-records` |
| 진료기록 상세 | GET | `/v1/medical-records/{id}` |
| 진료기록 수정 | PUT | `/v1/medical-records/{id}` |
| 진료기록 삭제 | DELETE | `/v1/medical-records/{id}` |

### 📄 의료문서 / OCR
| 기능 | 메서드 | 경로 |
|------|--------|------|
| 의료문서 업로드 | POST | `/v1/medical-documents` |
| 의료문서 목록 | GET | `/v1/medical-documents` |
| OCR 처리 시작 | POST | `/v1/medical-documents/{id}/ocr-jobs` |
| OCR 결과 조회 | GET | `/v1/ocr-jobs/{id}` |
| OCR 결과 확정 | PUT | `/v1/medical-documents/{id}/confirm` |
| 의료문서 삭제 | DELETE | `/v1/medical-documents/{id}` |

### 📖 안내문
| 기능 | 메서드 | 경로 |
|------|--------|------|
| 안내문 목록 | GET | `/v1/guides` |
| 안내문 상세 | GET | `/v1/guides/{id}` |
| 안내문 재생성 | POST | `/v1/guides/{id}/regenerate` |
| 안내문 평가 | POST | `/v1/guides/{id}/feedback` |

### 🔔 알림
| 기능 | 메서드 | 경로 |
|------|--------|------|
| 알림 목록 | GET | `/v1/notifications` |
| 알림 읽음 처리 | PUT | `/v1/notifications/{id}/read` |
| 알림 설정 조회 | GET | `/v1/notifications/settings` |
| 알림 설정 저장 | POST | `/v1/notifications/settings` |

### 🏠 대시보드 / 챗봇
| 기능 | 메서드 | 경로 |
|------|--------|------|
| 대시보드 | GET | `/v1/dashboard` |
| 챗봇 세션 생성 | POST | `/v1/chat/sessions` |
| 챗봇 메시지 전송 | POST | `/v1/chat/sessions/{id}/messages` |
| 챗봇 대화 내역 | GET | `/v1/chat/sessions/{id}/messages` |

---

## 🗂 파일 구조

```
PythonProject/
├── main.py                          # FastAPI 앱 진입점
├── models.py                        # DB 모델 (User 등)
├── schemas.py                       # Pydantic 스키마
├── database.py                      # DB/Redis 연결
├── security.py                      # JWT 토큰 처리
├── Dockerfile                       # Docker 설정
├── docker-compose.yml               # Docker Compose 설정
├── requirements.txt                 # 패키지 목록
├── routers/
│   ├── auth.py                      # 이메일 로그인/회원가입
│   ├── social_auth.py               # 구글/네이버 소셜 로그인 ✅ NEW
│   ├── users.py                     # 유저 정보
│   ├── medical_documents.py         # 의료문서/OCR
│   ├── medical_records.py           # 진료기록
│   ├── guides.py                    # 안내문
│   ├── notifications.py             # 알림
│   ├── chats.py                     # 챗봇
│   └── dashboard.py                 # 대시보드
└── envs/
    └── .local.env                   # 환경변수 (gitignore 적용)
```

---

## 🛠 기술 스택

```
FastAPI (Python)
├── fastapi                   # 웹 프레임워크
├── sqlalchemy                # ORM
├── pymysql                   # MySQL 드라이버
├── redis                     # 토큰 저장소
├── httpx                     # 소셜 로그인 HTTP 클라이언트 ✅ NEW
├── python-jose               # JWT 토큰
└── passlib                   # 비밀번호 해싱

인프라
├── MySQL 8.0                 # 데이터베이스
├── Redis                     # 토큰/캐시 저장소
├── Nginx                     # 리버스 프록시
└── Docker Compose            # 컨테이너 오케스트레이션
```

---

## 🚀 실행 방법

### 1. 환경변수 설정
`envs/.local.env` 파일 생성 후 아래 내용 입력:
```
DATABASE_URL=mysql+pymysql://root:비밀번호@mysql:3306/mydb
REDIS_PASSWORD=비밀번호
GOOGLE_WEB_CLIENT_ID=...
GOOGLE_ANDROID_CLIENT_ID=...
GOOGLE_IOS_CLIENT_ID=...
NAVER_CLIENT_ID=...
NAVER_CLIENT_SECRET=...
```

### 2. 서버 실행
```bash
docker compose up -d --build
```

### 3. 브랜치
```
feature/이승혁-backend
```

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
- 소셜 로그인 키는 절대 코드에 하드코딩 금지 (`.env` 파일 사용)
