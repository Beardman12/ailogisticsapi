import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

from app.config import settings
from app.database import Base, engine
from app.routers import auth, chat, orders
from app.utils.logging import (
    build_system_request_log,
    configure_logging,
    ensure_current_log_files,
    log_system_request,
    parse_request_body,
    parse_response_body,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Path("data").mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

app.include_router(auth.router)
app.include_router(orders.router)
app.include_router(chat.router)

logger = logging.getLogger("mini_program_api")
configure_logging(settings.log_level)


async def _capture_response_body(response: Response) -> tuple[Response, Any]:
    content_type = response.headers.get("content-type")
    if content_type and "text/event-stream" in content_type.lower():
        return response, None

    body = getattr(response, "body", None)
    if body is not None:
        return response, parse_response_body(body, content_type)

    body_chunks: list[bytes] = []
    async for chunk in response.body_iterator:
        body_chunks.append(chunk)
    body = b"".join(body_chunks)

    rebuilt_response = Response(
        content=body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
        background=response.background,
    )
    return rebuilt_response, parse_response_body(body, content_type)


def _extract_error_from_response_body(response_body: Any) -> str | None:
    if isinstance(response_body, dict):
        message = response_body.get("message")
        detail = response_body.get("detail")
        if isinstance(message, str) and message.strip():
            return message
        if isinstance(detail, str) and detail.strip():
            return detail
    return None


@app.middleware("http")
async def log_requests(request: Request, call_next):
    ensure_current_log_files()
    start = time.perf_counter()
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    request_body = await request.body()

    try:
        response = await call_next(request)
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        payload = build_system_request_log(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query_params=request.query_params,
            client_ip=request.client.host if request.client else None,
            headers=request.headers,
            request_body=parse_request_body(request_body, request.headers.get("content-type")),
            status_code=500,
            elapsed_ms=elapsed_ms,
            error=f"{type(exc).__name__}: {exc}",
        )
        log_system_request(payload)
        raise

    response, response_body = await _capture_response_body(response)
    error_message = getattr(request.state, "error_message", None)
    if response.status_code >= 500 and not error_message:
        error_message = _extract_error_from_response_body(response_body) or "Internal Server Error"

    elapsed_ms = (time.perf_counter() - start) * 1000
    payload = build_system_request_log(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        query_params=request.query_params,
        client_ip=request.client.host if request.client else None,
        headers=request.headers,
        request_body=parse_request_body(request_body, request.headers.get("content-type")),
        response_body=response_body,
        status_code=response.status_code,
        elapsed_ms=elapsed_ms,
        error=error_message,
    )
    log_system_request(payload)
    logger.info("%s %s %s %.2fms request_id=%s", request.method, request.url.path, response.status_code, elapsed_ms, request_id)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = {"code": 40001, "message": "Validation error", "data": exc.errors()}
    request.state.error_message = "Validation error"
    return JSONResponse(
        status_code=422,
        content=body,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail_text = str(exc.detail)
    if exc.status_code >= 500:
        request.state.error_message = detail_text
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": 40005, "message": detail_text, "data": None},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request.state.error_message = f"{type(exc).__name__}: {exc}"
    logger.exception("Unhandled exception request_id=%s", getattr(request.state, "request_id", "-"))
    return JSONResponse(
        status_code=500,
        content={"code": 50000, "message": "Internal server error", "data": None},
    )


@app.get("/health")
def health_check():
    return {"code": 0, "message": "ok", "data": {"status": "healthy"}}
