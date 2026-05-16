import logging

import httpx
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models.database import Order, User
from app.models.schemas import LoginData, LoginRequest, OrdersSummary, UserOut
from app.utils.logging import log_external_api_interaction
from app.utils.security import create_access_token

logger = logging.getLogger(__name__)


def _code_to_session(code: str) -> dict:
    if not settings.wechat_appid or not settings.wechat_appsecret:
        raise HTTPException(status_code=500, detail="WeChat login is not configured")

    url = f"{settings.wechat_api_base_url.rstrip('/')}/sns/jscode2session"
    params = {
        "appid": settings.wechat_appid,
        "secret": settings.wechat_appsecret,
        "js_code": code,
        "grant_type": "authorization_code",
    }
    request_body = {
        "appid": settings.wechat_appid,
        "js_code": "***",
        "grant_type": "authorization_code",
    }

    try:
        with httpx.Client(timeout=settings.wechat_api_timeout_seconds) as client:
            response = client.get(url, params=params)
        response.raise_for_status()
        result = response.json()
        log_external_api_interaction(
            service_name="wechat.auth.code2session",
            method="GET",
            url=url,
            request_headers={},
            request_body=request_body,
            status_code=response.status_code,
            response_body={
                "openid": result.get("openid"),
                "has_session_key": bool(result.get("session_key")),
                "errcode": result.get("errcode"),
                "errmsg": result.get("errmsg"),
            },
        )
        if result.get("errcode") and result.get("errcode") != 0:
            raise HTTPException(status_code=401, detail=result.get("errmsg") or "WeChat login failed")
        return result
    except httpx.HTTPStatusError as exc:
        response = exc.response
        try:
            response_body = response.json()
        except ValueError:
            response_body = response.text
        log_external_api_interaction(
            service_name="wechat.auth.code2session",
            method="GET",
            url=url,
            request_headers={},
            request_body=request_body,
            status_code=response.status_code,
            response_body=response_body,
            error=str(exc),
        )
        raise HTTPException(status_code=502, detail="WeChat code2Session request failed") from exc
    except httpx.RequestError as exc:
        log_external_api_interaction(
            service_name="wechat.auth.code2session",
            method="GET",
            url=url,
            request_headers={},
            request_body=request_body,
            status_code=None,
            error=str(exc),
        )
        raise HTTPException(status_code=502, detail="WeChat code2Session request failed") from exc


def login(db: Session, payload: LoginRequest) -> LoginData:
    session_data = _code_to_session(payload.code)
    openid = session_data.get("openid")
    if not openid:
        logger.warning(
            "wechat code2session returned no openid: errcode=%s errmsg=%s",
            session_data.get("errcode"),
            session_data.get("errmsg"),
        )
        raise HTTPException(status_code=401, detail=session_data.get("errmsg") or "WeChat login failed")

    user = db.query(User).filter(User.openid == openid).first()

    if not user:
        user = User(
            openid=openid,
            nickname=payload.nickname,
            avatar_url=payload.avatar_url,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if payload.nickname is not None:
            user.nickname = payload.nickname
        if payload.avatar_url is not None:
            user.avatar_url = payload.avatar_url
        db.commit()
        db.refresh(user)

    total_count = db.query(func.count(Order.id)).filter(Order.user_id == user.id).scalar() or 0
    pending_count = (
        db.query(func.count(Order.id))
        .filter(Order.user_id == user.id, Order.order_status.in_(["draft", "submitted", "processing"]))
        .scalar()
        or 0
    )
    completed_count = (
        db.query(func.count(Order.id))
        .filter(Order.user_id == user.id, Order.order_status == "success")
        .scalar()
        or 0
    )

    token = create_access_token(user.id)
    return LoginData(
        token=token,
        user=UserOut.model_validate(user),
        orders_summary=OrdersSummary(
            total_count=total_count,
            pending_count=pending_count,
            completed_count=completed_count,
        ),
    )
