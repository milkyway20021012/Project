# 🤖 本地 Line Bot 設定指南

## 🎯 功能特色

這個本地 Line Bot 提供完整的集合管理功能：

- ✅ **智能時間解析**: 支援多種時間格式（下午2:35、14:35、2點35分等）
- ✅ **智能地點解析**: 自動識別集合地點
- ✅ **Flex Message**: 美觀的圖形化介面
- ✅ **智能提醒**: 集合前 10 分鐘、5 分鐘和準時提醒
- ✅ **集合管理**: 查看、取消集合
- ✅ **本地資料庫**: 無需外部服務

## 🚀 快速開始

### 步驟 1: 安裝依賴

```bash
pip install flask line-bot-sdk
```

### 步驟 2: 設定 Line Bot 憑證

1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 創建 Provider 和 Channel (Messaging API)
3. 獲取 Channel Access Token 和 Channel Secret

### 步驟 3: 修改設定

編輯 `simple_meeting_bot.py` 檔案，將以下行替換為您的憑證：

```python
CHANNEL_ACCESS_TOKEN = 'YOUR_CHANNEL_ACCESS_TOKEN'  # 替換為您的 Token
CHANNEL_SECRET = 'YOUR_CHANNEL_SECRET'  # 替換為您的 Secret
```

### 步驟 4: 設定 Webhook URL

在 LINE Developers Console 中：
- **Webhook URL**: `https://您的網域/callback`
- **Use webhook**: 啟用

### 步驟 5: 啟動 Bot

```bash
python3 simple_meeting_bot.py
```

## 📱 使用方式

### 設定集合
在 Line Bot 中輸入：
```
下午2:35 淺草寺集合
14:30 新宿車站見面
2點35分 澀谷集合
晚上7點 銀座碰面
```

### 管理集合
- 點擊「查看我的集合」查看所有集合
- 點擊「取消」按鈕取消不需要的集合
- 點擊「分享集合資訊」分享給朋友

### 智能提醒
系統會自動在以下時間發送提醒：
- ⏰ 集合前 10 分鐘
- 🚨 集合前 5 分鐘  
- 🎯 集合時間到

## 🔧 支援的時間格式

- **中文時間**: 下午2:35、上午10點、晚上7點半
- **24小時制**: 14:35、09:30
- **中文格式**: 2點35分、3點半、4點30分
- **混合格式**: 下午2點35分、晚上7點半

## 📍 支援的地點格式

- **預設地點**: 淺草寺、新宿車站、澀谷、銀座等
- **自定義地點**: 任何中文地名
- **地點關鍵字**: 在、到、約在、集合於等

## 🌐 部署選項

### 選項 1: 本地運行
適合開發和測試：
```bash
python3 simple_meeting_bot.py
```

### 選項 2: 使用 ngrok 公開
適合測試和演示：
```bash
# 安裝 ngrok
brew install ngrok  # macOS
# 或下載: https://ngrok.com/

# 啟動 ngrok
ngrok http 5000

# 使用提供的 URL 設定 Webhook
```

### 選項 3: 部署到雲端
可以部署到：
- Heroku
- Railway
- Render
- 或其他支援 Python 的雲端平台

## 📊 資料庫結構

集合資料儲存在 `meetings.db` 中：

```sql
CREATE TABLE meetings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    meeting_name TEXT NOT NULL,
    meeting_time TEXT NOT NULL,
    meeting_location TEXT NOT NULL,
    meeting_date TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active',
    reminder_10min_sent BOOLEAN DEFAULT FALSE,
    reminder_5min_sent BOOLEAN DEFAULT FALSE,
    reminder_on_time_sent BOOLEAN DEFAULT FALSE
);
```

## 🔍 故障排除

### 問題 1: Bot 沒有回應
**解決方案**:
- 檢查 Channel Access Token 和 Secret 是否正確
- 確認 Webhook URL 設定正確
- 檢查應用程式是否正常運行

### 問題 2: 時間解析錯誤
**解決方案**:
- 確保時間格式正確
- 檢查是否包含集合關鍵字（集合、見面、約等）

### 問題 3: 提醒沒有發送
**解決方案**:
- 檢查 Bot 是否持續運行
- 確認集合時間設定正確
- 檢查資料庫連接

## 🎉 完成！

設定完成後，您就可以享受完整的智能集合管理功能了！

**測試訊息**:
```
下午2:35 淺草寺集合
```

**預期回應**:
- ✅ 美觀的 Flex Message
- ✅ 顯示時間和地點
- ✅ 智能提醒已啟用
- ✅ 管理按鈕

---

**💡 提示**: 這個本地版本完全獨立，無需外部部署，適合快速測試和開發！ 