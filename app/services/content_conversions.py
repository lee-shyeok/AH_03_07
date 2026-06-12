import json
import os
import re
from datetime import datetime
from uuid import UUID

from gtts import gTTS
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

from app.core import config
from app.dtos.content_conversions import ContentConversionResponse
from app.models.auto_guide import AutoGuide
from app.models.content_conversions import ConversionStatus, ConversionType
from app.repositories.content_conversion_repository import ContentConversionRepository


class ContentConversionService:
    """콘텐츠 변환 비즈니스 로직 (CONT-001 카드뉴스, CONT-002 TTS)"""

    def __init__(self):
        self.repo = ContentConversionRepository()
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.output_dir = "/app/static/cards"
        self.audio_dir = "/app/static/audio"
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)

    async def extract_card_texts(self, guide_content: str) -> list[str]:
        """LLM으로 가이드 → 카드 3장 핵심 문구 추출"""
        prompt = f"""다음 건강 가이드를 카드뉴스 3장으로 만들기 위해
각 카드의 핵심 문구를 추출해주세요.

가이드:
{guide_content}

JSON 배열로만 반환해주세요. 각 문구는 한 줄 (20자 이내) 권장:
["카드1 핵심 문구", "카드2 핵심 문구", "카드3 핵심 문구"]"""

        response = self.openai_client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )

        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        return json.loads(content)

    def create_card_image(self, text: str, card_number: int, conversion_id: str) -> str:
        """Pillow로 카드 이미지 생성 (1080x1080)"""
        img = Image.new("RGB", (1080, 1080), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
        except Exception:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        draw.text((540, 100), f"{card_number} / 3", fill=(150, 150, 150), font=small_font, anchor="mm")

        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if len(test_line) <= 15:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        y_start = 540 - (len(lines) * 35)
        for i, line in enumerate(lines):
            draw.text((540, y_start + i * 80), line, fill=(0, 0, 0), font=font, anchor="mm")

        draw.text((540, 980), "AI Healthcare", fill=(180, 180, 180), font=small_font, anchor="mm")

        filename = f"{conversion_id}_{card_number}.png"
        filepath = os.path.join(self.output_dir, filename)
        img.save(filepath)

        return f"/static/cards/{filename}"

    async def create_card_news(self, user_id: UUID, guide_id: int) -> ContentConversionResponse:
        """카드뉴스 생성 (CONT-001 MVP)"""
        conversion = await self.repo.create(
            user_id=user_id,
            guide_id=guide_id,
            conversion_type=ConversionType.CARD,
        )

        try:
            guide = await AutoGuide.get_or_none(id=guide_id)
            if not guide:
                raise Exception("가이드를 찾을 수 없습니다")

            conversion.status = ConversionStatus.PROCESSING
            await conversion.save()

            guide_content = (
                f"{guide.medication_general or ''}\n{guide.symptom_summary or ''}\n{guide.lifestyle_info or ''}"
            )
            card_texts = await self.extract_card_texts(guide_content)

            file_urls = []
            for i, text in enumerate(card_texts[:3], 1):
                url = self.create_card_image(text, i, str(conversion.id))
                file_urls.append(url)

            conversion.status = ConversionStatus.COMPLETED
            conversion.file_urls = file_urls
            conversion.completed_at = datetime.now()
            await conversion.save()

        except Exception as e:
            conversion.status = ConversionStatus.FAILED
            conversion.error_message = str(e)
            await conversion.save()

        response = ContentConversionResponse.model_validate(conversion)
        response.guide_id = guide_id
        return response

    def clean_text_for_tts(self, text: str) -> str:
        """TTS용 텍스트 정제 (마크다운 제거 등)"""
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"\*+(.+?)\*+", r"\1", text)
        text = re.sub(r"_+(.+?)_+", r"\1", text)
        text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
        text = re.sub(r"```.+?```", "", text, flags=re.DOTALL)
        text = re.sub(r"`(.+?)`", r"\1", text)
        text = re.sub(r"\n{2,}", "\n", text)
        return text.strip()

    async def create_tts(self, user_id: UUID, guide_id: int) -> ContentConversionResponse:
        """가이드 → 음성 변환 (CONT-002 MVP)"""
        conversion = await self.repo.create(
            user_id=user_id,
            guide_id=guide_id,
            conversion_type=ConversionType.TTS,
        )

        try:
            guide = await AutoGuide.get_or_none(id=guide_id)
            if not guide:
                raise Exception("가이드를 찾을 수 없습니다")

            conversion.status = ConversionStatus.PROCESSING
            await conversion.save()

            guide_content = (
                f"{guide.medication_general or ''}\n{guide.symptom_summary or ''}\n{guide.lifestyle_info or ''}"
            )
            clean_text = self.clean_text_for_tts(guide_content)

            tts = gTTS(text=clean_text, lang="ko", slow=False)

            filename = f"{conversion.id}.mp3"
            filepath = os.path.join(self.audio_dir, filename)
            tts.save(filepath)

            file_url = f"/static/audio/{filename}"

            conversion.status = ConversionStatus.COMPLETED
            conversion.file_url = file_url
            conversion.completed_at = datetime.now()
            await conversion.save()

        except Exception as e:
            conversion.status = ConversionStatus.FAILED
            conversion.error_message = str(e)
            await conversion.save()

        response = ContentConversionResponse.model_validate(conversion)
        response.guide_id = guide_id
        return response
