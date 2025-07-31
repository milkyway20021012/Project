# TourHub Line Bot 集合功能說明

## 功能概述

TourHub Line Bot 的集合功能可以讓用戶通過自然語言輸入來設定集合時間和地點，系統會自動：

1. **解析時間和地點**：支援多種時間格式和地點表達方式
2. **生成 Flex Message**：創建美觀的集合設定確認訊息
3. **設定智能提醒**：自動在集合前 10 分鐘、5 分鐘和集合時間發送提醒

## 支援的輸入格式

### 時間格式

| 格式類型 | 範例 | 解析結果 |
|---------|------|---------|
| 上午/下午 + 冒號 | `下午2:35` | `14:35` |
| 上午/下午 + 點分 | `下午2點35分` | `14:35` |
| 上午/下午 + 點 | `晚上7點` | `19:00` |
| 24小時制 | `14:30` | `14:30` |
| 小數點格式 | `2.35` | `02:35` |

### 地點格式

系統支援以下地點表達方式：

- **預設地點**：淺草寺、新宿車站、澀谷、銀座等熱門景點
- **地標 + 集合動詞**：`淺草寺集合`、`新宿車站見面`
- **帶後綴的地點**：`東京車站`、`清水寺`、`大阪城`

### 完整輸入範例

```
下午2:35 淺草寺集合
14:30 新宿車站見面
晚上7點 銀座碰面
2.35 澀谷集合
上午10:00 東京鐵塔集合
```

## 功能流程

### 1. 用戶輸入處理

當用戶發送包含時間和地點的訊息時：

```python
# 檢查是否匹配集合模式
if re.search(MEETING_TIME_PATTERN, user_message):
    # 解析時間和地點
    meeting_time = parse_time(user_message)
    meeting_location = parse_location(user_message)
    
    if meeting_time and meeting_location:
        # 創建集合並發送確認訊息
        success, message, meeting_id = create_local_meeting(...)
```

### 2. 集合設定

系統會：
- 在本地資料庫創建集合記錄
- 生成唯一的集合 ID
- 設定提醒時間點

### 3. Flex Message 回應

生成包含以下資訊的美觀卡片：
- ⏰ 集合時間
- 📍 集合地點
- ✅ 設定狀態
- 📱 智能提醒時間表
- 🔗 操作按鈕（查看集合、分享資訊）

### 4. 智能提醒系統

系統會在以下時間點自動發送提醒：
- **集合前 10 分鐘**：⏰ 還有 10 分鐘就要集合了！
- **集合前 5 分鐘**：🚨 還有 5 分鐘就要集合了！
- **集合時間到**：🎯 集合時間到了！請準時到達！

## 技術實現

### 核心組件

1. **時間解析器** (`parse_time`)
   - 支援多種中文時間格式
   - 自動轉換為 24 小時制
   - 處理上午/下午/晚上/凌晨

2. **地點解析器** (`parse_location`)
   - 預設地點匹配
   - 正則表達式提取
   - 地標後綴識別

3. **集合管理器** (`MeetingManager`)
   - SQLite 資料庫存儲
   - 提醒線程管理
   - 狀態追蹤

4. **Flex Message 生成器**
   - 動態模板系統
   - 美觀的卡片設計
   - 互動按鈕

### 資料庫結構

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

## 使用範例

### 基本使用

```python
# 用戶輸入
user_message = "下午2:35 淺草寺集合"

# 系統處理
meeting_time = parse_time(user_message)      # "14:35"
meeting_location = parse_location(user_message)  # "淺草寺"

# 創建集合
success, message, meeting_id = meeting_manager.create_meeting(
    user_id="U1234567890",
    meeting_time=meeting_time,
    meeting_location=meeting_location
)

# 生成 Flex Message
flex_message = create_flex_message(
    "meeting_success",
    meeting_time=meeting_time,
    meeting_location=meeting_location,
    is_success=success
)
```

### 提醒系統

```python
# 設定提醒回調
meeting_manager.set_reminder_callback(reminder_callback_handler)

# 提醒處理函數
def reminder_callback_handler(reminder_data):
    user_id = reminder_data.get('user_id')
    meeting_time = reminder_data.get('meeting_time')
    meeting_location = reminder_data.get('meeting_location')
    reminder_type = reminder_data.get('reminder_type')
    
    # 發送提醒訊息
    send_reminder_message(user_id, meeting_time, meeting_location, reminder_type)
```

## 測試

運行測試腳本來驗證功能：

```bash
# 測試解析功能
python test_meeting_parser.py

# 測試完整流程
python example_usage.py
```

## 注意事項

1. **時間格式**：建議使用明確的時間格式，如「下午2:35」而非「2點多」
2. **地點名稱**：使用常見的地標名稱，系統對熱門景點有更好的識別率
3. **提醒精度**：提醒系統每分鐘檢查一次，精度為分鐘級別
4. **資料持久化**：集合資料存儲在本地 SQLite 資料庫中

## 擴展功能

未來可以考慮添加：
- 多日期集合支援
- 群組集合管理
- 地圖整合
- 天氣資訊
- 交通路線建議
