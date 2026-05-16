import hashlib

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.database import Order, User
from app.models.schemas import LoginData, LoginRequest, OrdersSummary, UserOut
from app.utils.security import create_access_token


def _mock_union_id(code: str) -> str:
    digest = hashlib.sha256(code.encode("utf-8")).hexdigest()[:24]
    return f"u_{digest}"


def login(db: Session, payload: LoginRequest) -> LoginData:
    union_id = _mock_union_id(payload.code)
    user = db.query(User).filter(User.union_id == union_id).first()

    if not user:
        user = User(
            union_id=union_id,
            nickname=payload.nickname,
            avatar_url=payload.avatar_url,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if payload.nickname is not None:
            user.nickname = payload.nickname
        if payload.avatar_url is not None:
            user.avatar_url = payload.avatar_url
        db.commit()
        db.refresh(user)

    total_count = db.query(func.count(Order.id)).filter(Order.user_id == user.id).scalar() or 0
    pending_count = (
        db.query(func.count(Order.id))
        .filter(Order.user_id == user.id, Order.order_status.in_(["draft", "submitted", "processing"]))
        .scalar()
        or 0
    )
    completed_count = (
        db.query(func.count(Order.id))
        .filter(Order.user_id == user.id, Order.order_status == "success")
        .scalar()
        or 0
    )

    token = create_access_token(user.id)
    return LoginData(
        token=token,
        user=UserOut.model_validate(user),
        orders_summary=OrdersSummary(
            total_count=total_count,
            pending_count=pending_count,
            completed_count=completed_count,
        ),
    )
