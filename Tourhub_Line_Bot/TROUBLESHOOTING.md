# TourHub Line Bot 故障排除指南

## 🚨 問題：「第一名」和「第一名詳細行程」不響應

### ✅ 已確認正常的部分

1. **關鍵字匹配**：✅ 正常
   - `第一名` → `leaderboard` 模板
   - `第一名詳細行程` → `leaderboard_details` 模板

2. **Flex Message 創建**：✅ 正常
   - 兩個功能的 Flex Message 都能成功創建

3. **其他功能**：✅ 正常
   - `排行榜`、`第二名`、`功能介紹` 等都能響應

### 🔍 增強的日誌功能

現在的版本包含詳細的日誌記錄，會顯示：

```
🔍 收到訊息: '第一名'
🔍 訊息長度: 3
🔍 訊息類型: <class 'str'>
✅ 匹配到模板: leaderboard, rank: 1
🔧 創建 leaderboard Flex Message, rank: 1
🔧 leaderboard Flex Message 創建結果: True
📤 準備發送訊息，Flex Message 存在: True
📤 Flex Message 類型: bubble
✅ 訊息發送成功
```

### 🔧 故障排除步驟

#### 步驟 1：檢查伺服器日誌

部署後，在 Line 中輸入 `第一名`，然後檢查伺服器日誌：

1. **如果看到完整的日誌流程**（如上所示）：
   - 問題可能在 Line 平台端
   - 檢查 Line Developer Console 的設定

2. **如果沒有看到 `🔍 收到訊息` 日誌**：
   - Webhook 沒有被觸發
   - 檢查 Webhook URL 設定

3. **如果看到錯誤日誌**：
   - 查看具體的錯誤訊息
   - 根據錯誤類型進行修復

#### 步驟 2：檢查 Line Developer Console

1. **Webhook 設定**：
   - URL：`https://你的域名/callback`
   - 確保 SSL 有效
   - 測試 Webhook 連接

2. **Bot 設定**：
   - 確保 Bot 已啟用
   - 檢查 Channel Access Token
   - 檢查 Channel Secret

#### 步驟 3：API 測試

訪問以下 URL 進行測試：

1. **健康檢查**：
   ```
   GET https://你的域名/api/health
   ```
   應該返回：
   ```json
   {
     "status": "running",
     "bot_configured": true
   }
   ```

2. **手動測試**（如果有實作）：
   ```
   POST https://你的域名/api/test
   Content-Type: application/json
   {
     "message": "第一名"
   }
   ```

#### 步驟 4：網路和環境檢查

1. **SSL 憑證**：
   - Line Bot 要求 HTTPS
   - 確保憑證有效且未過期

2. **防火牆**：
   - 確保 443 端口開放
   - 允許來自 Line 平台的請求

3. **伺服器資源**：
   - 檢查 CPU 和記憶體使用率
   - 確保伺服器沒有過載

### 🐛 常見問題和解決方案

#### 問題 1：Webhook 超時

**症狀**：Line Developer Console 顯示 Webhook 測試失敗

**解決方案**：
- 檢查伺服器響應時間
- 優化代碼性能
- 增加伺服器資源

#### 問題 2：SSL 憑證問題

**症狀**：Webhook URL 無法訪問

**解決方案**：
- 更新 SSL 憑證
- 使用 Let's Encrypt 等免費憑證
- 檢查憑證鏈完整性

#### 問題 3：環境變數問題

**症狀**：`bot_configured: false`

**解決方案**：
- 檢查 `.env` 文件
- 確認環境變數正確設定
- 重新部署應用

#### 問題 4：依賴套件問題

**症狀**：ImportError 或模組找不到

**解決方案**：
```bash
pip install -r requirements.txt
```

### 🔄 回退方案

如果問題持續存在，可以使用簡化版本：

1. **使用文字回應**：
   ```python
   # 在 handle_message 中添加
   if user_message == "第一名":
       # 發送簡單文字訊息而不是 Flex Message
       text_message = TextMessage(text="🥇 第一名：北海道夏季清涼之旅")
   ```

2. **逐步測試**：
   - 先確保文字回應正常
   - 再逐步添加 Flex Message 功能

### 📞 進階調試

如果需要更深入的調試：

1. **添加更多日誌**：
   ```python
   logger.info(f"Debug: {變數名} = {變數值}")
   ```

2. **使用 ngrok 本地測試**：
   ```bash
   ngrok http 5000
   ```
   將 ngrok URL 設定為 Webhook URL

3. **檢查 Line Bot SDK 版本**：
   ```bash
   pip show line-bot-sdk
   ```

### 📋 檢查清單

在聯繫技術支援前，請確認：

- [ ] 其他功能（如 `排行榜`）正常工作
- [ ] 伺服器日誌中有詳細的錯誤資訊
- [ ] Webhook URL 可以從外部訪問
- [ ] SSL 憑證有效
- [ ] Line Developer Console 設定正確
- [ ] 環境變數設定正確
- [ ] 依賴套件安裝完整

### 🎯 預期結果

修復後，當輸入 `第一名` 時，應該看到：

1. **伺服器日誌**：完整的處理流程
2. **Line Bot**：顯示第一名的詳細資訊 Flex Message
3. **無錯誤**：沒有異常或錯誤訊息

---

**注意**：由於代碼邏輯測試都正常，問題很可能出在部署環境或 Line 平台設定上。請重點檢查 Webhook 和網路相關設定。
