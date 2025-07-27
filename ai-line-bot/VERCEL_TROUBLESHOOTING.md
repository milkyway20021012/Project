# 🔧 Vercel 500 錯誤故障排除指南

## 🚨 問題診斷

您的 500 錯誤很可能是由以下原因之一造成的：

### 1. 環境變數未設定 ⭐⭐⭐⭐⭐ (最常見)

**症狀**：
- 部署成功但訪問時出現 500 錯誤
- 健康檢查端點返回錯誤
- LINE Bot 無法回應

**解決方案**：
1. 前往 [Vercel Dashboard](https://vercel.com/dashboard)
2. 選擇您的專案
3. 進入 **Settings** → **Environment Variables**
4. 添加以下環境變數：

```bash
CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
CHANNEL_SECRET=your_line_channel_secret
OPENAI_API_KEY=your_openai_api_key
```

5. 重新部署專案

### 2. 檢查部署狀態

訪問您的健康檢查端點：
```
https://your-project.vercel.app/health
```

應該看到類似這樣的回應：
```json
{
  "status": "healthy",
  "environment_variables": {
    "line_token_set": true,
    "line_secret_set": true,
    "openai_key_set": true
  }
}
```

如果看到 `false`，表示環境變數未正確設定。

### 3. 查看 Vercel 函數日誌

1. 前往 Vercel Dashboard
2. 選擇您的專案
3. 點擊 **Functions** 標籤
4. 查看 `app.py` 的日誌
5. 尋找錯誤訊息

### 4. 常見錯誤訊息及解決方案

#### 錯誤：`ModuleNotFoundError`
**原因**：缺少依賴套件
**解決方案**：檢查 `requirements.txt` 是否包含所有必要套件

#### 錯誤：`Invalid API Key`
**原因**：OpenAI API 金鑰無效
**解決方案**：
1. 檢查 API 金鑰是否正確
2. 確認 API 金鑰有足夠的額度
3. 檢查 API 金鑰是否過期

#### 錯誤：`LINE Bot API Error`
**原因**：LINE Bot 設定有問題
**解決方案**：
1. 檢查 Channel Access Token 是否正確
2. 檢查 Channel Secret 是否正確
3. 確認 LINE Bot 狀態是否正常

### 5. 測試步驟

#### 步驟 1：測試基本端點
```bash
curl https://your-project.vercel.app/
```

#### 步驟 2：測試健康檢查
```bash
curl https://your-project.vercel.app/health
```

#### 步驟 3：測試 LINE Webhook
1. 在 LINE 中發送訊息給您的 Bot
2. 檢查 Vercel 函數日誌
3. 確認 Bot 是否有回應

### 6. 重新部署

如果修改了環境變數，需要重新部署：

1. **自動部署**：推送到 GitHub 主分支
2. **手動部署**：在 Vercel Dashboard 中點擊 "Redeploy"

### 7. 進階故障排除

#### 檢查 Python 版本
確保 `runtime.txt` 包含正確的 Python 版本：
```
python-3.9
```

#### 檢查函數超時
如果函數執行時間過長，可能導致 500 錯誤。檢查 `vercel.json` 中的 `maxDuration` 設定。

#### 檢查記憶體使用量
Vercel 函數有記憶體限制，如果使用過多記憶體會導致錯誤。

### 8. 聯絡支援

如果以上步驟都無法解決問題：

1. 收集錯誤日誌
2. 記錄重現步驟
3. 提供專案 URL
4. 聯絡 Vercel 支援

## 🎯 快速檢查清單

- [ ] 環境變數已正確設定
- [ ] 專案已重新部署
- [ ] 健康檢查端點正常
- [ ] LINE Bot Webhook URL 正確
- [ ] 函數日誌中沒有錯誤
- [ ] API 金鑰有效且有額度

## 📞 需要幫助？

如果仍然遇到問題，請提供：
1. 您的 Vercel 專案 URL
2. 健康檢查端點的回應
3. 函數日誌中的錯誤訊息
4. 重現問題的步驟

---

**💡 提示**：大多數 500 錯誤都是由環境變數未正確設定造成的。請優先檢查環境變數設定！ 