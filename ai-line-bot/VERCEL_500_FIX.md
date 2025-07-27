# 🚨 Vercel 500 錯誤完全解決指南

## 🔍 問題診斷

您遇到的錯誤：
```
500: INTERNAL_SERVER_ERROR
Code: FUNCTION_INVOCATION_FAILED
ID: hkg1::6kzxm-1753588441087-d8faa4190cd6
```

這表示您的 Vercel 函數在執行時發生了內部錯誤。

## 🛠️ 解決步驟

### 步驟 1：檢查環境變數 ⭐⭐⭐⭐⭐

**最常見的原因**：環境變數未設定或設定錯誤

1. 前往 [Vercel Dashboard](https://vercel.com/dashboard)
2. 選擇您的專案
3. 進入 **Settings** → **Environment Variables**
4. 確保以下環境變數已正確設定：

```bash
CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
CHANNEL_SECRET=your_line_channel_secret
OPENAI_API_KEY=your_openai_api_key
```

### 步驟 2：使用診斷工具

我已經為您創建了簡化版本的應用程式：

1. **暫時替換主檔案**：
   - 將 `app.py` 重命名為 `app_backup.py`
   - 將 `app_simple.py` 重命名為 `app.py`
   - 將 `vercel_debug.json` 重命名為 `vercel.json`

2. **重新部署**：
   ```bash
   git add .
   git commit -m "使用簡化版本進行診斷"
   git push origin main
   ```

3. **測試端點**：
   - 訪問：`https://your-project.vercel.app/`
   - 測試：`https://your-project.vercel.app/test`
   - 健康檢查：`https://your-project.vercel.app/health`
   - 調試：`https://your-project.vercel.app/debug`

### 步驟 3：查看 Vercel 日誌

1. 前往 Vercel Dashboard
2. 選擇您的專案
3. 點擊 **Functions** 標籤
4. 查看 `app.py` 的日誌
5. 尋找具體的錯誤訊息

### 步驟 4：常見錯誤及解決方案

#### 錯誤 1：ModuleNotFoundError
**症狀**：缺少依賴套件
**解決方案**：
- 檢查 `requirements.txt` 是否包含所有必要套件
- 確保套件名稱正確

#### 錯誤 2：ImportError
**症狀**：無法導入模組
**解決方案**：
- 檢查 Python 版本是否正確
- 確保所有依賴都已安裝

#### 錯誤 3：Environment Variable Error
**症狀**：環境變數未載入
**解決方案**：
- 重新設定環境變數
- 重新部署專案

#### 錯誤 4：Timeout Error
**症狀**：函數執行超時
**解決方案**：
- 檢查 `vercel.json` 中的 `maxDuration` 設定
- 優化程式碼執行時間

### 步驟 5：測試流程

#### 測試 1：基本端點
```bash
curl https://your-project.vercel.app/
```
預期回應：
```json
{
  "message": "✅ LINE Bot on Vercel is running.",
  "timestamp": 1234567890,
  "status": "ok"
}
```

#### 測試 2：健康檢查
```bash
curl https://your-project.vercel.app/health
```
預期回應：
```json
{
  "status": "healthy",
  "environment_variables": {
    "CHANNEL_ACCESS_TOKEN": true,
    "CHANNEL_SECRET": true,
    "OPENAI_API_KEY": true
  },
  "all_vars_set": true
}
```

#### 測試 3：調試端點
```bash
curl https://your-project.vercel.app/debug
```
這會顯示詳細的系統資訊和環境變數狀態。

### 步驟 6：恢復完整功能

一旦診斷版本正常運作：

1. **恢復原始檔案**：
   ```bash
   git checkout HEAD -- app.py vercel.json
   ```

2. **逐步添加功能**：
   - 先確保基本 Flask 應用程式運作
   - 再添加 LINE Bot 功能
   - 最後添加 OpenAI 功能

3. **重新部署**：
   ```bash
   git add .
   git commit -m "恢復完整功能"
   git push origin main
   ```

## 🔧 進階故障排除

### 檢查 Python 版本
確保 `runtime.txt` 包含：
```
python-3.9
```

### 檢查依賴套件
確保 `requirements.txt` 包含：
```
flask==3.0.0
line-bot-sdk==3.7.0
python-dotenv==1.0.0
openai>=1.0.0
```

### 檢查 Vercel 配置
確保 `vercel.json` 配置正確：
```json
{
    "version": 2,
    "builds": [
        {
            "src": "app.py",
            "use": "@vercel/python"
        }
    ],
    "routes": [
        {
            "src": "/(.*)",
            "dest": "/app.py"
        }
    ]
}
```

## 📞 需要幫助？

如果按照以上步驟仍然無法解決問題，請提供：

1. **您的 Vercel 專案 URL**
2. **健康檢查端點的回應**
3. **Vercel 函數日誌中的錯誤訊息**
4. **調試端點的回應**

這樣我就能更精確地幫您診斷問題！

---

**💡 提示**：大多數 500 錯誤都是由環境變數或依賴套件問題造成的。使用診斷工具可以快速定位問題所在。 