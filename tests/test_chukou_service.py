from fastapi import HTTPException

from app.services import chukou_service


def test_get_tracking_info_builds_expected_request(monkeypatch):
    captured: dict[str, object] = {}

    def fake_request(method: str, path: str, *, json_body=None):
        captured["method"] = method
        captured["path"] = path
        captured["json_body"] = json_body
        return 200, {"TrackingNumber": "TN123"}

    monkeypatch.setattr(chukou_service, "_request", fake_request)

    status_code, payload = chukou_service.get_tracking_info("TN123", "en")

    assert status_code == 200
    assert payload == {"TrackingNumber": "TN123"}
    assert captured == {
        "method": "GET",
        "path": "/v1/trackings/TN123?lang=en",
        "json_body": None,
    }


def test_get_tracking_info_url_encodes_tracking_number(monkeypatch):
    captured: dict[str, object] = {}

    def fake_request(method: str, path: str, *, json_body=None):
        captured["method"] = method
        captured["path"] = path
        return 200, {}

    monkeypatch.setattr(chukou_service, "_request", fake_request)

    chukou_service.get_tracking_info("ABC 123/中文", "zh")

    assert captured["method"] == "GET"
    assert captured["path"] == "/v1/trackings/ABC%20123%2F%E4%B8%AD%E6%96%87?lang=zh"


def test_get_tracking_info_rejects_blank_tracking_number():
    try:
        chukou_service.get_tracking_info("   ", "zh")
        raise AssertionError("Expected HTTPException for blank tracking number")
    except HTTPException as exc:
        assert exc.status_code == 400
        assert str(exc.detail) == "tracking_number is required"


def test_get_tracking_info_rejects_invalid_lang():
    try:
        chukou_service.get_tracking_info("TN123", "jp")
        raise AssertionError("Expected HTTPException for invalid lang")
    except HTTPException as exc:
        assert exc.status_code == 400
        assert str(exc.detail) == "lang must be one of: zh, en"
