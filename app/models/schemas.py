from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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
    openid: str
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
    line_no: int = Field(ge=1)
    goods_desc_cn: str
    goods_desc_en: str
    unit_price_usd: Decimal = Field(gt=0)
    quantity: int = Field(ge=1)
    total_price_usd: Decimal = Field(gt=0)
    sku_code: str | None = None
    hs_code: str | None = None


class OrderCoreCreate(BaseModel):
    package_id: str = Field(min_length=1, max_length=64)
    platform_order_no: str | None = Field(default=None, max_length=64)
    service_code: str | None = Field(default=None, min_length=1, max_length=32)
    location_code: str | None = Field(default=None, max_length=20)
    submit_later: bool = False
    user_remark: str | None = Field(default=None, max_length=500)
    payable_amount: Decimal = Field(gt=0)
    payment_currency: str = Field(min_length=3, max_length=8)


class OrderSenderCreate(BaseModel):
    sender_name: str
    sender_phone_code: str
    sender_phone: str
    pickup_point_id: int | None = None
    pickup_point_name: str
    domestic_tracking_no: str | None = None


class OrderRecipientCreate(BaseModel):
    recipient_name: str
    phone_code: str
    phone: str
    country_code: str = Field(min_length=2, max_length=2)
    country_name: str
    province: str
    city: str
    district: str | None = None
    street1: str
    street2: str | None = None
    postcode: str
    email: str | None = None
    id_type: str
    id_number: str

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        return value.upper()


class OrderParcelCreate(BaseModel):
    cargo_type: str
    weight_g_input: int = Field(gt=0)
    length_cm_input: Decimal = Field(gt=0)
    width_cm_input: Decimal = Field(gt=0)
    height_cm_input: Decimal = Field(gt=0)


class OrderCreateRequest(BaseModel):
    order: OrderCoreCreate
    sender: OrderSenderCreate
    recipient: OrderRecipientCreate
    parcel: OrderParcelCreate
    items: list[OrderItemCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_items(self) -> "OrderCreateRequest":
        line_nos = [item.line_no for item in self.items]
        if len(line_nos) != len(set(line_nos)):
            raise ValueError("items.line_no must be unique")

        for item in self.items:
            expected_total = item.unit_price_usd * item.quantity
            if item.total_price_usd != expected_total:
                raise ValueError(
                    f"items[{item.line_no}].total_price_usd must equal unit_price_usd * quantity"
                )
        return self


class AiOrderCreateRequest(BaseModel):
    package_id: str | None = Field(default=None, max_length=64)
    platform_order_no: str | None = Field(default=None, max_length=64)
    location_code: str | None = Field(default=None, max_length=20)
    submit_later: bool = False
    user_remark: str | None = Field(default=None, max_length=500)
    payment_currency: str = Field(default="USD", min_length=3, max_length=8)
    payable_amount: Decimal | None = Field(default=None, gt=0)
    parcel: OrderParcelCreate
    items: list[OrderItemCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def normalize_and_validate(self) -> "AiOrderCreateRequest":
        if self.package_id is not None:
            self.package_id = self.package_id.strip() or None

        line_nos = [item.line_no for item in self.items]
        if len(line_nos) != len(set(line_nos)):
            raise ValueError("items.line_no must be unique")

        derived_total = Decimal("0")
        for item in self.items:
            expected_total = item.unit_price_usd * item.quantity
            if item.total_price_usd != expected_total:
                raise ValueError(
                    f"items[{item.line_no}].total_price_usd must equal unit_price_usd * quantity"
                )
            derived_total += item.total_price_usd

        if self.payable_amount is None:
            self.payable_amount = derived_total

        return self


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    line_no: int
    goods_desc_cn: str
    goods_desc_en: str
    unit_price_usd: Decimal
    quantity: int
    total_price_usd: Decimal
    sku_code: str | None
    hs_code: str | None


class OrderSenderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sender_name: str
    sender_phone_code: str
    sender_phone: str
    pickup_point_id: int | None
    pickup_point_name: str
    domestic_tracking_no: str | None


class OrderRecipientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recipient_name: str
    phone_code: str
    phone: str
    country_code: str
    country_name: str
    province: str
    city: str
    district: str | None
    street1: str
    street2: str | None
    postcode: str
    email: str | None
    id_type: str
    id_number: str


class OrderParcelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cargo_type: str
    weight_g_input: int
    length_cm_input: Decimal
    width_cm_input: Decimal
    height_cm_input: Decimal
    weight_g_verified: int | None
    length_cm_verified: Decimal | None
    width_cm_verified: Decimal | None
    height_cm_verified: Decimal | None
    charged_weight_g: int | None


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_no: str
    user_id: int
    package_id: str
    platform_order_no: str | None
    service_code: str
    location_code: str | None
    submit_later: bool
    order_status: str
    payment_status: str
    payable_amount: Decimal | None
    payment_currency: str | None
    user_remark: str | None
    total_amount: Decimal
    sender: OrderSenderOut | None
    recipient: OrderRecipientOut | None
    parcel: OrderParcelOut | None
    items: list[OrderItemOut]
    created_at: datetime
    updated_at: datetime


class OrderListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_no: str
    package_id: str
    service_code: str
    total_amount: Decimal
    order_status: str
    created_at: datetime


class OrderListData(BaseModel):
    items: list[OrderListItem]
    total: int
    skip: int
    limit: int


class ShippingEstimateRequest(BaseModel):
    destination: str | None = Field(default=None, min_length=1, max_length=100)
    destination_province: str | None = Field(default=None, min_length=1, max_length=100)
    destination_city: str | None = Field(default=None, min_length=1, max_length=100)
    item_type: str | None = Field(default=None, min_length=1, max_length=100)
    cargo_type: str | None = Field(default=None, min_length=1, max_length=100)
    weight_kg: Decimal | None = Field(default=None, gt=0)
    weight_kg_input: Decimal | None = Field(default=None, gt=0)
    weight_g_input: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def normalize(self) -> "ShippingEstimateRequest":
        if not self.destination:
            province = (self.destination_province or "").strip()
            city = (self.destination_city or "").strip()
            merged = " ".join(part for part in [province, city] if part)
            if merged:
                self.destination = merged

        if not self.item_type and self.cargo_type:
            self.item_type = self.cargo_type

        if self.weight_kg is None:
            if self.weight_kg_input is not None:
                self.weight_kg = self.weight_kg_input
            elif self.weight_g_input is not None:
                self.weight_kg = (Decimal(self.weight_g_input) / Decimal("1000")).quantize(Decimal("0.001"))

        missing_fields: list[str] = []
        if not self.destination:
            missing_fields.append("destination or destination_province/destination_city")
        if not self.item_type:
            missing_fields.append("item_type or cargo_type")
        if self.weight_kg is None:
            missing_fields.append("weight_kg or weight_kg_input or weight_g_input")

        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        return self


class ShippingEstimateData(BaseModel):
    destination: str
    item_type: str
    weight_kg: Decimal
    estimated_price: Decimal
    first_weight_price: Decimal
    additional_weight_price: Decimal
    estimated_delivery_time: str
    currency: str = "CNY"


class ChatCreateConversationData(BaseModel):
    conversation_id: int


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: int | None = None


class ChatMessageData(BaseModel):
    conversation_id: int
    message: str
    stream_events: list[Any] = Field(default_factory=list)
    requires_confirmation: bool = False
    pending_order_payload: AiOrderCreateRequest | None = None
    confirmed_order_id: int | None = None
    confirmed_order_no: str | None = None


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class SenderProfileCreate(BaseModel):
    profile_name: str | None = Field(default=None, max_length=100)
    sender_name: str
    sender_phone_code: str
    sender_phone: str
    pickup_point_id: int | None = None
    pickup_point_name: str
    domestic_tracking_no: str | None = None
    is_default: bool = False


class SenderProfileUpdate(BaseModel):
    profile_name: str | None = Field(default=None, max_length=100)
    sender_name: str
    sender_phone_code: str
    sender_phone: str
    pickup_point_id: int | None = None
    pickup_point_name: str
    domestic_tracking_no: str | None = None
    is_default: bool = False


class SenderProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    profile_name: str
    sender_name: str
    sender_phone_code: str
    sender_phone: str
    pickup_point_id: int | None
    pickup_point_name: str
    domestic_tracking_no: str | None
    is_default: bool
    created_at: datetime
    updated_at: datetime


class RecipientProfileCreate(BaseModel):
    profile_name: str | None = Field(default=None, max_length=100)
    recipient_name: str
    phone_code: str
    phone: str
    country_code: str = Field(min_length=2, max_length=2)
    country_name: str
    province: str
    city: str
    district: str | None = None
    street1: str
    street2: str | None = None
    postcode: str | None = None
    email: str | None = None
    id_type: str
    id_number: str
    is_default: bool = False

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        return value.upper()


class RecipientProfileUpdate(BaseModel):
    profile_name: str | None = Field(default=None, max_length=100)
    recipient_name: str
    phone_code: str
    phone: str
    country_code: str = Field(min_length=2, max_length=2)
    country_name: str
    province: str
    city: str
    district: str | None = None
    street1: str
    street2: str | None = None
    postcode: str | None = None
    email: str | None = None
    id_type: str
    id_number: str
    is_default: bool = False

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        return value.upper()


class RecipientProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    profile_name: str
    recipient_name: str
    phone_code: str
    phone: str
    country_code: str
    country_name: str
    province: str
    city: str
    district: str | None
    street1: str
    street2: str | None
    postcode: str | None
    email: str | None
    id_type: str
    id_number: str
    is_default: bool
    created_at: datetime
    updated_at: datetime


class AddressDefaultsOut(BaseModel):
    sender: SenderProfileOut | None
    recipient: RecipientProfileOut | None
