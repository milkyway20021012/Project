# 📱 LINE Bot Token 獲取完整指南

## 🔍 步驟 1：登入 LINE Developers Console

1. **開啟 LINE Developers Console**
   - 網址：https://developers.line.biz/
   - 使用您的 LINE 帳號登入

## 🏗️ 步驟 2：創建或選擇 Channel

### 創建新的 Channel（如果沒有）
1. 點擊 "Create a new channel"
2. 選擇 "Messaging API"
3. 填寫以下資訊：
   - **Channel name**: 您的 Bot 名稱
   - **Channel description**: Bot 描述
   - **Category**: 選擇適當的類別
   - **Subcategory**: 選擇子類別
   - **Email address**: 您的電子郵件

### 使用現有的 Channel
1. 點擊您已創建的 Channel

## 🔑 步驟 3：獲取 Channel Access Token

1. **進入 Messaging API 設定**
   - 在左側選單中點擊 "Messaging API"

2. **找到 Channel Access Token**
   - 在頁面中尋找 "Channel access token" 區塊
   - 點擊 "Issue" 按鈕
   - 系統會生成一個新的 Token

3. **複製 Token**
   - 複製生成的 Token
   - 格式類似：`f7a7h+8Ax4oTzQYjwl0TcD2lUJD8eEFGDaaB94qZPGc2mei6BaMJcwCV3DI8eKhfgCiJfVg11/sNW8mDhGtkjiQek3FZL3Pl8g1ix8sxbWM9mjj1sbAyEdr9XlJuMg7Jg2j2/P/PmDEevkDQjboGnQdB04t89/1O/w1cDnyilFU=`

## 🔐 步驟 4：獲取 Channel Secret

1. **進入 Basic settings**
   - 點擊左側選單的 "Basic settings"

2. **找到 Channel Secret**
   - 在頁面中找到 "Channel secret"
   - 複製這個值（格式類似：`568f8e8c2c6c24970ddd9512dc1fa46d`）

## 🌐 步驟 5：設定 Webhook URL

1. **回到 Messaging API 設定**
   - 點擊左側選單的 "Messaging API"

2. **設定 Webhook URL**
   - 找到 "Webhook URL" 欄位
   - 輸入您的 Vercel 部署 URL：
     ```
     https://your-project.vercel.app/callback
     ```
   - 開啟 "Use webhook" 選項

3. **驗證 Webhook**
   - 點擊 "Verify" 按鈕測試連接

## 📋 步驟 6：設定環境變數

將獲取的值設定到 Vercel 環境變數中：

```bash
# LINE Bot 設定
CHANNEL_ACCESS_TOKEN=您的Channel_Access_Token
CHANNEL_SECRET=您的Channel_Secret

# OpenAI 設定
OPENAI_API_KEY=您的OpenAI_API_Key
```

## 🧪 步驟 7：測試設定

1. **在 LINE 中搜尋您的 Bot**
   - 使用 Channel 名稱搜尋
   - 或掃描 QR Code

2. **發送測試訊息**
   - 發送 "你好"
   - 應該收到回覆

## 🔧 常見問題

### 問題 1：找不到 Messaging API 選項
**解決方案**：
- 確保您創建的是 "Messaging API" 類型的 Channel
- 不是 "LINE Login" 或其他類型

### 問題 2：Webhook 驗證失敗
**解決方案**：
- 確保 Vercel 部署成功
- 檢查 Webhook URL 是否正確
- 確認 Channel Secret 設定正確

### 問題 3：Bot 無回應
**解決方案**：
- 檢查 Vercel 函數日誌
- 確認環境變數設定正確
- 測試本地功能是否正常

## 📊 監控和維護

### 查看 Bot 狀態
- LINE Developers Console → 您的 Channel → Messaging API
- 查看 "Webhook URL" 狀態

### 查看使用統計
- LINE Developers Console → 您的 Channel → Analytics
- 查看訊息數量和用戶數

## 🎯 完成檢查清單

- [ ] 創建或選擇 Messaging API Channel
- [ ] 獲取 Channel Access Token
- [ ] 獲取 Channel Secret
- [ ] 設定 Webhook URL
- [ ] 在 Vercel 中設定環境變數
- [ ] 測試 Bot 功能

---

**🎉 完成以上步驟後，您的 LINE Bot 就可以正常運作了！** 