from types import SimpleNamespace
from datetime import datetime, timedelta

from app.services import chat_service


def _default_sender():
    return SimpleNamespace(
        sender_name="Alice",
        sender_phone_code="+86",
        sender_phone="13800000000",
        pickup_point_id=1,
        pickup_point_name="Shanghai Hub",
        domestic_tracking_no=None,
    )


def _default_recipient():
    return SimpleNamespace(
        recipient_name="Bob",
        phone_code="+51",
        phone="999888777",
        country_code="PE",
        country_name="Peru",
        province="Lima",
        city="Lima",
        district="Miraflores",
        street1="Av. Larco 100",
        street2=None,
        postcode="15074",
        email="bob@example.com",
        id_type="DNI",
        id_number="12345678",
    )


def test_handle_chat_message_proposes_order_and_requires_confirmation(monkeypatch):
    stored_messages = []

    def fake_add_message(db, conversation, role, content):
        stored_messages.append((role, content))
        return SimpleNamespace(id=len(stored_messages))

    monkeypatch.setattr(chat_service, "add_message", fake_add_message)
    monkeypatch.setattr(chat_service, "_handle_pending_confirmation", lambda db, user, c, m: None)
    monkeypatch.setattr(chat_service, "list_messages", lambda db, conversation: [])
    monkeypatch.setattr(chat_service.address_book_service, "get_default_sender_profile", lambda db, user: _default_sender())
    monkeypatch.setattr(
        chat_service.address_book_service,
        "get_default_recipient_profile",
        lambda db, user: _default_recipient(),
    )

    captured = {"called": False}

    def fake_upsert(db, user, conversation, payload):
        captured["called"] = True
        captured["payload"] = payload

    monkeypatch.setattr(chat_service, "_upsert_pending_confirmation", fake_upsert)
    monkeypatch.setattr(
        chat_service,
        "request_assistant_reply",
        lambda conversation, prompt: (
            '{"action":"propose_order","assistant_message":"我已整理好下单信息。","order_payload":{"payment_currency":"USD","parcel":{"cargo_type":"general","weight_g_input":500,"length_cm_input":20,"width_cm_input":10,"height_cm_input":8},"items":[{"line_no":1,"goods_desc_cn":"手机壳","goods_desc_en":"Phone Case","unit_price_usd":2.5,"quantity":2,"total_price_usd":5.0}]}}',
            [],
        ),
    )

    result = chat_service.handle_chat_message(
        db=object(),
        user=SimpleNamespace(id=1),
        conversation=SimpleNamespace(id=99),
        user_message="帮我下单，手机壳2个",
    )

    assert result.requires_confirmation is True
    assert result.pending_order_payload is not None
    assert captured["called"] is True
    assert result.pending_order_payload.parcel.weight_g_input == 500
    assert stored_messages[-1][0] == "assistant"


def test_handle_chat_message_returns_pending_confirmation_prompt(monkeypatch):
    monkeypatch.setattr(chat_service, "add_message", lambda db, conversation, role, content: None)
    monkeypatch.setattr(
        chat_service,
        "_handle_pending_confirmation",
        lambda db, user, c, m: ("请确认下单", True, None, None),
    )

    result = chat_service.handle_chat_message(
        db=object(),
        user=SimpleNamespace(id=1),
        conversation=SimpleNamespace(id=99),
        user_message="嗯",
    )

    assert result.message == "请确认下单"
    assert result.requires_confirmation is True


def test_handle_chat_message_propose_order_but_defaults_missing(monkeypatch):
    monkeypatch.setattr(chat_service, "add_message", lambda db, conversation, role, content: None)
    monkeypatch.setattr(chat_service, "_handle_pending_confirmation", lambda db, user, c, m: None)
    monkeypatch.setattr(chat_service, "list_messages", lambda db, conversation: [])
    monkeypatch.setattr(chat_service.address_book_service, "get_default_sender_profile", lambda db, user: None)
    monkeypatch.setattr(chat_service.address_book_service, "get_default_recipient_profile", lambda db, user: None)
    monkeypatch.setattr(chat_service, "_upsert_pending_confirmation", lambda db, user, c, p: None)
    monkeypatch.setattr(
        chat_service,
        "request_assistant_reply",
        lambda conversation, prompt: (
            '{"action":"propose_order","assistant_message":"准备下单","order_payload":{"parcel":{"cargo_type":"general","weight_g_input":500,"length_cm_input":20,"width_cm_input":10,"height_cm_input":8},"items":[{"line_no":1,"goods_desc_cn":"手机壳","goods_desc_en":"Phone Case","unit_price_usd":2.5,"quantity":2,"total_price_usd":5.0}]}}',
            [],
        ),
    )

    result = chat_service.handle_chat_message(
        db=object(),
        user=SimpleNamespace(id=1),
        conversation=SimpleNamespace(id=99),
        user_message="帮我下单",
    )

    assert result.requires_confirmation is False
    assert "默认收寄信息不完整" in result.message


def test_handle_chat_message_non_order_question_uses_general_reply(monkeypatch):
    monkeypatch.setattr(chat_service, "add_message", lambda db, conversation, role, content: None)
    monkeypatch.setattr(chat_service, "_handle_pending_confirmation", lambda db, user, c, m: None)
    monkeypatch.setattr(chat_service, "list_messages", lambda db, conversation: [])
    monkeypatch.setattr(chat_service.address_book_service, "get_default_sender_profile", lambda db, user: _default_sender())
    monkeypatch.setattr(
        chat_service.address_book_service,
        "get_default_recipient_profile",
        lambda db, user: _default_recipient(),
    )

    called = {"upsert": False}
    monkeypatch.setattr(chat_service, "_upsert_pending_confirmation", lambda db, user, c, p: called.__setitem__("upsert", True))
    monkeypatch.setattr(
        chat_service,
        "request_assistant_reply",
        lambda conversation, prompt: ("你可以在首页查看运费估算入口。", []),
    )

    result = chat_service.handle_chat_message(
        db=object(),
        user=SimpleNamespace(id=1),
        conversation=SimpleNamespace(id=99),
        user_message="怎么计算运费？",
    )

    assert result.requires_confirmation is False
    assert result.pending_order_payload is None
    assert called["upsert"] is False
    assert result.message == "你可以在首页查看运费估算入口。"


def test_handle_chat_message_order_payload_validation_shows_missing_fields(monkeypatch):
    monkeypatch.setattr(chat_service, "add_message", lambda db, conversation, role, content: None)
    monkeypatch.setattr(chat_service, "_handle_pending_confirmation", lambda db, user, c, m: None)
    monkeypatch.setattr(chat_service, "list_messages", lambda db, conversation: [])
    monkeypatch.setattr(chat_service.address_book_service, "get_default_sender_profile", lambda db, user: _default_sender())
    monkeypatch.setattr(
        chat_service.address_book_service,
        "get_default_recipient_profile",
        lambda db, user: _default_recipient(),
    )
    monkeypatch.setattr(chat_service, "_upsert_pending_confirmation", lambda db, user, c, p: None)
    monkeypatch.setattr(
        chat_service,
        "request_assistant_reply",
        lambda conversation, prompt: (
            '{"action":"propose_order","assistant_message":"我来帮你下单","order_payload":{"items":[{"line_no":1,"goods_desc_cn":"手机壳","goods_desc_en":"Phone Case","unit_price_usd":2.5,"quantity":2,"total_price_usd":5.0}]}}',
            [],
        ),
    )

    result = chat_service.handle_chat_message(
        db=object(),
        user=SimpleNamespace(id=1),
        conversation=SimpleNamespace(id=99),
        user_message="帮我下单",
    )

    assert result.requires_confirmation is False
    assert "以下字段缺失或格式不正确" in result.message
    assert "包裹信息" in result.message


def test_handle_chat_message_order_payload_missing_item_value_fields_is_human_readable(monkeypatch):
    monkeypatch.setattr(chat_service, "add_message", lambda db, conversation, role, content: None)
    monkeypatch.setattr(chat_service, "_handle_pending_confirmation", lambda db, user, c, m: None)
    monkeypatch.setattr(chat_service, "list_messages", lambda db, conversation: [])
    monkeypatch.setattr(chat_service.address_book_service, "get_default_sender_profile", lambda db, user: _default_sender())
    monkeypatch.setattr(
        chat_service.address_book_service,
        "get_default_recipient_profile",
        lambda db, user: _default_recipient(),
    )
    monkeypatch.setattr(chat_service, "_upsert_pending_confirmation", lambda db, user, c, p: None)
    monkeypatch.setattr(
        chat_service,
        "request_assistant_reply",
        lambda conversation, prompt: (
            '{"action":"propose_order","assistant_message":"我来帮你下单","order_payload":{"parcel":{"cargo_type":"general","weight_g_input":500,"length_cm_input":20,"width_cm_input":10,"height_cm_input":8},"items":[{"line_no":1,"goods_desc_cn":"手机壳","goods_desc_en":"Phone Case","quantity":2}]}}',
            [],
        ),
    )

    result = chat_service.handle_chat_message(
        db=object(),
        user=SimpleNamespace(id=1),
        conversation=SimpleNamespace(id=99),
        user_message="帮我下单",
    )

    assert result.requires_confirmation is False
    assert "第1个商品单价(USD)（必填）" in result.message
    assert "第1个商品总价(USD)（必填）" in result.message


def test_handle_chat_message_tracking_query_calls_server_and_returns_ai_final_reply(monkeypatch):
    monkeypatch.setattr(chat_service, "add_message", lambda db, conversation, role, content: None)
    monkeypatch.setattr(chat_service, "_handle_pending_confirmation", lambda db, user, c, m: None)
    monkeypatch.setattr(chat_service, "list_messages", lambda db, conversation: [])
    monkeypatch.setattr(chat_service.address_book_service, "get_default_sender_profile", lambda db, user: _default_sender())
    monkeypatch.setattr(
        chat_service.address_book_service,
        "get_default_recipient_profile",
        lambda db, user: _default_recipient(),
    )

    call_state = {"count": 0}

    def fake_assistant_reply(conversation, prompt):
        call_state["count"] += 1
        if "轨迹查询意图识别助手" in prompt:
            return (
                '{"action":"query_tracking","assistant_message":"我来帮你查一下轨迹。","tracking_number":"TN123456"}',
                [],
            )
        if "轨迹原始数据" in prompt:
            assert "字段说明" in prompt
            assert "Checkpoints时间线（服务端整理）" in prompt
            assert "Checkpoints" in prompt
            return ("跟踪号 TN123456 当前状态：运输中。最新节点：包裹已离开处理中心。", [])
        raise AssertionError("unexpected prompt")

    monkeypatch.setattr(chat_service, "request_assistant_reply", fake_assistant_reply)

    captured = {}

    def fake_get_tracking_info(tracking_number: str, lang: str = "zh"):
        captured["tracking_number"] = tracking_number
        captured["lang"] = lang
        return 200, {
            "TrackingNumber": tracking_number,
            "TrackingStatus": "InTransit",
            "Checkpoints": [{"Message": "包裹已离开处理中心"}],
        }

    monkeypatch.setattr(chat_service.chukou_service, "get_tracking_info", fake_get_tracking_info)

    result = chat_service.handle_chat_message(
        db=object(),
        user=SimpleNamespace(id=1),
        conversation=SimpleNamespace(id=99),
        user_message="请帮我查一下 TN123456 的轨迹",
    )

    assert call_state["count"] == 2
    assert captured["tracking_number"] == "TN123456"
    assert captured["lang"] == "zh"
    assert "当前状态" in result.message
    assert result.requires_confirmation is False


def test_handle_chat_message_tracking_without_number_returns_prompt(monkeypatch):
    monkeypatch.setattr(chat_service, "add_message", lambda db, conversation, role, content: None)
    monkeypatch.setattr(chat_service, "_handle_pending_confirmation", lambda db, user, c, m: None)
    monkeypatch.setattr(chat_service, "list_messages", lambda db, conversation: [])
    monkeypatch.setattr(chat_service.address_book_service, "get_default_sender_profile", lambda db, user: _default_sender())
    monkeypatch.setattr(
        chat_service.address_book_service,
        "get_default_recipient_profile",
        lambda db, user: _default_recipient(),
    )
    monkeypatch.setattr(
        chat_service,
        "request_assistant_reply",
        lambda conversation, prompt: (
            '{"action":"reply","assistant_message":"请提供跟踪号，我再为你查询。","tracking_number":null}',
            [],
        ),
    )

    called = {"tracking_called": False}

    def fake_get_tracking_info(tracking_number: str, lang: str = "zh"):
        called["tracking_called"] = True
        _ = (tracking_number, lang)
        return 200, {}

    monkeypatch.setattr(chat_service.chukou_service, "get_tracking_info", fake_get_tracking_info)

    result = chat_service.handle_chat_message(
        db=object(),
        user=SimpleNamespace(id=1),
        conversation=SimpleNamespace(id=99),
        user_message="帮我查下这个包裹现在到哪了",
    )

    assert called["tracking_called"] is False
    assert "请提供跟踪号" in result.message
    assert result.requires_confirmation is False


def test_confirm_message_requires_exact_phrase():
    assert chat_service._is_confirm_message("确认下单") is True
    assert chat_service._is_confirm_message("ok") is False
    assert chat_service._is_confirm_message("yes") is False


def test_handle_pending_confirmation_expires(monkeypatch):
    payload_json = (
        '{"payment_currency":"USD","parcel":{"cargo_type":"general","weight_g_input":500,'
        '"length_cm_input":20,"width_cm_input":10,"height_cm_input":8},'
        '"items":[{"line_no":1,"goods_desc_cn":"手机壳","goods_desc_en":"Phone Case",'
        '"unit_price_usd":2.5,"quantity":2,"total_price_usd":5.0}]}'
    )
    pending = SimpleNamespace(
        payload_json=payload_json,
        status="pending",
        created_at=datetime.now() - timedelta(minutes=11),
    )
    monkeypatch.setattr(chat_service, "_get_pending_confirmation", lambda db, user, conversation: pending)

    class FakeDb:
        def __init__(self):
            self.commit_count = 0

        def commit(self):
            self.commit_count += 1

    db = FakeDb()

    result = chat_service._handle_pending_confirmation(
        db=db,
        user=SimpleNamespace(id=1),
        conversation=SimpleNamespace(id=99),
        user_message="确认下单",
    )

    assert result is not None
    message, requires_confirmation, pending_payload, confirmed_order_id = result
    assert "超时失效" in message
    assert requires_confirmation is False
    assert pending_payload is None
    assert confirmed_order_id is None
    assert pending.status == "expired"
    assert db.commit_count == 1
