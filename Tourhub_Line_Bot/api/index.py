from flask import Flask, request, abort
import os
import logging
import requests
from bs4 import BeautifulSoup
import re
import json

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
from linebot.v3.webhooks import MessageEvent, TextMessageContent

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 建立 Flask app
app = Flask(__name__)

# 消息模板配置
MESSAGE_TEMPLATES = {
    "reminder": {
        "10_min_before": {
            "emoji": "⏰",
            "title": "集合提醒",
            "message": "還有 10 分鐘就要集合了！",
            "color": "#F39C12"
        },
        "5_min_before": {
            "emoji": "🚨",
            "title": "緊急提醒",
            "message": "還有 5 分鐘就要集合了！",
            "color": "#E74C3C"
        },
        "on_time": {
            "emoji": "🎯",
            "title": "集合時間到了！",
            "message": "集合時間到了！請準時到達！",
            "color": "#E74C3C"
        }
    },
    "features": {
        "leaderboard": {
            "title": "🏆 排行榜",
            "description": "查看最新的排行榜",
            "sub_description": "點擊下方按鈕查看詳細排名",
            "button_text": "查看排行榜",
            "color": "#FF6B6B",
            "url": "https://tourhub-ashy.vercel.app/?state=n6sFheuU2eAl&liffClientId=2007678368&liffRedirectUri=https%3A%2F%2Ftourhub-ashy.vercel.app%2F&code=DJhtwXyqmCdyhnBlGs3s"
        },
        "trip_management": {
            "title": "🗓️ 行程管理",
            "description": "建立屬於您的專屬行程內容",
            "sub_description": "點擊下方按鈕開始規劃您的完美旅程",
            "button_text": "管理行程",
            "color": "#4ECDC4",
            "url": "https://tripfrontend.vercel.app/linetrip"
        },
        "locker": {
            "title": "🛅 置物櫃",
            "description": "快速定位附近有空位的置物櫃",
            "sub_description": "輕鬆寄存行李，讓您的旅程更輕鬆",
            "button_text": "尋找置物櫃",
            "color": "#FFA500",
            "url": "https://tripfrontend.vercel.app/linelocker"
        },
        "split_bill": {
            "title": "💰 分帳工具",
            "description": "記錄每一筆費用，自動計算每人應付金額",
            "sub_description": "輕鬆分攤旅費，避免尷尬的算帳時刻",
            "button_text": "開始分帳",
            "color": "#28A745",
            "url": "https://liff.line.me/2007317887-Dq8Rorg5"
        }
    },
    "meeting_success": {
        "title": "📍 集合設定成功",
        "color": "#9B59B6",
        "status_success": "已同步到 TourClock",
        "status_success_color": "#27AE60",
        "status_local": "本地設定",
        "status_local_color": "#F39C12",
        "reminder_info": "⏰ 智能提醒設定",
        "reminder_details": "• 集合前 10 分鐘提醒\n• 集合前 5 分鐘提醒\n• 集合時間到提醒"
    },
    "help": {
        "title": "📱 TourHub 功能介紹",
        "color": "#6C5CE7",
        "features": [
            {
                "emoji": "🏆",
                "name": "排行榜",
                "description": "提供其他使用者的行程資訊進行排行，幫助您做行程規劃"
            },
            {
                "emoji": "🗓️",
                "name": "行程管理",
                "description": "建立屬於您的專屬行程內容"
            },
            {
                "emoji": "📍",
                "name": "集合功能",
                "description": "設定集合地點，方便分散活動後重新集合"
            },
            {
                "emoji": "🛅",
                "name": "置物櫃",
                "description": "快速定位附近有空位的置物櫃，輕鬆寄存行李"
            },
            {
                "emoji": "💰",
                "name": "分帳工具",
                "description": "記錄每一筆費用，自動計算每人應付金額"
            }
        ]
    }
}

# 排行榜數據配置
LEADERBOARD_DATA = {
    "1": {
        "title": "🥇 排行榜第一名",
        "color": "#FFD700",
        "destination": "東京",
        "duration": "5天4夜",
        "participants": "4人",
        "feature": "經典關東地區深度遊",
        "itinerary": "Day 1: 淺草寺 → 晴空塔 → 秋葉原\nDay 2: 明治神宮 → 原宿 → 澀谷\nDay 3: 新宿 → 池袋 → 銀座\nDay 4: 台場 → 築地市場 → 東京鐵塔\nDay 5: 上野公園 → 阿美橫町 → 機場"
    },
    "2": {
        "title": "🥈 排行榜第二名",
        "color": "#C0C0C0",
        "destination": "大阪",
        "duration": "4天3夜",
        "participants": "3人",
        "feature": "關西美食文化之旅",
        "itinerary": "Day 1: 大阪城 → 道頓堀 → 心齋橋\nDay 2: 環球影城一日遊\nDay 3: 天保山摩天輪 → 海遊館 → 梅田藍天大廈\nDay 4: 通天閣 → 新世界 → 機場"
    },
    "3": {
        "title": "🥉 排行榜第三名",
        "color": "#CD7F32",
        "destination": "京都",
        "duration": "6天5夜",
        "participants": "2人",
        "feature": "古都文化深度體驗",
        "itinerary": "Day 1: 金閣寺 → 龍安寺 → 二条城\nDay 2: 清水寺 → 地主神社 → 祇園\nDay 3: 伏見稻荷大社 → 東福寺 → 三十三間堂\nDay 4: 嵐山竹林 → 天龍寺 → 渡月橋\nDay 5: 銀閣寺 → 哲學之道 → 南禪寺\nDay 6: 西陣織會館 → 機場"
    },
    "4": {
        "title": "🏅 排行榜第四名",
        "color": "#4ECDC4",
        "destination": "沖繩",
        "duration": "5天4夜",
        "participants": "5人",
        "feature": "海島度假放鬆之旅",
        "itinerary": "Day 1: 首里城 → 國際通 → 牧志公設市場\nDay 2: 美麗海水族館 → 古宇利島 → 名護鳳梨園\nDay 3: 萬座毛 → 真榮田岬 → 殘波岬\nDay 4: 座喜味城跡 → 讀谷村 → 北谷町美國村\nDay 5: 瀨長島 → 機場"
    },
    "5": {
        "title": "🎖️ 排行榜第五名",
        "color": "#FF6B9D",
        "destination": "北海道",
        "duration": "7天6夜",
        "participants": "6人",
        "feature": "北國風情深度探索",
        "itinerary": "Day 1: 札幌市區 → 大通公園 → 狸小路商店街\nDay 2: 小樽運河 → 小樽音樂盒堂 → 北一硝子\nDay 3: 函館山夜景 → 五稜郭公園 → 元町異人館\nDay 4: 富良野薰衣草田 → 美瑛青池 → 白金溫泉\nDay 5: 洞爺湖 → 昭和新山 → 登別溫泉\nDay 6: 旭山動物園 → 層雲峽 → 大雪山\nDay 7: 機場"
    }
}

def create_flex_message(template_type, **kwargs):
    """
    動態創建 Flex Message
    template_type: 'reminder', 'feature', 'leaderboard', 'meeting_success', 'help'
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
        data = LEADERBOARD_DATA[rank]
        
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
            
            # 使用動態模板系統處理消息
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
            elif re.search(MEETING_TIME_PATTERN, user_message):
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

            else:
                # 遇到不認識的指令時不回應
                pass
        except Exception as e:
            logger.error(f"Reply error: {str(e)}")

# Vercel 需要的 app 變數
# 這是關鍵！Vercel 會自動尋找這個變數
if __name__ != "__main__":
    # 在 Vercel 上運行時
    pass
else:
    # 本地開發時
    app.run(debug=True)