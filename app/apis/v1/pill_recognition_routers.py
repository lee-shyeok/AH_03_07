from typing import Annotated

from fastapi import APIRouter, Depends, Query, UploadFile, status
from fastapi.responses import JSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.pill_recognition import PillRecognitionHistoryItem, PillRecognizeResponse
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


@pill_router.get("/recognitions", status_code=status.HTTP_200_OK, response_model=list[PillRecognitionHistoryItem])
async def get_recognitions(
    current_user: Annotated[User, Depends(get_request_user)],
    service: Annotated[PillRecognitionService, Depends(PillRecognitionService)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=50)] = 10,
) -> Response:
    result = await service.get_recognitions(current_user, page, size)
    return Response(content=[r.model_dump(mode="json") for r in result], status_code=status.HTTP_200_OK)