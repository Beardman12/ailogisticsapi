from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.database import Order, OrderItem, User
from app.models.schemas import OrderCreateRequest
from app.utils.helpers import generate_order_no


def create_order(db: Session, user: User, payload: OrderCreateRequest) -> Order:
    order = Order(
        order_no=generate_order_no(),
        user_id=user.id,
        total_amount=payload.total_amount,
        status="pending",
    )
    db.add(order)
    db.flush()

    for item in payload.items:
        db.add(
            OrderItem(
                order_id=order.id,
                product_name=item.product_name,
                quantity=item.quantity,
                price=item.price,
            )
        )

    db.commit()
    db.refresh(order)
    return order


def list_orders(db: Session, user: User, status: str | None, skip: int, limit: int) -> tuple[list[Order], int]:
    query = db.query(Order).filter(Order.user_id == user.id)
    if status:
        query = query.filter(Order.status == status)

    total = query.count()
    items = query.order_by(Order.id.desc()).offset(skip).limit(limit).all()
    return items, total


def get_order_for_user(db: Session, user: User, order_id: int) -> Order:
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


def complete_order(db: Session, order: Order) -> None:
    if order.status in {"cancelled", "completed"}:
        raise HTTPException(status_code=400, detail="Order cannot be completed")
    order.status = "completed"
    db.commit()


def cancel_order(db: Session, order: Order) -> None:
    if order.status == "completed":
        raise HTTPException(status_code=400, detail="Completed order cannot be cancelled")
    if order.status == "cancelled":
        return
    order.status = "cancelled"
    db.commit()
