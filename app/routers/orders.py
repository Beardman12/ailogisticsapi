from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.database import User
from app.models.schemas import ApiResponse, OrderCreateRequest, OrderListData, OrderListItem, OrderOut
from app.services import order_service
from app.utils.helpers import ok
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=ApiResponse)
def create_order(
    payload: OrderCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    order = order_service.create_order(db, current_user, payload)
    db.refresh(order)
    return ok(data=OrderOut.model_validate(order), message="Order created")


@router.get("", response_model=ApiResponse)
def list_orders(
    order_status: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    orders, total = order_service.list_orders(db, current_user, order_status, skip, limit)
    data = OrderListData(
        items=[OrderListItem.model_validate(item) for item in orders],
        total=total,
        skip=skip,
        limit=limit,
    )
    return ok(data=data)


@router.get("/{order_id}", response_model=ApiResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    order = order_service.get_order_for_user(db, current_user, order_id)
    return ok(data=OrderOut.model_validate(order))


@router.put("/{order_id}/complete", response_model=ApiResponse)
def complete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    order = order_service.get_order_for_user(db, current_user, order_id)
    order_service.complete_order(db, order)
    return ok(message="Order completed")


@router.put("/{order_id}/cancel", response_model=ApiResponse)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    order = order_service.get_order_for_user(db, current_user, order_id)
    order_service.cancel_order(db, order)
    return ok(message="Order cancelled")
