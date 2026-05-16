from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    union_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    nickname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_no: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    package_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    platform_order_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    service_code: Mapped[str] = mapped_column(String(32), index=True)
    location_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    submit_later: Mapped[bool] = mapped_column(Boolean, default=False)

    order_status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    payment_status: Mapped[str] = mapped_column(String(32), default="unpaid", index=True)
    payment_channel: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payment_order_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payable_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    payment_currency: Mapped[str | None] = mapped_column(String(8), nullable=True)

    chukou_status: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    tracking_number: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    extra_track_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    shipping_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    submit_failed_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    submit_failed_message: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user_remark: Mapped[str | None] = mapped_column(String(500), nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    success_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    sender: Mapped["OrderSender"] = relationship(
        "OrderSender", back_populates="order", uselist=False, cascade="all, delete-orphan"
    )
    recipient: Mapped["OrderRecipient"] = relationship(
        "OrderRecipient", back_populates="order", uselist=False, cascade="all, delete-orphan"
    )
    parcel: Mapped["OrderParcel"] = relationship(
        "OrderParcel", back_populates="order", uselist=False, cascade="all, delete-orphan"
    )

    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )


class OrderSender(Base):
    __tablename__ = "order_sender"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True, index=True)
    sender_name: Mapped[str] = mapped_column(String(100))
    sender_phone_code: Mapped[str] = mapped_column(String(8))
    sender_phone: Mapped[str] = mapped_column(String(32))
    pickup_point_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pickup_point_name: Mapped[str] = mapped_column(String(100))
    domestic_tracking_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    order: Mapped[Order] = relationship("Order", back_populates="sender")


class OrderRecipient(Base):
    __tablename__ = "order_recipient"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True, index=True)
    recipient_name: Mapped[str] = mapped_column(String(100))
    phone_code: Mapped[str] = mapped_column(String(8))
    phone: Mapped[str] = mapped_column(String(32))
    country_code: Mapped[str] = mapped_column(String(2))
    country_name: Mapped[str] = mapped_column(String(64))
    province: Mapped[str] = mapped_column(String(100))
    city: Mapped[str] = mapped_column(String(100))
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    street1: Mapped[str] = mapped_column(String(255))
    street2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    postcode: Mapped[str] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    id_type: Mapped[str] = mapped_column(String(32))
    id_number: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    order: Mapped[Order] = relationship("Order", back_populates="recipient")


class OrderParcel(Base):
    __tablename__ = "order_parcel"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True, index=True)
    cargo_type: Mapped[str] = mapped_column(String(32))
    weight_g_input: Mapped[int] = mapped_column(Integer)
    length_cm_input: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    width_cm_input: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    height_cm_input: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    weight_g_verified: Mapped[int | None] = mapped_column(Integer, nullable=True)
    length_cm_verified: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    width_cm_verified: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    height_cm_verified: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    charged_weight_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    order: Mapped[Order] = relationship("Order", back_populates="parcel")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    line_no: Mapped[int] = mapped_column(Integer)
    goods_desc_cn: Mapped[str] = mapped_column(String(200))
    goods_desc_en: Mapped[str] = mapped_column(String(200))
    unit_price_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    quantity: Mapped[int] = mapped_column(Integer)
    total_price_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    sku_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hs_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    order: Mapped[Order] = relationship("Order", back_populates="items")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    conversation: Mapped[Conversation] = relationship("Conversation", back_populates="messages")
