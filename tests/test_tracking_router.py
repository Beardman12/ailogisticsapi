from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app
from app.services import chukou_service
from app.utils.security import get_current_user


def test_get_tracking_endpoint_returns_upstream_payload(monkeypatch):
    def fake_get_current_user():
        return SimpleNamespace(id=1)

    def fake_get_tracking_info(tracking_number: str, lang: str = "zh"):
        assert tracking_number == "TN123"
        assert lang == "en"
        return 200, {
            "TrackingNumber": "TN123",
            "TrackingStatus": "InTransit",
            "Checkpoints": [
                {"Message": "package accepted"},
            ],
        }

    app.dependency_overrides[get_current_user] = fake_get_current_user
    monkeypatch.setattr(chukou_service, "get_tracking_info", fake_get_tracking_info)

    client = TestClient(app)
    response = client.get("/api/trackings/TN123?lang=en")

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["message"] == "success"
    assert body["data"]["TrackingNumber"] == "TN123"
    assert body["data"]["TrackingStatus"] == "InTransit"

    app.dependency_overrides.clear()
