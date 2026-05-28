import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv('envs/.local.env')

logger = logging.getLogger(__name__)

SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", 587))
SMTP_USER     = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM    = os.getenv("EMAIL_FROM", "")

if not all([SMTP_USER, SMTP_PASSWORD, EMAIL_FROM]):
    logger.warning("SMTP 환경변수가 설정되지 않았습니다.")


def send_verification_email(to: str, code: str) -> None:
    if not all([SMTP_USER, SMTP_PASSWORD, EMAIL_FROM]):
        raise RuntimeError("SMTP 설정이 없습니다.")

    subject = "[MedApp] 이메일 인증코드 안내"
    body = f"""
    <html><body>
    <h2>이메일 인증코드</h2>
    <p>아래 6자리 인증코드를 입력해주세요.</p>
    <h1 style="letter-spacing:8px; color:#2563eb;">{code}</h1>
    <p style="color:#888;">인증코드는 <strong>5분간</strong> 유효합니다.</p>
    <hr>
    <p style="font-size:12px; color:#aaa;">본 메일은 발신 전용입니다.</p>
    </body></html>
    """

    message = MIMEMultipart("alternative")
    message["From"] = EMAIL_FROM
    message["To"]   = to
    message["Subject"] = subject
    message.attach(MIMEText(body, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, to, message.as_string())
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP 인증 실패")
        raise
    except smtplib.SMTPException as e:
        logger.error(f"SMTP 오류: {e}")
        raise
    except Exception as e:
        logger.error(f"이메일 발송 중 예외: {e}")
        raise
