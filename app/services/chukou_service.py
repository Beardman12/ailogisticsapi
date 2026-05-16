from typing import Any
from time import perf_counter

import httpx
from fastapi import HTTPException

from app.config import settings
from app.utils.logging import log_external_api_interaction


def _validate_settings() -> tuple[str, str]:
    if not settings.chukou_api_base_url:
        raise HTTPException(status_code=500, detail="CHUKOU_API_BASE_URL is not configured")
    if not settings.chukou_access_token:
        raise HTTPException(status_code=500, detail="CHUKOU_ACCESS_TOKEN is not configured")
    return settings.chukou_api_base_url.rstrip("/"), settings.chukou_access_token


def _request(method: str, path: str, *, json_body: dict[str, Any] | None = None) -> tuple[int, Any]:
    base_url, access_token = _validate_settings()
    request_url = f"{base_url}{path}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    start = perf_counter()

    try:
        with httpx.Client(timeout=settings.chukou_timeout_seconds) as client:
            response = client.request(
                method=method,
                url=request_url,
                headers=headers,
                json=json_body,
            )
    except httpx.HTTPError as exc:
        log_external_api_interaction(
            service_name="chukou",
            method=method,
            url=request_url,
            request_headers=headers,
            request_body=json_body,
            status_code=None,
            elapsed_ms=(perf_counter() - start) * 1000,
            error=str(exc),
        )
        raise HTTPException(status_code=502, detail="Chukou API is unavailable") from exc

    data: Any
    try:
        data = response.json()
    except ValueError:
        data = {"raw": response.text}

    log_external_api_interaction(
        service_name="chukou",
        method=method,
        url=request_url,
        request_headers=headers,
        request_body=json_body,
        status_code=response.status_code,
        response_body=data,
        elapsed_ms=(perf_counter() - start) * 1000,
        error=None if response.status_code < 400 else "http_error_response",
    )

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
