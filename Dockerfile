FROM python:3.10-slim

WORKDIR /app

# 패키지 먼저 설치 (레이어 캐시 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사 (.dockerignore로 .env 파일 제외됨)
COPY . .

# [수정] 비루트 사용자 생성 및 전환
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
