"""
TourHub LINE Bot 靈活消息系統使用示例

這個文件展示了如何使用新的動態模板系統來靈活地處理各種消息類型。
"""

from config import (
    MESSAGE_TEMPLATES, 
    LEADERBOARD_DATA, 
    KEYWORD_MAPPINGS, 
    MEETING_LOCATIONS, 
    TIME_PATTERNS, 
    MEETING_TIME_PATTERN
)

def example_add_new_feature():
    """
    示例：如何添加新功能
    """
    # 1. 在 config.py 的 MESSAGE_TEMPLATES["features"] 中添加新功能
    new_feature = {
        "weather": {
            "title": "🌤️ 天氣查詢",
            "description": "查詢目的地天氣資訊",
            "sub_description": "幫助您規劃最佳出行時間",
            "button_text": "查詢天氣",
            "color": "#87CEEB",
            "url": "https://weather.example.com"
        }
    }
    
    # 2. 在 KEYWORD_MAPPINGS 中添加關鍵字映射
    new_keyword_mapping = {
        "weather": {
            "keywords": ["天氣", "氣象", "weather", "Weather", "溫度", "下雨"],
            "template": "feature",
            "feature_name": "weather"
        }
    }
    
    print("✅ 新功能已添加到配置中")

def example_modify_existing_feature():
    """
    示例：如何修改現有功能
    """
    # 修改排行榜的顏色和描述
    modified_leaderboard = {
        "title": "🏆 熱門排行榜",
        "description": "查看最受歡迎的旅遊行程",
        "sub_description": "點擊下方按鈕查看詳細排名",
        "button_text": "查看排行榜",
        "color": "#FF8C00",  # 修改顏色
        "url": "https://tourhub-ashy.vercel.app/?state=n6sFheuU2eAl&liffClientId=2007678368&liffRedirectUri=https%3A%2F%2Ftourhub-ashy.vercel.app%2F&code=DJhtwXyqmCdyhnBlGs3s"
    }
    
    print("✅ 排行榜功能已更新")

def example_add_new_reminder_type():
    """
    示例：如何添加新的提醒類型
    """
    # 在 MESSAGE_TEMPLATES["reminder"] 中添加新的提醒類型
    new_reminder = {
        "30_min_before": {
            "emoji": "📢",
            "title": "提前提醒",
            "message": "還有 30 分鐘就要集合了！",
            "color": "#3498DB"
        }
    }
    
    print("✅ 新的提醒類型已添加")

def example_add_new_location():
    """
    示例：如何添加新的集合地點
    """
    new_locations = [
        "台北101", "故宮博物院", "九份老街", "淡水老街", 
        "陽明山", "士林夜市", "西門町", "信義區"
    ]
    
    print("✅ 新的集合地點已添加")

def example_custom_message_template():
    """
    示例：如何創建自定義消息模板
    """
    custom_template = {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🎉 自定義標題",
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
                    "text": "這是自定義的消息內容",
                    "size": "md",
                    "color": "#555555",
                    "align": "center",
                    "margin": "md"
                }
            ],
            "paddingAll": "20px"
        }
    }
    
    print("✅ 自定義模板已創建")

def example_dynamic_keyword_handling():
    """
    示例：如何動態處理關鍵字
    """
    def handle_dynamic_keywords(user_message):
        # 檢查是否包含特定關鍵字
        if "排行榜" in user_message:
            # 提取排名數字
            import re
            rank_match = re.search(r'第(\d+)名', user_message)
            if rank_match:
                rank = rank_match.group(1)
                return f"leaderboard_{rank}"
        
        # 檢查是否包含地點關鍵字
        for location in MEETING_LOCATIONS:
            if location in user_message:
                return "location_found"
        
        return None
    
    print("✅ 動態關鍵字處理功能已實現")

def example_configuration_management():
    """
    示例：如何管理配置
    """
    # 從文件讀取配置
    import json
    
    def load_config_from_file(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_config_to_file(config, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    # 動態更新配置
    def update_feature_config(feature_name, new_config):
        MESSAGE_TEMPLATES["features"][feature_name].update(new_config)
        print(f"✅ {feature_name} 配置已更新")
    
    print("✅ 配置管理功能已實現")

def example_error_handling():
    """
    示例：錯誤處理
    """
    def safe_create_message(template_type, **kwargs):
        try:
            # 檢查必要參數
            if template_type == "reminder" and not all(k in kwargs for k in ['reminder_type', 'meeting_time', 'meeting_location']):
                raise ValueError("缺少必要參數")
            
            # 創建消息
            return create_flex_message(template_type, **kwargs)
        except KeyError as e:
            print(f"❌ 模板配置錯誤: {e}")
            return None
        except ValueError as e:
            print(f"❌ 參數錯誤: {e}")
            return None
        except Exception as e:
            print(f"❌ 未知錯誤: {e}")
            return None
    
    print("✅ 錯誤處理功能已實現")

if __name__ == "__main__":
    print("🚀 TourHub LINE Bot 靈活消息系統示例")
    print("=" * 50)
    
    example_add_new_feature()
    example_modify_existing_feature()
    example_add_new_reminder_type()
    example_add_new_location()
    example_custom_message_template()
    example_dynamic_keyword_handling()
    example_configuration_management()
    example_error_handling()
    
    print("=" * 50)
    print("✅ 所有示例已完成")
    print("\n📝 使用說明：")
    print("1. 修改 config.py 來添加新功能")
    print("2. 使用 create_flex_message() 創建消息")
    print("3. 使用 get_message_template() 獲取模板配置")
    print("4. 使用 parse_time() 和 parse_location() 解析用戶輸入") 