# TourHub LINE Bot 靈活消息系統

## 🎯 系統概述

這個新的靈活消息系統讓你可以輕鬆地管理和修改 LINE Bot 的消息內容，而不需要手動編寫大量的硬編碼代碼。

## 🚀 主要特性

### 1. 動態模板系統
- **配置驅動**：所有消息模板都在 `config.py` 中集中管理
- **易於修改**：只需修改配置文件，無需觸及核心代碼
- **類型安全**：支持多種消息類型（提醒、功能、排行榜等）

### 2. 關鍵字映射
- **靈活匹配**：支持多種關鍵字觸發同一功能
- **易於擴展**：添加新關鍵字只需修改配置
- **智能解析**：自動識別用戶意圖

### 3. 時間和地點解析
- **多種格式**：支持標準時間、中文時間、上午下午等格式
- **地點識別**：自動識別預設的集合地點
- **錯誤處理**：優雅的錯誤處理機制

## 📁 文件結構

```
api/
├── index.py          # 主程序文件
├── config.py         # 配置文件（新增）
└── example_usage.py  # 使用示例（新增）
```

## 🔧 使用方法

### 1. 添加新功能

在 `config.py` 中添加新功能配置：

```python
# 在 MESSAGE_TEMPLATES["features"] 中添加
"new_feature": {
    "title": "🆕 新功能",
    "description": "新功能的描述",
    "sub_description": "詳細說明",
    "button_text": "使用新功能",
    "color": "#FF6B6B",
    "url": "https://example.com"
}

# 在 KEYWORD_MAPPINGS 中添加關鍵字映射
"new_feature": {
    "keywords": ["新功能", "new", "New"],
    "template": "feature",
    "feature_name": "new_feature"
}
```

### 2. 修改現有功能

直接修改 `config.py` 中的配置：

```python
# 修改排行榜顏色
MESSAGE_TEMPLATES["features"]["leaderboard"]["color"] = "#FF8C00"

# 修改描述文字
MESSAGE_TEMPLATES["features"]["leaderboard"]["description"] = "新的描述"
```

### 3. 添加新的提醒類型

```python
# 在 MESSAGE_TEMPLATES["reminder"] 中添加
"30_min_before": {
    "emoji": "📢",
    "title": "提前提醒",
    "message": "還有 30 分鐘就要集合了！",
    "color": "#3498DB"
}
```

### 4. 添加新的集合地點

```python
# 在 MEETING_LOCATIONS 中添加
MEETING_LOCATIONS.extend([
    "台北101", "故宮博物院", "九份老街"
])
```

## 🎨 自定義消息模板

### 基本模板結構

```python
def create_custom_message():
    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "自定義標題",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#ffffff",
                    "align": "center"
                }
            ],
            "backgroundColor": "#FF6B6B",
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "自定義內容",
                    "size": "md",
                    "color": "#555555",
                    "align": "center",
                    "margin": "md"
                }
            ],
            "paddingAll": "20px"
        }
    }
```

## 🔍 核心函數

### 1. `create_flex_message(template_type, **kwargs)`
創建 Flex Message 的主要函數

```python
# 創建功能消息
flex_message = create_flex_message(
    "feature",
    feature_name="leaderboard"
)

# 創建排行榜消息
flex_message = create_flex_message(
    "leaderboard",
    rank="1"
)

# 創建提醒消息
flex_message = create_flex_message(
    "reminder",
    reminder_type="10_min_before",
    meeting_time="14:30",
    meeting_location="東京鐵塔"
)
```

### 2. `get_message_template(user_message)`
根據用戶消息獲取對應的模板配置

```python
template_config = get_message_template("排行榜")
if template_config:
    # 處理模板配置
    pass
```

### 3. `parse_time(user_message)`
解析各種時間格式

```python
time = parse_time("下午2:30 集合")
# 返回: "14:30"
```

### 4. `parse_location(user_message)`
解析集合地點

```python
location = parse_location("東京鐵塔集合")
# 返回: "東京鐵塔"
```

## 📝 配置說明

### MESSAGE_TEMPLATES
包含所有消息模板的配置：

- `reminder`: 提醒消息模板
- `features`: 功能消息模板
- `meeting_success`: 集合成功消息模板
- `help`: 幫助消息模板

### KEYWORD_MAPPINGS
關鍵字到模板的映射：

```python
{
    "feature_name": {
        "keywords": ["關鍵字1", "關鍵字2"],
        "template": "feature",
        "feature_name": "feature_name"
    }
}
```

### LEADERBOARD_DATA
排行榜數據配置：

```python
{
    "1": {
        "title": "🥇 排行榜第一名",
        "color": "#FFD700",
        "destination": "東京",
        "duration": "5天4夜",
        "participants": "4人",
        "feature": "經典關東地區深度遊",
        "itinerary": "詳細行程..."
    }
}
```

## 🛠️ 擴展指南

### 添加新消息類型

1. 在 `MESSAGE_TEMPLATES` 中添加新類型
2. 在 `create_flex_message` 函數中添加處理邏輯
3. 在 `KEYWORD_MAPPINGS` 中添加關鍵字映射

### 添加新的解析功能

1. 創建新的解析函數
2. 在主處理邏輯中調用
3. 更新相關配置

### 錯誤處理

系統包含完整的錯誤處理機制：

```python
try:
    flex_message = create_flex_message(template_type, **kwargs)
    # 發送消息
except Exception as e:
    logger.error(f"創建消息失敗: {str(e)}")
    # 處理錯誤
```

## 🎯 優勢

1. **維護性**：配置與代碼分離，易於維護
2. **擴展性**：輕鬆添加新功能和關鍵字
3. **一致性**：統一的模板系統確保消息風格一致
4. **靈活性**：支持多種消息類型和格式
5. **可讀性**：清晰的配置結構，易於理解

## 📞 支持

如果你在使用過程中遇到問題，可以：

1. 查看 `example_usage.py` 中的示例
2. 檢查 `config.py` 中的配置
3. 參考這個 README 文件

---

**🎉 現在你可以輕鬆地靈活呈現各種消息內容，而不需要手動編寫大量硬編碼！** 