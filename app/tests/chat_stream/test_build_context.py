from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tortoise.contrib.test import TestCase

from app.models.chat_message import ChatMessage, MessageRole
from app.models.chat_session import ChatMode, ChatSession
from app.models.health_guides import GuideStatus, GuideType, HealthGuideContent
from app.models.user_disease import DiseaseCode, UserDisease
from app.models.users import Gender, User
from app.services.chat_stream_service import ChatStreamService


async def _make_user(email: str, phone: str) -> User:
    return await User.create(
        email=email,
        hashed_password="hashed",
        name="테스터",
        gender=Gender.FEMALE,
        birthday="1990-01-01",
        phone_number=phone,
    )


async def _make_session(user: User, mode: ChatMode = ChatMode.GENERAL) -> ChatSession:
    return await ChatSession.create(user=user, mode=mode)


class TestBuildContext(TestCase):
    async def test_history_window_limits_to_10_messages(self):
        """12개 메시지 있을 때 최근 10개(사용자 5턴+챗봇 5턴)만 컨텍스트에 포함"""
        user = await _make_user("ctx1@test.com", "01011110001")
        session = await _make_session(user)
        for i in range(12):
            role = MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT
            await ChatMessage.create(
                session=session,
                role=role,
                content=f"msg{i}",
                rag_sources=[],
                blocked_by_filter=False,
            )
        service = ChatStreamService()
        _, history = await service._build_context(session, user)
        assert len(history) == 10

    async def test_system_prompt_includes_mode_and_disease(self):
        """시스템 프롬프트에 세션 모드와 등록 질환(SLE) 포함"""
        user = await _make_user("ctx2@test.com", "01011110002")
        session = await _make_session(user, mode=ChatMode.AUTOIMMUNE)
        await UserDisease.create(user=user, disease_code=DiseaseCode.SLE)
        service = ChatStreamService()
        system_prompt, _ = await service._build_context(session, user)
        assert "AUTOIMMUNE" in system_prompt
        assert "SLE" in system_prompt

    async def test_system_prompt_includes_recent_guide_and_excludes_old(self):
        """30일 이내 완료 가이드는 포함, 31일 초과 가이드는 제외"""
        user = await _make_user("ctx3@test.com", "01011110003")
        session = await _make_session(user)
        guide = await HealthGuideContent.create(
            user=user,
            guide_type=GuideType.GENERAL,
            status=GuideStatus.COMPLETED,
            user_question="q",
            guide_content="최근가이드내용",
        )
        service = ChatStreamService()

        system_prompt, _ = await service._build_context(session, user)
        assert "최근가이드내용" in system_prompt

        # 31일 전으로 변경 → 제외 대상
        old_time = datetime.now(tz=UTC) - timedelta(days=31)
        await HealthGuideContent.filter(id=guide.id).update(created_at=old_time)
        system_prompt_old, _ = await service._build_context(session, user)
        assert "최근가이드내용" not in system_prompt_old

    async def test_context_builds_normally_without_guide(self):
        """가이드 없어도 시스템 프롬프트와 빈 히스토리 정상 반환"""
        user = await _make_user("ctx4@test.com", "01011110004")
        session = await _make_session(user)
        service = ChatStreamService()
        system_prompt, history = await service._build_context(session, user)
        assert "당신은 의료 정보 안내 어시스턴트입니다" in system_prompt
        assert history == []
