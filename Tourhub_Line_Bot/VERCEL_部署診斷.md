# Vercel 部署診斷指南

## 問題分析

您的 Line Bot 在 Vercel 上沒有回應的可能原因：

### 1. 環境變數問題
- `CHANNEL_ACCESS_TOKEN` 未設定或錯誤
- `CHANNEL_SECRET` 未設定或錯誤

### 2. Webhook URL 問題
- Line Bot 的 Webhook URL 設定錯誤
- SSL 憑證問題

### 3. 代碼兼容性問題
- SQLite 資料庫在 Vercel 無法使用（無狀態環境）
- 後台線程在 Vercel 無法運行
- 相對導入路徑問題

## 解決方案

### 步驟 1: 使用測試版本

我已經創建了一個簡化的測試版本 `api/test_vercel.py`，並修改了 `vercel.json` 來使用它。

### 步驟 2: 檢查環境變數

在 Vercel Dashboard 中確認以下環境變數已正確設定：

```
CHANNEL_ACCESS_TOKEN=你的_Channel_Access_Token
CHANNEL_SECRET=你的_Channel_Secret
```

### 步驟 3: 更新 Line Bot Webhook URL

在 Line Developers Console 中，將 Webhook URL 設定為：
```
https://你的vercel域名.vercel.app/callback
```

### 步驟 4: 測試部署

1. **健康檢查**：訪問 `https://你的vercel域名.vercel.app/`
   - 應該看到：`{"status": "running", "bot_configured": true, "version": "vercel_test_v1.0"}`

2. **除錯資訊**：訪問 `https://你的vercel域名.vercel.app/debug`
   - 檢查環境變數是否正確設定

3. **Line Bot 測試**：
   - 在 Line 中發送任何訊息，應該收到回應
   - 嘗試發送：`下午2:35 淺草寺集合`

## 常見問題排除

### 問題 1: 收不到任何回應

**檢查項目：**
1. Vercel 部署是否成功
2. 環境變數是否設定正確
3. Line Bot Webhook URL 是否正確
4. Line Bot 是否已加為好友

**解決方法：**
```bash
# 檢查 Vercel 日誌
vercel logs 你的部署URL

# 或在 Vercel Dashboard 查看 Functions 日誌
```

### 問題 2: 收到錯誤訊息

**可能原因：**
- Line Bot SDK 版本不兼容
- 環境變數格式錯誤
- 代碼語法錯誤

**解決方法：**
1. 檢查 `requirements.txt` 中的套件版本
2. 查看 Vercel 建置日誌
3. 檢查代碼是否有語法錯誤

### 問題 3: 部分功能不工作

**原因：**
- Vercel 是無狀態環境，不支援：
  - 本地檔案存儲（SQLite）
  - 後台線程
  - 持久化記憶體

**解決方法：**
- 使用外部資料庫（PostgreSQL、MySQL）
- 使用 Vercel Cron Jobs 替代後台線程
- 使用 Redis 或其他外部存儲

## 測試版本功能

當前的測試版本 (`test_vercel.py`) 包含：

### ✅ 支援的功能
- 基本訊息處理
- 時間解析（下午2:35、14:30）
- 地點解析（淺草寺、新宿車站等）
- 簡化的 Flex Message 回應
- 健康檢查端點
- 除錯資訊端點

### ❌ 暫時移除的功能
- 資料庫存儲
- 智能提醒系統
- 複雜的 Flex Message 模板
- 集合管理功能

## 下一步

### 如果測試版本工作正常：

1. **恢復完整功能**：
   - 設定外部資料庫
   - 實現 Vercel Cron Jobs
   - 恢復完整的 Flex Message

2. **修改 vercel.json**：
   ```json
   {
     "version": 2,
     "builds": [{"src": "api/*.py", "use": "@vercel/python"}],
     "routes": [{"src": "/(.*)", "dest": "/api/index.py"}]
   }
   ```

### 如果測試版本仍不工作：

1. **檢查基礎設定**：
   - Line Bot Channel 設定
   - Webhook URL 設定
   - SSL 憑證

2. **查看詳細日誌**：
   - Vercel Functions 日誌
   - Line Bot 事件日誌

## 部署命令

```bash
# 部署到 Vercel
vercel --prod

# 查看日誌
vercel logs

# 查看環境變數
vercel env ls
```

## 聯絡支援

如果問題持續存在，請提供：
1. Vercel 部署 URL
2. Line Bot Channel ID
3. 錯誤訊息截圖
4. Vercel 日誌內容
