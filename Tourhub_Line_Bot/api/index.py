from flask import Flask, request, abort
import os
import logging
import re
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

# 導入集合管理器 - 使用 Vercel 兼容版本
from api.vercel_meeting_manager import meeting_manager
logger.info("使用 Vercel 兼容的集合管理器")

# 建立 Flask app
app = Flask(__name__)

def create_meeting_list_message(meetings):
    """創建集合列表 Flex Message"""
    meeting_contents = []
    
    for meeting in meetings[:5]:  # 最多顯示5個集合
        meeting_contents.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": meeting["meeting_name"],
                            "weight": "bold",
                            "size": "sm",
                            "color": "#555555"
                        },
                        {
                            "type": "text",
                            "text": f"⏰ {meeting['meeting_time']}",
                            "size": "xs",
                            "color": "#888888",
                            "marginTop": "sm"
                        },
                        {
                            "type": "text",
                            "text": f"📍 {meeting['meeting_location']}",
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
                        "label": "取消",
                        "data": f"cancel_meeting:{meeting['id']}"
                    },
                    "style": "secondary",
                    "color": "#E74C3C",
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
                    "text": "📝 我的集合列表",
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
            "contents": meeting_contents,
            "paddingAll": "20px"
        }
    }

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
        
        # 檢查資料庫中是否有該排名
        if rank in leaderboard_data:
            data = leaderboard_data.get(rank)
        else:
            # 如果資料庫中沒有該排名，返回空缺訊息
            return {
                "type": "bubble",
                "size": "kilo",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"🏆 排行榜第{rank}名",
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
                            "type": "text",
                            "text": "📭 此排名目前空缺",
                            "weight": "bold",
                            "size": "md",
                            "color": "#555555",
                            "align": "center"
                        },
                        {
                            "type": "text",
                            "text": f"排行榜第{rank}名目前沒有資料，請稍後再查看或選擇其他排名。",
                            "size": "sm",
                            "color": "#888888",
                            "align": "center",
                            "wrap": True
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
                                "label": "查看完整排行榜",
                                "uri": "https://tourhub-ashy.vercel.app/?state=n6sFheuU2eAl&liffClientId=2007678368&liffRedirectUri=https%3A%2F%2Ftourhub-ashy.vercel.app%2F&code=DJhtwXyqmCdyhnBlGs3s"
                            },
                            "style": "primary",
                            "color": "#9B59B6",
                            "height": "sm"
                        }
                    ],
                    "paddingAll": "20px"
                }
            }
        
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
        meeting_id = kwargs.get('meeting_id')  # 保留以備未來使用
        is_success = kwargs.get('is_success', False)
        template = MESSAGE_TEMPLATES["meeting_success"]

        status_text = template["status_success"] if is_success else template["status_local"]
        status_color = template["status_success_color"] if is_success else template["status_local_color"]

        # 計算提醒時間
        from datetime import datetime, timedelta
        try:
            # 假設是今天的時間
            today = datetime.now().strftime("%Y-%m-%d")
            meeting_datetime = datetime.strptime(f"{today} {meeting_time}", "%Y-%m-%d %H:%M")
            reminder_10min = (meeting_datetime - timedelta(minutes=10)).strftime("%H:%M")
            reminder_5min = (meeting_datetime - timedelta(minutes=5)).strftime("%H:%M")
        except:
            reminder_10min = "提醒前10分鐘"
            reminder_5min = "提醒前5分鐘"

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
                    {"type": "text", "text": "已成功設定集合時間和地點，智能提醒已啟用", "size": "xs", "color": "#888888", "align": "center", "wrap": True, "margin": "sm"},
                    {"type": "separator", "margin": "md"},
                    {"type": "text", "text": "📱 智能提醒時間", "weight": "bold", "size": "sm", "color": template["color"], "align": "center", "margin": "md"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": f"🔔 {reminder_10min} (集合前10分鐘)", "size": "xs", "color": "#888888", "align": "center"},
                            {"type": "text", "text": f"🔔 {reminder_5min} (集合前5分鐘)", "size": "xs", "color": "#888888", "align": "center", "marginTop": "xs"},
                            {"type": "text", "text": f"🔔 {meeting_time} (集合時間到)", "size": "xs", "color": "#888888", "align": "center", "marginTop": "xs"}
                        ],
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
                            "type": "postback",
                            "label": "查看我的集合",
                            "data": "view_meetings"
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
                            "uri": f"https://line.me/R/msg/text/?⏰ 集合時間：{meeting_time}%0A📍 集合地點：{meeting_location}%0A%0A🤖 由 TourHub Bot 智能管理"
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
                                "text": f"⏰ {trip['duration']}",
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
        
        # 處理行程內容 - 支援字串和字典格式
        if isinstance(trip["itinerary"], str):
            # 如果是字串格式，按行分割
            itinerary_lines = trip["itinerary"].split('\n')
            for i, line in enumerate(itinerary_lines, 1):
                if line.strip():
                    itinerary_contents.append({
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": f"Day {i}",
                                "weight": "bold",
                                "size": "sm",
                                "color": "#9B59B6",
                                "flex": 0
                            },
                            {
                                "type": "text",
                                "text": line.strip(),
                                "size": "sm",
                                "color": "#555555",
                                "flex": 1,
                                "wrap": True,
                                "marginStart": "md"
                            }
                        ],
                        "marginBottom": "sm"
                    })
        else:
            # 如果是字典格式，按原來的邏輯處理
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
                            {"type": "text", "text": "📍", "size": "md", "flex": 0},
                            {"type": "text", "text": f"亮點：{trip.get('highlights', trip.get('description', '精彩行程'))}", "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
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

    elif template_type == "leaderboard_details":
        rank_data = kwargs.get('rank_data')

        if not rank_data:
            return {
                "type": "bubble",
                "size": "kilo",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "抱歉，無法獲取詳細行程資料，請稍後再試。",
                            "size": "sm",
                            "color": "#888888",
                            "align": "center",
                            "wrap": True
                        }
                    ],
                    "paddingAll": "20px"
                }
            }

        # 構建行程詳細內容 - 使用新的格式
        itinerary_contents = []
        itinerary_list = rank_data.get('itinerary_list', [])

        if itinerary_list:
            for i, day_info in enumerate(itinerary_list):
                # 每個行程項目之間添加分隔線（除了第一個）
                if i > 0:
                    itinerary_contents.append({
                        "type": "separator",
                        "margin": "md"
                    })

                # 分割日期、時間、地點
                lines = day_info.split('\n')

                # 添加日期（第一行）
                if len(lines) >= 1:
                    itinerary_contents.append({
                        "type": "text",
                        "text": lines[0],  # 日期和星期
                        "size": "sm",
                        "color": "#333333",
                        "weight": "bold",
                        "margin": "md"
                    })

                # 添加時間（第二行）
                if len(lines) >= 2:
                    itinerary_contents.append({
                        "type": "text",
                        "text": lines[1],  # 時間
                        "size": "sm",
                        "color": "#666666",
                        "margin": "xs"
                    })

                # 添加地點（第三行）
                if len(lines) >= 3:
                    itinerary_contents.append({
                        "type": "text",
                        "text": lines[2],  # 地點
                        "size": "sm",
                        "color": "#444444",
                        "margin": "xs"
                    })

        # 如果沒有詳細行程，顯示提示
        if not itinerary_contents:
            itinerary_contents.append({
                "type": "text",
                "text": "暫無詳細行程資料",
                "size": "sm",
                "color": "#888888",
                "align": "center",
                "margin": "md"
            })

        # 根據排名設定顏色
        rank_colors = {1: "#FFD700", 2: "#C0C0C0", 3: "#CD7F32", 4: "#4ECDC4", 5: "#FF6B9D"}
        rank = rank_data.get('rank', 1)
        color = rank_colors.get(rank, "#9B59B6")

        return {
            "type": "bubble",
            "size": "giga",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"{rank_data.get('rank_title', '詳細行程')}",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#ffffff",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": rank_data.get('title', '未知行程'),
                        "size": "sm",
                        "color": "#ffffff",
                        "align": "center",
                        "margin": "sm"
                    }
                ],
                "backgroundColor": color,
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
                            {"type": "text", "text": f"目的地：{rank_data.get('area', '未知地區')}", "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
                        ],
                        "marginBottom": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "📅", "size": "md", "flex": 0},
                            {"type": "text", "text": f"行程天數：{rank_data.get('duration', '未知')}", "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
                        ],
                        "marginBottom": "md"
                    },
                    {"type": "separator", "margin": "md"},
                    {"type": "text", "text": "📋 詳細行程安排", "weight": "bold", "size": "md", "color": "#555555", "margin": "md"},
                    *itinerary_contents,
                    {"type": "separator", "margin": "md"},
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {"type": "text", "text": "❤️", "size": "sm", "align": "center"},
                                    {"type": "text", "text": str(rank_data.get('favorite_count', 0)), "size": "xs", "color": "#888888", "align": "center"}
                                ],
                                "flex": 1
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {"type": "text", "text": "📤", "size": "sm", "align": "center"},
                                    {"type": "text", "text": str(rank_data.get('share_count', 0)), "size": "xs", "color": "#888888", "align": "center"}
                                ],
                                "flex": 1
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {"type": "text", "text": "👁️", "size": "sm", "align": "center"},
                                    {"type": "text", "text": str(rank_data.get('view_count', 0)), "size": "xs", "color": "#888888", "align": "center"}
                                ],
                                "flex": 1
                            }
                        ],
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
                            "label": "查看完整排行榜",
                            "uri": "https://tourhub-ashy.vercel.app/?state=n6sFheuU2eAl&liffClientId=2007678368&liffRedirectUri=https%3A%2F%2Ftourhub-ashy.vercel.app%2F&code=DJhtwXyqmCdyhnBlGs3s"
                        },
                        "style": "primary",
                        "color": color,
                        "height": "sm"
                    }
                ],
                "paddingAll": "20px"
            }
        }

# 預建立關鍵字索引以提高匹配速度
_keyword_index = None

def build_keyword_index():
    """建立關鍵字索引"""
    global _keyword_index
    if _keyword_index is not None:
        return _keyword_index

    _keyword_index = {}
    for mapping_key, mapping in KEYWORD_MAPPINGS.items():
        for keyword in mapping["keywords"]:
            if keyword not in _keyword_index:
                _keyword_index[keyword] = []
            _keyword_index[keyword].append((mapping, len(keyword)))

    # 按關鍵字長度排序，優先匹配更長的關鍵字
    for keyword in _keyword_index:
        _keyword_index[keyword].sort(key=lambda x: x[1], reverse=True)

    return _keyword_index

def get_message_template(user_message):
    """
    根據用戶消息獲取對應的模板配置（優化版本）
    支持完全匹配和部分匹配，優先匹配更具體的關鍵字
    """
    keyword_index = build_keyword_index()

    # 首先嘗試完全匹配
    if user_message in keyword_index:
        return keyword_index[user_message][0][0]  # 返回第一個匹配的模板

    # 部分匹配 - 找到最長的匹配關鍵字
    best_match = None
    best_keyword_length = 0

    for keyword, mappings in keyword_index.items():
        if keyword in user_message and len(keyword) > best_keyword_length:
            best_match = mappings[0][0]  # 取第一個（最長的）匹配
            best_keyword_length = len(keyword)

    return best_match

def parse_time(user_message):
    """解析各種時間格式"""
    from datetime import datetime

    # 優先處理上午/下午/晚上/凌晨 (冒號格式) - 例如：下午2:35
    am_pm_colon_match = re.search(TIME_PATTERNS["am_pm_colon"], user_message)
    if am_pm_colon_match:
        period = am_pm_colon_match.group(1)
        hour = int(am_pm_colon_match.group(2))
        minute = am_pm_colon_match.group(3)

        # 轉換為24小時制
        if period == "下午" and hour != 12:
            hour += 12
        elif period == "晚上" and hour != 12:
            hour += 12
        elif period == "凌晨" and hour == 12:
            hour = 0
        elif period == "上午" and hour == 12:
            hour = 0

        return f"{hour:02d}:{minute.zfill(2)}"

    # 處理上午/下午/晚上/凌晨 (點分格式) - 例如：下午2點35分
    am_pm_match = re.search(TIME_PATTERNS["am_pm"], user_message)
    if am_pm_match:
        period = am_pm_match.group(1)
        hour = int(am_pm_match.group(2))
        minute = am_pm_match.group(3)

        # 轉換為24小時制
        if period == "下午" and hour != 12:
            hour += 12
        elif period == "晚上" and hour != 12:
            hour += 12
        elif period == "凌晨" and hour == 12:
            hour = 0
        elif period == "上午" and hour == 12:
            hour = 0

        return f"{hour:02d}:{minute.zfill(2)}"
    
    # 處理上午/下午/晚上/凌晨 (簡化格式) - 例如：下午2點
    am_pm_simple_match = re.search(TIME_PATTERNS["am_pm_simple"], user_message)
    if am_pm_simple_match:
        period = am_pm_simple_match.group(1)
        hour = int(am_pm_simple_match.group(2))
        
        # 轉換為24小時制
        if period == "下午" and hour != 12:
            hour += 12
        elif period == "晚上" and hour != 12:
            hour += 12
        elif period == "凌晨" and hour == 12:
            hour = 0
        
        return f"{hour:02d}:00"
    
    # 處理 "點半" 或 "點30分"
    natural_time_match = re.search(TIME_PATTERNS["natural_time"], user_message)
    if natural_time_match:
        hour = natural_time_match.group(1) or natural_time_match.group(2)
        return f"{hour.zfill(2)}:30"
    
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
    
    # 標準時間格式 14:30 (最後處理，避免與上午/下午格式衝突)
    time_match = re.search(TIME_PATTERNS["standard"], user_message)
    if time_match:
        return time_match.group(1)
    
    # 處理冒號格式但沒有前後文的情況
    colon_time_match = re.search(TIME_PATTERNS["time_with_colon"], user_message)
    if colon_time_match:
        hour = colon_time_match.group(1)
        minute = colon_time_match.group(2)
        return f"{hour.zfill(2)}:{minute.zfill(2)}"

    # 處理小數點格式 - 例如：2.35
    decimal_time_match = re.search(TIME_PATTERNS["decimal_time"], user_message)
    if decimal_time_match:
        hour = decimal_time_match.group(1)
        minute = decimal_time_match.group(2)
        return f"{hour.zfill(2)}:{minute.zfill(2)}"

    return None

def parse_location(user_message):
    """解析集合地點"""
    # 優先檢查預設地點列表
    for location in MEETING_LOCATIONS:
        if location in user_message:
            return location
    
    # 模糊比對預設地點
    for location in MEETING_LOCATIONS:
        if any(word in user_message for word in location.split()):
            return location
    
    # 使用正則表達式提取地點
    # 匹配 "在/到/約在/集合於/見面於 + 地點" 的格式
    location_patterns = [
        r'(在|到|約在|集合於|見面於|於)([\u4e00-\u9fa5A-Za-z0-9\s]+?)(集合|見面|碰面|會合|$|\s|，|,|。|！|！)',
        r'([\u4e00-\u9fa5A-Za-z0-9\s]+?)(集合|見面|碰面|會合)',
        r'集合.*?([\u4e00-\u9fa5A-Za-z0-9\s]+?)(\s|，|,|。|！|！|$)',
        r'([\u4e00-\u9fa5A-Za-z0-9\s]{2,10})(車站|寺|公園|廣場|商場|大樓|塔|橋|市場|通|町|村|城|館|園|山|湖|溫泉)'
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, user_message)
        if match:
            location = match.group(1) if '集合' not in match.group(1) else match.group(2)
            # 清理地點名稱
            location = location.strip()
            if len(location) >= 2:  # 至少2個字符
                return location
    
    # 如果還是找不到，嘗試提取中文地名
    chinese_location_match = re.search(r'([\u4e00-\u9fa5]{2,10})', user_message)
    if chinese_location_match:
        return chinese_location_match.group(1)
    
    return None

def find_location_trips(user_message):
    """根據用戶訊息查找地區相關行程"""
    from api.database_utils import get_trips_by_location
    
    # 簡單的地區關鍵字匹配
    location_keywords = {
        "北海道": ["北海道", "hokkaido", "Hokkaido", "HOKKAIDO"],
        "東京": ["東京", "tokyo", "Tokyo", "TOKYO"],
        "大阪": ["大阪", "osaka", "Osaka", "OSAKA"],
        "京都": ["京都", "kyoto", "Kyoto", "KYOTO"],
        "大版": ["大版", "osaka", "Osaka", "OSAKA"],  # 修正錯字
        "tokyo": ["tokyo", "Tokyo", "TOKYO", "東京"]
    }
    
    for location, keywords in location_keywords.items():
        for keyword in keywords:
            if keyword in user_message:
                # 從資料庫查詢該地區的行程
                trips = get_trips_by_location(location, limit=5)
                return location, trips
    
    return None, []

def find_trip_by_id(trip_id):
    """根據ID查找行程（使用緩存）"""
    try:
        trip_id_int = int(trip_id)
        return get_cached_trip_details(trip_id_int)
    except (ValueError, TypeError):
        logger.error(f"無效的行程ID: {trip_id}")
        return None

# 緩存系統
_leaderboard_cache = None
_leaderboard_cache_timestamp = 0
_rank_details_cache = {}  # 存儲不同排名的詳細資料
_rank_details_cache_timestamp = {}
_trip_details_cache = {}  # 存儲行程詳細資料
_trip_details_cache_timestamp = {}

CACHE_DURATION = 300  # 5分鐘緩存
DETAILS_CACHE_DURATION = 600  # 詳細資料緩存10分鐘（更新頻率較低）

def get_leaderboard_data():
    """從資料庫獲取排行榜資料"""
    global _leaderboard_cache, _leaderboard_cache_timestamp

    # 檢查緩存是否有效
    current_time = time.time()
    if _leaderboard_cache and (current_time - _leaderboard_cache_timestamp) < CACHE_DURATION:
        logger.info("使用緩存的排行榜資料")
        return _leaderboard_cache
    
    try:
        # 從資料庫獲取排行榜資料
        from api.database_utils import get_leaderboard_from_database
        leaderboard_data = get_leaderboard_from_database()
        
        if leaderboard_data:
            # 更新緩存
            _leaderboard_cache = leaderboard_data
            _leaderboard_cache_timestamp = current_time
            
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

def get_cached_rank_details(rank: int):
    """獲取緩存的排行榜詳細資料"""
    global _rank_details_cache, _rank_details_cache_timestamp

    current_time = time.time()
    cache_key = str(rank)

    # 檢查緩存是否有效
    if (cache_key in _rank_details_cache and
        cache_key in _rank_details_cache_timestamp and
        (current_time - _rank_details_cache_timestamp[cache_key]) < DETAILS_CACHE_DURATION):
        logger.info(f"使用緩存的第{rank}名詳細資料")
        return _rank_details_cache[cache_key]

    # 緩存無效，從資料庫獲取
    try:
        from api.database_utils import get_leaderboard_rank_details
        rank_data = get_leaderboard_rank_details(rank)

        if rank_data:
            # 更新緩存
            _rank_details_cache[cache_key] = rank_data
            _rank_details_cache_timestamp[cache_key] = current_time
            logger.info(f"成功獲取並緩存第{rank}名詳細資料")
            return rank_data
        else:
            logger.warning(f"無法獲取第{rank}名詳細資料")
            return None

    except Exception as e:
        logger.error(f"獲取第{rank}名詳細資料失敗: {e}")
        return None

def get_cached_trip_details(trip_id: int):
    """獲取緩存的行程詳細資料"""
    global _trip_details_cache, _trip_details_cache_timestamp

    current_time = time.time()
    cache_key = str(trip_id)

    # 檢查緩存是否有效
    if (cache_key in _trip_details_cache and
        cache_key in _trip_details_cache_timestamp and
        (current_time - _trip_details_cache_timestamp[cache_key]) < DETAILS_CACHE_DURATION):
        logger.info(f"使用緩存的行程{trip_id}詳細資料")
        return _trip_details_cache[cache_key]

    # 緩存無效，從資料庫獲取
    try:
        from api.database_utils import get_trip_details_by_id
        trip_data = get_trip_details_by_id(trip_id)

        if trip_data:
            # 更新緩存
            _trip_details_cache[cache_key] = trip_data
            _trip_details_cache_timestamp[cache_key] = current_time
            logger.info(f"成功獲取並緩存行程{trip_id}詳細資料")
            return trip_data
        else:
            logger.warning(f"無法獲取行程{trip_id}詳細資料")
            return None

    except Exception as e:
        logger.error(f"獲取行程{trip_id}詳細資料失敗: {e}")
        return None

def warm_up_cache():
    """預熱緩存 - 預先加載常用資料"""
    logger.info("開始預熱緩存...")

    try:
        # 預熱排行榜資料
        get_leaderboard_data()

        # 預熱前3名的詳細資料
        for rank in range(1, 4):
            get_cached_rank_details(rank)

        logger.info("緩存預熱完成")
    except Exception as e:
        logger.error(f"緩存預熱失敗: {e}")

# 集合管理函數已整合到 meeting_manager 中

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

def reminder_callback_handler(reminder_data):
    """
    處理集合管理器的提醒回調
    """
    try:
        user_id = reminder_data.get('user_id')
        meeting_time = reminder_data.get('meeting_time')
        meeting_location = reminder_data.get('meeting_location')
        reminder_type = reminder_data.get('reminder_type')

        if all([user_id, meeting_time, meeting_location, reminder_type]):
            send_reminder_message(user_id, meeting_time, meeting_location, reminder_type)
            logger.info(f"成功處理提醒回調: {reminder_type} for user {user_id}")
        else:
            logger.error(f"提醒回調資料不完整: {reminder_data}")

    except Exception as e:
        logger.error(f"處理提醒回調失敗: {str(e)}")

# 環境變數檢查
CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.environ.get('CHANNEL_SECRET')

if CHANNEL_ACCESS_TOKEN and CHANNEL_SECRET:
    configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
    line_handler = WebhookHandler(CHANNEL_SECRET)

    # 設定集合管理器的提醒回調
    meeting_manager.set_reminder_callback(reminder_callback_handler)

    # 預熱緩存以提高響應速度
    warm_up_cache()

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
                    # 使用集合管理系統
                    success, message, meeting_id = meeting_manager.create_meeting(
                        user_id=event.source.user_id,
                        meeting_time=meeting_time,
                        meeting_location=meeting_location
                    )

                    # 創建回應訊息
                    flex_message = create_flex_message(
                        "meeting_success",
                        meeting_time=meeting_time,
                        meeting_location=meeting_location,
                        meeting_id=meeting_id,
                        is_success=success
                    )
                    
                    with ApiClient(configuration) as api_client:
                        line_bot_api = MessagingApi(api_client)
                        line_bot_api.reply_message_with_http_info(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[FlexMessage(alt_text="集合設定", contents=FlexContainer.from_dict(flex_message))]
                            )
                        )
                    
                    # 記錄結果
                    if success:
                        logger.info(f"成功設定集合: {meeting_time} @ {meeting_location}, TourClock ID: {meeting_id}")
                    else:
                        logger.warning(f"集合設定失敗: {message}")
                        
                elif meeting_time and not meeting_location:
                    # 只有時間沒有地點
                    flex_message = {
                        "type": "bubble",
                        "size": "kilo",
                        "header": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "⏰ 集合時間已識別",
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
                                    "type": "text",
                                    "text": f"✅ 時間：{meeting_time}",
                                    "size": "md",
                                    "color": "#27AE60",
                                    "margin": "md"
                                },
                                {
                                    "type": "text",
                                    "text": "❌ 地點：未識別",
                                    "size": "md",
                                    "color": "#E74C3C",
                                    "margin": "sm"
                                },
                                {
                                    "type": "text",
                                    "text": "請明確指定集合地點，例如：淺草寺、新宿車站等",
                                    "size": "sm",
                                    "color": "#888888",
                                    "wrap": True,
                                    "margin": "md"
                                }
                            ],
                            "paddingAll": "20px"
                        }
                    }
                    
                    with ApiClient(configuration) as api_client:
                        line_bot_api = MessagingApi(api_client)
                        line_bot_api.reply_message_with_http_info(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[FlexMessage(alt_text="集合設定", contents=FlexContainer.from_dict(flex_message))]
                            )
                        )
                        
                elif meeting_location and not meeting_time:
                    # 只有地點沒有時間
                    flex_message = {
                        "type": "bubble",
                        "size": "kilo",
                        "header": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "📍 集合地點已識別",
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
                                    "type": "text",
                                    "text": "❌ 時間：未識別",
                                    "size": "md",
                                    "color": "#E74C3C",
                                    "margin": "md"
                                },
                                {
                                    "type": "text",
                                    "text": f"✅ 地點：{meeting_location}",
                                    "size": "md",
                                    "color": "#27AE60",
                                    "margin": "sm"
                                },
                                {
                                    "type": "text",
                                    "text": "請明確指定集合時間，例如：下午2:35、14:35、2點35分等",
                                    "size": "sm",
                                    "color": "#888888",
                                    "wrap": True,
                                    "margin": "md"
                                }
                            ],
                            "paddingAll": "20px"
                        }
                    }
                    
                    with ApiClient(configuration) as api_client:
                        line_bot_api = MessagingApi(api_client)
                        line_bot_api.reply_message_with_http_info(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[FlexMessage(alt_text="集合設定", contents=FlexContainer.from_dict(flex_message))]
                            )
                        )
                else:
                    # 時間和地點都沒有識別到
                    flex_message = {
                        "type": "bubble",
                        "size": "kilo",
                        "header": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "📝 集合設定說明",
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
                                    "type": "text",
                                    "text": "請輸入包含時間和地點的集合資訊，例如：",
                                    "size": "md",
                                    "color": "#555555",
                                    "margin": "md"
                                },
                                {
                                    "type": "text",
                                    "text": "• 下午2:35 淺草寺集合\n• 14:30 新宿車站見面\n• 明天3點 澀谷集合\n• 晚上7點 銀座碰面",
                                    "size": "sm",
                                    "color": "#888888",
                                    "wrap": True,
                                    "margin": "sm"
                                }
                            ],
                            "paddingAll": "20px"
                        }
                    }
                    
                    with ApiClient(configuration) as api_client:
                        line_bot_api = MessagingApi(api_client)
                        line_bot_api.reply_message_with_http_info(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[FlexMessage(alt_text="集合設定說明", contents=FlexContainer.from_dict(flex_message))]
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
                        elif template_config["template"] == "leaderboard_details":
                            # 獲取排行榜詳細行程資料（使用緩存）
                            rank = int(template_config["rank"])
                            rank_data = get_cached_rank_details(rank)

                            flex_message = create_flex_message(
                                "leaderboard_details",
                                rank_data=rank_data
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
            
            # 處理查看集合列表
            elif postback_data == "view_meetings":
                user_id = event.source.user_id
                meetings = meeting_manager.get_user_meetings(user_id)
                
                if meetings:
                    # 創建集合列表 Flex Message
                    flex_message = create_meeting_list_message(meetings)
                    
                    with ApiClient(configuration) as api_client:
                        line_bot_api = MessagingApi(api_client)
                        line_bot_api.reply_message_with_http_info(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[FlexMessage(alt_text="我的集合列表", contents=FlexContainer.from_dict(flex_message))]
                            )
                        )
                else:
                    # 沒有集合時的回應
                    flex_message = {
                        "type": "bubble",
                        "size": "kilo",
                        "header": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "📝 我的集合",
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
                                    "type": "text",
                                    "text": "目前沒有設定任何集合",
                                    "size": "md",
                                    "color": "#555555",
                                    "align": "center",
                                    "margin": "md"
                                },
                                {
                                    "type": "text",
                                    "text": "試試輸入「下午2:35 淺草寺集合」來設定您的第一個集合！",
                                    "size": "sm",
                                    "color": "#888888",
                                    "align": "center",
                                    "wrap": True,
                                    "margin": "sm"
                                }
                            ],
                            "paddingAll": "20px"
                        }
                    }
                    
                    with ApiClient(configuration) as api_client:
                        line_bot_api = MessagingApi(api_client)
                        line_bot_api.reply_message_with_http_info(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[FlexMessage(alt_text="我的集合", contents=FlexContainer.from_dict(flex_message))]
                            )
                        )
            
            # 處理取消集合
            elif postback_data.startswith("cancel_meeting:"):
                meeting_id = int(postback_data.split(":")[1])
                user_id = event.source.user_id
                
                success, message = meeting_manager.cancel_meeting(meeting_id, user_id)
                
                if success:
                    flex_message = {
                        "type": "bubble",
                        "size": "kilo",
                        "header": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "✅ 集合已取消",
                                    "weight": "bold",
                                    "size": "lg",
                                    "color": "#ffffff",
                                    "align": "center"
                                }
                            ],
                            "backgroundColor": "#27AE60",
                            "paddingAll": "20px"
                        },
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": message,
                                    "size": "md",
                                    "color": "#555555",
                                    "align": "center",
                                    "margin": "md"
                                }
                            ],
                            "paddingAll": "20px"
                        }
                    }
                else:
                    flex_message = {
                        "type": "bubble",
                        "size": "kilo",
                        "header": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "❌ 取消失敗",
                                    "weight": "bold",
                                    "size": "lg",
                                    "color": "#ffffff",
                                    "align": "center"
                                }
                            ],
                            "backgroundColor": "#E74C3C",
                            "paddingAll": "20px"
                        },
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": message,
                                    "size": "md",
                                    "color": "#555555",
                                    "align": "center",
                                    "margin": "md"
                                }
                            ],
                            "paddingAll": "20px"
                        }
                    }
                
                with ApiClient(configuration) as api_client:
                    line_bot_api = MessagingApi(api_client)
                    line_bot_api.reply_message_with_http_info(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[FlexMessage(alt_text="取消集合", contents=FlexContainer.from_dict(flex_message))]
                        )
                    )
            
        except Exception as e:
            logger.error(f"Postback error: {str(e)}")

# Vercel 會自動檢測名為 'app' 的 Flask 實例
# 確保 app 在模組級別可用

# 為了兼容性，保留原有的條件
if __name__ == "__main__":
    # 本地開發時
    app.run(debug=True, port=5000)