# 🏥 AI 헬스케어 앱 - 백엔드 수정사항

> AI-HealthCare-03 | 7조 | 이승혁 담당 백엔드 수정

## 🔧 수정 사항

### 1. DB 연결 설정 수정
- `DATABASE_URL` 호스트를 `127.0.0.1` → `mysql` 로 변경 (Docker 컨테이너 통신)
- `REDIS_URL` 호스트를 `localhost` → `redis` 로 변경

### 2. bcrypt 버그 수정
- `passlib[bcrypt]` 버전 충돌로 인한 `ValueError: password cannot be longer than 72 bytes` 오류 수정
- `requirements.txt` 에 `bcrypt==4.0.1` 고정 버전 추가
- `security.py` 의 `hash_password` 함수에서 비밀번호 72자 제한 처리

### 3. Redis 인증 설정
- `REDIS_PASSWORD` 환경변수 추가
- `REDIS_URL` 에 비밀번호 포함 형식으로 수정

### 4. MySQL 초기화 설정
- `MYSQL_ROOT_PASSWORD`, `MYSQL_DATABASE` 환경변수 추가

## 🛠 기술 스택

```
FastAPI (Python)
├── MySQL 8.0
├── Redis (Alpine)
├── Docker + Docker Compose
├── Nginx (리버스 프록시)
└── Celery (비동기 작업)
```

## 🚀 실행 방법

### 1. 환경변수 설정
`envs/.local.env` 파일 생성:
```
DATABASE_URL=mysql+pymysql://root:비번@mysql:3306/mydb
REDIS_URL=redis://:비번@redis:6379/0
REDIS_PASSWORD=비번
MYSQL_ROOT_PASSWORD=비번
MYSQL_DATABASE=mydb
SECRET_KEY=직접설정
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=이메일
SMTP_PASSWORD=앱비밀번호
OPENAI_API_KEY=키입력
```

### 2. Docker 실행
```bash
docker compose down
docker compose up -d --build
```

### 3. 서버 확인
```bash
docker ps
# fastapi1, mysql, redis, nginx, ai-worker 전부 Up 확인

# API 문서
http://localhost/api/docs
```

## 📡 주요 수정 API

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/v1/notification-settings` | GET | 알림 설정 조회 |
| `/v1/notification-settings` | PATCH | 알림 설정 수정 |
| `/v1/reminders` | GET | 복약 알림 목록 |
| `/v1/reminders` | POST | 복약 알림 등록 |
| `/v1/reminders/{id}` | PATCH | 복약 알림 수정 |
| `/v1/reminders/{id}` | DELETE | 복약 알림 삭제 |
