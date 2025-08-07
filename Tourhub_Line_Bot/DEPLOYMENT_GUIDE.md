# TourHub Line Bot 部署指南

## 🚨 問題解決方案

由於原始的複雜版本可能在部署環境中遇到問題，我們創建了一個**簡化版本**來確保基本功能正常工作。

## 📁 文件說明

- `api/index.py` - **當前使用的簡化版本**（文字回應）
- `api/index_backup.py` - 原始複雜版本的備份（Flex Message）
- `api/index_debug.py` - 調試版本

## 🎯 當前功能

### 支援的關鍵字和回應

| 用戶輸入 | Bot 回應 |
|---------|---------|
| `排行榜` | 🏆 這是排行榜功能！ |
| `第一名` | 🥇 第一名：北海道夏季清涼之旅 |
| `第一名詳細行程` | 📅 第一名詳細行程：<br>2025年08月15日 (星期五)<br>10:00 - 18:00 札幌市區・大通公園 |
| `第二名` | 🥈 第二名：大阪美食文化之旅 |
| `第二名詳細行程` | 📅 第二名詳細行程：<br>2025年08月01日 (星期五)<br>09:00 - 16:00 大阪城・天守閣 |
| `功能介紹` | 📱 TourHub 功能介紹<br>• 排行榜<br>• 第一名<br>• 第一名詳細行程<br>• 第二名<br>• 第二名詳細行程 |
| 其他 | 您好！我是 TourHub Bot。請嘗試輸入：<br>• 排行榜<br>• 第一名<br>• 第一名詳細行程<br>• 功能介紹 |

## 🚀 部署步驟

### 1. 確認環境變數

確保 `.env` 文件包含正確的 Line Bot 設定：

```env
CHANNEL_ACCESS_TOKEN=你的_ACCESS_TOKEN
CHANNEL_SECRET=你的_CHANNEL_SECRET
```

### 2. 安裝依賴

```bash
pip install -r requirements.txt
```

### 3. 本地測試

```bash
python api/index.py
```

訪問 `http://localhost:5000/api/health` 檢查狀態。

### 4. 部署到生產環境

將整個專案部署到你的伺服器（Vercel、Heroku 等）。

## 🔧 測試方法

### API 測試

1. **健康檢查**：
   ```
   GET /api/health
   ```
   
2. **功能測試**：
   ```
   GET /api/test
   ```

### Line Bot 測試

在 Line 中發送以下訊息測試：

1. `排行榜` - 應該回應排行榜功能
2. `第一名` - 應該回應第一名資訊
3. `第一名詳細行程` - 應該回應詳細行程
4. `功能介紹` - 應該回應功能列表

## 🐛 故障排除

### 如果 Line Bot 仍然沒有回應：

1. **檢查 Webhook URL**：
   - 確保 Line Developer Console 中的 Webhook URL 正確
   - URL 格式：`https://你的域名/callback`

2. **檢查環境變數**：
   - 訪問 `/api/health` 確認 `bot_configured: true`

3. **檢查日誌**：
   - 查看伺服器日誌是否有錯誤訊息

4. **測試 Webhook**：
   - 在 Line Developer Console 中測試 Webhook 連接

### 如果需要恢復複雜版本：

```bash
cp api/index_backup.py api/index.py
```

## 📈 升級計劃

一旦簡化版本正常工作，可以逐步升級：

1. **階段1**：確保基本文字回應正常
2. **階段2**：添加簡單的 Flex Message
3. **階段3**：整合網頁爬蟲功能
4. **階段4**：恢復完整功能

## 🎊 成功指標

當以下測試都通過時，表示部署成功：

- ✅ `/api/health` 返回 `bot_configured: true`
- ✅ 在 Line 中輸入 `第一名` 有回應
- ✅ 在 Line 中輸入 `第一名詳細行程` 有回應
- ✅ 在 Line 中輸入 `排行榜` 有回應

## 📞 支援

如果問題持續存在，請檢查：

1. Line Developer Console 的設定
2. Webhook URL 是否可以從外部訪問
3. SSL 憑證是否有效
4. 伺服器是否正常運行

---

**注意**：這個簡化版本使用文字訊息而不是 Flex Message，以確保最大的相容性和穩定性。
