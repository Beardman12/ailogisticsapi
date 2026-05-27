from types import SimpleNamespace

from fastapi import HTTPException

from app.models.schemas import AiOrderCreateRequest
from app.services import order_service


def _build_payload() -> AiOrderCreateRequest:
    return AiOrderCreateRequest(
        parcel={
            "cargo_type": "general",
            "weight_g_input": 500,
            "length_cm_input": "20",
            "width_cm_input": "10",
            "height_cm_input": "8",
        },
        items=[
            {
                "line_no": 1,
                "goods_desc_cn": "手机壳",
                "goods_desc_en": "Phone Case",
                "unit_price_usd": "2.50",
                "quantity": 2,
                "total_price_usd": "5.00",
            }
        ],
    )


def test_ai_create_order_uses_default_profiles_and_calls_create_order(monkeypatch):
    sender = SimpleNamespace(
        sender_name="Alice",
        sender_phone_code="+86",
        sender_phone="13800000000",
        pickup_point_id=1,
        pickup_point_name="Shanghai Hub",
        domestic_tracking_no="CN001",
    )
    recipient = SimpleNamespace(
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

    monkeypatch.setattr(order_service.address_book_service, "get_default_sender_profile", lambda db, user: sender)
    monkeypatch.setattr(
        order_service.address_book_service,
        "get_default_recipient_profile",
        lambda db, user: recipient,
    )

    captured = {}
    expected_order = object()

    def fake_create_order(db, user, payload):
        captured["db"] = db
        captured["user"] = user
        captured["payload"] = payload
        return expected_order

    monkeypatch.setattr(order_service, "create_order", fake_create_order)

    db = object()
    user = SimpleNamespace(id=9)
    payload = _build_payload()

    result = order_service.ai_create_order(db, user, payload)

    assert result is expected_order
    assert captured["db"] is db
    assert captured["user"] is user
    assert captured["payload"].sender.sender_name == "Alice"
    assert captured["payload"].recipient.recipient_name == "Bob"
    assert captured["payload"].order.payable_amount == payload.payable_amount
    assert captured["payload"].parcel.weight_g_input == 500


def test_ai_create_order_requires_default_sender(monkeypatch):
    monkeypatch.setattr(order_service.address_book_service, "get_default_sender_profile", lambda db, user: None)
    monkeypatch.setattr(
        order_service.address_book_service,
        "get_default_recipient_profile",
        lambda db, user: SimpleNamespace(postcode="100000"),
    )

    try:
        order_service.ai_create_order(object(), SimpleNamespace(id=1), _build_payload())
        raise AssertionError("Expected HTTPException when default sender is missing")
    except HTTPException as exc:
        assert exc.status_code == 422
        assert str(exc.detail) == "Default sender profile is required"


def test_ai_create_order_requires_default_recipient_postcode(monkeypatch):
    monkeypatch.setattr(
        order_service.address_book_service,
        "get_default_sender_profile",
        lambda db, user: SimpleNamespace(
            sender_name="Alice",
            sender_phone_code="+86",
            sender_phone="13800000000",
            pickup_point_id=1,
            pickup_point_name="Shanghai Hub",
            domestic_tracking_no=None,
        ),
    )
    monkeypatch.setattr(
        order_service.address_book_service,
        "get_default_recipient_profile",
        lambda db, user: SimpleNamespace(postcode=None),
    )

    try:
        order_service.ai_create_order(object(), SimpleNamespace(id=1), _build_payload())
        raise AssertionError("Expected HTTPException when default recipient postcode is missing")
    except HTTPException as exc:
        assert exc.status_code == 422
        assert str(exc.detail) == "Default recipient postcode is required"
