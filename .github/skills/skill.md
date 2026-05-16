# 小程序后端 API - 技能定义文档

## 项目信息

- **项目名称**: mini_program_api
- **项目类型**: RESTful API 后端服务
- **目标用户**: 微信小程序前端开发团队

## 技术能力要求

### 1. Python 3.12 技能

#### 1.1 核心语法

- 异步编程：`async/await` 语法
- 类型注解：完整使用 `typing` 模块
- 数据类：`dataclasses` 和 `Pydantic` 模型
- 上下文管理：`with` 语句和 `contextmanager`
- 装饰器：自定义装饰器和 FastAPI 依赖注入

#### 1.2 标准库

- `datetime`: 日期时间处理
- `json`: JSON 编解码
- `hashlib`: 加密哈希（JWT 签名）
- `secrets`: 安全随机数生成
- `uuid`: UUID 生成
- `typing`: 类型注解和泛型

### 2. FastAPI 框架技能

#### 2.1 路由与请求

```python
# 路径参数
@router.get("/items/{item_id}")

# 查询参数
@router.get("/items", params={"skip": 0, "limit": 100})

# 请求体
@router.post("/items", response_model=Item)

# Header 参数
async def read_item(x_token: str = Header(...))

# 表单数据
@router.post("/login", form=LoginForm)
```

#### 2.2 响应处理

```python
# JSON 响应
@router.get("/items", response_model=list[Item])

# 自定义响应
from fastapi.responses import StreamingResponse, JSONResponse

# 文件下载
from fastapi.responses import FileResponse

# 流式响应 (SSE)
async def stream_chat():
    async def event_generator():
        for chunk in response_stream():
            yield f"data: {chunk}\n\n"
        yield "event: done\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

#### 2.3 依赖注入

```python
from fastapi import Depends

# 函数依赖
async def get_db():
    yield Database()

# 类依赖
class Container:
    db: Database

container = Container()

# 使用
@router.get("/items", dependencies=[Depends(get_db)])
```

#### 2.4 中间件与异常

```python
from fastapi import Middleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# 自定义异常
class BusinessException(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
```

### 3. 数据库技能

#### 3.1 SQLite + SQLAlchemy

```python
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    union_id = Column(String(100), unique=True, index=True)
    nickname = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

# 数据库连接
DATABASE_URL = "sqlite:///./data/app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# CRUD 操作
def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()
```

#### 3.2 索引与查询优化

```python
# 索引
from sqlalchemy import Index
Index('idx_user_union_id', 'union_id')

# 分页查询
def get_orders_paginated(db: Session, skip: int = 0, limit: int = 20):
    return db.query(Order).offset(skip).limit(limit).all()

# 关联查询
from sqlalchemy.orm import joinedload
def get_order_with_items(db: Session, order_id: int):
    return db.query(Order).options(joinedload(Order.items)).filter(Order.id == order_id).first()
```

### 4. JWT 认证技能

#### 4.1 Token 生成与验证

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise BusinessException(40002, "Token 无效或已过期")
```

#### 4.2 依赖注入认证

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise BusinessException(40002, "认证失败")

    user = get_user(db, int(user_id))
    if user is None:
        raise BusinessException(40004, "用户不存在")
    return user
```

### 5. AI 集成技能

#### 5.1 普通请求响应模式

```python
import httpx

async def chat_with_ai(user_message: str, conversation_history: list[dict]) -> str:
    """调用外部 AI API 并获取完整回复"""
    messages = conversation_history + [{"role": "user", "content": user_message}]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.example.com/v1/chat/completions",
            json={
                "model": "gpt-3.5-turbo",
                "messages": messages
            },
            headers={"Authorization": f"Bearer {AI_API_KEY}"},
            timeout=30.0
        )
        result = response.json()
        return result["choices"][0]["message"]["content"]

@router.post("/chat/message")
async def send_message(request: ChatRequest):
    # 获取对话历史
    history = await chat_service.get_conversation_history(request.conversation_id)

    # 调用 AI
    ai_response = await chat_with_ai(request.message, history)

    # 保存消息
    await chat_service.save_message(request.conversation_id, "user", request.message)
    await chat_service.save_message(request.conversation_id, "assistant", ai_response)

    return {
        "code": 0,
        "message": "success",
        "data": {
            "conversation_id": request.conversation_id,
            "message": ai_response
        }
    }
```

#### 5.2 AI 对话服务实现

```python
from sqlalchemy.orm import Session
from app.models.database import Conversation, Message
from typing import List

class ChatService:
    def __init__(self, db: Session):
        self.db = db

    async def create_conversation(self, user_id: int) -> Conversation:
        """创建新对话会话"""
        conversation = Conversation(user_id=user_id)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    async def get_conversation_history(self, conversation_id: int) -> List[dict]:
        """获取对话历史"""
        messages = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).all()

        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

    async def save_message(self, conversation_id: int, role: str, content: str) -> Message:
        """保存消息记录"""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
```

### 6. 数据验证技能

#### 6.1 Pydantic 模型

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class UserBase(BaseModel):
    union_id: str = Field(..., min_length=1, max_length=100)
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(..., min_length=1)
    total_amount: Decimal = Field(..., gt=0)

class OrderItemCreate(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=200)
    quantity: int = Field(..., gt=0)
    price: Decimal = Field(..., ge=0)

# 枚举类型
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
```

#### 6.2 自定义验证器

```python
class UserRegister(BaseModel):
    phone: str = Field(..., regex=r"^1[3-9]\d{9}$")

    @validator("phone")
    def validate_phone(cls, v):
        if not v.isdigit():
            raise ValueError("手机号必须为数字")
        return v
```

### 7. 配置管理技能

#### 7.1 Pydantic Settings

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/app.db"
    secret_key: str
    ai_api_key: str = ""
    ai_base_url: str = "https://api.example.com"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()
```

#### 7.2 环境变量加载

```bash
# .env 文件
DATABASE_URL=sqlite:///./data/app.db
SECRET_KEY=your-secret-key-change-in-production
AI_API_KEY=your-api-key
AI_BASE_URL=https://api.openai.com/v1
LOG_LEVEL=INFO
```

### 8. 日志与调试技能

#### 8.1 日志配置

```python
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(
            "logs/app.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
    ]
)

logger = logging.getLogger(__name__)
```

#### 8.2 请求日志中间件

```python
from starlette.middleware.base import BaseHTTPMiddleware
import time

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s"
        )
        return response
```

### 9. 测试技能

#### 9.1 pytest 基础

```python
import pytest
from httpx import AsyncClient
from app.main import app
from app.database import Base, engine, SessionLocal

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db):
    def _get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = _get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_login():
    response = await client.post("/api/auth/login", json={
        "code": "test_code"
    })
    assert response.status_code == 200
    assert "token" in response.json()
```

#### 9.2 Mock 对象

```python
from unittest.mock import Mock, AsyncMock, patch

def test_order_creation():
    with patch("app.services.order_service.generate_order_no", return_value="ORD20240101"):
        response = client.post("/api/orders", json={
            "items": [
                {"product_name": "测试商品", "quantity": 1, "price": 100.00}
            ],
            "total_amount": 100.00
        })
        assert response.status_code == 200
```

## 代码模板参考

### 1. FastAPI 项目初始化模板

```python
# app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import engine, Base
from app.routers import auth, orders, chat
from app.middleware import LoggingMiddleware

# 创建表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="小程序后端 API",
    description="小程序 POC 验证后端服务",
    version="1.0.0"
)

# 注册中间件
app.add_middleware(LoggingMiddleware)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(orders.router, prefix="/api/orders", tags=["订单"])
app.include_router(chat.router, prefix="/api/chat", tags=["客服"])

# 异常处理
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"code": 40001, "message": "参数错误", "data": exc.errors()}
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail}
    )
```

### 2. Service 层模板

```python
# app/services/order_service.py
from sqlalchemy.orm import Session
from app.models.schemas import OrderCreate, OrderResponse
from app.models.database import Order, OrderItem
from app.services.order_service import generate_order_no
from typing import List

class OrderService:
    def __init__(self, db: Session):
        self.db = db

    def create_order(self, user_id: int, order_data: OrderCreate) -> OrderResponse:
        order_no = generate_order_no()

        order = Order(
            order_no=order_no,
            user_id=user_id,
            total_amount=order_data.total_amount,
            status="pending"
        )
        self.db.add(order)
        self.db.flush()

        for item in order_data.items:
            order_item = OrderItem(
                order_id=order.id,
                product_name=item.product_name,
                quantity=item.quantity,
                price=item.price
            )
            self.db.add(order_item)

        self.db.commit()
        self.db.refresh(order)

        return self._to_response(order)

    def _to_response(self, order: Order) -> OrderResponse:
        return OrderResponse(
            id=order.id,
            order_no=order.order_no,
            user_id=order.user_id,
            total_amount=order.total_amount,
            status=order.status,
            items=[{"product_name": i.product_name, "quantity": i.quantity, "price": i.price} for i in order.items],
            created_at=order.created_at,
            updated_at=order.updated_at
        )
```

### 3. 流式响应模板

```python
# app/services/chat_stream.py
import asyncio
import json
from typing import AsyncGenerator

async def generate_stream(user_message: str, conversation_id: int) -> AsyncGenerator[str, None]:
    """生成 SSE 格式的流式响应"""

    # 模拟 AI 处理
    ai_response = process_user_message(user_message)

    # 逐字符发送
    for char in ai_response:
        chunk = {
            "type": "content",
            "content": char,
            "conversation_id": conversation_id
        }
        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.02)  # 控制发送速率

    # 发送完成信号
    yield f"event: done\n\n"
```

## 性能优化建议

1. **数据库连接池**: SQLite 使用单连接，避免并发写入
2. **索引优化**: 对高频查询字段添加索引
3. **缓存**: 使用内存缓存减少数据库查询
4. **异步**: 所有 I/O 操作使用异步方式
5. **分页**: 列表查询必须支持分页

## 安全检查清单

- [ ] 所有密码加密存储
- [ ] JWT Token 设置合理过期时间
- [ ] 输入参数严格验证
- [ ] SQL 注入防护（使用 ORM）
- [ ] 敏感信息不写入日志
- [ ] CORS 配置正确
- [ ] 速率限制（生产环境）

## 文档生成要求

编码完成后，确保包含以下文档：

1. **README.md**: 安装、配置、运行说明
2. **API 文档**: 使用 FastAPI 自动生成的 OpenAPI 文档
3. **数据字典**: 数据库表结构说明
4. **错误码表**: 业务错误码定义