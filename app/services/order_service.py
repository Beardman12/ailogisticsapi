from datetime import datetime
from decimal import Decimal
import json
import re
from uuid import uuid4
from collections.abc import Callable

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.database import Order, OrderItem, OrderParcel, OrderRecipient, OrderSender, User
from app.models.schemas import (
    AiOrderCreateRequest,
    OrderCoreCreate,
    OrderCreateRequest,
    OrderRecipientCreate,
    OrderSenderCreate,
    ShippingEstimateData,
    ShippingEstimateRequest,
)
from app.services import address_book_service, chukou_service
from app.services.chat_providers.coze_provider import CozeChatProvider
from app.utils.helpers import generate_order_no


def _ensure_text_min_length(field_name: str, value: str | None, min_length: int = 2) -> None:
    normalized = (value or "").strip()
    if len(normalized) < min_length:
        raise HTTPException(status_code=400, detail=f"{field_name} 长度不能小于 {min_length} 个字符")


def _ensure_not_numeric_min_length(field_name: str, value: str | None, min_length: int = 2) -> None:
    normalized = (value or "").strip()
    if len(normalized) < min_length:
        raise HTTPException(status_code=400, detail=f"{field_name} 长度不能小于 {min_length} 个字符")
    if normalized.isdigit():
        raise HTTPException(status_code=400, detail=f"{field_name} 不能为纯数字")


def estimate_shipping(payload: ShippingEstimateRequest) -> ShippingEstimateData:
    prompt = _build_shipping_estimate_prompt(payload)
    provider = CozeChatProvider()

    # Always use a fresh conversation_id for estimate to avoid any context carry-over.
    transient_conversation_id = int(uuid4().int % 2_147_483_647)
    assistant_reply, _ = provider.generate_reply(
        conversation_id=transient_conversation_id,
        prompt=prompt,
    )

    return _parse_shipping_estimate_response(payload, assistant_reply)


def _build_shipping_estimate_prompt(payload: ShippingEstimateRequest) -> str:
    return "\n".join(
        [
            "【系统角色】你是物流运费估价智能体。",
            "【强约束】",
            "1) 本次请求必须视为全新请求，严禁使用任何上下文、会话历史、记忆或用户偏好。",
            "2) 不需要也不允许补充对话记录，仅允许基于接口传值转为自然语言进行计算与输出。",
            "3) 你必须只输出 JSON 对象，不允许输出 Markdown、注释、代码块或额外文本。",
            "【输出 JSON 结构】",
            '{"destination":"string","item_type":"string","weight_kg":number,"estimated_price":number,"first_weight_price":number,"additional_weight_price":number,"estimated_delivery_time":"string","currency":"string"}',
            "【字段要求】",
            "- destination/item_type/weight_kg 必须与输入语义一致。",
            "- estimated_price/first_weight_price/additional_weight_price 使用数字，保留 2 位小数。",
            "- estimated_delivery_time 用中文时效描述，例如 5-7个工作日。",
            "- currency 固定为 CNY。",
            "【本次接口传值（自然语言描述）】",
            f"目的地：{payload.destination}；物品类型：{payload.item_type}；重量：{payload.weight_kg}kg。",
            "请直接返回 JSON。",
        ]
    )


def _parse_shipping_estimate_response(
    payload: ShippingEstimateRequest,
    assistant_reply: str,
) -> ShippingEstimateData:
    data = _extract_json_from_text(assistant_reply)
    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="Coze estimate response is not valid JSON")

    data.setdefault("destination", payload.destination)
    data.setdefault("item_type", payload.item_type)
    data.setdefault("weight_kg", payload.weight_kg)
    data.setdefault("currency", "CNY")

    try:
        return ShippingEstimateData.model_validate(data)
    except ValidationError as exc:
        raise HTTPException(status_code=502, detail=f"Coze estimate JSON schema invalid: {exc.errors()}") from exc


def _extract_json_from_text(raw_text: str) -> dict | None:
    text = (raw_text or "").strip()
    if not text:
        return None

    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass

    fence_match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
    if fence_match:
        try:
            parsed = json.loads(fence_match.group(1))
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            pass

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            parsed = json.loads(text[start : end + 1])
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def create_order(db: Session, user: User, payload: OrderCreateRequest) -> Order:
    existing_order = db.query(Order).filter(Order.package_id == payload.order.package_id).first()
    if existing_order:
        raise HTTPException(status_code=400, detail="package_id already exists")

    _ensure_not_numeric_min_length("recipient.street1", payload.recipient.street1)

    order = Order(
        order_no=generate_order_no(),
        user_id=user.id,
        package_id=payload.order.package_id,
        platform_order_no=payload.order.platform_order_no,
        service_code=settings.chukou_service_code,
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

    # Immediately submit to CHUKOU once local order data is created and validated.
    complete_order(db, order)
    db.refresh(order)
    return order


def ai_create_order(db: Session, user: User, payload: AiOrderCreateRequest) -> Order:
    default_sender = address_book_service.get_default_sender_profile(db, user)
    if not default_sender:
        raise HTTPException(status_code=422, detail="Default sender profile is required")

    default_recipient = address_book_service.get_default_recipient_profile(db, user)
    if not default_recipient:
        raise HTTPException(status_code=422, detail="Default recipient profile is required")

    if not default_recipient.postcode:
        raise HTTPException(status_code=422, detail="Default recipient postcode is required")

    full_payload = OrderCreateRequest(
        order=OrderCoreCreate(
            package_id=payload.package_id or generate_order_no(),
            platform_order_no=payload.platform_order_no,
            location_code=payload.location_code,
            submit_later=payload.submit_later,
            user_remark=payload.user_remark,
            payable_amount=payload.payable_amount,
            payment_currency=payload.payment_currency,
        ),
        sender=OrderSenderCreate(
            sender_name=default_sender.sender_name,
            sender_phone_code=default_sender.sender_phone_code,
            sender_phone=default_sender.sender_phone,
            pickup_point_id=default_sender.pickup_point_id,
            pickup_point_name=default_sender.pickup_point_name,
            domestic_tracking_no=default_sender.domestic_tracking_no,
        ),
        recipient=OrderRecipientCreate(
            recipient_name=default_recipient.recipient_name,
            phone_code=default_recipient.phone_code,
            phone=default_recipient.phone,
            country_code=default_recipient.country_code,
            country_name=default_recipient.country_name,
            province=default_recipient.province,
            city=default_recipient.city,
            district=default_recipient.district,
            street1=default_recipient.street1,
            street2=default_recipient.street2,
            postcode=default_recipient.postcode,
            email=default_recipient.email,
            id_type=default_recipient.id_type,
            id_number=default_recipient.id_number,
        ),
        parcel=payload.parcel,
        items=payload.items,
    )
    return create_order(db, user, full_payload)


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


def _build_chukou_package_id(order_id: int) -> str:
    return f"mini{order_id:010d}"


def _build_submit_payload(order: Order) -> dict:
    if not order.sender or not order.recipient or not order.parcel or not order.items:
        raise HTTPException(status_code=400, detail="Order data is incomplete")

    _ensure_not_numeric_min_length("recipient.street1", order.recipient.street1)

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

    skus = []
    for item in order.items:
        _ensure_text_min_length("DeclareNameEn", item.goods_desc_en)
        _ensure_text_min_length("DeclareNameCn", item.goods_desc_cn)
        _ensure_text_min_length("ProductName", item.goods_desc_en)
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

    chukou_package_id = _build_chukou_package_id(order.id)

    package = {
        "PackageId": chukou_package_id,
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
        "Skus": skus,
    }

    payload = {
        "Location": order.location_code,
        "Package": {k: v for k, v in package.items() if v is not None},
        "Remark": order.user_remark,
        "SubmitLater": order.submit_later,
    }
    cleaned_payload = {k: v for k, v in payload.items() if v is not None}
    if cleaned_payload.get("SubmitLater") is False:
        cleaned_payload.pop("SubmitLater", None)
    return cleaned_payload


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


def complete_order(
    db: Session,
    order: Order,
    *,
    debug_collector: Callable[[dict], None] | None = None,
) -> None:
    if order.order_status in {"cancelled", "success"}:
        raise HTTPException(status_code=400, detail="Order cannot be completed")

    payload = _build_submit_payload(order)
    if debug_collector:
        debug_collector({"stage": "submit_request", "payload": payload})

    try:
        status_code, response_data = chukou_service.create_direct_express_order(payload)
        if debug_collector:
            debug_collector(
                {
                    "stage": "submit_response",
                    "status_code": status_code,
                    "response_data": response_data,
                }
            )
    except HTTPException as exc:
        if debug_collector:
            debug_collector(
                {
                    "stage": "submit_error",
                    "status_code": exc.status_code,
                    "detail": str(exc.detail),
                }
            )
        raise

    order.submitted_at = datetime.now()
    order.order_status = "submitted"
    order.chukou_status = "Submitted"
    order.submit_failed_code = None
    order.submit_failed_message = None

    # 200 means duplicate submit, 201 means accepted; both are non-error according to upstream API.
    if status_code not in {200, 201}:
        if debug_collector:
            debug_collector(
                {
                    "stage": "submit_unexpected_status",
                    "status_code": status_code,
                    "response_data": response_data,
                }
            )
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
                if debug_collector:
                    debug_collector(
                        {
                            "stage": "submit_business_error",
                            "error_code": order.submit_failed_code,
                            "error_message": order.submit_failed_message,
                        }
                    )
                raise HTTPException(status_code=400, detail=order.submit_failed_message or "Submit failed")

    # Try a single status query right after submit. If upstream has not finished async processing,
    # keep local order in creating state and let later polling endpoint/scheduler continue.
    try:
        status_package_id = _build_chukou_package_id(order.id)
        _, status_payload = chukou_service.get_direct_express_order_status(status_package_id)
        if debug_collector:
            debug_collector({"stage": "status_response", "response_data": status_payload})
        if isinstance(status_payload, dict):
            _apply_status_snapshot(order, status_payload)
        else:
            order.order_status = "creating"
    except HTTPException as exc:
        if debug_collector:
            debug_collector(
                {
                    "stage": "status_error",
                    "status_code": exc.status_code,
                    "detail": str(exc.detail),
                }
            )
        order.order_status = "creating"

    db.commit()


def cancel_order(db: Session, order: Order) -> None:
    if order.order_status == "success":
        raise HTTPException(status_code=400, detail="Completed order cannot be cancelled")
    if order.order_status == "cancelled":
        return
    order.order_status = "cancelled"
    db.commit()
