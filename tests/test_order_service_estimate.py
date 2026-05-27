from types import SimpleNamespace

from fastapi import HTTPException

from app.models.schemas import ShippingEstimateRequest
from app.services import order_service


def test_estimate_shipping_uses_fresh_coze_request_and_parses_json(monkeypatch):
    captured = {}

    class FakeProvider:
        def generate_reply(self, *, conversation_id: int, prompt: str):
            captured["conversation_id"] = conversation_id
            captured["prompt"] = prompt
            return (
                '{"destination":"秘鲁 利马","item_type":"普货","weight_kg":0.8,'
                '"estimated_price":35.5,"first_weight_price":22.0,'
                '"additional_weight_price":9.0,"estimated_delivery_time":"5-7个工作日","currency":"CNY"}',
                [],
            )

    monkeypatch.setattr(order_service, "CozeChatProvider", lambda: FakeProvider())

    payload = ShippingEstimateRequest(
        destination="秘鲁 利马",
        item_type="普货",
        weight_kg="0.8",
    )

    result = order_service.estimate_shipping(payload)

    assert isinstance(captured["conversation_id"], int)
    assert captured["conversation_id"] > 0
    assert "严禁使用任何上下文、会话历史、记忆或用户偏好" in captured["prompt"]
    assert "仅允许基于接口传值转为自然语言" in captured["prompt"]
    assert "你必须只输出 JSON 对象" in captured["prompt"]
    assert result.destination == "秘鲁 利马"
    assert float(result.estimated_price) == 35.5
    assert result.currency == "CNY"


def test_estimate_shipping_raises_when_coze_reply_is_not_json(monkeypatch):
    class FakeProvider:
        def generate_reply(self, *, conversation_id: int, prompt: str):
            _ = conversation_id, prompt
            return ("这不是 JSON", [])

    monkeypatch.setattr(order_service, "CozeChatProvider", lambda: FakeProvider())

    payload = ShippingEstimateRequest(
        destination="秘鲁 利马",
        item_type="普货",
        weight_kg="0.8",
    )

    try:
        order_service.estimate_shipping(payload)
        raise AssertionError("Expected HTTPException for invalid Coze response")
    except HTTPException as exc:
        assert exc.status_code == 502
        assert "valid JSON" in str(exc.detail)