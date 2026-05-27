import json
import re
from datetime import datetime, timedelta

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.database import Conversation, Message, PendingOrderConfirmation, User
from app.models.schemas import AiOrderCreateRequest, ChatMessageData
from app.services import address_book_service, order_service
from app.services.chat_providers import get_chat_provider


def create_conversation(db: Session, user: User) -> Conversation:
    conversation = Conversation(user_id=user.id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_conversation(db: Session, user: User, conversation_id: int) -> Conversation:
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


def add_message(db: Session, conversation: Conversation, role: str, content: str) -> Message:
    message = Message(conversation_id=conversation.id, role=role, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def list_messages(db: Session, conversation: Conversation) -> list[Message]:
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.id.asc())
        .all()
    )


def build_general_prompt(
    history_messages: list[Message],
    current_user_message: str,
) -> str:
    lines: list[str] = [
        "【系统提示】你是物流客服助手。请基于当前对话记录和用户输入，直接给出自然语言回答。",
        "【当前对话记录（角色：内容）】",
    ]
    for message in history_messages:
        lines.append(f"{message.role}：{message.content}")

    lines.append("【当前用户输入】")
    lines.append(f"user：{current_user_message}")
    return "\n".join(lines)


def build_order_decision_prompt(
    history_messages: list[Message],
    current_user_message: str,
    default_sender: object | None,
    default_recipient: object | None,
) -> str:
    sender_info = _serialize_profile(default_sender)
    recipient_info = _serialize_profile(default_recipient)

    lines: list[str] = [
        "【系统提示】你是物流下单助手。你只能依据当前对话、默认收寄信息、当前用户输入做判断。",
        "【输出格式】你必须返回严格 JSON，对象结构如下：",
        '{"action":"reply|propose_order","assistant_message":"给用户显示的回复","order_payload":null|{...}}',
        "【规则】",
        "1) 如果用户只是咨询/闲聊，action=reply，order_payload=null。",
        "2) 只有当你能从用户信息中提取完整包裹和商品字段时，才能 action=propose_order。",
        "3) 如果默认寄件人或默认收件人缺失，必须 action=reply，提醒先补全默认地址簿，不要输出 propose_order。",
        "4) propose_order 的 order_payload 字段必须符合 ai 下单接口的输入格式：",
        "   package_id/platform_order_no/location_code/submit_later/user_remark/payment_currency/payable_amount/parcel/items",
        "5) 其中关键必填：parcel.cargo_type/weight_g_input/length_cm_input/width_cm_input/height_cm_input，",
        "   items[].line_no/goods_desc_cn/goods_desc_en/unit_price_usd/quantity/total_price_usd。",
        "6) 如果字段不完整，action 必须是 reply，并在 assistant_message 中点明缺失字段名。",
        "7) 你不执行下单，只做识别与参数抽取。",
        f"【默认寄件人信息】{json.dumps(sender_info, ensure_ascii=False)}",
        f"【默认收件人信息】{json.dumps(recipient_info, ensure_ascii=False)}",
        "【当前对话记录（角色：内容）】",
    ]
    for message in history_messages:
        lines.append(f"{message.role}：{message.content}")

    lines.append("【当前用户输入】")
    lines.append(f"user：{current_user_message}")
    return "\n".join(lines)


def request_assistant_reply(
    *,
    conversation: Conversation,
    prompt: str,
):
    provider = get_chat_provider()
    return provider.generate_reply(conversation_id=conversation.id, prompt=prompt)


def handle_chat_message(db: Session, user: User, conversation: Conversation, user_message: str) -> ChatMessageData:
    add_message(db, conversation, role="user", content=user_message)

    pending_result = _handle_pending_confirmation(db, user, conversation, user_message)
    if pending_result is not None:
        assistant_reply, requires_confirmation, pending_payload, confirmed_order_id = pending_result
        add_message(db, conversation, role="assistant", content=assistant_reply)
        return ChatMessageData(
            conversation_id=conversation.id,
            message=assistant_reply,
            stream_events=[],
            requires_confirmation=requires_confirmation,
            pending_order_payload=pending_payload,
            confirmed_order_id=confirmed_order_id,
        )

    history_messages = list_messages(db, conversation)
    default_sender = address_book_service.get_default_sender_profile(db, user)
    default_recipient = address_book_service.get_default_recipient_profile(db, user)

    if not _is_order_intent(user_message):
        general_prompt = build_general_prompt(history_messages, user_message)
        assistant_reply, stream_events = request_assistant_reply(
            conversation=conversation,
            prompt=general_prompt,
        )
        add_message(db, conversation, role="assistant", content=assistant_reply)
        return ChatMessageData(
            conversation_id=conversation.id,
            message=assistant_reply,
            stream_events=stream_events,
            requires_confirmation=False,
            pending_order_payload=None,
            confirmed_order_id=None,
        )

    prompt = build_order_decision_prompt(history_messages, user_message, default_sender, default_recipient)

    assistant_reply, stream_events = request_assistant_reply(
        conversation=conversation,
        prompt=prompt,
    )

    decision = _parse_ai_decision(assistant_reply)
    reply_text = assistant_reply
    requires_confirmation = False
    pending_payload: AiOrderCreateRequest | None = None

    if decision is not None:
        reply_text = decision["assistant_message"]
        if decision["action"] == "propose_order":
            missing_default_fields = _get_missing_default_profile_fields(default_sender, default_recipient)
            if missing_default_fields:
                missing_text = "、".join(_humanize_field_path(field) for field in missing_default_fields)
                reply_text = (
                    "检测到你希望下单，但默认收寄信息不完整，请先补全以下字段后再试："
                    f"{missing_text}"
                )
            else:
                try:
                    pending_payload = AiOrderCreateRequest.model_validate(decision.get("order_payload") or {})
                except ValidationError as exc:
                    reply_text = _build_order_payload_validation_message(exc)
                else:
                    _upsert_pending_confirmation(db, user, conversation, pending_payload)
                    requires_confirmation = True
                    if "确认" not in reply_text:
                        reply_text = (
                            f"{reply_text.rstrip()}\n\n"
                            "请回复“确认下单”继续，或回复“取消下单”放弃本次下单。"
                        )

    add_message(db, conversation, role="assistant", content=reply_text)
    return ChatMessageData(
        conversation_id=conversation.id,
        message=reply_text,
        stream_events=stream_events,
        requires_confirmation=requires_confirmation,
        pending_order_payload=pending_payload,
    )


def _serialize_profile(profile: object | None) -> dict:
    if profile is None:
        return {"exists": False}

    fields = [
        "sender_name",
        "sender_phone_code",
        "sender_phone",
        "pickup_point_id",
        "pickup_point_name",
        "domestic_tracking_no",
        "recipient_name",
        "phone_code",
        "phone",
        "country_code",
        "country_name",
        "province",
        "city",
        "district",
        "street1",
        "street2",
        "postcode",
        "email",
        "id_type",
        "id_number",
    ]
    data = {"exists": True}
    for field in fields:
        if hasattr(profile, field):
            data[field] = getattr(profile, field)
    return data


def _parse_ai_decision(raw_text: str) -> dict | None:
    payload = _extract_json_from_text(raw_text)
    if not isinstance(payload, dict):
        return None

    action = payload.get("action")
    if action not in {"reply", "propose_order"}:
        return None

    assistant_message = payload.get("assistant_message")
    if not isinstance(assistant_message, str) or not assistant_message.strip():
        return None

    return {
        "action": action,
        "assistant_message": assistant_message.strip(),
        "order_payload": payload.get("order_payload"),
    }


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


def _get_pending_confirmation(
    db: Session, user: User, conversation: Conversation
) -> PendingOrderConfirmation | None:
    return (
        db.query(PendingOrderConfirmation)
        .filter(
            PendingOrderConfirmation.user_id == user.id,
            PendingOrderConfirmation.conversation_id == conversation.id,
            PendingOrderConfirmation.status == "pending",
        )
        .order_by(PendingOrderConfirmation.id.desc())
        .first()
    )


def _upsert_pending_confirmation(
    db: Session,
    user: User,
    conversation: Conversation,
    payload: AiOrderCreateRequest,
) -> PendingOrderConfirmation:
    existing = _get_pending_confirmation(db, user, conversation)
    payload_json = payload.model_dump_json()
    if existing:
        existing.payload_json = payload_json
        db.commit()
        db.refresh(existing)
        return existing

    pending = PendingOrderConfirmation(
        user_id=user.id,
        conversation_id=conversation.id,
        payload_json=payload_json,
        status="pending",
    )
    db.add(pending)
    db.commit()
    db.refresh(pending)
    return pending


def _handle_pending_confirmation(
    db: Session,
    user: User,
    conversation: Conversation,
    user_message: str,
) -> tuple[str, bool, AiOrderCreateRequest | None, int | None] | None:
    pending = _get_pending_confirmation(db, user, conversation)
    if not pending:
        return None

    if _is_pending_expired(pending):
        pending.status = "expired"
        db.commit()
        return (
            "你有一笔待确认下单已超时失效，请重新描述下单需求，我会重新为你生成确认单。",
            False,
            None,
            None,
        )

    normalized = user_message.strip().lower()
    if _is_confirm_message(normalized):
        payload = AiOrderCreateRequest.model_validate(json.loads(pending.payload_json))
        order = order_service.ai_create_order(db, user, payload)
        pending.status = "confirmed"
        db.commit()
        return (
            f"已为你提交下单，订单号：{order.order_no}，当前状态：{order.order_status}。",
            False,
            None,
            order.id,
        )

    if _is_cancel_message(normalized):
        pending.status = "cancelled"
        db.commit()
        return ("已取消本次待确认下单。", False, None, None)

    payload = AiOrderCreateRequest.model_validate(json.loads(pending.payload_json))
    return (
        "检测到你有一笔待确认下单。请严格回复“确认下单”继续，或回复“取消下单”放弃本次下单。",
        True,
        payload,
        None,
    )


def _is_confirm_message(text: str) -> bool:
    return text in {"确认下单"}


def _is_cancel_message(text: str) -> bool:
    return text in {"取消下单", "放弃下单", "取消订单"}


def _is_order_intent(user_message: str) -> bool:
    normalized = (user_message or "").lower()
    keywords = [
        "下单",
        "寄",
        "发货",
        "创建订单",
        "提交订单",
        "order",
        "place order",
        "create order",
    ]
    return any(keyword in normalized for keyword in keywords)


def _get_missing_default_profile_fields(default_sender: object | None, default_recipient: object | None) -> list[str]:
    missing: list[str] = []

    sender_required = ["sender_name", "sender_phone_code", "sender_phone", "pickup_point_name"]
    recipient_required = [
        "recipient_name",
        "phone_code",
        "phone",
        "country_code",
        "country_name",
        "province",
        "city",
        "street1",
        "postcode",
        "id_type",
        "id_number",
    ]

    if default_sender is None:
        missing.append("default_sender")
    else:
        for field in sender_required:
            value = getattr(default_sender, field, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(f"default_sender.{field}")

    if default_recipient is None:
        missing.append("default_recipient")
    else:
        for field in recipient_required:
            value = getattr(default_recipient, field, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(f"default_recipient.{field}")

    return missing


def _build_order_payload_validation_message(exc: ValidationError) -> str:
    fields: list[str] = []
    global_errors: list[str] = []
    for error in exc.errors():
        loc = error.get("loc", ())
        msg = str(error.get("msg", "")).strip()

        if not loc:
            if msg:
                global_errors.append(_humanize_validation_reason(msg))
            continue

        path = _format_error_location(loc)
        if not path:
            continue

        field_name = _humanize_field_path(path)
        reason_text = _humanize_validation_reason(msg)
        combined = f"{field_name}（{reason_text}）" if reason_text else field_name
        if combined not in fields:
            fields.append(combined)

    if not fields and not global_errors:
        return "我已识别到下单意图，但下单信息不完整或格式不正确，请补充后重试。"

    if fields and global_errors:
        return (
            "我已识别到下单意图，但以下字段缺失或格式不正确："
            + "、".join(fields)
            + "。"
            + "；".join(global_errors)
        )

    if fields:
        return "我已识别到下单意图，但以下字段缺失或格式不正确：" + "、".join(fields)

    return "我已识别到下单意图，但下单信息不完整：" + "；".join(global_errors)


def _format_error_location(loc: tuple[object, ...]) -> str:
    parts: list[str] = []
    for token in loc:
        if isinstance(token, int):
            if not parts:
                parts.append(f"[{token}]")
            else:
                parts[-1] = f"{parts[-1]}[{token}]"
            continue
        token_text = str(token)
        if token_text == "__root__":
            continue
        parts.append(token_text)
    return ".".join(parts)


def _humanize_field_path(path: str) -> str:
    direct_mapping = {
        "package_id": "包裹编号",
        "platform_order_no": "平台订单号",
        "location_code": "仓库代码",
        "submit_later": "延迟提交",
        "user_remark": "订单备注",
        "payment_currency": "币种",
        "payable_amount": "应付金额",
        "parcel": "包裹信息",
        "parcel.cargo_type": "包裹类型",
        "parcel.weight_g_input": "包裹重量(克)",
        "parcel.length_cm_input": "包裹长(cm)",
        "parcel.width_cm_input": "包裹宽(cm)",
        "parcel.height_cm_input": "包裹高(cm)",
        "items": "商品列表",
        "default_sender": "默认寄件人信息",
        "default_sender.sender_name": "默认寄件人姓名",
        "default_sender.sender_phone_code": "默认寄件人电话区号",
        "default_sender.sender_phone": "默认寄件人电话",
        "default_sender.pickup_point_name": "默认揽收点名称",
        "default_recipient": "默认收件人信息",
        "default_recipient.recipient_name": "默认收件人姓名",
        "default_recipient.phone_code": "默认收件人电话区号",
        "default_recipient.phone": "默认收件人电话",
        "default_recipient.country_code": "默认收件国家代码",
        "default_recipient.country_name": "默认收件国家",
        "default_recipient.province": "默认收件省/州",
        "default_recipient.city": "默认收件城市",
        "default_recipient.street1": "默认收件地址1",
        "default_recipient.postcode": "默认收件邮编",
        "default_recipient.id_type": "默认证件类型",
        "default_recipient.id_number": "默认证件号",
    }

    if path in direct_mapping:
        return direct_mapping[path]

    item_match = re.match(r"items\[(\d+)\]\.([a-zA-Z0-9_]+)", path)
    if item_match:
        idx = int(item_match.group(1)) + 1
        field = item_match.group(2)
        item_field_mapping = {
            "line_no": "行号",
            "goods_desc_cn": "中文品名",
            "goods_desc_en": "英文品名",
            "unit_price_usd": "单价(USD)",
            "quantity": "数量",
            "total_price_usd": "总价(USD)",
            "sku_code": "SKU",
            "hs_code": "HS编码",
        }
        field_name = item_field_mapping.get(field, field)
        return f"第{idx}个商品{field_name}"

    return path.replace("_", " ")


def _humanize_validation_reason(msg: str) -> str:
    if not msg:
        return "格式不正确"

    normalized = msg.strip().lower()
    if "field required" in normalized:
        return "必填"
    if "greater than 0" in normalized:
        return "必须大于0"
    if "must be unique" in normalized:
        return "必须唯一"
    if "must equal" in normalized:
        return "与数量和单价计算结果不一致"

    readable = msg.strip()
    readable = re.sub(r"\s+", " ", readable)
    readable = readable.replace("Value error, ", "")
    return readable


def _is_pending_expired(pending: PendingOrderConfirmation) -> bool:
    created_at = getattr(pending, "created_at", None)
    if not isinstance(created_at, datetime):
        return False
    expire_at = created_at + timedelta(minutes=settings.pending_order_confirm_expire_minutes)
    return datetime.now() >= expire_at
