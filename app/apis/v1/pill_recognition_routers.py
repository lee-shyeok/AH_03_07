from typing import Annotated

from fastapi import APIRouter, Depends, Query, UploadFile, status
from fastapi.responses import JSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.pill_recognition import PillConfirmRequest, PillRecognitionHistoryItem, PillRecognizeResponse
from app.models.users import User
from app.services.pill_recognition_service import PillRecognitionService

pill_router = APIRouter(prefix="/pills", tags=["pills"])


@pill_router.post("/recognize", status_code=status.HTTP_200_OK, response_model=PillRecognizeResponse)
async def recognize_pill(
    file: UploadFile,
    current_user: Annotated[User, Depends(get_request_user)],
    service: Annotated[PillRecognitionService, Depends(PillRecognitionService)],
) -> Response:
    result = await service.recognize(current_user, file)
    return Response(content=result.model_dump(mode="json"), status_code=status.HTTP_200_OK)


@pill_router.put(
    "/recognitions/{recognition_id}/confirm",
    status_code=status.HTTP_200_OK,
    response_model=PillRecognitionHistoryItem,
)
async def confirm_pill_recognition(
    recognition_id: int,
    body: PillConfirmRequest,
    current_user: Annotated[User, Depends(get_request_user)],
    service: Annotated[PillRecognitionService, Depends(PillRecognitionService)],
) -> Response:
    result = await service.confirm(current_user, recognition_id, body.selected_drug_name)
    return Response(content=result.model_dump(mode="json"), status_code=status.HTTP_200_OK)


@pill_router.get("/recognitions", status_code=status.HTTP_200_OK, response_model=list[PillRecognitionHistoryItem])
async def get_recognitions(
    current_user: Annotated[User, Depends(get_request_user)],
    service: Annotated[PillRecognitionService, Depends(PillRecognitionService)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=50)] = 10,
) -> Response:
    result = await service.get_recognitions(current_user, page, size)
    return Response(content=[r.model_dump(mode="json") for r in result], status_code=status.HTTP_200_OK)


@pill_router.get("/search", status_code=status.HTTP_200_OK)
async def search_drug(
    q: str,
    current_user: Annotated[User, Depends(get_request_user)],
) -> Response:
    from app.services.drug_info import DrugInfoService

    service = DrugInfoService()
    result = await service.search_drug(q)
    return Response(content=[d.model_dump(mode="json") for d in result.drugs], status_code=status.HTTP_200_OK)
