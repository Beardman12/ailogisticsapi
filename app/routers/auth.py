from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.database import User
from app.models.schemas import ApiResponse, LoginRequest, UserOut
from app.services import auth_service
from app.utils.helpers import ok
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=ApiResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> ApiResponse:
    data = auth_service.login(db, payload)
    return ok(data=data, message="Login successful")


@router.get("/profile", response_model=ApiResponse)
def profile(current_user: User = Depends(get_current_user)) -> ApiResponse:
    return ok(data=UserOut.model_validate(current_user))
