# 🔗 跨平台內容創建整合指南

## 📋 概述

本指南詳細說明如何實現從 Line Bot 輸入指令（如「創建東京三日遊行程」）到實際在各個網站創建內容的完整流程。

## 🎯 目標流程

```
用戶在 Line Bot 輸入：創建東京三日遊行程
↓
Line Bot 解析指令並提取資訊
↓
調用統一用戶管理系統驗證用戶
↓
調用行程管理網站的 API 創建行程
↓
返回創建結果給用戶，包含查看連結
```

## 🛠️ 實現方案

### 方案一：直接 API 整合（推薦）

#### 1. 各網站需要提供的 API 端點

**行程管理網站 (https://tripfrontend.vercel.app)**
```javascript
// POST /api/line-bot/trips
{
  "line_user_id": "U1234567890",
  "unified_token": "abc123...",
  "trip_data": {
    "title": "東京三日遊行程",
    "location": "東京",
    "days": 3,
    "description": "透過 Line Bot 創建的東京三日遊行程",
    "created_via": "line_bot"
  }
}

// 回應
{
  "success": true,
  "trip_id": "trip_20241215_143022",
  "message": "行程創建成功",
  "url": "/trip/trip_20241215_143022"
}
```

**集合管理網站 (https://tourclock-dvf2.vercel.app)**
```javascript
// POST /api/line-bot/meetings
{
  "line_user_id": "U1234567890",
  "unified_token": "abc123...",
  "meeting_data": {
    "title": "明天9點東京車站集合",
    "location": "東京車站",
    "date": "2024-01-16",
    "time": "09:00",
    "description": "透過 Line Bot 創建的集合",
    "created_via": "line_bot"
  }
}
```

**分帳管理網站 (https://split-front-pearl.vercel.app)**
```javascript
// POST /api/line-bot/bills
{
  "line_user_id": "U1234567890",
  "unified_token": "abc123...",
  "bill_data": {
    "title": "東京旅遊分帳",
    "currency": "TWD",
    "description": "透過 Line Bot 創建的分帳",
    "created_via": "line_bot"
  }
}
```

#### 2. 統一認證機制

**各網站需要支援統一 Token 驗證**：
```javascript
// 中間件：驗證統一 Token
app.use('/api/line-bot/*', async (req, res, next) => {
  const { line_user_id, unified_token } = req.body;
  
  // 調用統一用戶管理 API 驗證
  const isValid = await verifyUnifiedToken(line_user_id, unified_token);
  
  if (!isValid) {
    return res.status(401).json({
      success: false,
      error: '認證失敗'
    });
  }
  
  // 獲取或創建對應的網站用戶
  req.user = await getOrCreateWebsiteUser(line_user_id);
  next();
});
```

### 方案二：Webhook 通知機制

#### 1. Line Bot 發送 Webhook

```python
# 在 website_proxy.py 中實現
def _call_website_api(self, website: str, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        config = self.website_configs.get(website)
        if not config:
            return {'success': False, 'error': f'未知網站: {website}'}
        
        # 構建 API URL
        url = config['base_url'] + config['api_endpoints'][endpoint]
        
        # 設定請求標頭
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {data.get('unified_token')}",
            'X-Line-Bot-Source': 'tourhub-line-bot'
        }
        
        # 發送 POST 請求
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            return {'success': False, 'error': '認證失敗，請重新綁定'}
        elif response.status_code == 404:
            return {'success': False, 'error': 'API 端點不存在'}
        else:
            return {
                'success': False, 
                'error': f'API 調用失敗: HTTP {response.status_code}'
            }
            
    except requests.RequestException as e:
        logger.error(f"API 調用錯誤: {e}")
        return {'success': False, 'error': f'網路錯誤: {str(e)}'}
```

#### 2. 各網站接收 Webhook

**行程管理網站範例**：
```javascript
// routes/line-bot.js
app.post('/api/line-bot/trips', async (req, res) => {
  try {
    const { line_user_id, unified_token, trip_data } = req.body;
    
    // 驗證統一 Token
    const user = await verifyAndGetUser(line_user_id, unified_token);
    if (!user) {
      return res.status(401).json({
        success: false,
        error: '用戶驗證失敗'
      });
    }
    
    // 創建行程
    const trip = await Trip.create({
      ...trip_data,
      user_id: user.id,
      created_via: 'line_bot',
      created_at: new Date()
    });
    
    // 返回結果
    res.json({
      success: true,
      trip_id: trip.id,
      message: '行程創建成功',
      url: `/trip/${trip.id}`
    });
    
  } catch (error) {
    console.error('創建行程錯誤:', error);
    res.status(500).json({
      success: false,
      error: '服務器錯誤'
    });
  }
});
```

## 🔐 統一認證實現

### 1. 統一用戶管理 API

需要創建一個統一的用戶管理 API 服務：

```python
# 新增檔案：api/auth_service.py
from flask import Flask, request, jsonify
import jwt
import datetime

app = Flask(__name__)

@app.route('/api/auth/verify-token', methods=['POST'])
def verify_unified_token():
    data = request.json
    line_user_id = data.get('line_user_id')
    unified_token = data.get('unified_token')
    
    # 驗證 Token
    user = user_manager.get_or_create_user(line_user_id)
    if user and user['unified_token'] == unified_token:
        return jsonify({
            'valid': True,
            'user_id': user['id'],
            'line_user_id': line_user_id
        })
    
    return jsonify({'valid': False}), 401

@app.route('/api/auth/get-user', methods=['POST'])
def get_user_info():
    data = request.json
    line_user_id = data.get('line_user_id')
    
    user = user_manager.get_or_create_user(line_user_id)
    if user:
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'line_user_id': line_user_id,
                'unified_token': user['unified_token']
            }
        })
    
    return jsonify({'success': False}), 404
```

### 2. 各網站的認證中間件

```javascript
// 各網站共用的認證中間件
const axios = require('axios');

const AUTH_SERVICE_URL = 'https://your-auth-service.vercel.app';

async function verifyUnifiedToken(line_user_id, unified_token) {
  try {
    const response = await axios.post(`${AUTH_SERVICE_URL}/api/auth/verify-token`, {
      line_user_id,
      unified_token
    });
    
    return response.data.valid;
  } catch (error) {
    console.error('Token 驗證失敗:', error);
    return false;
  }
}

async function getOrCreateWebsiteUser(line_user_id) {
  // 根據 line_user_id 獲取或創建網站用戶
  let user = await User.findOne({ line_user_id });
  
  if (!user) {
    user = await User.create({
      line_user_id,
      created_via: 'line_bot',
      created_at: new Date()
    });
  }
  
  return user;
}
```

## 📱 完整實現步驟

### 步驟 1：更新 Line Bot 的 API 調用

```python
# 更新 website_proxy.py 中的 _call_website_api 方法
def _call_website_api(self, website: str, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        config = self.website_configs.get(website)
        if not config:
            return {'success': False, 'error': f'未知網站: {website}'}
        
        url = config['base_url'] + config['api_endpoints'][endpoint]
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {data.get('unified_token')}",
            'X-Line-Bot-Source': 'tourhub-line-bot'
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                'success': False,
                'error': f'API 調用失敗: {response.status_code}'
            }
            
    except requests.RequestException as e:
        logger.error(f"API 調用錯誤: {e}")
        return {'success': False, 'error': f'網路錯誤: {str(e)}'}
```

### 步驟 2：各網站添加 Line Bot API 端點

每個網站都需要添加對應的 API 端點來接收 Line Bot 的請求。

### 步驟 3：部署統一認證服務

可以部署一個獨立的認證服務，或者將認證邏輯整合到現有的某個網站中。

### 步驟 4：測試整合

創建測試腳本驗證整個流程是否正常運作。

## 🎯 預期效果

實現後，用戶體驗將是：

```
用戶：創建東京三日遊行程
Bot：✅ 行程「東京三日遊行程」創建成功！
     📝 標題：東京三日遊行程
     📍 地點：東京
     📅 天數：3天
     [查看行程] ← 點擊直接跳轉到網站查看
```

用戶點擊「查看行程」後，會直接跳轉到行程管理網站，並且已經自動登入，可以看到剛才創建的行程。

---

**🚀 這樣就實現了真正的跨平台內容創建！**
