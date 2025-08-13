# 🚀 TourHub Line Bot 跨平台整合部署指南

## 📋 部署步驟總覽

要實現從 Line Bot 直接創建內容到各個網站，需要完成以下步驟：

### 步驟 1：部署統一認證服務

#### 1.1 準備認證服務
```bash
# 將 auth_service.py 部署到 Vercel 或其他平台
# 設定環境變數
AUTH_SERVICE_URL=https://your-auth-service.vercel.app
MYSQL_HOST=trip.mysql.database.azure.com
MYSQL_USER=b1129005
MYSQL_PASSWORD=Anderson3663
MYSQL_DB=tourhub
```

#### 1.2 測試認證服務
```bash
# 健康檢查
curl https://your-auth-service.vercel.app/api/auth/health

# 測試 Token 驗證
curl -X POST https://your-auth-service.vercel.app/api/auth/verify-token \
  -H "Content-Type: application/json" \
  -d '{"line_user_id":"test_user","unified_token":"test_token"}'
```

### 步驟 2：更新各個網站

#### 2.1 行程管理網站 (https://tripfrontend.vercel.app)

**添加依賴**：
```json
{
  "dependencies": {
    "axios": "^1.6.0"
  }
}
```

**添加 API 端點**：
- 複製 `website_api_examples/trip_management_api.js` 到專案中
- 根據現有資料庫結構調整代碼
- 設定環境變數：`AUTH_SERVICE_URL`

**測試端點**：
```bash
curl -X POST https://tripfrontend.vercel.app/api/line-bot/trips \
  -H "Content-Type: application/json" \
  -d '{
    "line_user_id": "test_user",
    "unified_token": "valid_token",
    "trip_data": {
      "title": "東京三日遊行程",
      "location": "東京",
      "days": 3,
      "description": "測試行程"
    }
  }'
```

#### 2.2 集合管理網站 (https://tourclock-dvf2.vercel.app)

**添加 API 端點**：
- 複製 `website_api_examples/tour_clock_api.js` 到專案中
- 調整資料庫模型和邏輯
- 設定環境變數：`AUTH_SERVICE_URL`

#### 2.3 分帳系統網站 (https://split-front-pearl.vercel.app)

**添加 API 端點**：
- 複製 `website_api_examples/bill_split_api.js` 到專案中
- 調整資料庫模型和邏輯
- 設定環境變數：`AUTH_SERVICE_URL`

### 步驟 3：啟用 Line Bot 實際 API 調用

#### 3.1 設定環境變數
```bash
# 在 Line Bot 部署環境中設定
USE_REAL_API=true
AUTH_SERVICE_URL=https://your-auth-service.vercel.app
```

#### 3.2 測試 Line Bot 創建功能
```
用戶在 Line Bot 中輸入：創建東京三日遊行程
預期結果：
✅ 行程「東京三日遊行程」創建成功！
📝 標題：東京三日遊行程
📍 地點：東京
📅 天數：3天
[查看行程] ← 點擊跳轉到網站
```

## 🔧 技術實現細節

### 認證流程
```
1. 用戶在 Line Bot 輸入創建指令
2. Line Bot 解析指令，提取資訊
3. 獲取用戶的統一 Token
4. 調用目標網站的 /api/line-bot/* 端點
5. 網站驗證 Token（調用認證服務）
6. 創建內容並返回結果
7. Line Bot 顯示結果給用戶
```

### API 請求格式
```json
{
  "line_user_id": "U1234567890",
  "unified_token": "abc123...",
  "trip_data": {
    "title": "東京三日遊行程",
    "location": "東京",
    "days": 3,
    "description": "透過 Line Bot 創建",
    "created_via": "line_bot"
  }
}
```

### API 回應格式
```json
{
  "success": true,
  "trip_id": "trip_20241215_143022",
  "message": "行程創建成功",
  "url": "/trip/trip_20241215_143022",
  "data": {
    "id": "trip_20241215_143022",
    "title": "東京三日遊行程",
    "location": "東京",
    "days": 3,
    "created_at": "2024-12-15T14:30:22Z"
  }
}
```

## 🧪 測試策略

### 1. 單元測試
```python
# 測試 API 調用
def test_create_trip_api():
    result = website_proxy.create_trip("test_user", {
        "title": "測試行程",
        "location": "東京",
        "days": 3
    })
    assert result['success'] == True
    assert 'trip_id' in result
```

### 2. 整合測試
```bash
# 測試完整流程
# 1. 在 Line Bot 中輸入創建指令
# 2. 檢查網站是否成功創建內容
# 3. 驗證返回的連結是否正確
```

### 3. 錯誤處理測試
```python
# 測試各種錯誤情況
- Token 無效
- 網站 API 不可用
- 網路連接問題
- 資料格式錯誤
```

## 📊 監控和日誌

### 1. API 調用監控
```python
# 在 website_proxy.py 中添加監控
logger.info(f"🌐 調用 API: {url}")
logger.info(f"📤 請求數據: {data}")
logger.info(f"📥 回應狀態: {response.status_code}")
```

### 2. 成功率統計
```sql
-- 統計 API 調用成功率
SELECT 
  module_name,
  COUNT(*) as total_calls,
  SUM(CASE WHEN result_status = 'success' THEN 1 ELSE 0 END) as successful_calls,
  (SUM(CASE WHEN result_status = 'success' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as success_rate
FROM user_operation_logs 
WHERE operation_type IN ('create_trip', 'create_meeting', 'create_bill')
GROUP BY module_name;
```

## 🚨 故障排除

### 常見問題

#### 1. 認證失敗
```
錯誤：認證失敗，請重新綁定帳號
解決：檢查統一認證服務是否正常運行
```

#### 2. API 端點不存在
```
錯誤：API 端點不存在，請聯繫技術支援
解決：確認各網站已添加對應的 API 端點
```

#### 3. 網路連接問題
```
錯誤：無法連接到服務，請檢查網路連接
解決：檢查網站是否正常運行，防火牆設定
```

### 除錯工具
```python
# 啟用詳細日誌
import logging
logging.basicConfig(level=logging.DEBUG)

# 檢查 API 回應
print(f"API Response: {response.text}")
```

## 🎯 預期效果

完成部署後，用戶體驗將是：

```
用戶：創建東京三日遊行程
Bot：✅ 行程「東京三日遊行程」創建成功！
     📝 標題：東京三日遊行程
     📍 地點：東京  
     📅 天數：3天
     [查看行程] ← 點擊直接跳轉並自動登入

用戶：設定明天9點東京車站集合  
Bot：✅ 集合「明天9點東京車站集合」創建成功！
     📍 地點：東京車站
     ⏰ 時間：明天 09:00
     [查看集合] ← 點擊直接跳轉並自動登入

用戶：建立東京旅遊分帳
Bot：✅ 分帳「東京旅遊分帳」創建成功！
     💰 幣別：TWD
     👥 參與者：1人
     [查看分帳] ← 點擊直接跳轉並自動登入
```

---

**🚀 完成這些步驟後，就能實現真正的跨平台內容創建！**
