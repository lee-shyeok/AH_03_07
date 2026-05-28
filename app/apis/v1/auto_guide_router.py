"""REQ-AUTO-005 맞춤 안내문 수동 생성 엔드포인트."""

from fastapi import APIRouter, Depends

from app.auto_guide.schema import OrchestratorResult
from app.auto_guide.service import orchestrate
from app.dependencies.security import get_request_user
from app.models.users import User

auto_guide_router = APIRouter(prefix="/guide", tags=["guide"])


@auto_guide_router.post("/generate", response_model=OrchestratorResult)
async def generate_guide_endpoint(
    current_user: User = Depends(get_request_user),
) -> OrchestratorResult:
    """맞춤 안내문 수동 생성 (REQ-AUTO-005).

    자가면역 모드 + 질환 등록 + 입력 소스 조건이 충족되어야 안내문이 생성된다.
    조건 미충족 시 TRIGGER_NOT_MET 상태를 반환한다.
    """
    return await orchestrate(user_id=current_user.id)
