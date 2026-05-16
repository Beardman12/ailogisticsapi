import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import Base, engine
from app.routers import auth, chat, orders
from app.utils.logging import build_system_request_log, configure_logging, log_system_request, parse_request_body


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


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    request_body = await request.body()

    try:
        response = await call_next(request)
    except Exception:
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
        )
        log_system_request(payload)
        raise

    elapsed_ms = (time.perf_counter() - start) * 1000
    payload = build_system_request_log(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        query_params=request.query_params,
        client_ip=request.client.host if request.client else None,
        headers=request.headers,
        request_body=parse_request_body(request_body, request.headers.get("content-type")),
        status_code=response.status_code,
        elapsed_ms=elapsed_ms,
    )
    log_system_request(payload)
    logger.info("%s %s %s %.2fms request_id=%s", request.method, request.url.path, response.status_code, elapsed_ms, request_id)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"code": 40001, "message": "Validation error", "data": exc.errors()},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": 40005, "message": str(exc.detail), "data": None},
    )


@app.get("/health")
def health_check():
    return {"code": 0, "message": "ok", "data": {"status": "healthy"}}
