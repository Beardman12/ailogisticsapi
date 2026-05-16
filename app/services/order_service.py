from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.database import Order, OrderItem, OrderParcel, OrderRecipient, OrderSender, User
from app.models.schemas import OrderCreateRequest
from app.services import chukou_service
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


def _decimal_to_float(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _build_submit_payload(order: Order) -> dict:
    if not order.sender or not order.recipient or not order.parcel or not order.items:
        raise HTTPException(status_code=400, detail="Order data is incomplete")

    ship_to_address = {
        "Country": order.recipient.country_code,
        "Province": order.recipient.province,
        "City": order.recipient.city,
        "District": order.recipient.district,
        "Street1": order.recipient.street1,
        "Street2": order.recipient.street2,
        "Postcode": order.recipient.postcode,
        "Contact": order.recipient.recipient_name,
        "Phone": f"{order.recipient.phone_code}{order.recipient.phone}",
        "Email": order.recipient.email,
        "IDNumber": order.recipient.id_number,
    }

    sender = {
        "Contact": order.sender.sender_name,
        "Phone": f"{order.sender.sender_phone_code}{order.sender.sender_phone}",
    }

    skus = []
    for item in order.items:
        skus.append(
            {
                "Sku": item.sku_code or f"ITEM-{item.line_no}",
                "Quantity": item.quantity,
                "Weight": order.parcel.weight_g_input,
                "DeclareValue": _decimal_to_float(item.unit_price_usd),
                "DeclareNameEn": item.goods_desc_en,
                "DeclareNameCn": item.goods_desc_cn,
                "ProductName": item.goods_desc_en,
                "Price": _decimal_to_float(item.unit_price_usd),
                "HsCode": item.hs_code,
            }
        )

    package = {
        "PackageId": order.package_id,
        "PlatformOrderNo": order.platform_order_no,
        "ServiceCode": order.service_code,
        "Weight": order.parcel.weight_g_input,
        "Length": _decimal_to_float(order.parcel.length_cm_input),
        "Width": _decimal_to_float(order.parcel.width_cm_input),
        "Height": _decimal_to_float(order.parcel.height_cm_input),
        "SellPrice": _decimal_to_float(order.total_amount),
        "SellPriceCurrency": order.payment_currency,
        "ImportTrackingNumber": order.sender.domestic_tracking_no,
        "Custom": order.user_remark,
        "Remark": order.user_remark,
        "ShipToAddress": {k: v for k, v in ship_to_address.items() if v not in (None, "")},
        "Sender": {k: v for k, v in sender.items() if v not in (None, "")},
        "Skus": skus,
    }

    payload = {
        "Location": order.location_code,
        "Package": {k: v for k, v in package.items() if v is not None},
        "Remark": order.user_remark,
        "SubmitLater": order.submit_later,
    }
    return {k: v for k, v in payload.items() if v is not None}


def _apply_status_snapshot(order: Order, status_payload: dict) -> None:
    chukou_status = status_payload.get("Status")
    tracking_number = status_payload.get("TrackingNumber")

    order.chukou_status = chukou_status
    order.tracking_number = tracking_number
    order.extra_track_number = status_payload.get("ExtraTrackNumber")
    order.shipping_provider = status_payload.get("ShippingProvider")

    create_failed = status_payload.get("CreateFailedReason")
    if isinstance(create_failed, dict):
        order.submit_failed_code = create_failed.get("ReasonCode")
        order.submit_failed_message = create_failed.get("ReasonText")
    else:
        order.submit_failed_code = None
        order.submit_failed_message = None

    if chukou_status == "Created" and tracking_number:
        order.order_status = "success"
        order.success_at = datetime.now()
        return

    if create_failed:
        order.order_status = "failed"
        return

    order.order_status = "creating"


def complete_order(db: Session, order: Order) -> None:
    if order.order_status in {"cancelled", "success"}:
        raise HTTPException(status_code=400, detail="Order cannot be completed")

    payload = _build_submit_payload(order)
    status_code, response_data = chukou_service.create_direct_express_order(payload)

    order.submitted_at = datetime.now()
    order.order_status = "submitted"
    order.chukou_status = "Submitted"
    order.submit_failed_code = None
    order.submit_failed_message = None

    # 200 means duplicate submit, 201 means accepted; both are non-error according to upstream API.
    if status_code not in {200, 201}:
        raise HTTPException(status_code=502, detail="Unexpected status from Chukou create order API")

    if isinstance(response_data, dict):
        errors = response_data.get("Errors")
        if isinstance(errors, list) and errors:
            first = errors[0]
            if isinstance(first, dict):
                order.submit_failed_code = first.get("Code")
                order.submit_failed_message = first.get("Message")
                order.order_status = "failed"
                db.commit()
                raise HTTPException(status_code=400, detail=order.submit_failed_message or "Submit failed")

    # Try a single status query right after submit. If upstream has not finished async processing,
    # keep local order in creating state and let later polling endpoint/scheduler continue.
    try:
        _, status_payload = chukou_service.get_direct_express_order_status(order.package_id)
        if isinstance(status_payload, dict):
            _apply_status_snapshot(order, status_payload)
        else:
            order.order_status = "creating"
    except HTTPException:
        order.order_status = "creating"

    db.commit()


def cancel_order(db: Session, order: Order) -> None:
    if order.order_status == "success":
        raise HTTPException(status_code=400, detail="Completed order cannot be cancelled")
    if order.order_status == "cancelled":
        return
    order.order_status = "cancelled"
    db.commit()
