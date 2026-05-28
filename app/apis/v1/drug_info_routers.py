from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies.security import get_request_user
from app.dtos.drug_info import DrugSearchResponse
from app.models.users import User
from app.services.drug_info import DrugInfoService

drug_info_router = APIRouter(prefix="/drug-info", tags=["drug-info"])


@drug_info_router.get("/search", response_model=DrugSearchResponse)
async def search_drug(
    drug_name: Annotated[str, Query(description="약품명 (예: 타이레놀)")],
    user: Annotated[User, Depends(get_request_user)],
    num_of_rows: Annotated[int, Query(ge=1, le=20, description="결과 개수")] = 5,
):
    """약품명으로 의약품 정보 검색 (REQ-PILL-003)"""
    service = DrugInfoService()
    return await service.search_drug(drug_name, num_of_rows)
