from flask import Flask, request, abort
import os
import logging
import requests
from bs4 import BeautifulSoup
import re
import json
import time

# 導入配置文件
from api.config import (
    MESSAGE_TEMPLATES, 
    LEADERBOARD_DATA, 
    KEYWORD_MAPPINGS, 
    MEETING_LOCATIONS, 
    TIME_PATTERNS, 
    MEETING_TIME_PATTERN
)

# LINE Bot imports
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage,
    FlexMessage,
    FlexContainer
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, PostbackEvent

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 建立 Flask app
app = Flask(__name__)

def create_flex_message(template_type, **kwargs):
    """
    動態創建 Flex Message
    template_type: 'reminder', 'feature', 'leaderboard', 'meeting_success', 'help', 'trip_list', 'trip_detail'
    """
    if template_type == "reminder":
        reminder_type = kwargs.get('reminder_type')
        meeting_time = kwargs.get('meeting_time')
        meeting_location = kwargs.get('meeting_location')
        
        template = MESSAGE_TEMPLATES["reminder"][reminder_type]
        
        return {
            "type": "bubble",
            "size": "kilo",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": template["title"],
                        "weight": "bold",
                        "size": "lg",
                        "color": "#ffffff",
                        "align": "center"
                    }
                ],
                "backgroundColor": template["color"],
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"{template['emoji']} {template['message']}\n📍 集合地點：{meeting_location}\n⏰ 集合時間：{meeting_time}",
                        "size": "sm",
                        "color": "#555555",
                        "wrap": True,
                        "margin": "md"
                    }
                ],
                "paddingAll": "20px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": "查看地圖",
                            "uri": f"https://maps.google.com/maps?q={meeting_location}"
                        },
                        "style": "primary",
                        "color": template["color"],
                        "height": "sm"
                    }
                ],
                "paddingAll": "20px"
            }
        }
    
    elif template_type == "feature":
        feature_name = kwargs.get('feature_name')
        template = MESSAGE_TEMPLATES["features"][feature_name]
        
        return {
            "type": "bubble",
            "size": "kilo",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": template["title"],
                        "weight": "bold",
                        "size": "lg",
                        "color": "#ffffff",
                        "align": "center"
                    }
                ],
                "backgroundColor": template["color"],
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": template["description"],
                        "size": "md",
                        "color": "#555555",
                        "align": "center",
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": template["sub_description"],
                        "size": "sm",
                        "color": "#888888",
                        "align": "center",
                        "margin": "sm"
                    }
                ],
                "paddingAll": "20px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": template["button_text"],
                            "uri": template["url"]
                        },
                        "style": "primary",
                        "color": template["color"],
                        "height": "sm"
                    }
                ],
                "paddingAll": "20px"
            }
        }
    
    elif template_type == "leaderboard":
        rank = kwargs.get('rank')
        # 使用資料庫的排行榜資料
        leaderboard_data = get_leaderboard_data()
        data = leaderboard_data.get(rank, LEADERBOARD_DATA.get(rank, {}))
        
        return {
            "type": "bubble",
            "size": "giga",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": data["title"],
                        "weight": "bold",
                        "size": "lg",
                        "color": "#ffffff",
                        "align": "center"
                    }
                ],
                "backgroundColor": data["color"],
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "📍", "size": "md", "flex": 0},
                            {"type": "text", "text": f"目的地：{data['destination']}", "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
                        ],
                        "marginBottom": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "📅", "size": "md", "flex": 0},
                            {"type": "text", "text": f"行程天數：{data['duration']}", "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
                        ],
                        "marginBottom": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "👥", "size": "md", "flex": 0},
                            {"type": "text", "text": f"參與人數：{data['participants']}", "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
                        ],
                        "marginBottom": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "💡", "size": "md", "flex": 0},
                            {"type": "text", "text": f"特色：{data['feature']}", "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
                        ],
                        "marginBottom": "md"
                    },
                    {"type": "separator", "margin": "md"},
                    {"type": "text", "text": "📋 詳細行程", "weight": "bold", "size": "md", "color": "#555555", "margin": "md"},
                    {"type": "text", "text": data["itinerary"], "size": "xs", "color": "#888888", "wrap": True, "margin": "sm"}
                ],
                "paddingAll": "20px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": "查看完整排行榜",
                            "uri": "https://tourhub-ashy.vercel.app/?state=n6sFheuU2eAl&liffClientId=2007678368&liffRedirectUri=https%3A%2F%2Ftourhub-ashy.vercel.app%2F&code=DJhtwXyqmCdyhnBlGs3s"
                        },
                        "style": "primary",
                        "color": data["color"],
                        "height": "sm"
                    }
                ],
                "paddingAll": "20px"
            }
        }
    
    elif template_type == "meeting_success":
        meeting_time = kwargs.get('meeting_time')
        meeting_location = kwargs.get('meeting_location')
        is_success = kwargs.get('is_success', False)
        template = MESSAGE_TEMPLATES["meeting_success"]
        
        status_text = template["status_success"] if is_success else template["status_local"]
        status_color = template["status_success_color"] if is_success else template["status_local_color"]
        
        return {
            "type": "bubble",
            "size": "kilo",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": template["title"],
                        "weight": "bold",
                        "size": "lg",
                        "color": "#ffffff",
                        "align": "center"
                    }
                ],
                "backgroundColor": template["color"],
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "⏰", "size": "md", "flex": 0},
                            {"type": "text", "text": f"集合時間：{meeting_time}", "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
                        ],
                        "marginBottom": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "📍", "size": "md", "flex": 0},
                            {"type": "text", "text": f"集合地點：{meeting_location}", "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
                        ],
                        "marginBottom": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "✅", "size": "md", "flex": 0},
                            {"type": "text", "text": f"狀態：{status_text}", "size": "sm", "color": status_color, "flex": 1, "marginStart": "md"}
                        ],
                        "marginBottom": "md"
                    },
                    {"type": "separator", "margin": "md"},
                    {"type": "text", "text": "🎉 集合設定完成！", "weight": "bold", "size": "sm", "color": "#27AE60", "align": "center", "margin": "md"},
                    {"type": "text", "text": "已成功設定集合時間和地點，所有成員都會收到通知", "size": "xs", "color": "#888888", "align": "center", "wrap": True, "margin": "sm"},
                    {"type": "separator", "margin": "md"},
                    {"type": "text", "text": template["reminder_info"], "weight": "bold", "size": "sm", "color": template["color"], "align": "center", "margin": "md"},
                    {"type": "text", "text": template["reminder_details"], "size": "xs", "color": "#888888", "align": "center", "wrap": True, "margin": "sm"}
                ],
                "paddingAll": "20px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": "查看 TourClock",
                            "uri": "https://tourclock.vercel.app/"
                        },
                        "style": "primary",
                        "color": template["color"],
                        "height": "sm"
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": "分享集合資訊",
                            "uri": f"https://line.me/R/msg/text/?⏰ 集合時間：{meeting_time}%0A📍 集合地點：{meeting_location}%0A%0A🌐 查看詳情：https://tourclock.vercel.app/"
                        },
                        "style": "secondary",
                        "color": template["color"],
                        "height": "sm",
                        "marginTop": "sm"
                    }
                ],
                "paddingAll": "20px"
            }
        }
    
    elif template_type == "help":
        template = MESSAGE_TEMPLATES["help"]
        
        feature_contents = []
        for feature in template["features"]:
            feature_contents.extend([
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": feature["emoji"], "size": "lg", "flex": 0},
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {"type": "text", "text": feature["name"], "weight": "bold", "size": "sm", "color": "#555555"},
                                {"type": "text", "text": feature["description"], "size": "xs", "color": "#888888", "wrap": True}
                            ],
                            "flex": 1,
                            "marginStart": "md"
                        }
                    ],
                    "marginBottom": "md"
                }
            ])
        
        return {
            "type": "bubble",
            "size": "giga",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": template["title"],
                        "weight": "bold",
                        "size": "lg",
                        "color": "#ffffff",
                        "align": "center"
                    }
                ],
                "backgroundColor": template["color"],
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": feature_contents,
                "paddingAll": "20px"
            }
        }
    
    elif template_type == "trip_list":
        location = kwargs.get('location')
        trips = kwargs.get('trips')
        
        trip_contents = []
        for i, trip in enumerate(trips[:5]):  # 最多顯示5條行程
            trip_contents.append({
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": trip["title"],
                                "weight": "bold",
                                "size": "sm",
                                "color": "#555555"
                            },
                            {
                                "type": "text",
                                "text": f"⏰ {trip['duration']} | ⭐ {trip['rating']}",
                                "size": "xs",
                                "color": "#888888",
                                "marginTop": "sm"
                            },
                            {
                                "type": "text",
                                "text": f"📍 {trip['highlights']}",
                                "size": "xs",
                                "color": "#888888",
                                "wrap": True,
                                "marginTop": "sm"
                            }
                        ],
                        "flex": 1
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "查看詳情",
                            "data": f"trip_detail:{trip['id']}"
                        },
                        "style": "primary",
                        "color": "#9B59B6",
                        "height": "sm",
                        "marginStart": "md"
                    }
                ],
                "marginBottom": "md",
                "paddingAll": "sm",
                "backgroundColor": "#f8f9fa",
                "cornerRadius": "md"
            })
        
        return {
            "type": "bubble",
            "size": "giga",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"🗺️ {location} 行程推薦",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#ffffff",
                        "align": "center"
                    }
                ],
                "backgroundColor": "#9B59B6",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": trip_contents,
                "paddingAll": "20px"
            }
        }
    
    elif template_type == "trip_detail":
        trip = kwargs.get('trip')
        
        itinerary_contents = []
        for day_key, day_itinerary in trip["itinerary"].items():
            itinerary_contents.append({
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "text",
                        "text": day_key.replace("day", "Day "),
                        "weight": "bold",
                        "size": "sm",
                        "color": "#9B59B6",
                        "flex": 0
                    },
                    {
                        "type": "text",
                        "text": day_itinerary,
                        "size": "sm",
                        "color": "#555555",
                        "flex": 1,
                        "wrap": True,
                        "marginStart": "md"
                    }
                ],
                "marginBottom": "sm"
            })
        
        return {
            "type": "bubble",
            "size": "giga",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": trip["title"],
                        "weight": "bold",
                        "size": "lg",
                        "color": "#ffffff",
                        "align": "center"
                    }
                ],
                "backgroundColor": "#9B59B6",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "⏰", "size": "md", "flex": 0},
                            {"type": "text", "text": f"行程天數：{trip['duration']}", "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
                        ],
                        "marginBottom": "sm"
                    },

                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "⭐", "size": "md", "flex": 0},
                            {"type": "text", "text": f"評分：{trip['rating']}", "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
                        ],
                        "marginBottom": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "📍", "size": "md", "flex": 0},
                            {"type": "text", "text": f"亮點：{trip['highlights']}", "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
                        ],
                        "marginBottom": "md"
                    },
                    {"type": "separator", "margin": "md"},
                    {"type": "text", "text": "📋 詳細行程", "weight": "bold", "size": "md", "color": "#555555", "margin": "md"},
                    *itinerary_contents
                ],
                "paddingAll": "20px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": "開始規劃行程",
                            "uri": "https://tripfrontend.vercel.app/linetrip"
                        },
                        "style": "primary",
                        "color": "#9B59B6",
                        "height": "sm"
                    }
                ],
                "paddingAll": "20px"
            }
        }

def get_message_template(user_message):
    """
    根據用戶消息獲取對應的模板配置
    支持完全匹配和部分匹配，優先匹配更具體的關鍵字
    """
    # 首先嘗試完全匹配
    for key, mapping in KEYWORD_MAPPINGS.items():
        if user_message in mapping["keywords"]:
            return mapping
    
    # 如果完全匹配失敗，嘗試部分匹配
    # 優先匹配更具體的關鍵字（如"第一名"優先於"排行榜"）
    best_match = None
    best_keyword_length = 0
    
    for key, mapping in KEYWORD_MAPPINGS.items():
        for keyword in mapping["keywords"]:
            if keyword in user_message:
                # 選擇最長的關鍵字匹配（更具體）
                if len(keyword) > best_keyword_length:
                    best_match = mapping
                    best_keyword_length = len(keyword)
    
    return best_match

def parse_time(user_message):
    """解析各種時間格式"""
    # 標準時間格式 14:30
    time_match = re.search(TIME_PATTERNS["standard"], user_message)
    if time_match:
        return time_match.group(1)
    
    # 中文時間格式 2點30分
    chinese_time = re.search(TIME_PATTERNS["chinese"], user_message)
    if chinese_time:
        hour = chinese_time.group(1)
        minute = chinese_time.group(2)
        return f"{hour.zfill(2)}:{minute.zfill(2)}"
    
    # 簡化中文時間格式 2點
    simple_chinese_time = re.search(TIME_PATTERNS["simple_chinese"], user_message)
    if simple_chinese_time:
        hour = simple_chinese_time.group(1)
        return f"{hour.zfill(2)}:00"
    
    # 處理上午/下午/晚上/凌晨
    am_pm_match = re.search(TIME_PATTERNS["am_pm"], user_message)
    if am_pm_match:
        period = am_pm_match.group(1)
        hour = int(am_pm_match.group(2))
        minute = am_pm_match.group(3) if am_pm_match.group(3) else "00"
        
        # 轉換為24小時制
        if period == "下午" and hour != 12:
            hour += 12
        elif period == "晚上" and hour != 12:
            hour += 12
        elif period == "凌晨" and hour == 12:
            hour = 0
        
        return f"{hour:02d}:{minute.zfill(2)}"
    
    return None

def parse_location(user_message):
    """解析集合地點"""
    for location in MEETING_LOCATIONS:
        if location in user_message:
            return location
    return None

def find_location_trips(user_message):
    """查找地區相關行程"""
    from api.config import TRIP_DATABASE
    
    for location in TRIP_DATABASE.keys():
        if location in user_message:
            return location, TRIP_DATABASE[location]
    return None, None

def find_trip_by_id(trip_id):
    """根據ID查找行程"""
    from api.config import TRIP_DATABASE
    
    for location_trips in TRIP_DATABASE.values():
        for trip in location_trips:
            if trip["id"] == trip_id:
                return trip
    return None

# 排行榜資料緩存
_leaderboard_cache = None
_cache_timestamp = 0
CACHE_DURATION = 300  # 5分鐘緩存

def get_leaderboard_data():
    """從資料庫獲取排行榜資料"""
    global _leaderboard_cache, _cache_timestamp
    
    # 檢查緩存是否有效
    current_time = time.time()
    if _leaderboard_cache and (current_time - _cache_timestamp) < CACHE_DURATION:
        logger.info("使用緩存的排行榜資料")
        return _leaderboard_cache
    
    try:
        # 從資料庫獲取排行榜資料
        from api.database_utils import get_leaderboard_from_database
        leaderboard_data = get_leaderboard_from_database()
        
        if leaderboard_data:
            # 更新緩存
            _leaderboard_cache = leaderboard_data
            _cache_timestamp = current_time
            
            logger.info("成功從資料庫獲取排行榜資料並更新緩存")
            return leaderboard_data
        else:
            logger.warning("資料庫中沒有排行榜資料，使用預設資料")
            from api.config import LEADERBOARD_DATA
            return LEADERBOARD_DATA
        
    except Exception as e:
        logger.error(f"從資料庫獲取排行榜資料失敗: {str(e)}")
        # 如果資料庫獲取失敗，返回預設資料
        from api.config import LEADERBOARD_DATA
        return LEADERBOARD_DATA

# 提醒處理函數
def send_reminder_message(user_id, meeting_time, meeting_location, reminder_type):
    """
    發送提醒訊息給用戶
    reminder_type: '10_min_before', '5_min_before', 'on_time'
    """
    try:
        # 使用動態模板創建 Flex Message
        flex_message = create_flex_message(
            "reminder",
            reminder_type=reminder_type,
            meeting_time=meeting_time,
            meeting_location=meeting_location
        )
        
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.push_message_with_http_info(
                PushMessageRequest(
                    to=user_id,
                    messages=[FlexMessage(alt_text="集合提醒", contents=FlexContainer.from_dict(flex_message))]
                )
            )
            
        logger.info(f"已發送 {reminder_type} 提醒給用戶 {user_id}")
        
    except Exception as e:
        logger.error(f"發送提醒訊息失敗: {str(e)}")

# 環境變數檢查
CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.environ.get('CHANNEL_SECRET')

if CHANNEL_ACCESS_TOKEN and CHANNEL_SECRET:
    configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
    line_handler = WebhookHandler(CHANNEL_SECRET)
    logger.info("LINE Bot 設定成功")
else:
    configuration = None
    line_handler = None
    logger.warning("LINE Bot 環境變數未設定")

# 健康檢查
@app.route('/')
def health():
    return {
        "status": "running",
        "bot_configured": configuration is not None
    }

# 除錯端點
@app.route('/debug')
def debug():
    return {
        "has_token": bool(CHANNEL_ACCESS_TOKEN),
        "has_secret": bool(CHANNEL_SECRET),
        "token_length": len(CHANNEL_ACCESS_TOKEN) if CHANNEL_ACCESS_TOKEN else 0
    }

# TourClock 提醒回調端點
@app.route('/reminder', methods=['POST'])
def reminder_callback():
    try:
        data = request.get_json()
        
        if not data:
            return {"error": "No data received"}, 400
        
        # 解析提醒資料
        user_id = data.get('user_id')
        meeting_time = data.get('meeting_time')
        meeting_location = data.get('meeting_location')
        reminder_type = data.get('reminder_type')  # '10_min_before', '5_min_before', 'on_time'
        
        if not all([user_id, meeting_time, meeting_location, reminder_type]):
            return {"error": "Missing required fields"}, 400
        
        # 發送提醒訊息
        send_reminder_message(user_id, meeting_time, meeting_location, reminder_type)
        
        return {"status": "success", "message": f"Reminder sent: {reminder_type}"}, 200
        
    except Exception as e:
        logger.error(f"提醒回調處理錯誤: {str(e)}")
        return {"error": str(e)}, 500

# LINE Bot callback
@app.route('/callback', methods=['POST'])
def callback():
    if not line_handler:
        return "Bot not configured", 500
    
    try:
        signature = request.headers.get('X-Line-Signature')
        if not signature:
            abort(400)
        
        body = request.get_data(as_text=True)
        line_handler.handle(body, signature)
        return 'OK'
        
    except InvalidSignatureError:
        abort(400)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return "Internal error", 500

# 訊息處理
if line_handler:
    @line_handler.add(MessageEvent, message=TextMessageContent)
    def handle_message(event):
        try:
            user_message = event.message.text
            
            # 優先檢查是否包含時間地點的集合設定
            if re.search(MEETING_TIME_PATTERN, user_message):
                # 解析集合時間和地點
                meeting_time = parse_time(user_message)
                meeting_location = parse_location(user_message)
                
                if meeting_time and meeting_location:
                    
                    try:
                        # 向 TourClock 發送集合設定請求
                        tourclock_url = "https://tourclock.vercel.app/"
                        tourclock_data = {
                            "time": meeting_time,
                            "location": meeting_location,
                            "action": "create_meeting",
                            "user_id": event.source.user_id,  # 添加用戶ID
                            "reminders": {
                                "10_min_before": True,
                                "5_min_before": True,
                                "on_time": True
                            },
                            "callback_url": "https://your-vercel-app.vercel.app/reminder"  # 提醒回調URL
                        }
                        
                        # 發送 POST 請求到 TourClock
                        response = requests.post(tourclock_url, json=tourclock_data, timeout=10)
                        
                        if response.status_code == 200:
                            # 成功設定集合
                            flex_message = create_flex_message(
                                "meeting_success",
                                meeting_time=meeting_time,
                                meeting_location=meeting_location,
                                is_success=True
                            )
                        else:
                            # TourClock 設定失敗，但仍顯示本地設定
                            flex_message = create_flex_message(
                                "meeting_success",
                                meeting_time=meeting_time,
                                meeting_location=meeting_location,
                                is_success=False
                            )
                        
                        with ApiClient(configuration) as api_client:
                            line_bot_api = MessagingApi(api_client)
                            line_bot_api.reply_message_with_http_info(
                                ReplyMessageRequest(
                                    reply_token=event.reply_token,
                                    messages=[FlexMessage(alt_text="集合設定", contents=FlexContainer.from_dict(flex_message))]
                                )
                            )
                    except Exception as e:
                        # 發生錯誤時的處理
                        logger.error(f"TourClock 設定錯誤: {str(e)}")
                        flex_message = create_flex_message(
                            "meeting_success",
                            meeting_time=meeting_time,
                            meeting_location=meeting_location,
                            is_success=False
                        )
                        
                        with ApiClient(configuration) as api_client:
                            line_bot_api = MessagingApi(api_client)
                            line_bot_api.reply_message_with_http_info(
                                ReplyMessageRequest(
                                    reply_token=event.reply_token,
                                    messages=[FlexMessage(alt_text="集合設定", contents=FlexContainer.from_dict(flex_message))]
                                )
                            )
                else:
                    # 如果沒有找到時間或地點，提供使用說明
                    flex_message = create_flex_message(
                        "help"
                    )
                    
                    with ApiClient(configuration) as api_client:
                        line_bot_api = MessagingApi(api_client)
                        line_bot_api.reply_message_with_http_info(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[FlexMessage(alt_text="集合功能說明", contents=FlexContainer.from_dict(flex_message))]
                            )
                        )
            
            # 如果沒有包含時間地點的集合設定，則檢查其他功能
            else:
                # 優先檢查是否為地區查詢
                location, trips = find_location_trips(user_message)
                if location and trips:
                    # 創建行程列表 Flex Message
                    flex_message = create_flex_message(
                        "trip_list",
                        location=location,
                        trips=trips
                    )
                    
                    # 發送消息
                    with ApiClient(configuration) as api_client:
                        line_bot_api = MessagingApi(api_client)
                        line_bot_api.reply_message_with_http_info(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[FlexMessage(alt_text=f"{location} 行程推薦", contents=FlexContainer.from_dict(flex_message))]
                            )
                        )
                else:
                    # 檢查其他模板匹配
                    template_config = get_message_template(user_message)
                    
                    if template_config:
                        # 根據模板配置創建 Flex Message
                        if template_config["template"] == "feature":
                            flex_message = create_flex_message(
                                "feature",
                                feature_name=template_config["feature_name"]
                            )
                        elif template_config["template"] == "leaderboard":
                            flex_message = create_flex_message(
                                "leaderboard",
                                rank=template_config["rank"]
                            )
                        elif template_config["template"] == "help":
                            flex_message = create_flex_message("help")
                        
                        # 發送消息
                        with ApiClient(configuration) as api_client:
                            line_bot_api = MessagingApi(api_client)
                            line_bot_api.reply_message_with_http_info(
                                ReplyMessageRequest(
                                    reply_token=event.reply_token,
                                    messages=[FlexMessage(alt_text="功能回應", contents=FlexContainer.from_dict(flex_message))]
                                )
                            )
                    else:
                        # 遇到不認識的指令時不回應
                        pass
        except Exception as e:
            logger.error(f"Reply error: {str(e)}")

    @line_handler.add(PostbackEvent)
    def handle_postback(event):
        try:
            postback_data = event.postback.data
            
            # 處理行程詳情查詢
            if postback_data.startswith("trip_detail:"):
                trip_id = postback_data.split(":")[1]
                trip = find_trip_by_id(trip_id)
                
                if trip:
                    # 創建行程詳情 Flex Message
                    flex_message = create_flex_message(
                        "trip_detail",
                        trip=trip
                    )
                    
                    # 發送消息
                    with ApiClient(configuration) as api_client:
                        line_bot_api = MessagingApi(api_client)
                        line_bot_api.reply_message_with_http_info(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[FlexMessage(alt_text=f"{trip['title']} 詳細行程", contents=FlexContainer.from_dict(flex_message))]
                            )
                        )
                else:
                    logger.error(f"找不到行程 ID: {trip_id}")
            
        except Exception as e:
            logger.error(f"Postback error: {str(e)}")

# Vercel 需要的 app 變數
# 這是關鍵！Vercel 會自動尋找這個變數
if __name__ != "__main__":
    # 在 Vercel 上運行時
    pass
else:
    # 本地開發時
    app.run(debug=True)