from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse

from app.dependencies.security import get_request_user
from app.dtos.autoimmune_log import SymptomCheckCreateRequest, SymptomCheckResponse
from app.models.symptom_check_log import SymptomCheckLog, SymptomCode
from app.models.users import User
from app.services.autoimmune_log_service import SymptomCheckService

symptom_check_router = APIRouter(prefix="/symptom-checks", tags=["symptom-checks"])


def _build_response(log: SymptomCheckLog, red_flag_symptoms: list[SymptomCode]) -> dict:
    resp = SymptomCheckResponse.model_validate(log)
    resp.red_flag_symptoms = red_flag_symptoms
    return resp.model_dump()


@symptom_check_router.post("", response_model=SymptomCheckResponse, status_code=status.HTTP_201_CREATED)
async def create_symptom_check(
    body: SymptomCheckCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[SymptomCheckService, Depends(SymptomCheckService)],
) -> ORJSONResponse:
    log, red_flags = await service.create_check(user=user, data=body)
    return ORJSONResponse(_build_response(log, red_flags), status_code=status.HTTP_201_CREATED)


@symptom_check_router.get("", response_model=list[SymptomCheckResponse], status_code=status.HTTP_200_OK)
async def list_symptom_checks(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[SymptomCheckService, Depends(SymptomCheckService)],
) -> ORJSONResponse:
    items = await service.list_checks(user=user)
    return ORJSONResponse(
        [_build_response(log, red_flags) for log, red_flags in items],
        status_code=status.HTTP_200_OK,
    )
