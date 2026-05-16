import random
from datetime import datetime

from app.models.schemas import ApiResponse


def ok(data: object = None, message: str = "success") -> ApiResponse:
    return ApiResponse(code=0, message=message, data=data)


def generate_order_no() -> str:
    return f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}"
