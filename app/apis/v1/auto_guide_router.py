"""REQ-AUTO-005/006 맞춤 안내문 엔드포인트."""

from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.auto_guide.schema import (
    BlockedReason,
    GuideGenerationJobCreated,
    GuideGenerationJobStatusResponse,
    GuideSectionItem,
    GuideSectionType,
    GuideSourceItem,
    OrchestratorStatus,
)
from app.auto_guide.service import orchestrate
from app.core.logger import default_logger as logger
from app.dependencies.security import get_request_user
from app.models.auto_guide import AutoGuide, AutoGuideStatus
from app.models.guide_generation_job import GuideGenerationJob, GuideGenerationJobStatus
from app.models.users import User
from app.services.knowledge_source_validator import get_source_url

auto_guide_router = APIRouter(prefix="/guides", tags=["guides"])


async def _run_generation_job(job_id: int) -> None:
    job = await GuideGenerationJob.get_or_none(id=job_id)
    if job is None:
        logger.error("guide_generation_job_missing job_id=%s", job_id)
        return
    try:
        job.status = GuideGenerationJobStatus.PROCESSING
        await job.save()

        result = await orchestrate(user_id=job.user_id)
        job.trigger_emergency_modal = result.trigger_emergency_modal  # 모든 분기 이전 = 안전 신호 누락 방지

        if result.orchestrator_status == OrchestratorStatus.GENERATED and result.guide is not None:
            guide = result.guide
            saved = await AutoGuide.create(
                user_id=job.user_id,
                status=AutoGuideStatus.GENERATED,
                medication_general=guide.medication_general,
                side_effect_monitoring=guide.side_effect_monitoring,
                lifestyle_info=guide.lifestyle_info,
                symptom_summary=guide.symptom_summary,
                sources=[s.model_dump() for s in guide.sources],
                disclaimer=guide.disclaimer,
            )
            job.guide_id = saved.id
            job.status = GuideGenerationJobStatus.COMPLETED
        elif result.orchestrator_status == OrchestratorStatus.BLOCKED_HIGH_RISK:
            job.status = GuideGenerationJobStatus.BLOCKED
            job.blocked_reason = (
                BlockedReason.NEEDS_RECHECK.value
                if result.needs_recheck
                else BlockedReason.HIGH_RISK_GATE_BLOCKED.value
            )
        elif result.orchestrator_status == OrchestratorStatus.TRIGGER_NOT_MET:
            job.status = GuideGenerationJobStatus.FAILED
            missing = ", ".join(result.trigger_check.missing_conditions) if result.trigger_check else ""
            job.error_message = f"TRIGGER_NOT_MET: {missing}"
        else:  # GENERATION_FAILED 및 예기치 못한 상태
            job.status = GuideGenerationJobStatus.FAILED
            job.error_message = "GENERATION_FAILED"
        await job.save()
    except Exception:
        logger.exception("guide_generation_job_failed job_id=%s", job_id)
        job.status = GuideGenerationJobStatus.FAILED
        job.error_message = "internal error"
        await job.save()


@auto_guide_router.post("/generate", response_model=GuideGenerationJobCreated, status_code=202)
async def generate_guide_endpoint(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_request_user),
) -> GuideGenerationJobCreated:
    """맞춤 안내문 비동기 생성 요청 (REQ-AUTO-005).

    job을 생성하고 즉시 202를 반환한다. 실제 생성은 백그라운드에서 실행된다.
    """
    job = await GuideGenerationJob.create(
        user_id=current_user.id,
        status=GuideGenerationJobStatus.PENDING,
        trigger_type="manual",
    )
    background_tasks.add_task(_run_generation_job, job.id)
    return GuideGenerationJobCreated(job_id=job.id, status=job.status)


guide_generation_job_router = APIRouter(prefix="/guide-generation-jobs", tags=["guides"])


@guide_generation_job_router.get("/{job_id}", response_model=GuideGenerationJobStatusResponse)
async def get_generation_job(
    job_id: int,
    current_user: User = Depends(get_request_user),
) -> GuideGenerationJobStatusResponse:
    """안내문 생성 작업 상태 조회 (REQ-AUTO-005, 안내문-002)."""
    job = await GuideGenerationJob.get_or_none(id=job_id, user_id=current_user.id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return GuideGenerationJobStatusResponse(
        status=job.status,
        guide_id=job.guide_id,
        blocked_reason=job.blocked_reason,
        error_message=job.error_message,
        trigger_emergency_modal=job.trigger_emergency_modal,
    )


@auto_guide_router.get("/{guide_id}/sources", response_model=list[GuideSourceItem])
async def get_guide_sources(
    guide_id: int,
    current_user: User = Depends(get_request_user),
) -> list[GuideSourceItem]:
    """안내문 출처 목록 조회 (REQ-AUTO-005)."""
    guide = await AutoGuide.get_or_none(id=guide_id, user_id=current_user.id, deleted_at=None)
    if guide is None:
        raise HTTPException(status_code=404, detail="Guide not found")
    return [
        GuideSourceItem(
            citation_order=i + 1,
            source_title=s["title"],
            source_org=s["organization"],
            source_page=s.get("page"),
            source_url=get_source_url(s["organization"]),
            used_for_section=s.get("section"),
        )
        for i, s in enumerate(guide.sources)
    ]


@auto_guide_router.get("/{guide_id}/sections", response_model=list[GuideSectionItem])
async def get_guide_sections(
    guide_id: int,
    current_user: User = Depends(get_request_user),
) -> list[GuideSectionItem]:
    """안내문 섹션 목록 조회 (REQ-AUTO-006)."""
    guide = await AutoGuide.get_or_none(id=guide_id, user_id=current_user.id, deleted_at=None)
    if guide is None:
        raise HTTPException(status_code=404, detail="Guide not found")

    monitoring = guide.side_effect_monitoring
    side_effect_content = "\n".join(monitoring) if isinstance(monitoring, list) else monitoring

    return [
        GuideSectionItem(
            section_type=GuideSectionType.MEDICATION_GENERAL,
            section_title="복약 일반 정보",
            section_content=guide.medication_general,
            display_order=1,
        ),
        GuideSectionItem(
            section_type=GuideSectionType.SIDE_EFFECT,
            section_title="부작용 모니터링",
            section_content=side_effect_content,
            display_order=2,
        ),
        GuideSectionItem(
            section_type=GuideSectionType.LIFESTYLE,
            section_title="생활 정보",
            section_content=guide.lifestyle_info,
            display_order=3,
        ),
        GuideSectionItem(
            section_type=GuideSectionType.SYMPTOM_SUMMARY,
            section_title="증상 요약",
            section_content=guide.symptom_summary,
            display_order=4,
        ),
    ]


def _serialize_guide(guide: AutoGuide) -> dict:
    """auto_guides 레코드를 응답 JSON으로 직렬화 (REQ-GUIDE-003/004).

    필드명은 auto_guides 컬럼명을 그대로 사용한다(프론트도 동일 키로 파싱).
    id는 정수(BigInt)로 내려간다.
    """
    return {
        "id": guide.id,
        "status": str(guide.status),
        "created_at": guide.created_at.isoformat() if guide.created_at else None,
        "medication_general": guide.medication_general,
        "side_effect_monitoring": guide.side_effect_monitoring,
        "lifestyle_info": guide.lifestyle_info,
        "symptom_summary": guide.symptom_summary,
        "sources": guide.sources,
        "disclaimer": guide.disclaimer,
    }


@auto_guide_router.get("")
async def list_my_guides(
    current_user: User = Depends(get_request_user),
) -> dict:
    """내 안내문 목록 조회 (REQ-GUIDE-003).

    auto_guides 테이블에서 본인 것만 최신순으로 반환한다.
    """
    guides = await AutoGuide.filter(user_id=current_user.id, deleted_at=None).order_by("-created_at").all()
    return {"items": [_serialize_guide(g) for g in guides]}


@auto_guide_router.get("/{guide_id}")
async def get_guide_detail(
    guide_id: int,
    current_user: User = Depends(get_request_user),
) -> dict:
    """안내문 상세 조회 (REQ-GUIDE-004).

    guide_id는 정수(BigInt). 본인 소유가 아니면 404.
    """
    guide = await AutoGuide.get_or_none(id=guide_id, user_id=current_user.id, deleted_at=None)
    if guide is None:
        raise HTTPException(status_code=404, detail="Guide not found")
    return _serialize_guide(guide)


@auto_guide_router.delete("/{guide_id}", status_code=204)
async def delete_guide(
    guide_id: int,
    current_user: User = Depends(get_request_user),
) -> None:
    """안내문 소프트 삭제 (REQ-AUTO-005)."""
    guide = await AutoGuide.get_or_none(id=guide_id, user_id=current_user.id, deleted_at=None)
    if guide is None:
        raise HTTPException(status_code=404, detail="Guide not found")
    guide.deleted_at = datetime.now(tz=UTC)
    await guide.save(update_fields=["deleted_at"])
