
# AI 自动编码指令文档

## 项目概述

本项目是一个小程序后端 API 服务，用于快速 POC（概念验证）演示。提供用户登录、订单管理、AI 客服对话等核心功能。

## 技术栈

- **编程语言**: Python 3.12
- **Web 框架**: FastAPI
- **数据库**: SQLite
- **包管理工具**: uv
- **AI 集成**: 支持 AI 对话服务

## 项目结构

```
mini_program_api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接与初始化
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py       # Pydantic 数据模型
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py          # 认证相关路由
│   │   ├── orders.py        # 订单相关路由
│   │   └── chat.py          # AI 客服对话路由
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py  # 认证服务
│   │   ├── order_service.py # 订单服务
│   │   ├── chat_service.py  # AI 聊天服务
│   │   └── chukou_service.py # 出口易 OpenAPI 服务
│   └── utils/
│       ├── __init__.py
│       ├── helpers.py       # 工具函数
│       └── logging.py       # 日志配置与结构化日志工具
├── logs/                    # 日志目录
├── tests/                   # 测试目录
├── data/                    # SQLite 数据库文件目录
├── pyproject.toml           # uv 项目配置
├── README.md                # 项目说明文档
```

## 核心功能模块

### 1. 用户认证模块

**功能描述**: 小程序登录获取 unionId，用户再次登录时可查看历史订单。

**数据模型**:
```python
# 用户表
users:
  - id: INTEGER PRIMARY KEY
  - union_id: VARCHAR(100) UNIQUE  # 微信 union_id
  - nickname: VARCHAR(100)
  - avatar_url: VARCHAR(500)
  - created_at: DATETIME
  - updated_at: DATETIME
```

**API 端点**:
- `POST /api/auth/login` - 小程序登录
- `GET /api/auth/profile` - 获取用户信息

**业务逻辑**:
1. 小程序通过微信授权获取 code，调用本接口
2. 服务端通过 code 换取 union_id（模拟实现）
3. 检查用户是否存在，不存在则创建
4. 返回 JWT token 用于后续请求认证
5. 登录时返回用户所有订单摘要

### 2. 订单管理模块

**功能描述**: 创建订单、查询订单列表、手动完成订单，按真实业务入参进行落库。

**数据模型**:
```python
# 订单主表
orders:
  - id: INTEGER PRIMARY KEY
  - order_no: VARCHAR(50) UNIQUE
  - user_id: INTEGER FOREIGN KEY
  - package_id: VARCHAR(64) UNIQUE  # 幂等关键
  - platform_order_no: VARCHAR(64)
  - service_code: VARCHAR(32)
  - location_code: VARCHAR(20)
  - submit_later: BOOLEAN
  - order_status: VARCHAR(32)  # draft/submitted/processing/success/failed/cancelled
  - payment_status: VARCHAR(32)  # unpaid/paying/paid/failed/refunded
  - payable_amount: DECIMAL(10,2)
  - payment_currency: VARCHAR(8)
  - user_remark: VARCHAR(500)
  - total_amount: DECIMAL(10,2)
  - created_at: DATETIME
  - updated_at: DATETIME

# 寄件方信息
order_sender:
  - id: INTEGER PRIMARY KEY
  - order_id: INTEGER UNIQUE FOREIGN KEY
  - sender_name: VARCHAR(100)
  - sender_phone_code: VARCHAR(8)
  - sender_phone: VARCHAR(32)
  - pickup_point_id: INTEGER
  - pickup_point_name: VARCHAR(100)
  - domestic_tracking_no: VARCHAR(64)

# 收件方信息
order_recipient:
  - id: INTEGER PRIMARY KEY
  - order_id: INTEGER UNIQUE FOREIGN KEY
  - recipient_name: VARCHAR(100)
  - phone_code: VARCHAR(8)
  - phone: VARCHAR(32)
  - country_code: VARCHAR(2)
  - country_name: VARCHAR(64)
  - province/city/district/street1/street2/postcode/email
  - id_type: VARCHAR(32)
  - id_number: VARCHAR(64)

# 包裹信息
order_parcel:
  - id: INTEGER PRIMARY KEY
  - order_id: INTEGER UNIQUE FOREIGN KEY
  - cargo_type: VARCHAR(32)
  - weight_g_input: INTEGER
  - length_cm_input: DECIMAL(10,2)
  - width_cm_input: DECIMAL(10,2)
  - height_cm_input: DECIMAL(10,2)

# 货品明细
order_items:
  - id: INTEGER PRIMARY KEY
  - order_id: INTEGER FOREIGN KEY
  - line_no: INTEGER
  - goods_desc_cn: VARCHAR(200)
  - goods_desc_en: VARCHAR(200)
  - unit_price_usd: DECIMAL(10,2)
  - quantity: INTEGER
  - total_price_usd: DECIMAL(10,2)
  - sku_code: VARCHAR(64)
  - hs_code: VARCHAR(32)
```

**API 端点**:
- `POST /api/orders` - 创建订单
- `GET /api/orders?order_status=<status>` - 获取订单列表
- `GET /api/orders/{order_id}` - 获取订单详情
- `PUT /api/orders/{order_id}/complete` - 完成订单（POC 手动完成）
- `PUT /api/orders/{order_id}/cancel` - 取消订单

**业务逻辑**:
1. 创建订单时生成唯一订单号
2. `package_id` 必填且唯一，重复提交直接拒绝
3. 入参为五段式：`order/sender/recipient/parcel/items`
4. 关键校验：`items.line_no` 唯一；`total_price_usd = unit_price_usd * quantity`
5. 状态流转：`submitted -> success/cancelled`
6. 用户只能查看自己的订单

### 3. AI 客服对话模块

**功能描述**: AI 客服对话，支持普通请求响应模式。

**API 端点**:
- `POST /api/chat/message` - 发送消息，获取 AI 回复
- `GET /api/chat/history/{conversation_id}` - 获取对话历史
- `POST /api/chat/history` - 创建新对话会话

**数据模型**:
```python
# 对话会话表
conversations:
  - id: INTEGER PRIMARY KEY
  - user_id: INTEGER FOREIGN KEY
  - created_at: DATETIME
  - updated_at: DATETIME

# 消息表
messages:
  - id: INTEGER PRIMARY KEY
  - conversation_id: INTEGER FOREIGN KEY
  - role: VARCHAR(20)  # user/assistant
  - content: TEXT
  - created_at: DATETIME
```

**接口响应模式**:
- 使用标准 JSON 响应格式
- AI 回复完整返回，不使用流式传输
- 每次请求包含完整的用户消息和 AI 回复
- 支持会话上下文关联

## 认证与授权

### JWT Token

- 使用 HS256 算法签名
- Token 有效期：7 天
- Token 包含用户 ID 和过期时间
- 所有需要认证的接口通过 `Authorization: Bearer <token>` 头部

### 请求认证装饰器

```python
# 认证依赖
async def get_current_user(token: str = Header(...)) -> User:
    # 验证 token
    # 返回当前用户对象
```

## 错误处理

### 统一错误响应格式

```python
{
    "code": 40001,  # 业务错误码
    "message": "错误描述",
    "data": null
}
```

### 错误码定义

| 错误码 | 说明 |
|--------|------|
| 40001 | 参数错误 |
| 40002 | 认证失败 |
| 40003 | 权限不足 |
| 40004 | 资源不存在 |
| 40005 | 业务逻辑错误 |
| 50001 | 服务器内部错误 |

## 数据库初始化

### 自动初始化

- 应用启动时自动创建数据库表
- 使用 SQLAlchemy + SQLite
- 支持数据库迁移（可选）

### 初始化脚本

首次启动时自动创建必要表结构和初始数据。

## 配置管理

### 环境变量

```bash
# .env 文件
DATABASE_URL=sqlite:///./data/app.db
SECRET_KEY=your-secret-key-here
AI_API_KEY=your-ai-api-key
AI_BASE_URL=https://api.example.com
COZE_STREAM_RUN_URL=https://hkq24jmpqq.coze.site/stream_run
COZE_TOKEN=your-coze-token
COZE_PROJECT_ID=7637794329490407450
CHUKOU_API_BASE_URL=https://openapi.chukou1.cn:82
CHUKOU_ACCESS_TOKEN=your-chukou-access-token
CHUKOU_TIMEOUT_SECONDS=30
LOG_LEVEL=INFO
```

### 配置类

使用 Pydantic Settings 管理配置，支持环境变量覆盖。

### 日志架构

- 应用启动时创建 logs/yyyyMMdd 目录，并注册 app.log、system_requests.log、external_api.log 三类日志文件。
- 系统接口请求日志由 FastAPI 中间件统一记录，字段包括 request_id、method、path、query_params、headers、request_body、status_code、elapsed_ms。
- 第三方 API 日志由 service 层统一记录，至少包含 service、method、url、request_headers、request_body、status_code、response_body、elapsed_ms、error。
- Coze 与出口易调用均必须记录 request/response；敏感字段如 Authorization、token、cookie 必须脱敏。
- 所有接口响应头回传 X-Request-ID，便于前后端与日志对账。

## 开发规范

### 代码风格

- 遵循 PEP 8 规范
- 使用 type hints 类型注解
- 所有函数和类必须有 docstring
- 使用 async/await 异步编程

### 文件组织

- 路由处理：routers/
- 业务逻辑：services/
- 数据模型：models/
- 工具函数：utils/

### API 设计规范

1. 使用 RESTful 风格 URL
2. 所有请求/响应使用 JSON
3. 分页使用 limit/offset 方式
4. 日期时间使用 ISO 8601 格式
5. 金额使用分为单位或 Decimal 类型

## 测试要求

### 单元测试

- 每个 service 模块需要有对应的测试文件
- 使用 pytest 框架
- Mock 外部依赖

### 测试覆盖

- 核心业务逻辑 100% 覆盖
- API 端点基本覆盖

## 部署说明

### 开发环境

```bash
# 安装依赖
uv sync

# 运行开发服务器
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 生产环境

```bash
# 构建
uv build

# 使用 gunicorn + uvicorn workers
uv run gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## 注意事项

1. **POC 版本**: 本版本为快速验证版本，部分功能简化实现
2. **安全性**: 生产环境需加强安全措施（密钥管理、速率限制等）
3. **AI 服务**: 需要配置实际的 AI API 密钥
4. **数据库**: 当前使用 SQLite，生产环境建议迁移到 PostgreSQL/MySQL
5. **日志**: 所有操作需记录日志便于调试，系统请求与第三方 API 调用日志必须可追踪且包含 request_id

## 编码优先级

1. 完成核心数据模型和数据库初始化
2. 实现认证模块（登录、JWT）
3. 实现订单 CRUD 功能
4. 实现 AI 客服对话
5. 添加测试和错误处理
6. 优化和完善文档