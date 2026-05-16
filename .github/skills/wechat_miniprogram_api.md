# 微信小程序API对接指南

## 一、接口调用基础说明

### 1.1 必要配置

| 配置项 | 说明 |
|--------|------|
| AppID | 小程序唯一标识，在微信公众平台获取 |
| AppSecret | 小程序密钥，在微信公众平台获取 |
| 请求域名 | 需在微信公众平台配置服务器域名白名单 |
| TLS版本 | 接口要求TLS 1.2及以上 |

### 1.2 接口调用限制

| 接口 | 限制说明 |
|------|----------|
| auth.code2Session | 每个用户每分钟最多100次 |
| subscribeMessage.send | 开通支付能力：3000万/日；未开通：1000万/日 |

---

## 二、登录授权流程

### 2.1 完整登录时序图

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│   小程序端   │     │  开发者服务器  │     │   微信接口服务器      │     │    数据库       │
└──────┬──────┘     └──────┬──────┘     └──────────┬──────────┘     └─────────────────┘
       │                  │                      │
       │  1.调用wx.login() │                      │
       │ ──────────────────>│                      │
       │  返回code          │                      │
       │ <──────────────────│                      │
       │                  │                      │
       │  2.发送code到服务器│                      │
       │ ──────────────────>│                      │
       │                  │                      │
       │                  │  3.发送code+appid+secret│
       │                  │ ──────────────────────>│
       │                  │                      │
       │                  │  4.返回openid/session_key/unionid│
       │                  │ <──────────────────────│
       │                  │                      │
       │                  │  5.生成自定义登录态token│
       │                  │ ───────>│             │
       │                  │         │ 保存用户信息  │
       │                  │         │ <─────── │
       │                  │                      │
       │  6.返回token      │                      │
       │ <─────────────────│                      │
       │                  │                      │
```

### 2.2 判断条件说明

**UnionID获取条件**（满足任一即可）：
- 用户已关注公众号
- 用户曾在App或公众号进行过微信登录授权
- 用户在小程序中完成授权且开发者绑定了微信开放平台账号
- 小程序、公众号、App在同一微信开放平台账号下绑定

---

## 三、接口详细说明

### 获取登录凭证（wx.login）

**接口说明**：调用接口获取登录凭证（code）。通过凭证可换取用户登录态信息，包括openid、session_key和unionid。

**调用方式**：小程序端直接调用

#### 请求参数

无请求参数

#### 返回参数

| 参数名称 | 类型 | 说明 |
|----------|------|------|
| code | string | 登录凭证，有效期5分钟，每次调用会更新 |
| errMsg | string | 错误信息 |

#### 代码示例

```javascript
// 小程序端代码
wx.login({
  success: (res) => {
    if (res.code) {
      // 将code发送到开发者服务器换取用户信息
      wx.request({
        url: 'https://your-domain.com/api/login',
        method: 'POST',
        data: { code: res.code },
        success: (loginRes) => {
          // loginRes.data包含 openid, session_key, unionid, token等
          console.log('登录成功:', loginRes.data);
        }
      });
    } else {
      console.log('登录失败:', res.errMsg);
    }
  }
});
```

---

### 登录凭证校验（code2Session）

**接口说明**：登录凭证校验。通过wx.login接口获得临时登录凭证code后传到开发者服务器调用此接口完成登录流程。

**调用方式**：开发者服务器端调用

#### 请求地址

```
GET https://api.weixin.qq.com/sns/jscode2session?appid={appid}&secret={secret}&js_code={code}&grant_type=authorization_code
```

#### 请求参数

| 参数名称 | 类型 | 必须 | 说明 |
|----------|------|------|------|
| appid | string | 是 | 小程序appId |
| secret | string | 是 | 小程序appSecret |
| js_code | string | 是 | wx.login返回的code |
| grant_type | string | 是 | 授权类型，此处填写authorization_code |

#### 返回参数

| 参数名称 | 类型 | 说明 |
|----------|------|------|
| openid | string | 用户唯一标识 |
| session_key | string | 会话密钥 |
| unionid | string | 用户在开放平台的唯一标识符（需满足条件才返回） |
| errcode | number | 错误码 |
| errmsg | string | 错误信息 |

#### errcode合法值

| 值 | 说明 |
|-----|------|
| -1 | 系统繁忙，请稍后重试 |
| 0 | 请求成功 |
| 40029 | code无效 |
| 45011 | 频率限制，每个用户每分钟最多100次 |
| 40226 | 高风险等级用户，小程序登录拦截 |

#### 代码示例

```python
# Python示例
import requests

def code_to_session(appid, secret, code):
    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": appid,
        "secret": secret,
        "js_code": code,
        "grant_type": "authorization_code"
    }
    response = requests.get(url, params=params)
    result = response.json()

    if "openid" in result:
        return {
            "openid": result["openid"],
            "session_key": result["session_key"],
            "unionid": result.get("unionid"),  # 可能不存在
            "success": True
        }
    else:
        return {"success": False, "errcode": result.get("errcode"), "errmsg": result.get("errmsg")}
```

```javascript
// Node.js示例
const axios = require('axios');

async function codeToSession(appid, secret, code) {
  const url = 'https://api.weixin.qq.com/sns/jscode2session';
  const params = {
    appid,
    secret,
    js_code: code,
    grant_type: 'authorization_code'
  };

  try {
    const response = await axios.get(url, { params });
    const { openid, session_key, unionid } = response.data;

    return { openid, session_key, unionid, success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
}
```

---

### 获取用户信息（wx.getUserProfile）

**接口说明**：获取用户信息。页面产生点击事件（例如button上bindtap的回调中）后才可调用，每次请求都会弹出授权窗口，用户同意后返回userInfo。该接口用于替换wx.getUserInfo。

**调用方式**：小程序端直接调用

**基础库版本要求**：2.10.4及以上

#### 请求参数

| 参数名称 | 类型 | 必须 | 说明 |
|----------|------|------|------|
| desc | string | 是 | 声明获取用户个人信息后的用途，不超过30个字符 |
| lang | string | 否 | 指定返回信息的语言，zh_CN简体中文，en英文 |

#### 返回参数

| 参数名称 | 类型 | 说明 |
|----------|------|------|
| userInfo | object | 用户信息对象 |
| rawData | string | 不包括敏感信息的原始数据字符串 |
| signature | string | 使用sha1(rawData+sessionkey)得到字符串，用于校验用户信息 |
| encryptedData | string | 包括敏感信息在内的完整用户信息的加密数据 |
| iv | string | 加密算法的初始向量 |
| cloudID | string | 敏感数据对应的云ID，开通云开发后可用 |

#### userInfo对象结构

| 参数名称 | 类型 | 说明 |
|----------|------|------|
| nickName | string | 用户昵称 |
| avatarUrl | string | 用户头像URL |
| gender | number | 用户性别，0未知，1男性，2女性 |
| country | string | 用户所在国家 |
| province | string | 用户所在省份 |
| city | string | 用户所在城市 |
| language | string | 用户的语言 |

#### 代码示例

```xml
<!-- WXML -->
<button type="primary" bindtap="getUserProfile">授权登录</button>
<image src="{{avatarUrl}}" />
<text>{{nickName}}</text>
```

```javascript
// JS
Page({
  data: {
    avatarUrl: '',
    nickName: ''
  },

  getUserProfile(e) {
    // 推荐使用wx.getUserProfile获取用户信息
    wx.getUserProfile({
      desc: '用于完善用户资料',  // 声明获取用户信息后的用途
      lang: 'zh_CN',
      success: (res) => {
        console.log('用户信息:', res.userInfo);
        this.setData({
          avatarUrl: res.userInfo.avatarUrl,
          nickName: res.userInfo.nickName
        });

        // 可以同时获取登录态
        this.loginWithUserInfo(res);
      },
      fail: (err) => {
        console.log('用户拒绝授权', err);
        wx.showToast({
          title: '请允许授权',
          icon: 'none'
        });
      }
    });
  },

  loginWithUserInfo(userInfoRes) {
    // 先获取code
    wx.login({
      success: (loginRes) => {
        // 发送到服务器换取用户信息
        wx.request({
          url: 'https://your-domain.com/api/login',
          method: 'POST',
          data: {
            code: loginRes.code,
            userInfo: userInfoRes.userInfo,
            rawData: userInfoRes.rawData,
            signature: userInfoRes.signature,
            encryptedData: userInfoRes.encryptedData,
            iv: userInfoRes.iv
          },
          success: (res) => {
            // 保存登录态
            wx.setStorageSync('token', res.data.token);
            wx.setStorageSync('userInfo', res.data.userInfo);
          }
        });
      }
    });
  }
});
```

---

### 检查登录态（wx.checkSession）

**接口说明**：检查登录态是否有效。

**调用方式**：小程序端直接调用

#### 代码示例

```javascript
wx.checkSession({
  success: () => {
    // session_key未过期，可以使用
    console.log('登录态有效');
  },
  fail: () => {
    // session_key已过期，需要重新登录
    console.log('登录态已失效，需重新登录');
    this.doLogin();
  }
});
```

---

### 获取用户设置（wx.getSetting）

**接口说明**：获取用户的当前设置。

**调用方式**：小程序端直接调用

#### 返回参数

| 参数名称 | 类型 | 说明 |
|----------|------|------|
| authSetting | object | 用户授权结果信息 |

#### authSetting对象说明

| 参数名称 | 类型 | 说明 |
|----------|------|------|
| scope.userInfo | boolean | 是否授权用户信息 |
| scope.userLocation | boolean | 是否授权地理位置 |
| scope.address | boolean | 是否授权通讯地址 |
| scope.invoiceTitle | boolean | 是否授权发票抬头 |
| scope.werun | boolean | 是否授权微信运动步数 |
| scope.record | boolean | 是否授权录音功能 |
| scope.writePhotosAlbum | boolean | 是否授权保存到相册 |
| scope.camera | boolean | 是否授权摄像头 |

#### 代码示例

```javascript
wx.getSetting({
  success: (res) => {
    if (res.authSetting['scope.userInfo']) {
      // 已授权，可以获取用户信息
      wx.getUserProfile({
        desc: '用于完善用户资料',
        success: (profileRes) => {
          console.log('用户已授权:', profileRes.userInfo);
        }
      });
    } else {
      // 未授权，提示用户授权
      console.log('用户未授权userInfo');
    }
  }
});
```

---

## 四、完整登录流程实现

### 4.1 前端完整代码

```javascript
// 登录模块
const app = getApp();

class LoginService {
  // 完整登录流程
  static async login() {
    try {
      // 1. 获取登录凭证
      const loginResult = await this.wxLogin();
      if (!loginResult.code) {
        throw new Error('获取code失败');
      }

      // 2. 发送到服务器验证并获取用户信息
      const serverResult = await this.verifyCode(loginResult.code);

      // 3. 保存登录信息
      this.saveLoginInfo(serverResult);

      return serverResult;
    } catch (error) {
      console.error('登录失败:', error);
      throw error;
    }
  }

  // wx.login包装
  static wxLogin() {
    return new Promise((resolve, reject) => {
      wx.login({
        success: resolve,
        fail: reject
      });
    });
  }

  // 发送code到服务器
  static async verifyCode(code) {
    return new Promise((resolve, reject) => {
      wx.request({
        url: `${app.globalData.apiBaseUrl}/login`,
        method: 'POST',
        data: { code },
        success: (res) => {
          if (res.statusCode === 200 && res.data.success) {
            resolve(res.data.data);
          } else {
            reject(new Error(res.data.message || '登录失败'));
          }
        },
        fail: reject
      });
    });
  }

  // 保存登录信息
  static saveLoginInfo(data) {
    wx.setStorageSync('token', data.token);
    wx.setStorageSync('openid', data.openid);
    wx.setStorageSync('unionid', data.unionid);
    wx.setStorageSync('userInfo', data.userInfo);
  }

  // 退出登录
  static logout() {
    wx.removeStorageSync('token');
    wx.removeStorageSync('openid');
    wx.removeStorageSync('unionid');
    wx.removeStorageSync('userInfo');
  }

  // 检查登录态
  static async checkSession() {
    return new Promise((resolve) => {
      wx.checkSession({
        success: () => {
          resolve(true);
        },
        fail: () => {
          // 登录态失效，需要重新登录
          this.login().then(resolve).catch(() => resolve(false));
        }
      });
    });
  }
}

// 获取用户授权信息
async function getUserProfileWithLogin() {
  try {
    // 先检查登录态
    const isValidSession = await LoginService.checkSession();

    if (!isValidSession) {
      throw new Error('请先登录');
    }

    // 获取用户信息
    const profileResult = await new Promise((resolve, reject) => {
      wx.getUserProfile({
        desc: '用于完善会员资料',
        success: resolve,
        fail: reject
      });
    });

    // 更新服务器用户信息
    await updateUserInfo({
      ...profileResult.userInfo,
      rawData: profileResult.rawData
    });

    return profileResult.userInfo;
  } catch (error) {
    console.error('获取用户信息失败:', error);
    throw error;
  }
}

// 更新用户信息到服务器
function updateUserInfo(userInfo) {
  const token = wx.getStorageSync('token');
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${app.globalData.apiBaseUrl}/user/update`,
      method: 'POST',
      header: {
        'Authorization': `Bearer ${token}`,
        'content-type': 'application/json'
      },
      data: userInfo,
      success: resolve,
      fail: reject
    });
  });
}

module.exports = {
  LoginService,
  getUserProfileWithLogin
};
```

### 4.2 后端完整代码（Python Flask示例）

```python
from flask import Flask, request, jsonify
import requests
import redis
import json

app = Flask(__name__)
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# 配置
WECHAT_APPID = 'your_appid'
WECHAT_APPSECRET = 'your_appsecret'
SESSION_EXPIRE = 7200  # 2小时

@app.route('/api/login', methods=['POST'])
def login():
    """登录接口"""
    code = request.json.get('code')

    if not code:
        return jsonify({'success': False, 'message': '缺少code参数'}), 400

    # 1. 调用code2Session获取openid和session_key
    wechat_result = code2session(WECHAT_APPID, WECHAT_APPSECRET, code)

    if not wechat_result.get('openid'):
        return jsonify({
            'success': False,
            'message': '微信登录失败',
            'errcode': wechat_result.get('errcode'),
            'errmsg': wechat_result.get('errmsg')
        }), 401

    openid = wechat_result['openid']
    session_key = wechat_result['session_key']
    unionid = wechat_result.get('unionid')  # 可能不存在

    # 2. 生成自定义登录态token
    token = generate_token(openid)

    # 3. 保存用户会话信息到Redis
    user_session = {
        'openid': openid,
        'session_key': session_key,
        'unionid': unionid,
        'login_time': get_current_timestamp()
    }
    redis_client.setex(f'user_session:{token}', SESSION_EXPIRE, json.dumps(user_session))

    # 4. 查询或创建用户记录
    user = get_or_create_user(openid, unionid)

    # 5. 返回登录结果
    return jsonify({
        'success': True,
        'data': {
            'token': token,
            'openid': openid,
            'unionid': unionid,
            'userInfo': user
        }
    })


@app.route('/api/user/update', methods=['POST'])
def update_user():
    """更新用户信息接口"""
    # 验证token
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_session = get_user_session(token)

    if not user_session:
        return jsonify({'success': False, 'message': '登录已过期'}), 401

    # 获取用户更新信息
    user_info = request.json

    # 更新用户信息
    update_user_info(user_session['openid'], user_info)

    return jsonify({'success': True, 'message': '更新成功'})


def code2session(appid, secret, code):
    """调用微信code2Session接口"""
    url = 'https://api.weixin.qq.com/sns/jscode2session'
    params = {
        'appid': appid,
        'secret': secret,
        'js_code': code,
        'grant_type': 'authorization_code'
    }
    response = requests.get(url, params=params)
    return response.json()


def generate_token(openid):
    """生成自定义登录token"""
    import hashlib
    import time
    random_str = str(time.time()) + openid
    return hashlib.sha256(random_str.encode()).hexdigest()


def get_user_session(token):
    """从Redis获取用户会话"""
    session_str = redis_client.get(f'user_session:{token}')
    if session_str:
        return json.loads(session_str)
    return None


def get_or_create_user(openid, unionid=None):
    """获取或创建用户"""
    # 实现用户表查询和创建逻辑
    pass


def update_user_info(openid, user_info):
    """更新用户信息"""
    # 实现用户信息更新逻辑
    pass
```

---

## 五、微信支付接口

### 5.1 支付流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   小程序端   │     │  开发者服务器  │     │   微信支付服务器   │     │    微信服务器    │
└──────┬──────┘     └──────┬──────┘     └────────┬────────┘     └────────┬────────┘
       │                  │                      │                      │
       │  1.选择商品下单    │                      │                      │
       │ ──────────────────>│                      │                      │
       │                  │                      │                      │
       │                  │  2.调用统一下单接口     │                      │
       │                  │ ──────────────────────>│                      │
       │                  │                      │                      │
       │                  │  3.返回prepay_id       │                      │
       │                  │ <──────────────────────│                      │
       │                  │                      │                      │
       │                  │  4.二次签名           │                      │
       │                  │  5.返回支付参数        │                      │
       │  6.返回支付参数   │                      │                      │
       │ <─────────────────│                      │                      │
       │                  │                      │                      │
       │  7.调用wx.requestPayment│                 │                      │
       │ ───────────────────────────────────────────────────────────────>│
       │                  │                      │                      │
       │                  │                      │  8.支付成功通知       │
       │                  │                      │ <─────────────────────│
       │  9.支付成功回调   │                      │                      │
       │ <───────────────────────────────────────────────────────────────│
       │                  │                      │                      │
```

### 5.2 统一下单接口（后端调用）

**接口说明**：商户在小程序中先调用该接口在微信支付服务后台生成预支付交易单，返回正确的预支付交易后调起支付。

**调用方式**：开发者服务器端调用

#### 请求地址

```
POST https://api.mch.weixin.qq.com/pay/unifiedorder
```

#### 请求参数

| 参数名称 | 类型 | 必须 | 说明 |
|----------|------|------|------|
| appid | string | 是 | 小程序ID |
| mch_id | string | 是 | 商户号 |
| nonce_str | string | 是 | 随机字符串，不长于32位 |
| sign | string | 是 | 签名，详见签名算法 |
| body | string | 是 | 商品简单描述 |
| out_trade_no | string | 是 | 商户系统内部订单号 |
| total_fee | int | 是 | 订单总金额，单位为分 |
| spbill_create_ip | string | 是 | 终端IP |
| notify_url | string | 是 | 异步通知地址 |
| trade_type | string | 是 | 交易类型，小程序填JSAPI |
| openid | string | 是 | 用户标识（小程序必填） |

#### 返回参数

| 参数名称 | 类型 | 说明 |
|----------|------|------|
| return_code | string | 返回状态码 |
| return_msg | string | 返回信息 |
| result_code | string | 业务结果 |
| prepay_id | string | 预支付交易会话标识 |
| err_code | string | 错误代码 |
| err_code_desc | string | 错误代码描述 |

#### 代码示例

```python
import hashlib
import time
import random
import string
import requests
import xml.etree.ElementTree as ET

class WechatPay:
    def __init__(self, appid, mch_id, api_key, notify_url):
        self.appid = appid
        self.mch_id = mch_id
        self.api_key = api_key
        self.notify_url = notify_url

    def unified_order(self, body, out_trade_no, total_fee, openid, spbill_create_ip):
        """统一下单"""
        url = 'https://api.mch.weixin.qq.com/pay/unifiedorder'

        # 生成随机字符串
        nonce_str = ''.join(random.choices(string.ascii_letters + string.digits, k=32))

        # 构造请求参数
        params = {
            'appid': self.appid,
            'mch_id': self.mch_id,
            'nonce_str': nonce_str,
            'body': body,
            'out_trade_no': out_trade_no,
            'total_fee': total_fee,
            'spbill_create_ip': spbill_create_ip,
            'notify_url': self.notify_url,
            'trade_type': 'JSAPI',
            'openid': openid
        }

        # 生成签名
        sign = self.generate_sign(params)
        params['sign'] = sign

        # 发送请求
        xml_params = self.dict_to_xml(params)
        response = requests.post(url, data=xml_params.encode('utf-8'),
                                headers={'Content-Type': 'text/xml'})

        # 解析响应
        result = self.xml_to_dict(response.text)

        if result.get('return_code') == 'SUCCESS' and result.get('result_code') == 'SUCCESS':
            return {
                'success': True,
                'prepay_id': result.get('prepay_id')
            }
        else:
            return {
                'success': False,
                'err_msg': result.get('err_code_desc', result.get('return_msg'))
            }

    def generate_sign(self, params):
        """生成签名"""
        # 按字典键排序
        sorted_params = sorted(params.items())
        # 拼接字符串
        sign_str = '&'.join([f'{k}={v}' for k, v in sorted_params if v])
        # 拼接商户密钥
        sign_str = sign_str + f'&key={self.api_key}'
        # MD5签名
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()

    def dict_to_xml(self, params):
        """字典转XML"""
        xml = '<xml>'
        for k, v in params.items():
            xml += f'<{k}><![CDATA[{v}]]></{k}>'
        xml += '</xml>'
        return xml

    def xml_to_dict(self, xml_str):
        """XML转字典"""
        root = ET.fromstring(xml_str)
        result = {}
        for child in root:
            result[child.tag] = child.text
        return result

    def get_pay_params(self, prepay_id):
        """获取调起支付参数（二次签名）"""
        nonce_str = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        timestamp = str(int(time.time()))

        params = {
            'appId': self.appid,
            'timeStamp': timestamp,
            'nonceStr': nonce_str,
            'package': f'prepay_id={prepay_id}',
            'signType': 'MD5'
        }

        sign = self.generate_sign(params)

        return {
            'timeStamp': timestamp,
            'nonceStr': nonce_str,
            'package': f'prepay_id={prepay_id}',
            'paySign': sign,
            'signType': 'MD5'
        }
```

### 5.3 小程序调起支付（wx.requestPayment）

**接口说明**：调起微信支付。

**调用方式**：小程序端直接调用

#### 请求参数

| 参数名称 | 类型 | 必须 | 说明 |
|----------|------|------|------|
| timeStamp | string | 是 | 时间戳，从1970年1月1日00:00:00至今的秒数 |
| nonceStr | string | 是 | 随机字符串，长度32个字符以下 |
| package | string | 是 | 统一下单接口返回的prepay_id，格式prepay_id=* |
| signType | string | 是 | 签名算法，目前支持MD5和HMAC-SHA256 |
| paySign | string | 是 | 签名，详见签名算法 |

#### 代码示例

```javascript
// 1. 请求服务器获取支付参数
async function requestPayment(orderId) {
  try {
    // 获取登录态
    const token = wx.getStorageSync('token');

    // 调用后端接口获取支付参数
    const payParams = await new Promise((resolve, reject) => {
      wx.request({
        url: 'https://your-domain.com/api/pay/create',
        method: 'POST',
        header: {
          'Authorization': `Bearer ${token}`,
          'content-type': 'application/json'
        },
        data: { orderId },
        success: (res) => {
          if (res.data.success) {
            resolve(res.data.data);
          } else {
            reject(new Error(res.data.message));
          }
        },
        fail: reject
      });
    });

    // 调起微信支付
    await this.doRequestPayment(payParams);

    return { success: true };
  } catch (error) {
    console.error('支付失败:', error);
    throw error;
  }
}

// 2. 调起支付
doRequestPayment(payParams) {
  return new Promise((resolve, reject) => {
    wx.requestPayment({
      timeStamp: payParams.timeStamp,
      nonceStr: payParams.nonceStr,
      package: payParams.package,
      signType: payParams.signType,
      paySign: payParams.paySign,
      success: (res) => {
        console.log('支付成功');
        resolve(res);
      },
      fail: (err) => {
        console.error('支付失败:', err);
        // 用户取消支付
        if (err.errMsg === 'requestPayment:fail cancel') {
          reject(new Error('用户取消支付'));
        } else {
          reject(new Error(err.errMsg));
        }
      }
    });
  });
}
```

---

## 六、订阅消息接口

### 6.1 订阅流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│   小程序端   │     │  开发者服务器  │     │    微信服务器     │
└──────┬──────┘     └──────┬──────┘     └────────┬────────┘
       │                  │                      │
       │  1.调用订阅接口    │                      │
       │ ──────────────────>│                      │
       │  2.返回订阅结果    │                      │
       │ <──────────────────│                      │
       │                  │                      │
       │  3.业务完成后发送消息│                      │
       │                  │ ──────────────────────>│
       │                  │                      │
       │                  │  4.发送成功/失败通知    │
       │                  │ <──────────────────────│
       │                  │                      │
```

### 6.2 小程序端请求订阅（wx.requestSubscribeMessage）

**接口说明**：调起客户端小程序订阅消息界面，返回用户订阅消息的操作结果。

**调用方式**：小程序端直接调用

**触发条件**：用户发生点击行为或者发起支付回调后，才可以调起订阅消息界面。

#### 请求参数

| 参数名称 | 类型 | 必须 | 说明 |
|----------|------|------|------|
| tmplIds | string[] | 是 | 模板列表，数组长度最大为3 |

#### 返回参数

| 参数名称 | 类型 | 说明 |
|----------|------|------|
| [templateId] | string | 打游戏模板ID的订阅状态，accept接受，reject拒绝 |

#### 代码示例

```javascript
// 请求订阅消息
requestSubscribeMessage(tmplIds) {
  return new Promise((resolve, reject) => {
    // 检查是否支持订阅消息
    if (!wx.requestSubscribeMessage) {
      reject(new Error('当前版本不支持订阅消息'));
      return;
    }

    wx.requestSubscribeMessage({
      tmplIds: tmplIds,  // 模板ID数组
      success: (res) => {
        console.log('订阅结果:', res);

        // 处理每个模板的订阅结果
        const accepted = [];
        const rejected = [];

        for (const [templateId, status] of Object.entries(res)) {
          if (status === 'accept') {
            accepted.push(templateId);
          } else if (status === 'reject') {
            rejected.push(templateId);
          }
        }

        resolve({
          accepted,
          rejected,
          allAccepted: rejected.length === 0
        });
      },
      fail: (err) => {
        console.error('订阅失败:', err);
        reject(err);
      }
    });
  });
}

// 使用示例
async function onPlaceOrder() {
  try {
    // 下单成功后，请求订阅
    const subResult = await this.requestSubscribeMessage([
      'template_id_1',  // 订单通知模板
      'template_id_2'   // 物流通知模板
    ]);

    // 保存订阅状态到服务器
    await this.saveSubscriptionStatus(subResult);

  } catch (error) {
    console.error('订阅失败:', error);
  }
}
```

### 6.3 服务端发送订阅消息

**接口说明**：发送订阅消息给用户。

**调用方式**：开发者服务器端调用

#### 请求地址

```
POST https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={access_token}
```

#### 请求参数

| 参数名称 | 类型 | 必须 | 说明 |
|----------|------|------|------|
| touser | string | 是 | 用户的OpenID |
| template_id | string | 是 | 模板ID |
| page | string | 否 | 点击模板卡片后的跳转页面 |
| data | object | 是 | 模板内容，格式符合模板要求 |
| miniprogram_state | string | 否 | 跳转小程序类型，developer开发版，trial体验版，formal正式版 |

#### data格式说明

模板中的每个关键词对应一个对象，格式为 `{"value": "内容", "color": "#颜色"}`

#### 代码示例

```python
import requests
import json

class WechatSubscribeMessage:
    def __init__(self, appid, appsecret):
        self.appid = appid
        self.appsecret = appsecret
        self.access_token = None

    def get_access_token(self):
        """获取access_token"""
        url = f'https://api.weixin.qq.com/cgi-bin/token'
        params = {
            'grant_type': 'client_credential',
            'appid': self.appid,
            'secret': self.appsecret
        }
        response = requests.get(url, params=params)
        result = response.json()
        self.access_token = result.get('access_token')
        return self.access_token

    def send_message(self, openid, template_id, page, data, miniprogram_state='formal'):
        """发送订阅消息"""
        if not self.access_token:
            self.get_access_token()

        url = f'https://api.weixin.qq.com/cgi-bin/message/subscribe/send'
        params = {'access_token': self.access_token}

        payload = {
            'touser': openid,
            'template_id': template_id,
            'page': page,
            'data': data,
            'miniprogram_state': miniprogram_state
        }

        response = requests.post(url, params=params, json=payload)
        result = response.json()

        if result.get('errcode') == 0:
            return {'success': True, 'message': '发送成功'}
        else:
            return {'success': False, 'errcode': result.get('errcode'), 'errmsg': result.get('errmsg')}

    def send_order_notify(self, openid, order_no, status, remark=''):
        """发送订单通知"""
        template_id = 'your_template_id'  # 替换为实际模板ID
        page = f'/pages/order/detail?orderNo={order_no}'

        data = {
            'character_string1': {'value': order_no},      // 订单号
            'phrase2': {'value': status},                   // 状态
            'date3': {'value': self.get_current_time()},   // 时间
            'thing4': {'value': remark or '感谢您的使用'}    // 备注
        }

        return self.send_message(openid, template_id, page, data)


# 使用示例
wechat = WechatSubscribeMessage('appid', 'appsecret')

# 发送订单通知
result = wechat.send_order_notify(
    openid='user_openid',
    order_no='ORDER123456',
    status='已发货',
    remark='您的订单已发货，请注意查收'
)

print(result)
```

---

## 七、敏感数据解密

### 7.1 解密说明

当获取用户信息时，如果需要解密敏感数据（如encryptedData），需要使用session_key进行AES-128-CBC解密。

### 7.2 Python解密示例

```python
import base64
from Crypto.Cipher import AES
import json

class WechatDataDecryptor:
    def __init__(self, session_key):
        # session_key需要是16字节的AES密钥
        self.session_key = base64.b64decode(session_key + '==')
        # 确保session_key为16字节
        if len(self.session_key) > 16:
            self.session_key = self.session_key[:16]
        while len(self.session_key) < 16:
            self.session_key += b'\0'

    def decrypt(self, encrypted_data, iv):
        """解密微信敏感数据"""
        encrypted_data = base64.b64decode(encrypted_data)
        iv = base64.b64decode(iv)

        cipher = AES.new(self.session_key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(encrypted_data)

        # 去除补位
        pad_len = decrypted[-1]
        if pad_len > 16:
            raise ValueError('Invalid padding')
        decrypted = decrypted[:-pad_len]

        # 去除随机Padding
        decrypted = decrypted[16:]
        json_len = int.from_bytes(decrypted[:4], byteorder='big')
        json_str = decrypted[4:4+json_len].decode('utf-8')

        return json.loads(json_str)

    def decrypt_user_info(self, encrypted_data, iv):
        """解密用户信息"""
        return self.decrypt(encrypted_data, iv)

    def decrypt_phone(self, encrypted_data, iv):
        """解密手机号"""
        return self.decrypt(encrypted_data, iv)


# 使用示例
decryptor = WechatDataDecryptor(session_key)
user_info = decryptor.decrypt_user_info(encrypted_data, iv)
print('用户信息:', user_info)
```

---

## 八、错误码汇总

### 8.1 code2Session错误码

| errcode | 说明 |
|---------|------|
| -1 | 系统繁忙，请稍后重试 |
| 0 | 请求成功 |
| 40029 | code无效 |
| 45011 | 频率限制，每个用户每分钟最多100次 |
| 40226 | 高风险等级用户，小程序登录拦截 |

### 8.2 支付错误码

| errcode | 说明 |
|---------|------|
| NOAUTH | 商户权限异常 |
| NOTENOUGH | 余额不足 |
| ORDERPAID | 订单已支付 |
| ORDERCLOSED | 订单已关闭 |
| SYSTEMERROR | 系统错误 |
| APPID_NOT_EXIST | APPID不存在 |
| MCHID_NOT_EXIST | MCHID不存在 |
| APPID_MCHID_NOT_MATCH | appid和mch_id不匹配 |
| SIGN_ERROR | 签名错误 |
| XML_FORMAT_ERROR | XML格式错误 |
| POST_FORMAT_ERROR | POST数据格式错误 |
| LANGUAGE_NOT_SUPPORT | 语言不支持 |

### 8.3 订阅消息错误码

| errcode | 说明 |
|---------|------|
| 40001 | access_token无效 |
| 40003 | touser无效 |
| 40013 | invalid template_id |
| 43101 | 用户拒绝接受消息 |
| 104001 | 小程序订阅api权限被封禁 |

---

## 九、集成建议

### 9.1 登录流程最佳实践

1. **首次登录**：先调用wx.login获取code，再发送到服务器换取用户信息
2. **检查登录态**：每次进入小程序时调用wx.checkSession检查session是否过期
3. **Token管理**：服务器生成自定义token并设置过期时间，前端保存并随请求发送
4. **多端互通**：同一开放平台下的小程序、公众号、App可通过UnionID实现用户信息互通

### 9.2 安全建议

1. **不要在前端存储session_key**：session_key应仅在服务器端使用
2. **敏感数据解密**：encryptedData必须在服务器端解密，不要在前端暴露session_key
3. **签名验证**：获取用户信息后验证signature确保数据未被篡改
4. **access_token缓存**：access_token有效期为2小时，需在服务器端缓存并定时刷新
5. **支付安全**：统一下单和支付签名必须在服务器端完成

### 9.3 错误处理建议

| 场景 | 处理方式 |
|------|----------|
| code2Session失败 | 提示用户重新登录，记录错误日志 |
| 登录态过期 | 自动重新执行登录流程 |
| 支付失败 | 根据错误码提示用户，给出重试选项 |
| 订阅消息失败 | 降级处理，不影响主流程 |
| 网络异常 | 添加重试机制，超时提示 |

---

## 十、相关文档链接

| 文档 | 地址 |
|------|------|
| 小程序登录 | https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/login.html |
| code2Session | https://developers.weixin.qq.com/minigame/dev/api-backend/open-api/login/auth.code2Session.html |
| wx.getUserProfile | https://developers.weixin.qq.com/miniprogram/dev/api/open-api/user-info/wx.getUserProfile.html |
| UnionID机制 | https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/union-id.html |
| 调起支付API | https://pay.weixin.qq.com/doc/v3/merchant/4012791898 |
| 统一下单API | https://pay.weixin.qq.com/doc/v2/merchant/4011936987 |
| 订阅消息 | https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/subscribe-message.html |
| 发送订阅消息 | https://developers.weixin.qq.com/miniprogram/dev/api-backend/open-api/subscribe-message/subscribeMessage.send.html |