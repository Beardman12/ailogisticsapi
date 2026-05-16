from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.database import Order, OrderItem, OrderParcel, OrderRecipient, OrderSender, User
from app.models.schemas import OrderCreateRequest
from app.utils.helpers import generate_order_no


def create_order(db: Session, user: User, payload: OrderCreateRequest) -> Order:
    existing_order = db.query(Order).filter(Order.package_id == payload.order.package_id).first()
    if existing_order:
        raise HTTPException(status_code=400, detail="package_id already exists")

    order = Order(
        order_no=generate_order_no(),
        user_id=user.id,
        package_id=payload.order.package_id,
        platform_order_no=payload.order.platform_order_no,
        service_code=payload.order.service_code,
        location_code=payload.order.location_code,
        submit_later=payload.order.submit_later,
        order_status="submitted",
        payment_status="unpaid",
        payable_amount=payload.order.payable_amount,
        payment_currency=payload.order.payment_currency,
        user_remark=payload.order.user_remark,
        total_amount=payload.order.payable_amount,
    )
    db.add(order)
    db.flush()

    db.add(
        OrderSender(
            order_id=order.id,
            sender_name=payload.sender.sender_name,
            sender_phone_code=payload.sender.sender_phone_code,
            sender_phone=payload.sender.sender_phone,
            pickup_point_id=payload.sender.pickup_point_id,
            pickup_point_name=payload.sender.pickup_point_name,
            domestic_tracking_no=payload.sender.domestic_tracking_no,
        )
    )

    db.add(
        OrderRecipient(
            order_id=order.id,
            recipient_name=payload.recipient.recipient_name,
            phone_code=payload.recipient.phone_code,
            phone=payload.recipient.phone,
            country_code=payload.recipient.country_code,
            country_name=payload.recipient.country_name,
            province=payload.recipient.province,
            city=payload.recipient.city,
            district=payload.recipient.district,
            street1=payload.recipient.street1,
            street2=payload.recipient.street2,
            postcode=payload.recipient.postcode,
            email=payload.recipient.email,
            id_type=payload.recipient.id_type,
            id_number=payload.recipient.id_number,
        )
    )

    db.add(
        OrderParcel(
            order_id=order.id,
            cargo_type=payload.parcel.cargo_type,
            weight_g_input=payload.parcel.weight_g_input,
            length_cm_input=payload.parcel.length_cm_input,
            width_cm_input=payload.parcel.width_cm_input,
            height_cm_input=payload.parcel.height_cm_input,
        )
    )

    for item in payload.items:
        db.add(
            OrderItem(
                order_id=order.id,
                line_no=item.line_no,
                goods_desc_cn=item.goods_desc_cn,
                goods_desc_en=item.goods_desc_en,
                unit_price_usd=item.unit_price_usd,
                quantity=item.quantity,
                total_price_usd=item.total_price_usd,
                sku_code=item.sku_code,
                hs_code=item.hs_code,
            )
        )

    db.commit()
    db.refresh(order)
    return order


def list_orders(db: Session, user: User, status: str | None, skip: int, limit: int) -> tuple[list[Order], int]:
    query = db.query(Order).filter(Order.user_id == user.id)
    if status:
        query = query.filter(Order.order_status == status)

    total = query.count()
    items = query.order_by(Order.id.desc()).offset(skip).limit(limit).all()
    return items, total


def get_order_for_user(db: Session, user: User, order_id: int) -> Order:
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


def complete_order(db: Session, order: Order) -> None:
    if order.order_status in {"cancelled", "success"}:
        raise HTTPException(status_code=400, detail="Order cannot be completed")
    order.order_status = "success"
    db.commit()


def cancel_order(db: Session, order: Order) -> None:
    if order.order_status == "success":
        raise HTTPException(status_code=400, detail="Completed order cannot be cancelled")
    if order.order_status == "cancelled":
        return
    order.order_status = "cancelled"
    db.commit()
