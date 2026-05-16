# 小程序后端 API 服务

本项目是一个基于 FastAPI 框架构建的小程序后端 API 服务，专为快速 POC（概念验证）而设计。提供用户认证、订单管理、AI 客服对话等核心功能。

## 项目简介

本 API 服务旨在帮助开发团队快速验证小程序业务逻辑，通过简洁的接口设计和完善的文档支持，实现从开发到部署的快速迭代。服务采用 Python 3.12 编写，使用 FastAPI 作为 Web 框架，SQLite 作为数据存储，具备良好的扩展性和可维护性。

项目的核心价值在于快速交付。传统的后端开发需要配置复杂的数据库连接、编写冗长的配置代码，而本项目通过模块化的设计和自动化的初始化流程，大幅缩短了开发周期。所有核心功能都已封装为独立模块，开发者可以根据业务需求灵活组合使用。同时，服务内置了完善的错误处理机制和统一的响应格式，使得前后端对接更加顺畅。

## 核心功能

本项目提供以下五个核心功能模块，覆盖小程序常见的业务场景。

**用户认证模块**实现了基于微信 UnionId 的登录机制。小程序端通过微信授权获取用户 code，服务端验证后返回 JWT token，后续请求通过 token 进行身份认证。用户首次登录时系统自动创建用户档案，再次登录时可获取历史登录信息和订单摘要数据。认证流程设计简洁高效，既保证了安全性，又降低了开发复杂度。

**订单管理模块**提供了完整的订单生命周期管理。支持创建订单、查询订单列表、查看订单详情、手动完成订单、取消订单等操作。订单状态遵循标准的状态流转机制，从待支付到已支付再到已完成，每个状态都有明确的时间戳记录。POC 版本特别支持手动完成订单功能，方便进行业务演示和测试验证。

**AI 客服对话模块**实现了智能客服功能。每个用户拥有独立的对话会话，支持查看历史对话记录。AI 响应以完整消息形式返回，支持会话上下文关联，提供流畅的对话体验。

**数据持久化模块**基于 SQLite 数据库实现，使用 SQLAlchemy ORM 进行数据库操作。应用启动时自动创建必要的数据库表和索引，无需手动初始化。同时提供了数据库迁移的基础结构，支持后续平滑升级到 PostgreSQL 或 MySQL 等生产级数据库。

**日志与监控模块**记录所有 API 请求的详细日志，包括请求方法、路径、响应状态码和耗时。日志采用分级管理，支持DEBUG、INFO、WARNING、ERROR 四个级别。异常信息自动捕获并记录，便于问题排查和性能优化。

## 技术栈

本项目的技术选型遵循"简洁实用"的原则，在保证功能完整性的同时，最大程度降低技术门槛和学习成本。

**编程语言**采用 Python 3.12，这是目前最新的稳定版本，引入了更完善的内置类型注解支持和性能优化。选择 Python 的原因在于其丰富的生态系统、简洁的语法和强大的社区支持。无论是快速开发还是后期维护，Python 都能提供良好的开发体验。

**Web 框架**选用 FastAPI，这是一个现代、高性能的 Python Web 框架。FastAPI 基于 Starlette 构建，自动提供 OpenAPI 文档，支持异步请求处理，内置数据验证和序列化功能。使用 FastAPI 可以显著减少样板代码的编写，同时获得开箱即用的类型安全和自动文档生成能力。

**数据库**使用 SQLite，这是一个轻量级的嵌入式数据库，无需独立的服务进程。SQLite 将整个数据库存储在一个单独的磁盘文件中，部署简单，运维成本低。对于 POC 验证和小规模应用来说，SQLite 的性能完全满足需求。当业务规模扩大时，也可以轻松迁移到其他数据库系统。

**包管理工具**使用 uv，这是一个用 Rust 编写的极速 Python 包管理器。uv 提供了比 pip 更快更可靠的依赖解析和安装能力，同时兼容 pyproject.toml 配置格式。使用 uv 可以大幅缩短依赖安装时间，提升开发效率。

**AI 集成**方面，服务设计了通用的 AI API 接口层，可以对接各类支持流式输出的 AI 服务。默认实现了基于 HTTP 流式响应的 AI 调用逻辑，开发者只需配置相应的 API 密钥和端点即可使用。

## 项目结构

项目采用分层架构设计，将路由处理、业务逻辑和数据操作分离到不同的模块中。这种设计模式使得代码结构清晰，便于维护和测试。

```
mini_program_api/
├── app/                      # 应用主目录
│   ├── __init__.py           # 模块初始化
│   ├── main.py               # 应用入口点
│   ├── config.py             # 配置管理模块
│   ├── database.py           # 数据库连接和初始化
│   ├── models/               # 数据模型目录
│   │   ├── __init__.py
│   │   ├── database.py       # SQLAlchemy 模型定义
│   │   └── schemas.py        # Pydantic 数据模型
│   ├── routers/              # 路由目录
│   │   ├── __init__.py
│   │   ├── auth.py           # 认证相关路由
│   │   ├── orders.py         # 订单相关路由
│   │   └── chat.py          # AI 客服路由
│   ├── services/             # 业务逻辑目录
│   │   ├── __init__.py
│   │   ├── auth_service.py  # 认证业务逻辑
│   │   ├── order_service.py # 订单业务逻辑
│   │   └── chat_service.py   # AI 客服业务逻辑
│   └── utils/                # 工具函数目录
│       ├── __init__.py
│       ├── security.py        # 安全相关工具
│       └── helpers.py        # 通用辅助函数
├── data/                     # 数据存储目录
├── logs/                      # 日志目录
├── tests/                     # 测试目录
├── pyproject.toml            # 项目配置文件
├── uv.lock                   # 依赖锁定文件
├── README.md                 # 项目说明文档
├── instruction.md            # 开发指令文档
└── skill.md                  # 技能定义文档
```

## 快速开始

### 环境准备

在开始之前，请确保本地环境已安装 Python 3.12 和 uv 包管理工具。如果尚未安装 uv，可以通过以下命令安装：

```bash
# 使用 pip 安装 uv
pip install uv

# 或者使用 curl 安装（Linux/macOS）
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### SQLite 说明（POC）

POC版本统一使用SQLite。

- 运行API时：Python内置sqlite3模块，通常不需要额外安装数据库驱动。
- 本地排查数据时：建议安装sqlite3命令行工具。

Windows（可选安装sqlite3命令行）：

```bash
winget install SQLite.SQLite
sqlite3 --version
```

Linux/macOS（通常已自带，或按系统包管理器安装）：

```bash
sqlite3 --version
```

### 安装步骤

克隆项目代码后，进入项目目录并安装依赖：

```bash
# 进入项目目录
cd mini_program_api

# 使用 uv 安装依赖
uv sync
```

安装过程中，uv 会自动解析 pyproject.toml 中的依赖声明，下载并安装所有必要的包。安装完成后，所有依赖都会锁定在 uv.lock 文件中，确保团队成员的依赖环境一致。

### 配置说明

项目使用环境变量进行配置。在项目根目录创建 .env 文件，添加以下配置项：

```bash
# .env 配置文件示例

# 数据库配置
DATABASE_URL=sqlite:///./data/app.db

# JWT 密钥配置（生产环境请使用复杂的随机字符串）
SECRET_KEY=your-secret-key-change-in-production-please-use-complex-string

# AI 服务配置（可选，留空则使用模拟响应）
AI_API_KEY=your-ai-api-key
AI_BASE_URL=https://api.openai.com/v1

# Coze 流式聊天配置
COZE_STREAM_RUN_URL=https://hkq24jmpqq.coze.site/stream_run
COZE_TOKEN=your-coze-token
COZE_PROJECT_ID=7637794329490407450

# 出口易 OpenAPI 配置
CHUKOU_API_BASE_URL=https://openapi.chukou1.cn:82
CHUKOU_ACCESS_TOKEN=your-chukou-access-token
CHUKOU_TIMEOUT_SECONDS=30

# 日志级别配置
LOG_LEVEL=INFO
```

如果不创建 .env 文件，程序会使用代码中的默认值。开发环境下可以直接使用默认配置，生产环境必须修改 SECRET_KEY。

首次运行前，建议先确保数据库目录存在：

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force data
```

Linux/macOS：

```bash
mkdir -p data
```

### 启动服务

依赖安装和配置完成后，通过以下命令启动开发服务器：

```bash
# 启动开发服务器
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

命令执行后，服务会在 8000 端口启动。打开浏览器访问 http://localhost:8000/docs 可以查看自动生成的 API 文档。FastAPI 的交互式文档基于 OpenAPI 规范构建，支持在线调试所有接口。

## API 接口文档

服务启动后，可以通过访问以下地址查看完整的 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### curl 快速调用示例

以下示例默认服务运行在 `http://localhost:8000`。

```bash
# 1) 基础地址
BASE_URL="http://localhost:8000"

# 2) 健康检查
curl -X GET "$BASE_URL/health"

# 3) 登录（获取 token）
curl -X POST "$BASE_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
        "code": "demo-login-code",
        "nickname": "测试用户",
        "avatar_url": "https://example.com/avatar.png"
    }'

# 将登录响应中的 data.token 复制到这里
TOKEN="your-jwt-token"

# 4) 获取当前用户信息
curl -X GET "$BASE_URL/api/auth/profile" \
    -H "Authorization: Bearer $TOKEN"

# 5) 创建订单
curl -X POST "$BASE_URL/api/orders" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "order": {
            "package_id": "PKG202605160001",
            "platform_order_no": "PLAT-10001",
            "service_code": "CUE",
            "location_code": "GZ",
            "submit_later": false,
            "user_remark": "易碎品请轻拿轻放",
            "payable_amount": 39.80,
            "payment_currency": "CNY"
        },
        "sender": {
            "sender_name": "张三",
            "sender_phone_code": "+86",
            "sender_phone": "13800138000",
            "pickup_point_id": 1,
            "pickup_point_name": "广州天河揽收点",
            "domestic_tracking_no": "SF1234567890"
        },
        "recipient": {
            "recipient_name": "David Mcaffee",
            "phone_code": "+1",
            "phone": "9376898216",
            "country_code": "US",
            "country_name": "United States",
            "province": "Florida",
            "city": "Coral Springs",
            "district": "",
            "street1": "9110 NW 21st street",
            "street2": "",
            "postcode": "45429",
            "email": "david@example.com",
            "id_type": "PASSPORT",
            "id_number": "P12345678"
        },
        "parcel": {
            "cargo_type": "general",
            "weight_g_input": 600,
            "length_cm_input": 25,
            "width_cm_input": 10,
            "height_cm_input": 20
        },
        "items": [
            {
                "line_no": 1,
                "goods_desc_cn": "小梦书包",
                "goods_desc_en": "bag",
                "unit_price_usd": 5.00,
                "quantity": 2,
                "total_price_usd": 10.00,
                "sku_code": "bag-y001",
                "hs_code": "42021290"
            }
        ]
    }'

# 6) 查询订单列表
curl -X GET "$BASE_URL/api/orders?order_status=submitted&skip=0&limit=20" \
    -H "Authorization: Bearer $TOKEN"

# 7) 查询订单详情（将 1 替换为真实 order_id）
curl -X GET "$BASE_URL/api/orders/1" \
    -H "Authorization: Bearer $TOKEN"

# 8) 完成订单（将 1 替换为真实 order_id）
curl -X PUT "$BASE_URL/api/orders/1/complete" \
    -H "Authorization: Bearer $TOKEN"

# 9) 取消订单（将 1 替换为真实 order_id）
curl -X PUT "$BASE_URL/api/orders/1/cancel" \
    -H "Authorization: Bearer $TOKEN"

# 10) 创建聊天会话
curl -X POST "$BASE_URL/api/chat/history" \
    -H "Authorization: Bearer $TOKEN"

# 11) 发送聊天消息（将 1 替换为真实 conversation_id）
curl -X POST "$BASE_URL/api/chat/message" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "message": "我想查询我的订单状态",
        "conversation_id": 1
    }'

# 12) 查询聊天历史（将 1 替换为真实 conversation_id）
curl -X GET "$BASE_URL/api/chat/history/1" \
    -H "Authorization: Bearer $TOKEN"
```

### 认证相关接口

**登录接口**是小程序接入的第一个接口。小程序通过微信授权获取 code 后，调用此接口完成用户认证。接口会验证 code 的有效性，检查用户是否存在，不存在则自动创建。用户认证成功后返回 JWT token，后续请求需要在请求头中携带此 token。

```
POST /api/auth/login
Content-Type: application/json

请求体：
{
    "code": "微信授权code",
    "nickname": "用户昵称（可选）",
    "avatar_url": "头像URL（可选）"
}

响应示例：
{
    "code": 0,
    "message": "登录成功",
    "data": {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "user": {
            "id": 1,
            "union_id": "oXXXXXXXXXXXXXX",
            "nickname": "用户名",
            "avatar_url": "https://example.com/avatar.png",
            "created_at": "2024-01-01T00:00:00"
        },
        "orders_summary": {
            "total_count": 5,
            "pending_count": 1,
            "completed_count": 4
        }
    }
}
```

**获取用户信息接口**用于获取当前登录用户的详细信息。请求需要携带有效的 JWT token，接口会解析 token 中的用户ID，查询并返回完整的用户档案。

```
GET /api/auth/profile
Authorization: Bearer <token>

响应示例：
{
    "code": 0,
    "message": "success",
    "data": {
        "id": 1,
        "union_id": "oXXXXXXXXXXXXXX",
        "nickname": "用户名",
        "avatar_url": "https://example.com/avatar.png",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }
}
```

### 订单相关接口

**创建订单接口**用于生成新的订单。请求体采用真实业务结构，包含订单主信息、寄件方、收件方、包裹信息和货品明细。

字段必填矩阵（创建订单）：

| 路径 | 必填 | 类型 | 说明 |
|------|------|------|------|
| order.package_id | 是 | string | 包裹唯一标识，幂等关键 |
| order.platform_order_no | 否 | string | 平台订单号 |
| order.service_code | 是 | string | 物流服务代码 |
| order.location_code | 否 | string | 处理点/仓代码 |
| order.submit_later | 否 | boolean | 是否稍后提审，默认 false |
| order.user_remark | 否 | string | 用户备注 |
| order.payable_amount | 是 | number | 应付金额 |
| order.payment_currency | 是 | string | 货币，如 CNY |
| sender.sender_name | 是 | string | 寄件人姓名 |
| sender.sender_phone_code | 是 | string | 寄件方国家区号 |
| sender.sender_phone | 是 | string | 寄件方手机号 |
| sender.pickup_point_id | 否 | integer | 揽收点 ID |
| sender.pickup_point_name | 是 | string | 揽收点名称 |
| sender.domestic_tracking_no | 否 | string | 国内快递单号 |
| recipient.recipient_name | 是 | string | 收件人姓名 |
| recipient.phone_code | 是 | string | 收件方国家区号 |
| recipient.phone | 是 | string | 收件方电话 |
| recipient.country_code | 是 | string(2) | 国家二字码，会自动转大写 |
| recipient.country_name | 是 | string | 国家名称 |
| recipient.province | 是 | string | 省/州 |
| recipient.city | 是 | string | 城市 |
| recipient.district | 否 | string | 区县 |
| recipient.street1 | 是 | string | 详细地址 |
| recipient.street2 | 否 | string | 地址补充 |
| recipient.postcode | 是 | string | 邮编 |
| recipient.email | 否 | string | 邮箱 |
| recipient.id_type | 是 | string | 证件类型 |
| recipient.id_number | 是 | string | 证件号 |
| parcel.cargo_type | 是 | string | 货物类型 |
| parcel.weight_g_input | 是 | integer | 重量(g)，>0 |
| parcel.length_cm_input | 是 | number | 长(cm)，>0 |
| parcel.width_cm_input | 是 | number | 宽(cm)，>0 |
| parcel.height_cm_input | 是 | number | 高(cm)，>0 |
| items | 是 | array | 至少 1 条 |
| items[].line_no | 是 | integer | 行号，需唯一且>=1 |
| items[].goods_desc_cn | 是 | string | 中文品名 |
| items[].goods_desc_en | 是 | string | 英文品名 |
| items[].unit_price_usd | 是 | number | USD 单价，>0 |
| items[].quantity | 是 | integer | 数量，>=1 |
| items[].total_price_usd | 是 | number | 小计，必须=单价*数量 |
| items[].sku_code | 否 | string | SKU |
| items[].hs_code | 否 | string | HS 编码 |

```
POST /api/orders
Authorization: Bearer <token>
Content-Type: application/json

请求体：
{
    "order": {
        "package_id": "PKG202605160001",
        "platform_order_no": "PLAT-10001",
        "service_code": "CUE",
        "location_code": "GZ",
        "submit_later": false,
        "user_remark": "易碎品请轻拿轻放",
        "payable_amount": 39.80,
        "payment_currency": "CNY"
    },
    "sender": {
        "sender_name": "张三",
        "sender_phone_code": "+86",
        "sender_phone": "13800138000",
        "pickup_point_id": 1,
        "pickup_point_name": "广州天河揽收点",
        "domestic_tracking_no": "SF1234567890"
    },
    "recipient": {
        "recipient_name": "David Mcaffee",
        "phone_code": "+1",
        "phone": "9376898216",
        "country_code": "US",
        "country_name": "United States",
        "province": "Florida",
        "city": "Coral Springs",
        "district": "",
        "street1": "9110 NW 21st street",
        "street2": "",
        "postcode": "45429",
        "email": "david@example.com",
        "id_type": "PASSPORT",
        "id_number": "P12345678"
    },
    "parcel": {
        "cargo_type": "general",
        "weight_g_input": 600,
        "length_cm_input": 25,
        "width_cm_input": 10,
        "height_cm_input": 20
    },
    "items": [
        {
            "line_no": 1,
            "goods_desc_cn": "小梦书包",
            "goods_desc_en": "bag",
            "unit_price_usd": 5.00,
            "quantity": 2,
            "total_price_usd": 10.00,
            "sku_code": "bag-y001",
            "hs_code": "42021290"
        }
    ]
}

响应示例：
{
    "code": 0,
    "message": "Order created",
    "data": {
        "id": 1,
        "order_no": "ORD202605160001",
        "user_id": 1,
        "package_id": "PKG202605160001",
        "platform_order_no": "PLAT-10001",
        "service_code": "CUE",
        "location_code": "GZ",
        "submit_later": false,
        "order_status": "submitted",
        "payment_status": "unpaid",
        "payable_amount": "39.80",
        "payment_currency": "CNY",
        "user_remark": "易碎品请轻拿轻放",
        "total_amount": "39.80",
        "sender": {
            "sender_name": "张三",
            "sender_phone_code": "+86",
            "sender_phone": "13800138000",
            "pickup_point_id": 1,
            "pickup_point_name": "广州天河揽收点",
            "domestic_tracking_no": "SF1234567890"
        },
        "recipient": {
            "recipient_name": "David Mcaffee",
            "phone_code": "+1",
            "phone": "9376898216",
            "country_code": "US",
            "country_name": "United States",
            "province": "Florida",
            "city": "Coral Springs",
            "district": "",
            "street1": "9110 NW 21st street",
            "street2": "",
            "postcode": "45429",
            "email": "david@example.com",
            "id_type": "PASSPORT",
            "id_number": "P12345678"
        },
        "parcel": {
            "cargo_type": "general",
            "weight_g_input": 600,
            "length_cm_input": "25.00",
            "width_cm_input": "10.00",
            "height_cm_input": "20.00",
            "weight_g_verified": null,
            "length_cm_verified": null,
            "width_cm_verified": null,
            "height_cm_verified": null,
            "charged_weight_g": null
        },
        "items": [
            {
                "line_no": 1,
                "goods_desc_cn": "小梦书包",
                "goods_desc_en": "bag",
                "unit_price_usd": "5.00",
                "quantity": 2,
                "total_price_usd": "10.00",
                "sku_code": "bag-y001",
                "hs_code": "42021290"
            }
        ],
        "created_at": "2024-01-01T12:00:00",
        "updated_at": "2024-01-01T12:00:00"
    }
}
```

**订单列表接口**用于获取当前用户的所有订单。支持分页查询和状态筛选。

```
GET /api/orders?order_status=submitted&skip=0&limit=20
Authorization: Bearer <token>

响应示例：
{
    "code": 0,
    "message": "success",
    "data": {
        "items": [
            {
                "id": 1,
                "order_no": "ORD202605160001",
                "package_id": "PKG202605160001",
                "service_code": "CUE",
                "total_amount": "39.80",
                "order_status": "submitted",
                "created_at": "2024-01-01T12:00:00"
            }
        ],
        "total": 1,
        "skip": 0,
        "limit": 20
    }
}
```

**订单详情接口**用于获取单个订单的完整信息，包括订单状态变更记录。

```
GET /api/orders/{order_id}
Authorization: Bearer <token>

响应示例：
{
    "code": 0,
    "message": "success",
    "data": {
        "id": 1,
        "order_no": "ORD202605160001",
        "user_id": 1,
        "package_id": "PKG202605160001",
        "platform_order_no": "PLAT-10001",
        "service_code": "CUE",
        "location_code": "GZ",
        "submit_later": false,
        "order_status": "success",
        "payment_status": "unpaid",
        "payable_amount": "39.80",
        "payment_currency": "CNY",
        "user_remark": "易碎品请轻拿轻放",
        "total_amount": "39.80",
        "sender": {
            "sender_name": "张三",
            "sender_phone_code": "+86",
            "sender_phone": "13800138000",
            "pickup_point_id": 1,
            "pickup_point_name": "广州天河揽收点",
            "domestic_tracking_no": "SF1234567890"
        },
        "recipient": {
            "recipient_name": "David Mcaffee",
            "phone_code": "+1",
            "phone": "9376898216",
            "country_code": "US",
            "country_name": "United States",
            "province": "Florida",
            "city": "Coral Springs",
            "district": "",
            "street1": "9110 NW 21st street",
            "street2": "",
            "postcode": "45429",
            "email": "david@example.com",
            "id_type": "PASSPORT",
            "id_number": "P12345678"
        },
        "parcel": {
            "cargo_type": "general",
            "weight_g_input": 600,
            "length_cm_input": "25.00",
            "width_cm_input": "10.00",
            "height_cm_input": "20.00",
            "weight_g_verified": null,
            "length_cm_verified": null,
            "width_cm_verified": null,
            "height_cm_verified": null,
            "charged_weight_g": null
        },
        "items": [
            {
                "line_no": 1,
                "goods_desc_cn": "小梦书包",
                "goods_desc_en": "bag",
                "unit_price_usd": "5.00",
                "quantity": 2,
                "total_price_usd": "10.00",
                "sku_code": "bag-y001",
                "hs_code": "42021290"
            }
        ],
        "created_at": "2024-01-01T12:00:00",
        "updated_at": "2024-01-01T12:30:00"
    }
}
```

**完成订单接口**是 POC 版本特有的功能，允许手动将订单状态标记为已完成。

```
PUT /api/orders/{order_id}/complete
Authorization: Bearer <token>

响应示例：
{
    "code": 0,
    "message": "Order completed"
}
```

**取消订单接口**允许用户取消未完成的订单。

```
PUT /api/orders/{order_id}/cancel
Authorization: Bearer <token>

响应示例：
{
    "code": 0,
    "message": "Order cancelled"
}
```

### AI 客服接口

**发送消息接口**是 AI 客服的核心接口。客户端发送消息后，服务端返回 AI 的完整回复内容。

```
POST /api/chat/message
Authorization: Bearer <token>
Content-Type: application/json

请求体：
{
    "message": "我想查询我的订单状态",
    "conversation_id": 1
}

响应示例：
{
    "code": 0,
    "message": "success",
    "data": {
        "conversation_id": 1,
        "message": "好的，我来帮您查询订单状态。请稍等..."
    }
}
```

**创建对话会话接口**用于创建新的对话会话，返回会话ID用于后续消息关联。

```
POST /api/chat/history
Authorization: Bearer <token>

响应示例：
{
    "code": 0,
    "message": "success",
    "data": {
        "id": 1,
        "user_id": 1,
        "created_at": "2024-01-01T12:00:00"
    }
}
```

**对话历史接口**用于获取指定对话会话的所有消息记录。

```
GET /api/chat/history/{conversation_id}
Authorization: Bearer <token>

响应示例：
{
    "code": 0,
    "message": "success",
    "data": {
        "conversation_id": 1,
        "messages": [
            {
                "id": 1,
                "role": "user",
                "content": "我想查询订单",
                "created_at": "2024-01-01T12:00:00"
            },
            {
                "id": 2,
                "role": "assistant",
                "content": "好的，请问您的订单号是什么？",
                "created_at": "2024-01-01T12:00:01"
            }
        ]
    }
}
```

## 错误码说明

为了统一错误处理，接口返回的错误响应采用以下格式：

```json
{
    "code": 40001,
    "message": "参数错误",
    "data": null
}
```

主要错误码含义如下：

| 错误码 | 说明 | 常见原因 |
|--------|------|----------|
| 0 | 成功 | 请求处理正常 |
| 40001 | 参数错误 | 缺少必要参数或参数格式错误 |
| 40002 | 认证失败 | Token 无效或已过期 |
| 40003 | 权限不足 | 当前用户无权操作此资源 |
| 40004 | 资源不存在 | 查询的资源ID不存在 |
| 40005 | 业务逻辑错误 | 业务规则校验失败 |
| 50001 | 服务器错误 | 内部处理异常 |

## 测试验证

项目包含基础的单元测试，覆盖核心业务逻辑。测试文件位于 tests 目录下，使用 pytest 框架编写。

```bash
# 运行所有测试
uv run pytest

# 运行测试并查看详细输出
uv run pytest -v

# 运行特定测试文件
uv run pytest tests/test_auth.py

# 生成测试覆盖率报告
uv run pytest --cov=app --cov-report=html
```

## 部署说明

### 开发环境

开发环境下建议使用 uvicorn 的热重载模式，可以实时感知代码变化并重新加载：

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 生产环境

生产环境部署建议使用 gunicorn 作为应用服务器，配合 uvicorn worker 提供异步处理能力：

```bash
# 安装 gunicorn
uv add gunicorn

# 使用 4 个 worker 进程启动服务
uv run gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Docker 部署

项目支持 Docker 容器化部署。在项目根目录创建 Dockerfile：

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 安装依赖
RUN uv sync --frozen

# 复制应用代码
COPY app/ ./app/
COPY data/ ./data/
COPY logs/ ./logs/

# 创建非 root 用户
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

构建并运行容器：

```bash
# 构建镜像
docker build -t mini_program_api:latest .

# 运行容器
docker run -d -p 8000:8000 \
    -v $(pwd)/data:/app/data \
    -v $(pwd)/logs:/app/logs \
    -e SECRET_KEY=your-production-secret-key \
    mini_program_api:latest
```

## 性能优化

当前版本针对 POC 场景进行了优化，已实现以下性能提升措施：

数据库层面，所有高频查询字段都添加了索引。用户表按 union_id 建唯一索引，订单表按 user_id 和 created_at 建复合索引，确保列表查询的响应速度。分页查询使用游标分页方式，避免大偏移量导致的性能问题。

连接层面，SQLite 数据库配置了 WAL 模式，支持读写并发。同时限制了连接池大小，避免资源耗尽。对于需要复杂查询的场景，建议后续迁移到 PostgreSQL。

缓存层面，用户会话信息和订单摘要数据使用内存缓存，减少重复查询。缓存过期时间设置为 5 分钟，兼顾数据实时性和查询效率。

## 后续扩展

本项目作为 POC 版本，在功能完整性和技术深度上都有提升空间。以下几个方面可以在后续迭代中逐步完善：

**数据库升级**：当前使用 SQLite 适合小规模验证场景，当数据量增长后可迁移到 PostgreSQL 或 MySQL。SQLAlchemy 提供了统一的 ORM 接口，迁移时只需修改数据库连接配置。

**AI 服务增强**：当前版本的 AI 对话采用模拟响应，实际接入时只需替换 chat_service.py 中的调用逻辑。建议接入支持函数调用（Function Calling）的 AI 模型，实现查询订单、取消订单等实际操作。

**缓存优化**：可引入 Redis 作为缓存层，提升高频数据的访问速度。同时可以实现分布式 Session，支持多实例部署。

**监控告警**：建议接入 Prometheus + Grafana 监控体系，实时追踪接口响应时间和错误率。设置告警规则，及时发现和处理异常。

## 注意事项

在使用本项目时请注意以下事项：

生产环境部署必须更换默认的 SECRET_KEY，使用足够复杂的随机字符串。当前 POC 版本的 AI 对话功能使用的是模拟响应数据，如需接入真实 AI 服务，请在 chat_service.py 中实现实际的 API 调用逻辑并配置相应的 API 密钥。

数据库文件存储在 data 目录下，首次运行时会自动创建。生产环境建议将数据库目录挂载为持久化存储，避免数据丢失。日志文件存储在 logs 目录下，需要定期清理或归档。

所有接口都开启了基础的数据验证，对于恶意请求会返回相应的错误响应。生产环境建议额外配置速率限制（Rate Limiting），防止接口被滥用。