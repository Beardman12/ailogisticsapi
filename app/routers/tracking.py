from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.database import User
from app.models.schemas import ApiResponse
from app.services import chukou_service
from app.utils.helpers import ok
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/trackings", tags=["trackings"])


@router.get("/{tracking_number}", response_model=ApiResponse)
def get_tracking(
    tracking_number: str,
    lang: Literal["zh", "en"] = Query(default="zh"),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    _ = current_user
    try:
        _, tracking_data = chukou_service.get_tracking_info(tracking_number=tracking_number, lang=lang)
    except HTTPException as exc:
        raw_detail = str(exc.detail)
        if "800F1731" in raw_detail:
            raise HTTPException(status_code=404, detail="未查询到该单号的轨迹信息，请核对单号后重试") from exc
        raise
    return ok(data=tracking_data)