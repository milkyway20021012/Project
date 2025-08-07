# 統一LINE Login綁定系統使用指南

## 🎯 系統概述

這個統一綁定系統讓用戶只需要在LINE Bot中完成一次LINE Login綁定，就可以操作所有TourHub相關網站，無需對每個網站都登入一次。

## 🏗️ 系統架構

### 核心組件

1. **統一用戶管理系統** (`unified_user_manager.py`)
   - 管理用戶的統一帳號
   - 處理用戶資料的創建和更新
   - 記錄用戶操作日誌

2. **LINE Login處理器** (`line_login_handler.py`)
   - 處理LINE Login授權流程
   - 生成綁定邀請訊息
   - 處理授權回調

3. **網站API代理** (`website_proxy.py`)
   - 代理用戶對不同網站的操作
   - 統一處理API調用
   - 管理不同模組的操作

4. **資料庫表結構** (`unified_user_system.sql`)
   - `unified_users`: 統一用戶表
   - `website_modules`: 網站模組配置
   - `user_website_bindings`: 用戶網站綁定關係
   - `user_operation_logs`: 用戶操作日誌

## 🚀 使用流程

### 1. 用戶綁定流程

```
用戶輸入「綁定帳號」
    ↓
Bot顯示綁定邀請訊息
    ↓
用戶點擊「立即綁定帳號」按鈕
    ↓
跳轉到LINE Login授權頁面
    ↓
用戶完成LINE授權
    ↓
系統創建統一帳號
    ↓
綁定完成，返回成功頁面
```

### 2. 網站操作流程

```
用戶輸入「網站操作」
    ↓
Bot顯示可用網站列表
    ↓
用戶選擇要操作的網站
    ↓
Bot顯示該網站的操作選單
    ↓
用戶選擇具體操作
    ↓
後端代理執行API調用
    ↓
返回操作結果
```

## 📝 支援的關鍵字

### 帳號相關
- `綁定帳號`、`帳號綁定`、`登入`、`login`
- `我的帳號`、`個人資料`

### 網站操作
- `網站操作`、`操作網站`、`使用網站`
- `網站功能`、`我的操作`

### 原有功能（保留）
- `功能介紹`、`help`
- `第一名`、`第二名`、`第三名`
- `東京`、`大阪`、`京都`、`北海道`

## 🌐 支援的網站模組

### 1. TourHub排行榜 (`tourhub_leaderboard`)
- 🏆 查看排行榜 - https://tourhubashy.vercel.app/
- 🔥 熱門行程

### 2. 行程管理 (`trip_management`)
- 📋 管理我的行程 - https://tripfrontend.vercel.app/linetrip
- ➕ 創建新行程

### 3. 集合管理 (`tour_clock`)
- ⏰ 管理集合時間 - https://tourclock-dvf2.vercel.app/
- 📅 創建新集合

### 4. 置物櫃查找 (`locker_finder`)
- 🔍 查找置物櫃 - https://tripfrontend.vercel.app/linelocker
- 📍 按地點搜尋

### 5. 分帳系統 (`bill_split`)
- 💰 管理分帳 - https://split-front-pearl.vercel.app
- ➕ 新建分帳

## ⚙️ 環境變數設定

需要在Vercel或本地環境中設定以下環境變數：

```bash
# LINE Bot基本設定
CHANNEL_ACCESS_TOKEN=your_line_bot_token
CHANNEL_SECRET=your_line_bot_secret

# LINE Login設定
LINE_LOGIN_CHANNEL_ID=your_line_login_channel_id
LINE_LOGIN_CHANNEL_SECRET=your_line_login_channel_secret
LINE_LOGIN_REDIRECT_URI=https://your-domain.vercel.app/auth/line/callback

# 資料庫設定
DB_HOST=your_database_host
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
```

## 🗄️ 資料庫設定

1. 執行 `database/unified_user_system.sql` 創建必要的表格
2. 確保資料庫連接設定正確
3. 預設會插入4個網站模組配置

## 🔧 API端點

### 1. LINE Bot Webhook
- `POST /callback` - 處理LINE Bot訊息

### 2. LINE Login回調
- `GET /auth/line/callback` - 處理LINE Login授權回調

### 3. 除錯端點
- `GET /debug` - 檢查系統配置狀態
- `GET /` - 健康檢查

## 💡 使用範例

### 用戶綁定帳號
```
用戶: 綁定帳號
Bot: [顯示綁定邀請Flex Message，包含「立即綁定帳號」按鈕]
```

### 用戶操作網站
```
用戶: 網站操作
Bot: [顯示可用網站列表：TourHub排行榜、行程管理、集合管理、置物櫃查找、分帳系統]
用戶: [點擊「🌐 行程管理」]
Bot: [顯示行程管理操作選單：📋 管理我的行程、➕ 創建新行程]
用戶: [點擊「📋 管理我的行程」]
Bot: [顯示跳轉訊息，包含「🚀 開啟網站」按鈕]
用戶: [點擊按鈕跳轉到 https://tripfrontend.vercel.app/linetrip]
```

## 🔒 安全特性

1. **統一Token認證** - 每個用戶都有唯一的統一認證Token
2. **操作日誌記錄** - 所有用戶操作都會被記錄
3. **LINE官方認證** - 使用LINE Login確保身份安全
4. **Token過期管理** - 支援Token自動刷新機制

## 🚀 部署步驟

1. **設定環境變數** - 在Vercel中設定所有必要的環境變數
2. **部署資料庫** - 執行SQL腳本創建表格
3. **部署應用** - 推送代碼到Vercel
4. **設定LINE Bot** - 更新Webhook URL
5. **設定LINE Login** - 配置回調URL
6. **測試功能** - 驗證綁定和操作流程

## 📊 監控和日誌

系統會自動記錄：
- 用戶綁定操作
- 網站API調用
- 操作成功/失敗狀態
- 錯誤訊息和異常

可以通過查詢 `user_operation_logs` 表來監控系統使用情況。

## 🔄 擴展性

### 添加新網站模組
1. 在 `website_modules` 表中添加新模組
2. 在 `website_proxy.py` 中添加對應的操作處理
3. 在 `create_website_operation_menu` 中添加操作選單

### 添加新操作類型
1. 在對應的模組操作函數中添加新操作
2. 更新操作選單配置
3. 實現具體的API調用邏輯

---

**系統狀態**: ✅ 已完成並可部署
**最後更新**: 2025-08-07
**版本**: 1.0.0
