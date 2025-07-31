# 🤖 Line Bot 設定指南

## 🔍 問題診斷

**問題**: 輸入「下午2:35 淺草寺集合」後 Line Bot 沒有反應

**原因**: 環境變數 `CHANNEL_ACCESS_TOKEN` 和 `CHANNEL_SECRET` 未設定

## 🛠️ 解決方案

### 步驟 1: 獲取 Line Bot 憑證

#### 1.1 前往 LINE Developers Console
- 網址: https://developers.line.biz/
- 使用您的 LINE 帳號登入

#### 1.2 創建 Provider (如果沒有)
- 點擊「Create New Provider」
- 輸入 Provider 名稱
- 點擊「Create」

#### 1.3 創建 Channel
- 在 Provider 頁面點擊「Create New Channel」
- 選擇「Messaging API」
- 填寫 Channel 資訊：
  - **Channel name**: TourHub Bot
  - **Channel description**: 智能集合管理 Bot
  - **Category**: 選擇適合的類別
  - **Subcategory**: 選擇適合的子類別
- 點擊「Create」

#### 1.4 獲取憑證
在 Channel 設定頁面：
- **Channel Secret**: 複製這個值
- **Channel Access Token**: 點擊「Issue」生成並複製

### 步驟 2: 設定 Vercel 環境變數

#### 2.1 前往 Vercel Dashboard
- 網址: https://vercel.com/dashboard
- 選擇您的專案

#### 2.2 設定環境變數
- 點擊 **Settings** 標籤
- 點擊 **Environment Variables**
- 添加以下變數：

```
Name: CHANNEL_ACCESS_TOKEN
Value: 您的 Channel Access Token
Environment: Production, Preview, Development

Name: CHANNEL_SECRET  
Value: 您的 Channel Secret
Environment: Production, Preview, Development
```

#### 2.3 重新部署
- 點擊 **Deployments** 標籤
- 點擊 **Redeploy** 重新部署

### 步驟 3: 設定 Webhook URL

#### 3.1 獲取您的 Vercel URL
- 在 Vercel Dashboard 中查看您的應用程式 URL
- 格式: `https://您的專案名稱.vercel.app`

#### 3.2 設定 Line Bot Webhook
- 回到 LINE Developers Console
- 在您的 Channel 設定中：
  - **Webhook URL**: `https://您的專案名稱.vercel.app/callback`
  - **Use webhook**: 啟用
  - 點擊 **Verify** 驗證

### 步驟 4: 測試功能

#### 4.1 基本測試
在 Line Bot 中輸入：
```
下午2:35 淺草寺集合
```

#### 4.2 其他測試
```
14:30 新宿車站見面
2點35分 澀谷集合
下午3點 銀座碰面
```

## 🔧 故障排除

### 問題 1: 環境變數未生效
**解決方案**:
- 確保環境變數已設定到所有環境 (Production, Preview, Development)
- 重新部署應用程式
- 檢查變數名稱是否正確

### 問題 2: Webhook 驗證失敗
**解決方案**:
- 確保 URL 格式正確
- 確保 `/callback` 路徑存在
- 檢查應用程式是否正常運行

### 問題 3: Bot 仍然沒有回應
**解決方案**:
- 檢查 Vercel 部署日誌
- 確認 Channel Access Token 和 Secret 正確
- 測試健康檢查端點: `https://您的專案名稱.vercel.app/`

## 📋 檢查清單

- [ ] LINE Developers Console 已創建 Channel
- [ ] Channel Access Token 已獲取
- [ ] Channel Secret 已獲取
- [ ] Vercel 環境變數已設定
- [ ] 應用程式已重新部署
- [ ] Webhook URL 已設定
- [ ] Webhook 驗證成功
- [ ] 在 Line Bot 中測試功能

## 🎯 預期結果

設定完成後，當您在 Line Bot 中輸入「下午2:35 淺草寺集合」時，應該會收到：

1. ✅ 集合設定成功的 Flex Message
2. ✅ 顯示時間：14:35
3. ✅ 顯示地點：淺草寺
4. ✅ 智能提醒已啟用
5. ✅ 「查看我的集合」按鈕
6. ✅ 「分享集合資訊」按鈕

## 🆘 需要幫助？

如果按照以上步驟仍然無法解決問題，請：

1. 檢查 Vercel 部署日誌
2. 確認所有環境變數已正確設定
3. 測試健康檢查端點
4. 聯繫技術支援

---

**🎉 完成設定後，您就可以享受完整的智能集合管理功能了！** 