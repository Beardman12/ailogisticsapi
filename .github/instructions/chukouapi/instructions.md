# 出口易OpenAPI接口对接指南

## 一、接口调用基础说明

### 1.1 环境地址

| 环境 | 接口地址 |
|------|----------|
| 测试环境 | `https://openapi.chukou1.cn:81` |
| 正式环境 | `https://openapi.chukou1.cn:82` |

### 1.2 认证要求

所有接口调用都必须在HTTP Header中添加以下信息：

```
Authorization: Bearer {AccessToken}
Content-Type: application/json; charset=utf-8
```

其中 `{AccessToken}` 需要替换为实际获取的访问令牌。

### 1.3 HTTP状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 错误请求，提交的数据有误 |
| 401 | 验证错误，AccessToken无效或过期 |
| 404 | 找不到资源 |
| 412 | 不满足条件 |
| 500 | 服务器内部错误 |

### 1.4 错误响应格式

当请求失败时，接口返回的错误响应格式如下：

```json
{
  "Errors": [
    {
      "Code": "错误代码",
      "Message": "错误描述"
    }
  ],
  "TicketId": "工单ID",
  "UtcDateTime": "UTC时间戳",
  "RequestUri": "请求的URL"
}
```

---

## 二、接口列表

| 接口名称 | 请求方法 | URL路径 |
|----------|----------|---------|
| [创建中国直发订单](#创建中国直发订单) | POST | `/v1/directExpressOrders` |
| [查询中国直发服务列表](#查询中国直发服务列表) | GET | `/v1/directExpressServices` |
| [获取中国直发订单状态](#获取中国直发订单状态) | GET | `/v1/directExpressOrders/{packageId}/status` |

---

## 三、接口详细说明

### 创建中国直发订单

**接口说明**：创建中国直发订单（异步）。每个客户的不同PackageId第一次提交视作新增订单；如果数据改动后再次提交，视作修改订单（取消原订单，重新生成一个新订单）。创建中国直发订单后，需调用【获取直发订单状态】接口，当Status值为"Created"且TrackingNumber有值时，才算创建成功。

**请求方法**：POST

**测试环境URL**：`https://openapi.chukou1.cn:81/v1/directExpressOrders`

**正式环境URL**：`https://openapi.chukou1.cn:82/v1/directExpressOrders`

#### 请求头

```
Authorization: Bearer {AccessToken}
Content-Type: application/json; charset=utf-8
```

#### 请求参数（Body）

| 参数名称 | 类型 | 必须 | 说明 |
|----------|------|------|------|
| Location | string | 否 | 处理点，如不填则使用商家默认，最大长度20 |
| Package | object | 是 | 直发包裹信息，详见Package对象 |
| Remark | string | 否 | 备注，最大长度1000 |
| SubmitLater | boolean | 否 | 是否稍后提审，默认为false |

#### Package对象参数

| 参数名称 | 类型 | 必须 | 说明 |
|----------|------|------|------|
| PackageId | string | 是 | 包裹ID |
| PlatformOrderNo | string | 否 | 平台订单号 |
| ServiceCode | string | 是 | 服务代码，从查询服务列表接口获取 |
| LockerId | string | 否 | 储物柜ID |
| Weight | number | 否 | 重量（g） |
| WeightUnit | string | 否 | 重量单位 |
| Length | number | 否 | 长度（cm） |
| Width | number | 否 | 宽度（cm） |
| Height | number | 否 | 高度（cm） |
| SellPrice | number | 否 | 销售价格 |
| SellPriceCurrency | string | 否 | 销售价格货币，如CNY、USD |
| SalesPlatform | string | 否 | 销售平台，如Ebay、Amazon等 |
| OtherSalesPlatform | string | 否 | 其他销售平台 |
| ImportTrackingNumber | string | 否 | 进口追踪号 |
| ImportLabel | string | 否 | 进口标签 |
| CarrierName | string | 否 | 承运商名称 |
| Custom | string | 否 | 自定义信息 |
| Remark | string | 否 | 备注 |
| VatCode | string | 否 | VAT代码 |
| CodAmount | number | 否 | COD金额 |
| CodAmountStr | string | 否 | COD金额字符串 |
| IsCreateNewOrder | boolean | 否 | 是否创建新订单 |
| DutyTaxRate | number | 否 | 关税税率 |
| GoodsValueType | string | 否 | 货物价值类型 |
| ShipToAddress | object | 否 | 收货地址，详见ShipToAddress对象 |
| Sender | object | 否 | 发件人信息，详见Sender对象 |
| Skus | array | 否 | 商品列表，详见Skus数组 |
| ExportsInfo | object | 否 | 出口信息，详见ExportsInfo对象 |
| ImportsInfo | object | 否 | 进口信息，详见ImportsInfo对象 |

#### ShipToAddress（收货地址）对象参数

| 参数名称 | 类型 | 说明 |
|----------|------|------|
| TaxId | string | 税务ID |
| RecipientBirthday | string | 收件人生日 |
| IDNumber | string | 身份证号 |
| BankCardLast4digits | string | 银行卡后4位 |
| PaymentType | string | 支付类型 |
| IssuingInstitution | string | 发卡机构 |
| Taxfree | string | 免税 |
| DutyParagraph | string | 关税条款 |
| Department | string | 部门 |
| TypeOfTaxId | string | 税务ID类型 |
| ShortAddress | string | 简短地址 |
| Contact | string | 联系人 |
| Phone | string | 电话 |
| Email | string | 邮箱 |
| Country | string | 国家，如US、UK等 |
| Province | string | 省份/州 |
| City | string | 城市 |
| District | string | 区/县 |
| Street1 | string | 街道1（详细地址） |
| Street2 | string | 街道2 |
| HouseNumber | string | 门牌号 |
| Postcode | string | 邮编/邮政编码 |

#### Sender（发件人）对象参数

| 参数名称 | 类型 | 说明 |
|----------|------|------|
| Contact | string | 联系人 |
| Phone | string | 电话 |
| Email | string | 邮箱 |
| Country | string | 国家 |
| Department | string | 部门 |
| Province | string | 省份 |
| City | string | 城市 |
| District | string | 区/县 |
| Street1 | string | 街道1 |
| Street2 | string | 街道2 |
| HouseNumber | string | 门牌号 |
| Postcode | string | 邮编 |

#### Skus（商品列表）对象参数

| 参数名称 | 类型 | 说明 |
|----------|------|------|
| Sku | string | SKU编码 |
| Quantity | number | 数量 |
| Weight | number | 重量（g） |
| WeightUnit | string | 重量单位 |
| DeclareValue | number | 申报价值 |
| NewDeclareValue | object | 新申报价值，包含Value和Currency |
| ExportsDeclareValue | object | 出口申报价值，包含Value |
| CIFDeclareValue | object | CIF申报价值，包含Value |
| InsuranceDeclareValue | object | 保险申报价值，包含Value |
| FreightDeclareValue | object | 运费申报价值，包含Value |
| DeclareNameEn | string | 英文申报名称 |
| DeclareNameCn | string | 中文申报名称 |
| ProductName | string | 产品名称 |
| Price | number | 价格 |
| HsCode | string | HS编码 |
| HsCodeCN | string | 中国HS编码 |
| SaleURL | string | 销售URL |
| ProductLink | string | 产品链接 |
| ProductDescription | string | 产品描述 |
| ProductCategories | string | 产品类别 |
| MaterialEN | string | 英文材质 |
| Brand | string | 品牌 |
| ProductModel | string | 产品型号 |
| DutyTaxRate | number | 关税税率 |
| Duty | object | 关税，包含Value和Currency |
| PlatformItemId | string | 平台商品ID |
| PlatformTransactionId | string | 平台交易ID |
| ProducerSellerCreditCode | string | 生产者/卖家信用代码 |
| ProducerSellerName | string | 生产者/卖家名称 |

#### ExportsInfo（出口信息）对象参数

| 参数名称 | 类型 | 说明 |
|----------|------|------|
| EoriCode | string | EORI代码 |
| Country | string | 国家 |
| Department | string | 部门 |
| Province | string | 省份 |
| City | string | 城市 |
| Street1 | string | 街道1 |
| Street2 | string | 街道2 |
| Postcode | string | 邮编 |
| Contact | string | 联系人 |
| Company | string | 公司 |
| Phone | string | 电话 |
| Email | string | 邮箱 |

#### ImportsInfo（进口信息）对象参数

| 参数名称 | 类型 | 说明 |
|----------|------|------|
| EoriCode | string | EORI代码 |
| Country | string | 国家 |
| Department | string | 部门 |
| Province | string | 省份 |
| City | string | 城市 |
| Street1 | string | 街道1 |
| Street2 | string | 街道2 |
| Postcode | string | 邮编 |
| Contact | string | 联系人 |
| Company | string | 公司 |
| Phone | string | 电话 |
| Email | string | 邮箱 |

#### 请求示例

```json
{
  "Location": "GZ",
  "Package": {
    "PackageId": "SMT23015236489",
    "ServiceCode": "CUE",
    "ShipToAddress": {
      "Country": "US",
      "Province": "Florida",
      "City": "Coral Springs",
      "Street1": "9110 NW 21st street",
      "Postcode": "45429",
      "Contact": "David Mcaffee",
      "Phone": "937-689-8216",
      "Email": "23541566@gmail.com"
    },
    "Weight": 600,
    "Length": 25,
    "Width": 10,
    "Height": 20,
    "Skus": [
      {
        "Sku": "bag-y001",
        "Quantity": 1,
        "Weight": 600,
        "DeclareValue": 5,
        "DeclareNameEn": "bag",
        "DeclareNameCn": "小梦书包",
        "ProductName": "bag-red",
        "Price": 5
      },
      {
        "Sku": "bag-y002",
        "Quantity": 2,
        "Weight": 600,
        "DeclareValue": 5,
        "DeclareNameEn": "bag",
        "DeclareNameCn": "小梦书包",
        "ProductName": "bag-red",
        "Price": 5
      }
    ],
    "SellPrice": 20,
    "SellPriceCurrency": "CNY",
    "SalesPlatform": "Ebay",
    "Custom": "bag-red*1",
    "Remark": "bag-red*1"
  },
  "Remark": "remark"
}
```

#### 返回说明

| HTTP状态码 | 说明 |
|------------|------|
| 201 | 提交成功 |
| 200 | 订单已存在，忽略当前提交的订单 |
| 400 | 提交的数据有误，请检查请求参数 |

**重要提示**：返回成功不代表订单创建成功，需要调用【获取直发订单状态】接口，当Status值为"Created"且TrackingNumber有值时，才算创建成功。

---

### 查询中国直发服务列表

**接口说明**：获取出口易中国直发服务列表，返回所有可用的物流服务信息。

**请求方法**：GET

**测试环境URL**：`https://openapi.chukou1.cn:83/v1/directExpressServices`

**正式环境URL**：`https://openapi.chukou1.cn:82/v1/directExpressServices`

#### 请求头

```
Authorization: Bearer {AccessToken}
Content-Type: application/json; charset=utf-8
```

#### 请求参数

无请求参数。

#### 响应参数

| 参数名称 | 类型 | 必须 | 说明 |
|----------|------|------|------|
| ServiceCode | string | 是 | 出口易发货服务代码，用于创建订单时指定物流服务 |
| ServiceName | string | 是 | 发货服务名称，便于识别和展示 |
| IsTracking | boolean | 是 | 是否挂号，true表示提供物流追踪功能 |
| InService | boolean | 是 | 是否可用，true表示当前可以下单 |
| CanImportTracking | boolean | 是 | 是否可导入trackingNo，true表示支持用户自行导入物流追踪号 |

#### 响应示例

```json
[
  {
    "ServiceCode": "UPS",
    "ServiceName": "CK1无限电",
    "IsTracking": true,
    "InService": true,
    "CanImportTracking": true
  },
  {
    "ServiceCode": "NLR",
    "ServiceName": "Easy邮",
    "IsTracking": true,
    "InService": true,
    "CanImportTracking": false
  },
  {
    "ServiceCode": "DGR",
    "ServiceName": "DHL小包挂号",
    "IsTracking": true,
    "InService": true,
    "CanImportTracking": false
  }
]
```

#### 字段说明

| 字段 | 说明 |
|------|------|
| ServiceCode | 出口易系统中的发货服务代码，用于标识具体物流服务，创建订单时需使用此值 |
| ServiceName | 发货服务的名称，便于识别和展示 |
| IsTracking | 表示该物流服务是否提供物流追踪功能（挂号服务） |
| InService | 表示该服务当前是否可用（可下单） |
| CanImportTracking | 表示是否支持用户自行导入物流追踪号 |

---

### 获取中国直发订单状态

**接口说明**：获取中国直发订单状态，根据返回的Status属性判断订单是否创建成功。

**请求方法**：GET

**测试环境URL**：`https://openapi.chukou1.cn:81/v1/directExpressOrders/{packageId}/status`

**正式环境URL**：`https://openapi.chukou1.cn:82/v1/directExpressOrders/{packageId}/status`

#### 请求头

```
Authorization: Bearer {AccessToken}
Content-Type: application/json; charset=utf-8
```

#### 路径参数

| 参数名称 | 类型 | 必须 | 说明 |
|----------|------|------|------|
| packageId | string | 是 | 直发包裹ID，创建订单时提交的PackageId |

#### 响应参数

| 参数名称 | 类型 | 说明 |
|----------|------|------|
| WeightInit | integer | 初始包裹重量（g） |
| PackingInit | object | 初始包装尺寸，格式{"Length":1,"Width":2,"Height":3} |
| Weight | integer | 核实包裹重量（g） |
| Packing | object | 核实包装尺寸（cm） |
| ChargedWeight | integer | 计费重量（g） |
| ServiceCode | string | 产品代码 |
| MailingDate | string | 发件地当地发货日期，格式yyyy-MM-dd |
| CodAmount | string | COD金额 |
| CodAmountCurrency | string | COD金额币种 |
| TrackingState | integer | 状态，详见下方状态说明 |
| PackageId | string | 出库包裹ID |
| Ck1PackageId | string | 处理号 |
| Status | string | 状态，如Creating、Created等 |
| HandleStatus | string | 处理状态，如Initial、Submitted等 |
| TrackingNumber | string | 跟踪号/追踪号，创建成功后会返回 |
| ExtraTrackNumber | string | 副跟踪号 |
| IsFinalTrackingNumber | boolean | 是否是最终跟踪号（部分渠道是到仓后才会有最终跟踪号） |
| ShippingProvider | string | 承运商，如DHL、UPS等 |
| CreateFailedReason | object | 创建失败原因，详见下方说明 |
| ShippingCosts | array | 费用列表（已完成出库才会返回费用信息） |
| HasRemoteFee | boolean | 是否产生偏远地区费用 |
| WarehouseReceivedTime | string | 分拣仓收到货物时间，格式yyyy/MM/dd HH:mm:ss |
| WarehouseDepartedTime | string | 从分拣仓出库时间，格式yyyy/MM/dd HH:mm:ss |
| DestinationAscanTime | string | 目的国Ascan时间 |
| DeliveredTime | string | 妥投时间 |
| CreatedTime | string | 包裹创建时间，格式ISO 8601 |

#### TrackingState 状态说明

| 值 | 说明 |
|-----|------|
| 0 | 成功 |
| 1 | 获取标签失败 |
| 2 | 上传挂号失败 |
| 5 | 等待中 |
| 8 | 插队列失败 |
| 9 | 挂号请求预处理 |
| 10 | 标签重试获取失败 |

#### CreateFailedReason 对象说明

| 参数名称 | 类型 | 说明 |
|----------|------|------|
| ReasonCode | string | 原因代码 |
| ReasonText | string | 原因描述 |
| ExtendMessage | string | 扩展信息 |

#### ShippingCost 对象说明

| 参数名称 | 类型 | 说明 |
|----------|------|------|
| Money | number | 金额 |
| Currency | string | 币种 |
| Type | string | 类型 |
| Remark | string | 备注 |

#### Packing 对象说明

| 参数名称 | 类型 | 说明 |
|----------|------|------|
| Length | integer | 长度（cm） |
| Width | integer | 宽度（cm） |
| Height | integer | 高度（cm） |

#### 响应示例（成功）

```json
{
  "WeightInit": 600,
  "PackingInit": {
    "Length": 25,
    "Width": 10,
    "Height": 20
  },
  "Weight": 600,
  "Packing": {
    "Length": 25,
    "Width": 10,
    "Height": 20
  },
  "ChargedWeight": 600,
  "ServiceCode": "CUE",
  "MailingDate": "2024-11-08",
  "CodAmount": "",
  "CodAmountCurrency": "",
  "TrackingState": 0,
  "PackageId": "SMT23015236489",
  "Ck1PackageId": "EUU20160808TST00001",
  "Status": "Created",
  "HandleStatus": "Submitted",
  "TrackingNumber": "T024963157",
  "ExtraTrackNumber": "",
  "IsFinalTrackingNumber": true,
  "ShippingProvider": "DHL",
  "CreateFailedReason": null,
  "ShippingCosts": [],
  "HasRemoteFee": false,
  "WarehouseReceivedTime": "2024/11/08 10:30:00",
  "WarehouseDepartedTime": "2024/11/09 15:00:00",
  "DestinationAscanTime": "",
  "DeliveredTime": "",
  "CreatedTime": "2026-05-16T13:29:16.179+08:00"
}
```

#### 响应示例（订单不存在）

```json
{
  "Errors": [
    {
      "Code": "800F1533",
      "Message": "直发订单Sh0983125305不存在"
    }
  ],
  "TicketId": "b8ccb8c1-1b03-4380-a820-b34f153730d1",
  "UtcDateTime": "2016-03-20T07:19:25Z",
  "RequestUri": "https://openapi.chukou1.cn:82/v1/directExpressOrders/Sh0983125305/status"
}
```

#### 判断订单创建成功的条件

- HTTP状态码为200
- Status字段值为"Created"
- TrackingNumber字段有值（非空）

---

## 四、集成建议

### 4.1 标准调用流程

1. **获取AccessToken**：调用认证接口获取访问令牌
2. **查询服务列表**：调用查询服务列表接口获取可用的物流服务
3. **创建订单**：调用创建订单接口提交订单
4. **查询状态**：轮询调用订单状态接口，确认订单创建成功

### 4.2 状态轮询建议

创建订单后，建议按以下方式轮询订单状态：

- 首次查询：提交后立即查询
- 后续查询：每隔5-10秒查询一次
- 超时设置：最多轮询30分钟
- 成功判断：Status="Created" 且 TrackingNumber有值

### 4.3 错误处理建议

- 400错误：检查请求参数格式和必填项
- 401错误：重新获取AccessToken
- 404错误：检查PackageId是否正确
- 500错误：记录工单ID，联系技术支持

### 4.4 数据校验建议

创建订单前，请确保：

- PackageId唯一且不为空
- ServiceCode为有效的服务代码
- 收货地址信息完整（Country、City、Street1、Postcode）
- 商品信息完整（至少包含Sku、Quantity、DeclareValue）
- 重量和尺寸信息合理

---

## 五、接口地址汇总

| 环境 | 创建订单 | 查询服务列表 | 查询订单状态 |
|------|----------|--------------|--------------|
| 测试环境 | `https://openapi.chukou1.cn:81/v1/directExpressOrders` | `https://openapi.chukou1.cn:83/v1/directExpressServices` | `https://openapi.chukou1.cn:81/v1/directExpressOrders/{packageId}/status` |
| 正式环境 | `https://openapi.chukou1.cn:82/v1/directExpressOrders` | `https://openapi.chukou1.cn:82/v1/directExpressServices` | `https://openapi.chukou1.cn:82/v1/directExpressOrders/{packageId}/status` |

---

## 六、基于小程序下单页的订单表重设计

本章节用于替代当前过于简化的订单模型，目标是完整承接小程序下单页面填写信息，并支持后续对接出口易直发接口。

### 6.1 页面字段识别结果（来自 assets 截图）

#### A. 寄件方信息

| 页面字段 | 必填 | 说明 |
|----------|------|------|
| 姓名 | 是 | 寄件人姓名（中英文） |
| 手机号（含区号） | 是 | 示例：+86 + 手机号 |
| 揽收点 | 是 | 下拉选择 |
| 国内快递单号 | 否 | 货物到国内仓后用于查询 |

#### B. 收件方信息

| 页面字段 | 必填 | 说明 |
|----------|------|------|
| 真实姓名 | 是 | 收件人姓名 |
| 电话号码（含区号） | 是 | 示例：+51 + 手机号 |
| 国家 | 是 | 示例：秘鲁（Peru） |
| 邮编 | 是 | 邮政编码 |
| 省/州 | 是 | 收件省州 |
| 城市 | 是 | 收件城市 |
| 详细地址 | 是 | 街道详细地址 |
| 邮箱 | 否 | 可选填 |
| 证件类型 | 是 | 截图显示为 DNI |
| 证件号码 | 是 | 截图要求 8 位 |
| 保存地址 | 否 | 用户可将地址存为常用地址 |

#### C. 包裹信息

| 页面字段 | 必填 | 说明 |
|----------|------|------|
| 货品类型 | 是 | 普通货物 / 带电货物 |
| 货品描述（中文） | 是 | 申报中文名 |
| 货品描述（英文） | 是 | 申报英文名 |
| 销售单价（USD） | 是 | 商品单价 |
| 数量 | 是 | 件数 |
| 体重（g） | 是 | 包裹重量 |
| 体积（cm）长宽高 | 是 | 长、宽、高 |
| 核实包裹重量（g） | 否（系统回填） | 收货后仓库核实 |
| 核实包装尺寸（cm） | 否（系统回填） | 收货后仓库核实 |
| 备注 | 否 | 用户备注 |

### 6.2 重设计原则

1. 小程序“用户输入”与“系统回填/第三方回传”分层存储，避免字段混杂。
2. 订单主表只放核心标识与状态，地址、包裹、日志拆分子表。
3. 与出口易字段保持一一映射，保证请求组装与状态回写可追溯。
4. 支持一个订单多件商品（即使当前页面只录一条，也要预留扩展）。
5. 所有关键状态变化必须有日志表，便于客服与运维排查。

### 6.3 推荐表结构（SQLite，POC版）

本项目POC阶段统一使用SQLite。

- 应用运行层面：Python内置sqlite3驱动，通常无需单独安装数据库服务。
- 运维调试层面：建议安装sqlite3命令行工具，便于查看和排查数据。

Windows可选安装方式（用于本地调试）：

```bash
winget install SQLite.SQLite
sqlite3 --version
```

类型约定说明：以下表格里的bigint/varchar/decimal是逻辑类型；在SQLite中建议按下述方式落地。

| 逻辑类型 | SQLite建议类型 |
|----------|----------------|
| bigint/int | INTEGER |
| varchar/text | TEXT |
| decimal(10,2) | NUMERIC |
| boolean | INTEGER（0/1） |
| datetime | TEXT（ISO 8601） |
| json/text | TEXT |

#### 1) orders（订单主表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | bigint | PK | 自增主键 |
| order_no | varchar(32) | UK | 平台订单号（对外展示） |
| user_id | bigint | IDX | 下单用户ID |
| package_id | varchar(64) | UK | 对接出口易 PackageId |
| platform_order_no | varchar(64) | 可空 | 对接出口易 PlatformOrderNo |
| service_code | varchar(32) | IDX | 物流服务代码（出口易） |
| location_code | varchar(20) | 可空 | 处理点/仓代码（对应 Location） |
| submit_later | boolean | 默认false | 是否稍后提审 |
| order_status | varchar(32) | IDX | 业务状态（draft/submitted/processing/success/failed/cancelled） |
| payment_status | varchar(32) | IDX | 支付状态（unpaid/paying/paid/failed/refunded/partial_refunded） |
| payment_channel | varchar(32) | 可空 | 支付渠道（wechat/alipay/other） |
| payment_order_no | varchar(64) | 可空 | 支付单号（第三方支付流水号） |
| payable_amount | decimal(10,2) | 可空 | 应付金额 |
| payment_currency | varchar(8) | 可空 | 支付币种，如CNY/USD |
| chukou_status | varchar(32) | IDX | 出口易状态（Creating/Created/...） |
| tracking_number | varchar(64) | IDX | 主追踪号 |
| extra_track_number | varchar(64) | 可空 | 副追踪号 |
| shipping_provider | varchar(64) | 可空 | 承运商 |
| submit_failed_code | varchar(64) | 可空 | 创建失败代码 |
| submit_failed_message | varchar(255) | 可空 | 创建失败原因 |
| user_remark | varchar(500) | 可空 | 用户备注 |
| created_at | datetime | IDX | 创建时间 |
| updated_at | datetime |  | 更新时间 |
| paid_at | datetime | 可空 | 支付成功时间 |
| submitted_at | datetime | 可空 | 提交出口易时间 |
| success_at | datetime | 可空 | 创建成功时间（拿到Tracking） |

#### 2) order_sender（寄件方信息）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | bigint | PK | 主键 |
| order_id | bigint | UK, FK | 关联订单 |
| sender_name | varchar(100) | 非空 | 寄件人姓名 |
| sender_phone_code | varchar(8) | 非空 | 国家区号，如+86 |
| sender_phone | varchar(32) | 非空 | 手机号 |
| pickup_point_id | bigint | FK, 可空 | 揽收点ID |
| pickup_point_name | varchar(100) | 非空 | 揽收点名称（冗余快照） |
| domestic_tracking_no | varchar(64) | 可空 | 国内快递单号 |
| created_at | datetime |  | 创建时间 |
| updated_at | datetime |  | 更新时间 |

#### 3) order_recipient（收件方信息）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | bigint | PK | 主键 |
| order_id | bigint | UK, FK | 关联订单 |
| recipient_name | varchar(100) | 非空 | 收件人姓名 |
| phone_code | varchar(8) | 非空 | 国家区号，如+51 |
| phone | varchar(32) | 非空 | 电话号码 |
| country_code | varchar(2) | 非空 | 国家二字码，如PE |
| country_name | varchar(64) | 非空 | 国家名 |
| province | varchar(100) | 非空 | 省/州 |
| city | varchar(100) | 非空 | 城市 |
| district | varchar(100) | 可空 | 区县 |
| street1 | varchar(255) | 非空 | 详细地址 |
| street2 | varchar(255) | 可空 | 地址补充 |
| postcode | varchar(20) | 非空 | 邮编 |
| email | varchar(100) | 可空 | 邮箱 |
| id_type | varchar(32) | 非空 | 证件类型，如DNI |
| id_number | varchar(64) | 非空 | 证件号码 |
| created_at | datetime |  | 创建时间 |
| updated_at | datetime |  | 更新时间 |

#### 4) order_parcel（包裹物理信息）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | bigint | PK | 主键 |
| order_id | bigint | UK, FK | 一个订单一条包裹信息 |
| cargo_type | varchar(32) | 非空 | 普货/带电 |
| weight_g_input | int | 非空 | 用户填写重量(g) |
| length_cm_input | decimal(10,2) | 非空 | 用户填写长 |
| width_cm_input | decimal(10,2) | 非空 | 用户填写宽 |
| height_cm_input | decimal(10,2) | 非空 | 用户填写高 |
| weight_g_verified | int | 可空 | 核实重量(g) |
| length_cm_verified | decimal(10,2) | 可空 | 核实长 |
| width_cm_verified | decimal(10,2) | 可空 | 核实宽 |
| height_cm_verified | decimal(10,2) | 可空 | 核实高 |
| charged_weight_g | int | 可空 | 计费重（状态接口回传） |
| created_at | datetime |  | 创建时间 |
| updated_at | datetime |  | 更新时间 |

#### 5) order_items（包裹货品明细）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | bigint | PK | 主键 |
| order_id | bigint | FK, IDX | 关联订单 |
| line_no | int | 非空 | 行号，从1开始 |
| goods_desc_cn | varchar(200) | 非空 | 中文品名（DeclareNameCn） |
| goods_desc_en | varchar(200) | 非空 | 英文品名（DeclareNameEn） |
| unit_price_usd | decimal(10,2) | 非空 | 销售单价USD |
| quantity | int | 非空 | 数量 |
| total_price_usd | decimal(10,2) | 非空 | 小计=单价*数量 |
| sku_code | varchar(64) | 可空 | SKU（可后续自动生成/录入） |
| hs_code | varchar(32) | 可空 | 海关编码 |
| created_at | datetime |  | 创建时间 |
| updated_at | datetime |  | 更新时间 |

#### 6) user_address_book（用户收件地址簿）

用于支持页面“保存地址”。下次下单直接复用。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | bigint | PK | 主键 |
| user_id | bigint | IDX | 用户ID |
| recipient_name | varchar(100) | 非空 | 收件人姓名 |
| phone_code | varchar(8) | 非空 | 区号 |
| phone | varchar(32) | 非空 | 电话 |
| country_code | varchar(2) | 非空 | 国家码 |
| country_name | varchar(64) | 非空 | 国家名 |
| province | varchar(100) | 非空 | 省/州 |
| city | varchar(100) | 非空 | 城市 |
| district | varchar(100) | 可空 | 区县 |
| street1 | varchar(255) | 非空 | 详细地址 |
| street2 | varchar(255) | 可空 | 地址补充 |
| postcode | varchar(20) | 非空 | 邮编 |
| email | varchar(100) | 可空 | 邮箱 |
| id_type | varchar(32) | 非空 | 证件类型 |
| id_number | varchar(64) | 非空 | 证件号码 |
| is_default | boolean | 默认false | 是否默认地址 |
| created_at | datetime |  | 创建时间 |
| updated_at | datetime |  | 更新时间 |

#### 7) pickup_points（揽收点字典）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | bigint | PK | 主键 |
| point_code | varchar(32) | UK | 揽收点编码 |
| point_name | varchar(100) | 非空 | 揽收点名称 |
| country_code | varchar(2) | 可空 | 国家码 |
| province | varchar(100) | 可空 | 省州 |
| city | varchar(100) | 可空 | 城市 |
| address | varchar(255) | 可空 | 地址 |
| contact_phone | varchar(32) | 可空 | 联系电话 |
| is_active | boolean | 默认true | 是否启用 |
| created_at | datetime |  | 创建时间 |
| updated_at | datetime |  | 更新时间 |

#### 8) order_submit_logs（提交出口易日志）

记录每一次请求与响应，支持重试与审计。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | bigint | PK | 主键 |
| order_id | bigint | FK, IDX | 关联订单 |
| attempt_no | int | 非空 | 第几次提交 |
| request_url | varchar(255) | 非空 | 请求地址 |
| request_body | json/text | 非空 | 请求体快照 |
| response_status_code | int | 可空 | HTTP状态码 |
| response_body | json/text | 可空 | 响应体 |
| is_success | boolean | 默认false | 请求是否成功 |
| error_code | varchar(64) | 可空 | 业务错误码 |
| error_message | varchar(255) | 可空 | 错误信息 |
| created_at | datetime | IDX | 创建时间 |

#### 9) order_status_logs（订单状态流水）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | bigint | PK | 主键 |
| order_id | bigint | FK, IDX | 关联订单 |
| from_status | varchar(32) | 可空 | 旧状态 |
| to_status | varchar(32) | 非空 | 新状态 |
| source | varchar(32) | 非空 | 状态来源（user/system/chukouapi） |
| note | varchar(255) | 可空 | 说明 |
| raw_payload | json/text | 可空 | 原始回调/查询数据 |
| created_at | datetime | IDX | 发生时间 |

#### 10) order_payments（支付流水）

用于记录支付系统的每次支付/退款动作，支持一单多次支付尝试。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | bigint | PK | 主键 |
| order_id | bigint | FK, IDX | 关联订单 |
| action_type | varchar(32) | 非空 | 动作类型（pay/refund） |
| payment_status | varchar(32) | IDX | 支付状态（initiated/success/failed/closed/refunded） |
| channel | varchar(32) | 非空 | 支付渠道 |
| amount | decimal(10,2) | 非空 | 本次金额 |
| currency | varchar(8) | 非空 | 币种 |
| third_party_txn_no | varchar(64) | 可空 | 第三方交易号 |
| third_party_order_no | varchar(64) | 可空 | 第三方支付单号 |
| fail_code | varchar(64) | 可空 | 失败码 |
| fail_message | varchar(255) | 可空 | 失败原因 |
| callback_payload | json/text | 可空 | 回调原文 |
| created_at | datetime | IDX | 创建时间 |
| updated_at | datetime |  | 更新时间 |

### 6.4 关键索引与唯一约束建议

1. orders.package_id 唯一（出口易幂等关键）。
2. orders.order_no 唯一（平台侧业务单号）。
3. orders.user_id + created_at 联合索引（用户订单列表）。
4. orders.order_status + created_at 联合索引（后台筛选）。
5. orders.payment_status + created_at 联合索引（按支付状态筛选订单）。
6. order_submit_logs.order_id + attempt_no 唯一（避免重复编号）。
7. user_address_book.user_id + is_default 索引（快速取默认地址）。
8. order_payments.order_id + created_at 联合索引（按订单查支付流水）。

SQLite补充说明：SQLite支持UNIQUE约束和普通索引；POC阶段不使用分区表、函数索引等复杂特性。

### 6.5 小程序字段到出口易字段映射

| 小程序字段 | 建议存储字段 | 出口易字段 |
|------------|--------------|------------|
| 寄件人姓名 | order_sender.sender_name | Package.Sender.Contact |
| 寄件人手机号 | order_sender.sender_phone_code + sender_phone | Package.Sender.Phone |
| 揽收点 | order_sender.pickup_point_id/name | Location（或扩展字段） |
| 国内快递单号 | order_sender.domestic_tracking_no | Package.ImportTrackingNumber |
| 收件人姓名 | order_recipient.recipient_name | Package.ShipToAddress.Contact |
| 收件电话 | order_recipient.phone_code + phone | Package.ShipToAddress.Phone |
| 国家 | order_recipient.country_code | Package.ShipToAddress.Country |
| 省/州 | order_recipient.province | Package.ShipToAddress.Province |
| 城市 | order_recipient.city | Package.ShipToAddress.City |
| 详细地址 | order_recipient.street1 | Package.ShipToAddress.Street1 |
| 邮编 | order_recipient.postcode | Package.ShipToAddress.Postcode |
| 邮箱 | order_recipient.email | Package.ShipToAddress.Email |
| 证件号 | order_recipient.id_number | Package.ShipToAddress.IDNumber |
| 货品描述（中） | order_items.goods_desc_cn | Package.Skus[].DeclareNameCn |
| 货品描述（英） | order_items.goods_desc_en | Package.Skus[].DeclareNameEn |
| 销售单价USD | order_items.unit_price_usd | Package.Skus[].Price |
| 数量 | order_items.quantity | Package.Skus[].Quantity |
| 重量g | order_parcel.weight_g_input | Package.Weight / Package.Skus[].Weight |
| 长宽高cm | order_parcel.length/width/height_input | Package.Length/Width/Height |
| 备注 | orders.user_remark | Remark / Package.Remark |

### 6.6 推荐订单状态机（履约）

| 状态 | 说明 | 触发条件 |
|------|------|----------|
| draft | 草稿 | 用户开始填写，尚未提交 |
| submitted | 已提交 | 已调用创建订单接口 |
| creating | 创建中 | 状态查询返回Creating/Submitted |
| success | 创建成功 | Status=Created 且 TrackingNumber非空 |
| failed | 创建失败 | 返回失败或超时失败 |
| cancelled | 已取消 | 用户取消或系统撤销 |

### 6.6.1 推荐支付状态机

| 状态 | 说明 | 触发条件 |
|------|------|----------|
| unpaid | 未支付 | 订单创建后默认状态 |
| paying | 支付中 | 拉起支付后，等待支付回调 |
| paid | 已支付 | 支付回调成功或主动查询支付成功 |
| failed | 支付失败 | 支付回调失败或超时关闭 |
| refunded | 全额退款 | 退款成功且退款金额=实付金额 |
| partial_refunded | 部分退款 | 退款成功但退款金额<实付金额 |

建议规则：只有 payment_status=paid 的订单才能进入 submitted（提交出口易）流程，避免未支付订单占用物流资源。

### 6.7 与当前模型相比的改进点

1. 从“单表混存”升级为“主表+地址+包裹+明细+日志”分层模型。
2. 完整覆盖截图中的实际填写字段，避免接口调用前临时拼接缺字段。
3. 支持出口易异步创建场景，具备可审计的提交和状态追踪能力。
4. 支持地址簿、揽收点字典等小程序高频功能，减少重复输入。
5. 为后续多商品、多包裹扩展留足空间（当前先支持一单一包裹）。
6. 支付状态与履约状态解耦，支持“已下单未支付”“已支付待提交”“已退款”等真实业务场景。