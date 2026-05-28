import base64
import os
import time
import uuid

import httpx
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("CLOVA_OCR_SECRET_KEY")
API_URL = os.getenv("CLOVA_OCR_API_URL")


async def recognize_image(image_bytes: bytes, format: str = "jpg") -> str:
    encoded = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "version": "V2",
        "requestId": str(uuid.uuid4()),
        "timestamp": int(time.time() * 1000),
        "images": [
            {
                "format": format,
                "name": "ocr_image",
                "data": encoded,
            }
        ],
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            API_URL,
            headers={
                "Content-Type": "application/json",
                "X-OCR-SECRET": SECRET_KEY,
            },
            json=payload,
            timeout=30.0,
        )

    response.raise_for_status()
    result = response.json()

    fields = result["images"][0].get("fields", [])
    return " ".join(f["inferText"] for f in fields)
