# 🚀 TourHub Line Bot - 跨平台旅遊服務整合

一個完整的 LINE Bot 系統，實現從聊天機器人直接創建內容到各個旅遊網站的跨平台整合。

## ✨ 核心特色

### 🔗 跨平台內容創建
用戶在 Line Bot 中輸入指令，直接在對應網站創建內容：
```
用戶：創建東京三日遊行程
Bot：✅ 行程「東京三日遊行程」創建成功！
     [查看行程] ← 點擊直接跳轉到網站並自動登入
```

### 🔐 統一用戶管理
- 一個 Line 帳號自動綁定所有服務
- 跨平台統一身份認證
- 無縫的用戶體驗

## 🌟 主要功能

### 1. 🗓️ 行程管理整合
- **創建指令**：`創建東京三日遊行程`
- **目標網站**：https://tripfrontend.vercel.app
- **功能**：直接在網站創建行程，自動登入查看

### 2. ⏰ 集合管理整合
- **創建指令**：`設定明天9點東京車站集合`
- **目標網站**：https://tourclock-dvf2.vercel.app
- **功能**：創建集合時間，智能時間管理

### 3. 💰 分帳系統整合
- **創建指令**：`建立東京旅遊分帳`
- **目標網站**：https://split-front-pearl.vercel.app
- **功能**：創建分帳項目，多人費用管理

### 4. 🏆 排行榜查詢
- **查詢指令**：`排行榜`、`第一名`
- **目標網站**：https://tourhub-ashy.vercel.app
- **功能**：熱門行程排行，詳細資訊展示

### 5. 🛅 置物櫃查找
- **查詢指令**：`查找置物櫃`
- **目標網站**：https://tripfrontend.vercel.app/linelocker
- **功能**：附近置物櫃位置查詢

### 6. 👤 用戶管理
- **帳號查詢**：`我的帳號`
- **綁定管理**：`綁定狀態`
- **問題修復**：`重新綁定`

## 🛠️ 技術架構

### 核心組件
```
Line Bot ←→ 統一用戶管理 ←→ API 代理 ←→ 各個網站
    ↓           ↓              ↓         ↓
 訊息處理    身份認證        API調用    內容創建
```

### 關鍵技術
- **統一認證系統**：SHA256 加密的跨平台 Token
- **API 代理服務**：統一的網站 API 調用接口
- **智能內容解析**：自動提取創建參數
- **錯誤處理機制**：完善的異常處理和重試

### 資料庫設計
- `unified_users` - 統一用戶資料
- `user_website_bindings` - 跨平台綁定關係
- `user_operation_logs` - 完整操作記錄
- `website_modules` - 網站模組配置

## 🚀 部署指南

### 環境需求
- Python 3.8+
- MySQL 資料庫
- LINE Bot Channel

### 核心環境變數
```bash
# LINE Bot 配置
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret

# 資料庫配置
MYSQL_HOST=trip.mysql.database.azure.com
MYSQL_USER=b1129005
MYSQL_PASSWORD=Anderson3663
MYSQL_DB=tourhub

# API 模式配置
USE_REAL_API=false  # true=實際API, false=模擬模式
AUTH_SERVICE_URL=https://your-auth-service.vercel.app
```

### 快速部署
```bash
# 1. 克隆專案
git clone <repository_url>
cd Tourhub_Line_Bot

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 初始化資料庫
mysql -u your_user -p your_database < database/unified_user_system.sql

# 4. 部署到 Vercel
vercel --prod
```

## 📁 專案結構

### 核心檔案
```
api/
├── index.py                 # 主程式 - Line Bot 訊息處理
├── unified_user_manager.py  # 統一用戶管理系統
├── website_proxy.py         # 跨平台 API 代理
├── content_creator.py       # 內容創建處理器
├── auth_service.py          # 統一認證服務
└── config.py               # 關鍵字配置

database/
└── unified_user_system.sql  # 資料庫結構

website_api_examples/        # 各網站 API 實現範例
├── trip_management_api.js   # 行程管理 API
├── tour_clock_api.js        # 集合管理 API
└── bill_split_api.js        # 分帳系統 API
```

### 文件檔案
- `USER_BINDING_GUIDE.md` - 用戶綁定使用指南
- `CROSS_PLATFORM_INTEGRATION_GUIDE.md` - 技術整合指南
- `CROSS_PLATFORM_DEPLOYMENT.md` - 詳細部署指南
- `CROSS_PLATFORM_SUMMARY.md` - 實現總結報告

## 🎯 使用方式

### 內容創建指令
```
創建東京三日遊行程          → 在行程管理網站創建行程
設定明天9點東京車站集合      → 在集合管理網站創建集合
建立東京旅遊分帳           → 在分帳系統創建分帳項目
```

### 查詢指令
```
排行榜                    → 查看熱門行程排行
第一名                    → 查看排行榜第一名
第一名詳細行程             → 查看詳細行程安排
功能介紹                  → 查看所有可用功能
```

### 用戶管理指令
```
我的帳號                  → 查看帳號資訊和綁定狀態
綁定狀態                  → 查看各服務綁定詳情
重新綁定                  → 修復連接問題
```

## 🔄 運作模式

### 模擬模式 (預設)
- 完整功能體驗
- 無需外部 API 依賴
- 適合開發和測試

### 實際 API 模式
- 真實跨平台整合
- 需要各網站配合部署 API 端點
- 設定 `USE_REAL_API=true` 啟用

## 📊 測試結果

最新測試顯示系統運作正常：
```
✅ 行程創建成功 - trip_20250813_111353
✅ 集合創建成功 - meeting_20250813_111405
✅ 分帳創建成功 - bill_20250813_111417
📊 成功率: 100%
```

## 🤝 各網站整合

要啟用實際 API 模式，各網站需要：

1. **添加 API 端點**：根據 `website_api_examples/` 中的範例
2. **實現統一認證**：驗證 Line Bot 用戶的 Token
3. **支援跨域請求**：允許 Line Bot 的 API 調用

詳細實現方式請參考 `CROSS_PLATFORM_DEPLOYMENT.md`

## 🎉 專案成果

- ✅ **完整的跨平台整合架構**
- ✅ **統一用戶管理系統**
- ✅ **智能內容創建處理**
- ✅ **完善的錯誤處理機制**
- ✅ **詳細的實現文件和範例**

現在只需要各網站配合添加 API 端點，就能實現真正的跨平台內容創建！🚀

## 📄 授權

此專案採用 MIT 授權條款。