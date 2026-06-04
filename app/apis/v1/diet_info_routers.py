from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies.security import get_request_user
from app.dtos.diet_info import DietInfoResponse
from app.models.users import User
from app.services.diet_info import DietInfoService

diet_info_router = APIRouter(prefix="/diet-info", tags=["diet-info"])


@diet_info_router.get("", response_model=DietInfoResponse)
async def get_diet_info(
    drug_name: Annotated[str, Query(min_length=1, description="약품명 (예: 타크로리무스)")],
    user: Annotated[User, Depends(get_request_user)],
) -> DietInfoResponse:
    """약품명으로 공식 외부 링크 진입점 4개를 반환한다 (REQ-DIET-001).

    앱은 콘텐츠를 생성·수집·재가공하지 않으며, 공식 기관 검색 URL만 제공한다.
    """
    service = DietInfoService()
    return service.get_external_links(drug_name)
