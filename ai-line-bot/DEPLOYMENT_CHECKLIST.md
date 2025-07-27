# ✅ Vercel 部署檢查清單

## 📋 部署前檢查

### GitHub 倉庫
- [ ] 程式碼已推送到 GitHub
- [ ] 包含 `app.py`
- [ ] 包含 `requirements.txt`
- [ ] 包含 `vercel.json`
- [ ] 包含 `.gitignore`

### 環境變數準備
- [ ] LINE Channel Access Token
- [ ] LINE Channel Secret
- [ ] OpenAI API Key

## 🚀 部署步驟

### Vercel 設定
- [ ] 登入 Vercel
- [ ] 連接 GitHub 帳號
- [ ] 選擇專案：`milkyway20021012/Project`
- [ ] 選擇目錄：`ai-line-bot`

### 環境變數設定
- [ ] 添加 `CHANNEL_ACCESS_TOKEN`
- [ ] 添加 `CHANNEL_SECRET`
- [ ] 添加 `OPENAI_API_KEY`

### 部署設定
- [ ] Framework Preset: Other
- [ ] Build Command: 留空
- [ ] Output Directory: 留空
- [ ] Install Command: 留空

## 🔗 LINE Bot 設定

### Webhook 設定
- [ ] 前往 LINE Developers Console
- [ ] 選擇您的 Channel
- [ ] 進入 Messaging API 設定
- [ ] 設定 Webhook URL: `https://your-project.vercel.app/callback`
- [ ] 啟用 "Use webhook"

## 🧪 測試檢查

### 部署測試
- [ ] 訪問 Vercel URL
- [ ] 看到 "✅ LINE Bot on Vercel is running."
- [ ] 檢查 Vercel 函數日誌

### LINE Bot 測試
- [ ] 在 LINE 中搜尋 Bot
- [ ] 發送測試訊息
- [ ] 收到正確回覆

### 功能測試
- [ ] 測試快速回覆（你好、hi、幫助）
- [ ] 測試 AI 回覆（其他訊息）
- [ ] 檢查錯誤處理

## 🔧 故障排除

### 如果部署失敗
- [ ] 檢查 GitHub 倉庫設定
- [ ] 確認環境變數正確
- [ ] 查看 Vercel 錯誤日誌

### 如果 Bot 無回應
- [ ] 檢查 Webhook URL 設定
- [ ] 確認 LINE Channel Secret
- [ ] 查看 Vercel 函數日誌

### 如果 API 錯誤
- [ ] 確認 OpenAI API Key 正確
- [ ] 檢查 API 使用量
- [ ] 測試本地功能

## 📊 部署後監控

### 日常檢查
- [ ] 查看 Vercel 部署狀態
- [ ] 檢查函數日誌
- [ ] 監控 API 使用量
- [ ] 測試 Bot 功能

### 維護任務
- [ ] 定期更新依賴套件
- [ ] 監控錯誤率
- [ ] 備份重要設定

---

**🎯 完成所有檢查項目後，您的 LINE Bot 就準備好為用戶服務了！** 