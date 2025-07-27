# 🚀 LINE Bot Vercel 部署完整教程

## 📋 前置準備

### 1. 確保 GitHub 倉庫準備就緒
- ✅ 程式碼已推送到 GitHub
- ✅ 包含所有必要檔案
- ✅ 環境變數已正確設定

### 2. 準備 LINE Bot 設定
- LINE Channel Access Token
- LINE Channel Secret
- OpenAI API Key

## 🔧 部署步驟

### 步驟 1：連接 Vercel 到 GitHub

1. **前往 Vercel**
   - 開啟 https://vercel.com
   - 使用 GitHub 帳號登入

2. **導入專案**
   - 點擊 "New Project"
   - 選擇您的 GitHub 倉庫：`milkyway20021012/Project`
   - 選擇 `ai-line-bot` 目錄

### 步驟 2：設定環境變數

在 Vercel 專案設定中，添加以下環境變數：

```bash
# LINE Bot 設定
CHANNEL_ACCESS_TOKEN=your_line_channel_access_token

CHANNEL_SECRET=your_line_channel_secret

# OpenAI 設定
OPENAI_API_KEY=your_openai_api_key
```

### 步驟 3：部署設定

1. **Framework Preset**: 選擇 "Other"
2. **Build Command**: 留空（使用預設）
3. **Output Directory**: 留空（使用預設）
4. **Install Command**: 留空（使用預設）

### 步驟 4：部署

1. 點擊 "Deploy"
2. 等待部署完成（約 2-3 分鐘）
3. 記下部署的 URL（例如：https://your-project.vercel.app）

## 🔗 設定 LINE Bot Webhook

### 步驟 1：更新 LINE Bot 設定

1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 選擇您的 Channel
3. 進入 "Messaging API" 設定

### 步驟 2：設定 Webhook URL

在 "Webhook URL" 欄位中輸入：
```
https://your-project.vercel.app/callback
```

### 步驟 3：啟用 Webhook

- 開啟 "Use webhook" 選項
- 儲存設定

## 🧪 測試部署

### 測試 1：檢查部署狀態

訪問您的 Vercel URL：
```
https://your-project.vercel.app/
```

應該看到：
```
✅ LINE Bot on Vercel is running.
```

### 測試 2：測試 LINE Bot

1. 在 LINE 中搜尋您的 Bot
2. 發送訊息：`你好`
3. 應該收到回覆

### 測試 3：檢查日誌

在 Vercel Dashboard 中查看函數日誌：
1. 前往專案頁面
2. 點擊 "Functions" 標籤
3. 查看 `app.py` 的日誌

## 🔧 故障排除

### 常見問題 1：環境變數未載入

**症狀**：API 金鑰錯誤
**解決方案**：
- 檢查 Vercel 環境變數設定
- 確保變數名稱正確（OPENAI_API_KEY）
- 重新部署

### 常見問題 2：Webhook 驗證失敗

**症狀**：LINE 無法連接到 Bot
**解決方案**：
- 檢查 Webhook URL 是否正確
- 確保 Vercel 部署成功
- 檢查 LINE Channel Secret 設定

### 常見問題 3：函數超時

**症狀**：Bot 回應緩慢或無回應
**解決方案**：
- 檢查 API 調用是否正常
- 查看 Vercel 函數日誌
- 確認網路連接

## 📊 監控和維護

### 1. 查看部署狀態
- Vercel Dashboard → 專案 → Deployments

### 2. 查看函數日誌
- Vercel Dashboard → 專案 → Functions → app.py

### 3. 監控使用量
- Vercel Dashboard → 專案 → Analytics

## 🚀 自動部署

設定完成後，每次推送到 GitHub 主分支都會自動觸發重新部署。

## 📞 支援

如果遇到問題：
1. 檢查 Vercel 函數日誌
2. 確認環境變數設定
3. 測試本地功能是否正常
4. 查看 GitHub 倉庫中的測試腳本

---

**🎉 恭喜！您的 LINE Bot 現在已經部署到 Vercel 並可以正常使用了！** 