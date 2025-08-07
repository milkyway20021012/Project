# TourHub LINE Bot 統一綁定系統

## 🎯 系統概述

TourHub LINE Bot 提供便捷的旅遊資訊查詢和功能導航，讓用戶輕鬆使用所有 TourHub 相關網站。

## 🌐 整合的網站

1. **🏆 TourHub排行榜** - https://tourhub-ashy.vercel.app/
2. **📋 行程管理** - https://tripfrontend.vercel.app/linetrip
3. **⏰ 集合管理** - https://tourclock-dvf2.vercel.app/
4. **🔍 置物櫃查找** - https://tripfrontend.vercel.app/linelocker
5. **💰 分帳系統** - https://split-front-pearl.vercel.app

## 🚀 功能特色

### 關鍵字功能
- `網站操作` - 查看可用網站並進行操作
- `功能介紹` - 查看 Bot 功能說明
- `第一名`、`第二名`、`第三名` - 查看排行榜
- `東京`、`大阪`、`京都`、`北海道` - 地區行程查詢

## 🔧 技術架構

### 核心組件
- **統一用戶管理** (`unified_user_manager.py`)
- **網站API代理** (`website_proxy.py`)
- **資料庫系統** (`database/unified_user_system.sql`)

### 資料庫表格
- `unified_users` - 統一用戶管理
- `website_modules` - 網站模組配置
- `user_website_bindings` - 用戶網站綁定關係
- `user_operation_logs` - 用戶操作日誌
- `system_configs` - 系統配置

## ⚙️ 環境變數

```bash
# LINE Bot
CHANNEL_ACCESS_TOKEN=你的LINE_Bot_Token
CHANNEL_SECRET=你的LINE_Bot_Secret

# 資料庫
MYSQL_HOST=trip.mysql.database.azure.com
MYSQL_USER=b1129005
MYSQL_PASSWORD=Anderson3663
MYSQL_DB=tourhub
MYSQL_PORT=3306
```

## 🔄 用戶使用流程

1. **使用網站功能**
   ```
   用戶輸入「網站操作」→ 選擇網站 → 點擊按鈕 → 跳轉到對應網站
   ```

2. **查詢排行榜**
   ```
   用戶輸入「第一名」→ 查看排行榜第一名詳細資訊
   ```

## 📋 API 端點

- `POST /callback` - LINE Bot Webhook
- `GET /debug` - 系統狀態檢查

## 🔐 安全特性

- 使用 LINE 官方 Webhook 驗證
- 完整的操作日誌記錄
- 安全的資料庫連接

## 📊 部署資訊

- **平台**: Vercel
- **域名**: https://line-bot-theta-dun.vercel.app/
- **資料庫**: Azure MySQL
- **狀態**: ✅ 已部署並運行

## 📚 相關文檔

本專案為 TourHub LINE Bot 主要功能實現。

---

**版本**: 1.0.0  
**最後更新**: 2025-08-07  
**狀態**: 生產環境就緒
