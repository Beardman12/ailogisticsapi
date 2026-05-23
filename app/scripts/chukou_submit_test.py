from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.database import SessionLocal, ensure_initialized
from app.models.database import Order, User
from app.services.order_service import complete_order


def _serialize_order(order: Order) -> dict[str, Any]:
    return {
        "id": order.id,
        "order_no": order.order_no,
        "user_id": order.user_id,
        "package_id": order.package_id,
        "service_code": order.service_code,
        "order_status": order.order_status,
        "chukou_status": order.chukou_status,
        "tracking_number": order.tracking_number,
        "submit_failed_code": order.submit_failed_code,
        "submit_failed_message": order.submit_failed_message,
    }


def _append_test_log(entry: dict[str, Any]) -> Path:
    log_dir = Path("logs") / datetime.now().strftime("%Y%m%d")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "chukou_submit_test.log"
    with log_path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return log_path


def _ensure_test_user(test_openid: str, nickname: str) -> tuple[User, bool]:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.openid == test_openid).first()
        created = False
        if not user:
            user = User(openid=test_openid, nickname=nickname)
            db.add(user)
            db.commit()
            db.refresh(user)
            created = True
        return user, created
    finally:
        db.close()


def _find_target_order(db, order_id: int | None) -> Order | None:
    query = db.query(Order)
    if order_id is not None:
        return query.filter(Order.id == order_id).first()

    return (
        query.filter(~Order.order_status.in_(["success", "cancelled"]))
        .order_by(Order.id.desc())
        .first()
    )


def run(order_id: int | None, test_openid: str, nickname: str) -> int:
    ensure_initialized()
    user, created = _ensure_test_user(test_openid=test_openid, nickname=nickname)

    db = SessionLocal()
    try:
        target_order = _find_target_order(db, order_id)
        if not target_order:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "message": "No order found in orders table",
                        "test_user": {
                            "id": user.id,
                            "openid": user.openid,
                            "created": created,
                        },
                    },
                    ensure_ascii=False,
                )
            )
            return 1

        before = _serialize_order(target_order)
        debug_events: list[dict[str, Any]] = []

        def _collect_debug_event(event: dict[str, Any]) -> None:
            debug_events.append(event)

        try:
            complete_order(db, target_order, debug_collector=_collect_debug_event)
            db.refresh(target_order)
            output = {
                "ok": True,
                "message": "CHUKOU submit request completed",
                "test_user": {
                    "id": user.id,
                    "openid": user.openid,
                    "created": created,
                },
                "before": before,
                "after": _serialize_order(target_order),
                "chukou_interactions": debug_events,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            }
            log_path = _append_test_log(output)
            output["saved_log_path"] = str(log_path)
            print(json.dumps(output, ensure_ascii=False))
            return 0
        except HTTPException as exc:
            db.refresh(target_order)
            output = {
                "ok": False,
                "message": "CHUKOU submit request failed",
                "error": {
                    "status_code": exc.status_code,
                    "detail": str(exc.detail),
                },
                "test_user": {
                    "id": user.id,
                    "openid": user.openid,
                    "created": created,
                },
                "before": before,
                "after": _serialize_order(target_order),
                "chukou_interactions": debug_events,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            }
            log_path = _append_test_log(output)
            output["saved_log_path"] = str(log_path)
            print(json.dumps(output, ensure_ascii=False))
            return 2
    finally:
        db.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a test user, read an order from DB, and submit to CHUKOU API"
    )
    parser.add_argument("--order-id", type=int, default=None, help="Specific order id to submit")
    parser.add_argument(
        "--test-openid",
        type=str,
        default="test_chukou_api_user",
        help="OpenID for the test user",
    )
    parser.add_argument(
        "--nickname",
        type=str,
        default="CHUKOU测试用户",
        help="Nickname for the test user",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return run(order_id=args.order_id, test_openid=args.test_openid, nickname=args.nickname)


if __name__ == "__main__":
    sys.exit(main())
