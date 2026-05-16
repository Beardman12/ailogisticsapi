from typing import Any

import httpx
from fastapi import HTTPException

from app.config import settings


def _validate_settings() -> tuple[str, str]:
    if not settings.chukou_api_base_url:
        raise HTTPException(status_code=500, detail="CHUKOU_API_BASE_URL is not configured")
    if not settings.chukou_access_token:
        raise HTTPException(status_code=500, detail="CHUKOU_ACCESS_TOKEN is not configured")
    return settings.chukou_api_base_url.rstrip("/"), settings.chukou_access_token


def _request(method: str, path: str, *, json_body: dict[str, Any] | None = None) -> tuple[int, Any]:
    base_url, access_token = _validate_settings()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8",
    }

    try:
        with httpx.Client(timeout=settings.chukou_timeout_seconds) as client:
            response = client.request(
                method=method,
                url=f"{base_url}{path}",
                headers=headers,
                json=json_body,
            )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Chukou API is unavailable") from exc

    data: Any
    try:
        data = response.json()
    except ValueError:
        data = {"raw": response.text}

    if response.status_code >= 400:
        message = "Chukou API request failed"
        if isinstance(data, dict):
            errors = data.get("Errors")
            if isinstance(errors, list) and errors:
                first = errors[0]
                if isinstance(first, dict):
                    err_code = first.get("Code")
                    err_message = first.get("Message")
                    if err_code and err_message:
                        message = f"Chukou API request failed: {err_code} {err_message}"
                    elif err_message:
                        message = f"Chukou API request failed: {err_message}"
        raise HTTPException(status_code=502, detail=message)

    return response.status_code, data


def create_direct_express_order(payload: dict[str, Any]) -> tuple[int, Any]:
    return _request("POST", "/v1/directExpressOrders", json_body=payload)


def get_direct_express_order_status(package_id: str) -> tuple[int, Any]:
    return _request("GET", f"/v1/directExpressOrders/{package_id}/status")
