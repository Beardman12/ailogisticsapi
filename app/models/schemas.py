from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Any = None


class LoginRequest(BaseModel):
    code: str = Field(min_length=1)
    nickname: str | None = None
    avatar_url: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    union_id: str
    nickname: str | None
    avatar_url: str | None
    created_at: datetime
    updated_at: datetime


class OrdersSummary(BaseModel):
    total_count: int
    pending_count: int
    completed_count: int


class LoginData(BaseModel):
    token: str
    user: UserOut
    orders_summary: OrdersSummary


class OrderItemCreate(BaseModel):
    product_name: str
    quantity: int = Field(ge=1)
    price: Decimal = Field(gt=0)


class OrderCreateRequest(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1)
    total_amount: Decimal = Field(gt=0)


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_name: str
    quantity: int
    price: Decimal


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_no: str
    user_id: int
    total_amount: Decimal
    status: str
    items: list[OrderItemOut]
    created_at: datetime
    updated_at: datetime


class OrderListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_no: str
    total_amount: Decimal
    status: str
    created_at: datetime


class OrderListData(BaseModel):
    items: list[OrderListItem]
    total: int
    skip: int
    limit: int


class ChatCreateConversationData(BaseModel):
    conversation_id: int


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: int | None = None


class ChatMessageData(BaseModel):
    conversation_id: int
    message: str


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime
