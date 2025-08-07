from flask import Flask, request, abort
import os
import logging
import re
import time

# 加載環境變數
try:
    from dotenv import load_dotenv
    load_dotenv()
    logging.info("環境變數文件已加載")
except ImportError:
    logging.warning("python-dotenv 未安裝，跳過 .env 文件加載")
except Exception as e:
    logging.error(f"加載環境變數失敗: {e}")

# 導入配置文件
from api.config import (
    MESSAGE_TEMPLATES,
    KEYWORD_MAPPINGS
)

# 導入統一用戶管理系統
from api.unified_user_manager import unified_user_manager
from api.website_proxy import website_proxy

# LINE Bot imports
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    # PushMessageRequest 和 TextMessage 已移除（集合功能不再需要）
    FlexMessage,
    FlexContainer
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, PostbackEvent

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 集合管理功能已移除

# 建立 Flask app
app = Flask(__name__)

# 集合相關函數已移除

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
                                "uri": "https://tourhub-ashy.vercel.app/"
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
                            "uri": "https://tourhub-ashy.vercel.app/"
                        },
                        "style": "primary",
                        "color": data["color"],
                        "height": "sm"
                    }
                ],
                "paddingAll": "20px"
            }
        }
    
    # 集合成功模板已移除
    
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



    elif template_type == "website_operations":
        line_user_id = kwargs.get('line_user_id')
        if line_user_id:
            return create_website_operations_message(line_user_id)
        else:
            return create_default_error_message("無法獲取用戶資訊")

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
                            "uri": "https://tourhub-ashy.vercel.app/"
                        },
                        "style": "primary",
                        "color": color,
                        "height": "sm"
                    }
                ],
                "paddingAll": "20px"
            }
        }

    # 創建行程成功模板已移除
    elif False:
        trip_data = kwargs.get('trip_data')

        if not trip_data:
            return {
                "type": "bubble",
                "size": "kilo",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "行程創建失敗，請稍後再試。",
                            "size": "sm",
                            "color": "#888888",
                            "align": "center",
                            "wrap": True
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
                        "text": "🎉 行程創建成功！",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#ffffff",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": trip_data.get('title', '未知行程'),
                        "size": "sm",
                        "color": "#ffffff",
                        "align": "center",
                        "margin": "sm"
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
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "🆔", "size": "md", "flex": 0},
                            {"type": "text", "text": f"行程編號：{trip_data.get('trip_id')}", "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
                        ],
                        "marginBottom": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "📍", "size": "md", "flex": 0},
                            {"type": "text", "text": f"目的地：{trip_data.get('area', '未指定')}", "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
                        ],
                        "marginBottom": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "📅", "size": "md", "flex": 0},
                            {"type": "text", "text": f"行程天數：{trip_data.get('duration_days')}天", "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
                        ],
                        "marginBottom": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "🗓️", "size": "md", "flex": 0},
                            {"type": "text", "text": f"開始日期：{trip_data.get('start_date')}", "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
                        ],
                        "marginBottom": "md"
                    },
                    {"type": "separator", "margin": "md"},
                    {
                        "type": "text",
                        "text": "💡 接下來您可以：",
                        "weight": "bold",
                        "size": "sm",
                        "color": "#555555",
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": f"• 輸入「{trip_data.get('title')}第一天詳細行程為...」來添加第一天的行程安排\n• 輸入「我的行程」查看所有創建的行程",
                        "size": "xs",
                        "color": "#666666",
                        "wrap": True,
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
                        "type": "text",
                        "text": "💡 輸入「我的行程」查看所有行程，或繼續添加詳細安排",
                        "size": "xs",
                        "color": "#666666",
                        "wrap": True,
                        "align": "center"
                    }
                ],
                "paddingAll": "20px"
            }
        }

    # 我的行程模板已移除
    elif False and template_type == "my_trips":
        trips = kwargs.get('trips', [])

        if not trips:
            return {
                "type": "bubble",
                "size": "kilo",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "您還沒有創建任何行程",
                            "size": "md",
                            "color": "#555555",
                            "align": "center",
                            "wrap": True
                        },
                        {
                            "type": "text",
                            "text": "試試輸入「創建日本沖繩三日遊」來創建您的第一個行程！",
                            "size": "sm",
                            "color": "#888888",
                            "align": "center",
                            "wrap": True,
                            "margin": "md"
                        }
                    ],
                    "paddingAll": "20px"
                }
            }

        # 構建行程列表內容
        trip_contents = []
        for i, trip in enumerate(trips[:5]):  # 最多顯示5個行程
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
                                "text": f"📍 {trip['area']} • ⏰ {trip['duration']}",
                                "size": "xs",
                                "color": "#888888",
                                "marginTop": "sm"
                            },
                            {
                                "type": "text",
                                "text": f"📝 已添加 {trip['detail_count']} 個詳細行程",
                                "size": "xs",
                                "color": "#888888",
                                "marginTop": "xs"
                            }
                        ],
                        "flex": 1
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "查看",
                            "data": f"trip_detail:{trip['trip_id']}"
                        },
                        "style": "primary",
                        "color": "#3498DB",
                        "height": "sm",
                        "marginStart": "md"
                    }
                ],
                "paddingAll": "md",
                "backgroundColor": "#F8F9FA" if i % 2 == 0 else "#FFFFFF",
                "cornerRadius": "md",
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
                        "text": "📋 我的行程",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#ffffff",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": f"共 {len(trips)} 個行程",
                        "size": "sm",
                        "color": "#ffffff",
                        "align": "center",
                        "margin": "sm"
                    }
                ],
                "backgroundColor": "#3498DB",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": trip_contents,
                "paddingAll": "20px"
            }
        }

    # 添加詳細行程成功模板已移除
    elif False and template_type == "add_detail_success":
        detail_data = kwargs.get('detail_data')

        if not detail_data:
            return {
                "type": "bubble",
                "size": "kilo",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "添加行程詳細失敗，請稍後再試。",
                            "size": "sm",
                            "color": "#888888",
                            "align": "center",
                            "wrap": True
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
                        "text": "✅ 行程詳細添加成功！",
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
                        "text": f"第{detail_data.get('day_number')}天行程",
                        "weight": "bold",
                        "size": "md",
                        "color": "#555555"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "📅", "size": "md", "flex": 0},
                            {"type": "text", "text": detail_data.get('date'), "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
                        ],
                        "marginTop": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "⏰", "size": "md", "flex": 0},
                            {"type": "text", "text": f"{detail_data.get('start_time')} - {detail_data.get('end_time')}", "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
                        ],
                        "marginTop": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "📍", "size": "md", "flex": 0},
                            {"type": "text", "text": detail_data.get('location'), "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md", "wrap": True}
                        ],
                        "marginTop": "sm"
                    },
                    {"type": "separator", "margin": "md"},
                    {
                        "type": "text",
                        "text": "💡 繼續添加其他天的行程安排，或輸入「我的行程」查看完整行程。",
                        "size": "xs",
                        "color": "#666666",
                        "wrap": True,
                        "margin": "md"
                    }
                ],
                "paddingAll": "20px"
            }
        }

    # 查看行程詳細模板已移除
    elif False and template_type == "view_trip_details":
        trip_data = kwargs.get('trip_data')

        if not trip_data:
            return {
                "type": "bubble",
                "size": "kilo",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "找不到該行程，請確認行程名稱是否正確。",
                            "size": "sm",
                            "color": "#888888",
                            "align": "center",
                            "wrap": True
                        }
                    ],
                    "paddingAll": "20px"
                }
            }

        # 構建詳細行程內容
        detail_contents = []
        details = trip_data.get('details', [])

        if details:
            for i, detail in enumerate(details):
                if i > 0:
                    detail_contents.append({
                        "type": "separator",
                        "margin": "md"
                    })

                # 日期
                if detail.get('date'):
                    detail_contents.append({
                        "type": "text",
                        "text": detail['date'],
                        "size": "sm",
                        "color": "#333333",
                        "weight": "bold",
                        "margin": "md"
                    })

                # 時間
                if detail.get('time'):
                    detail_contents.append({
                        "type": "text",
                        "text": detail['time'],
                        "size": "sm",
                        "color": "#666666",
                        "margin": "xs"
                    })

                # 地點
                if detail.get('location'):
                    detail_contents.append({
                        "type": "text",
                        "text": detail['location'],
                        "size": "sm",
                        "color": "#444444",
                        "margin": "xs",
                        "wrap": True
                    })
        else:
            detail_contents.append({
                "type": "text",
                "text": "尚未添加詳細行程安排",
                "size": "sm",
                "color": "#888888",
                "align": "center",
                "margin": "md"
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
                        "text": "📋 行程詳細",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#ffffff",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": trip_data.get('title', '未知行程'),
                        "size": "sm",
                        "color": "#ffffff",
                        "align": "center",
                        "margin": "sm"
                    }
                ],
                "backgroundColor": "#3498DB",
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
                            {"type": "text", "text": f"目的地：{trip_data.get('area', '未知')}", "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
                        ],
                        "marginBottom": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "🗓️", "size": "md", "flex": 0},
                            {"type": "text", "text": f"日期：{trip_data.get('start_date')} ~ {trip_data.get('end_date')}", "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
                        ],
                        "marginBottom": "md"
                    },
                    {"type": "separator", "margin": "md"},
                    {
                        "type": "text",
                        "text": "📅 詳細行程安排",
                        "weight": "bold",
                        "size": "md",
                        "color": "#555555",
                        "margin": "md"
                    },
                    *detail_contents
                ],
                "paddingAll": "20px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"💡 輸入「{trip_data.get('title')}第X天詳細行程為...」來添加更多行程安排",
                        "size": "xs",
                        "color": "#666666",
                        "wrap": True,
                        "align": "center"
                    }
                ],
                "paddingAll": "20px"
            }
        }

    # 編輯行程成功模板已移除
    elif False and template_type == "edit_trip_success":
        old_title = kwargs.get('old_title')
        new_title = kwargs.get('new_title')

        return {
            "type": "bubble",
            "size": "kilo",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "✅ 行程標題更新成功！",
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
                        "text": f"原標題：{old_title}",
                        "size": "sm",
                        "color": "#666666",
                        "wrap": True
                    },
                    {
                        "type": "text",
                        "text": f"新標題：{new_title}",
                        "size": "sm",
                        "color": "#333333",
                        "weight": "bold",
                        "wrap": True,
                        "margin": "sm"
                    }
                ],
                "paddingAll": "20px"
            }
        }

    # 刪除行程成功模板已移除
    elif False and template_type == "delete_trip_success":
        trip_info = kwargs.get('trip_info')

        return {
            "type": "bubble",
            "size": "kilo",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🗑️ 行程刪除成功",
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
                        "text": f"已刪除行程：{trip_info.get('title')}",
                        "size": "sm",
                        "color": "#333333",
                        "wrap": True
                    },
                    {
                        "type": "text",
                        "text": f"包含 {trip_info.get('deleted_details', 0)} 個詳細行程項目",
                        "size": "xs",
                        "color": "#666666",
                        "margin": "sm"
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

# 集合時間解析函數已移除

# 集合地點解析函數已移除

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

# 獨立行程管理解析函數已移除

def create_default_error_message(error_text: str) -> dict:
    """創建預設錯誤訊息"""
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"❌ {error_text}",
                    "wrap": True,
                    "color": "#E74C3C",
                    "size": "sm"
                }
            ],
            "paddingAll": "20px"
        }
    }

def create_website_operations_message(line_user_id: str) -> dict:
    """創建網站操作訊息"""
    # 獲取用戶資料和綁定狀態
    user_data = unified_user_manager.get_user_by_line_id(line_user_id)
    bindings = unified_user_manager.get_user_website_bindings(line_user_id)
    available_modules = unified_user_manager.get_available_modules()

    if not user_data or not user_data.get('is_verified'):
        # 用戶未綁定，提示先綁定
        return {
            "type": "bubble",
            "size": "giga",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🔐 需要先綁定帳號",
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
                        "text": "請先完成帳號綁定，才能使用網站操作功能。",
                        "wrap": True,
                        "color": "#666666",
                        "size": "sm",
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": "輸入「綁定帳號」開始綁定流程",
                        "wrap": True,
                        "color": "#00B900",
                        "size": "sm",
                        "weight": "bold",
                        "margin": "md"
                    }
                ],
                "paddingAll": "20px"
            }
        }

    # 創建操作按鈕
    operation_contents = []

    for module in available_modules:
        is_bound = any(b['module_id'] == module['id'] for b in bindings)
        if is_bound:
            operation_contents.append({
                "type": "button",
                "action": {
                    "type": "postback",
                    "label": f"🌐 {module['module_display_name']}",
                    "data": f"website_operation:{module['module_name']}"
                },
                "style": "primary",
                "color": "#00B900",
                "height": "sm",
                "margin": "sm"
            })

    if not operation_contents:
        operation_contents.append({
            "type": "text",
            "text": "目前沒有可用的網站操作",
            "color": "#888888",
            "size": "sm",
            "align": "center"
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
                    "text": "🌐 網站操作",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#ffffff",
                    "align": "center"
                },
                {
                    "type": "text",
                    "text": f"歡迎 {user_data.get('display_name', '用戶')}",
                    "size": "sm",
                    "color": "#ffffff",
                    "align": "center",
                    "margin": "sm"
                }
            ],
            "backgroundColor": "#00B900",
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "選擇要操作的網站：",
                    "weight": "bold",
                    "size": "md",
                    "color": "#333333",
                    "margin": "md"
                }
            ] + operation_contents,
            "paddingAll": "20px"
        }
    }

# 查看行程解析函數已移除

# 編輯行程解析函數已移除

# 刪除行程解析函數已移除

# 移除用戶資料獲取功能 - LINE Bot 現在專注於行程管理，不需要用戶資料同步

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

# 集合管理和提醒功能已移除

# 環境變數檢查
CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.environ.get('CHANNEL_SECRET')

if CHANNEL_ACCESS_TOKEN and CHANNEL_SECRET:
    configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
    line_handler = WebhookHandler(CHANNEL_SECRET)

    # 初始化數據庫連接池
    try:
        from api.database_utils import initialize_connection_pool
        if initialize_connection_pool():
            logger.info("數據庫連接池初始化成功")
        else:
            logger.warning("數據庫連接池初始化失敗")
    except Exception as e:
        logger.error(f"數據庫連接池初始化錯誤: {e}")

    # 運行數據庫優化（僅在生產環境）
    try:
        if os.environ.get('ENVIRONMENT') == 'production':
            from api.database_optimization import run_database_optimization
            run_database_optimization()
    except Exception as e:
        logger.warning(f"數據庫優化失敗: {e}")

    # 預熱緩存以提高響應速度（使用安全模式）
    try:
        # 先嘗試基礎緩存預熱
        warm_up_cache()
        logger.info("基礎緩存預熱完成")

        # 然後嘗試高級功能（如果失敗不影響主要功能）
        try:
            from api.advanced_cache import warm_up_cache_advanced
            warm_up_cache_advanced()
            logger.info("高級緩存預熱完成")
        except Exception as e:
            logger.warning(f"高級緩存預熱失敗（不影響主要功能）: {e}")

        # 異步預加載（如果失敗不影響主要功能）
        try:
            from api.async_processor import preload_data
            preload_data()
            logger.info("異步預加載完成")
        except Exception as e:
            logger.warning(f"異步預加載失敗（不影響主要功能）: {e}")

        logger.info("所有優化系統已啟動")
    except Exception as e:
        logger.error(f"緩存預熱失敗: {e}")
        logger.info("跳過緩存預熱，使用基本模式")

    logger.info("LINE Bot 設定成功")
else:
    configuration = None
    line_handler = None
    logger.warning("LINE Bot 環境變數未設定")

# 排行榜頁面
@app.route('/')
def leaderboard():
    """排行榜主頁面"""
    return {"message": "TourHub Line Bot API", "status": "running"}

# 健康檢查 API
@app.route('/api/health')
def health():
    return {
        "status": "running",
        "bot_configured": configuration is not None
    }

# 緩存統計 API
@app.route('/api/cache/stats')
def cache_stats():
    """獲取緩存統計信息"""
    try:
        from api.advanced_cache import get_cache_stats
        stats = get_cache_stats()
        return {
            "status": "success",
            "cache_stats": stats
        }
    except Exception as e:
        logger.error(f"獲取緩存統計失敗: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

# 清空緩存 API
@app.route('/api/cache/clear', methods=['POST'])
def clear_cache_api():
    """清空所有緩存"""
    try:
        from api.advanced_cache import clear_cache
        clear_cache()
        return {
            "status": "success",
            "message": "緩存已清空"
        }
    except Exception as e:
        logger.error(f"清空緩存失敗: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

# 性能統計 API
@app.route('/api/performance/stats')
def performance_stats():
    """獲取性能統計信息"""
    try:
        from api.performance_monitor import get_performance_stats
        stats = get_performance_stats()
        return {
            "status": "success",
            "performance_stats": stats
        }
    except Exception as e:
        logger.error(f"獲取性能統計失敗: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

# 健康檢查 API
@app.route('/api/health/detailed')
def detailed_health():
    """詳細健康檢查"""
    try:
        from api.performance_monitor import get_health_status
        health = get_health_status()
        return {
            "status": "success",
            "health": health
        }
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

# 移除所有網頁相關的 API 端點
# LINE Bot 現在完全獨立運作，不需要網頁整合



# 除錯端點
@app.route('/debug')
def debug():
    return {
        "has_token": bool(CHANNEL_ACCESS_TOKEN),
        "has_secret": bool(CHANNEL_SECRET),
        "token_length": len(CHANNEL_ACCESS_TOKEN) if CHANNEL_ACCESS_TOKEN else 0
    }







# 提醒回調端點已移除

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
        from api.performance_monitor import monitor_performance

        @monitor_performance("line_message_handler")
        def _handle_message_with_monitoring():
            return _process_message(event)

        try:
            return _handle_message_with_monitoring()
        except Exception as e:
            logger.error(f"訊息處理錯誤: {str(e)}")

    def _process_message(event):
        """處理訊息的核心邏輯"""
        try:
            user_message = event.message.text
            
            # 獨立行程管理功能已移除，保留關鍵字跳轉功能
            # 檢查模板匹配
            template_config = get_message_template(user_message)

            if template_config:
                # 使用優化的模板系統創建 Flex Message
                try:
                    from api.flex_templates import create_optimized_flex_message
                    from api.config import MESSAGE_TEMPLATES

                    if template_config["template"] == "feature":
                        feature_name = template_config["feature_name"]
                        template_data = MESSAGE_TEMPLATES["features"][feature_name]
                        flex_message = create_optimized_flex_message("feature", **template_data)

                    elif template_config["template"] == "tour_clock":
                        # TourClock 集合功能
                        template_data = MESSAGE_TEMPLATES["features"]["tour_clock"]
                        flex_message = create_optimized_flex_message("feature", **template_data)

                    elif template_config["template"] == "location_trips":
                        # 地區行程查詢
                        location = template_config.get("location", "未知地區")
                        try:
                            from api.database_utils import get_trips_by_location
                            trips = get_trips_by_location(location, 5)
                            flex_message = create_optimized_flex_message("location_trips",
                                trips=trips, location=location)
                        except Exception as e:
                            logger.error(f"獲取 {location} 行程失敗: {e}")
                            flex_message = create_optimized_flex_message("error",
                                message=f"抱歉，獲取 {location} 行程時發生錯誤，請稍後再試。")

                    elif template_config["template"] == "leaderboard":
                        rank = template_config["rank"]
                        rank_data = get_cached_rank_details(int(rank))
                        if rank_data:
                            flex_message = create_optimized_flex_message("leaderboard", **rank_data)
                        else:
                            flex_message = create_optimized_flex_message("error",
                                message=f"無法獲取第{rank}名的資料")

                    elif template_config["template"] == "leaderboard_details":
                        rank = int(template_config["rank"])
                        rank_data = get_cached_rank_details(rank)
                        if rank_data:
                            flex_message = create_flex_message("leaderboard_details", rank_data=rank_data)
                        else:
                            flex_message = create_optimized_flex_message("error",
                                message=f"無法獲取第{rank}名的詳細資料")

                    elif template_config["template"] == "help":
                        flex_message = create_flex_message("help")

                    else:
                        # 使用舊的創建方式作為後備
                        flex_message = create_flex_message(
                            template_config["template"],
                            **template_config
                        )

                except Exception as e:
                    logger.error(f"優化模板創建失敗，使用舊版本: {e}")
                    # 後備到舊的模板系統
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
                    else:
                        flex_message = create_flex_message(template_config["template"])
                else:
                    # 預設回應
                    flex_message = {
                        "type": "bubble",
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "抱歉，我不太理解您的訊息。請嘗試輸入「功能介紹」查看可用功能。",
                                    "wrap": True,
                                    "color": "#666666"
                                }
                            ],
                            "paddingAll": "20px"
                        }
                    }

                # 發送消息
                with ApiClient(configuration) as api_client:
                    line_bot_api = MessagingApi(api_client)
                    line_bot_api.reply_message_with_http_info(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[FlexMessage(alt_text="TourHub Bot", contents=FlexContainer.from_dict(flex_message))]
                        )
                    )
            else:
                # 沒有匹配的模板，發送預設回應
                flex_message = {
                    "type": "bubble",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "抱歉，我不太理解您的訊息。請嘗試輸入「功能介紹」查看可用功能。",
                                "wrap": True,
                                "color": "#666666"
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
                            messages=[FlexMessage(alt_text="TourHub Bot", contents=FlexContainer.from_dict(flex_message))]
                        )
                    )
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

            # 處理網站操作
            elif postback_data.startswith("website_operation:"):
                module_name = postback_data.split(":")[1]
                line_user_id = event.source.user_id

                # 創建網站操作選單
                flex_message = create_website_operation_menu(line_user_id, module_name)

                with ApiClient(configuration) as api_client:
                    line_bot_api = MessagingApi(api_client)
                    line_bot_api.reply_message_with_http_info(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[FlexMessage(alt_text=f"{module_name} 操作選單", contents=FlexContainer.from_dict(flex_message))]
                        )
                    )

            # 處理具體的網站操作
            elif postback_data.startswith("execute_operation:"):
                parts = postback_data.split(":")
                if len(parts) >= 3:
                    module_name = parts[1]
                    operation = parts[2]
                    line_user_id = event.source.user_id

                    # 執行操作
                    result = website_proxy.execute_operation(line_user_id, module_name, operation)

                    # 創建結果訊息
                    if result.get('success'):
                        flex_message = create_operation_success_message(module_name, operation, result.get('data'))
                    else:
                        flex_message = create_operation_error_message(module_name, operation, result.get('error'))

                    with ApiClient(configuration) as api_client:
                        line_bot_api = MessagingApi(api_client)
                        line_bot_api.reply_message_with_http_info(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[FlexMessage(alt_text="操作結果", contents=FlexContainer.from_dict(flex_message))]
                            )
                        )

            # 集合相關的postback處理已移除
            
        except Exception as e:
            logger.error(f"Postback error: {str(e)}")

# Vercel 會自動檢測名為 'app' 的 Flask 實例
# 確保 app 在模組級別可用

def create_website_operation_menu(line_user_id: str, module_name: str) -> dict:
    """創建網站操作選單"""
    # 根據不同模組創建不同的操作選單
    module_operations = {
        'tourhub_leaderboard': [
            {'name': '🏆 查看排行榜', 'operation': 'view_leaderboard'},
            {'name': '🔥 熱門行程', 'operation': 'get_top_trips'}
        ],
        'trip_management': [
            {'name': '📋 管理我的行程', 'operation': 'manage_trips'},
            {'name': '➕ 創建新行程', 'operation': 'create_new_trip'}
        ],
        'tour_clock': [
            {'name': '⏰ 管理集合時間', 'operation': 'manage_meetings'},
            {'name': '📅 創建新集合', 'operation': 'create_meeting'}
        ],
        'locker_finder': [
            {'name': '🔍 查找置物櫃', 'operation': 'find_lockers'},
            {'name': '📍 按地點搜尋', 'operation': 'search_by_location'}
        ],
        'bill_split': [
            {'name': '💰 管理分帳', 'operation': 'manage_bills'},
            {'name': '➕ 新建分帳', 'operation': 'create_bill'}
        ]
    }

    operations = module_operations.get(module_name, [])

    # 創建操作按鈕
    operation_buttons = []
    for op in operations:
        operation_buttons.append({
            "type": "button",
            "action": {
                "type": "postback",
                "label": op['name'],
                "data": f"execute_operation:{module_name}:{op['operation']}"
            },
            "style": "secondary",
            "height": "sm",
            "margin": "sm"
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
                    "text": f"🌐 {module_name.replace('_', ' ').title()}",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#ffffff",
                    "align": "center"
                },
                {
                    "type": "text",
                    "text": "選擇要執行的操作",
                    "size": "sm",
                    "color": "#ffffff",
                    "align": "center",
                    "margin": "sm"
                }
            ],
            "backgroundColor": "#00B900",
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": operation_buttons,
            "paddingAll": "20px"
        }
    }

def create_operation_success_message(module_name: str, operation: str, data: dict = None) -> dict:
    """創建操作成功訊息"""
    # 檢查是否需要跳轉到網站
    if data and data.get('action') == 'redirect':
        url = data.get('url')
        message = data.get('message', '正在為您開啟頁面...')

        return {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🌐 跳轉到網站",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#ffffff",
                        "align": "center"
                    }
                ],
                "backgroundColor": "#00B900",
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
                        "color": "#333333",
                        "align": "center",
                        "wrap": True,
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": "點擊下方按鈕開啟網站",
                        "size": "sm",
                        "color": "#666666",
                        "align": "center",
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
                            "label": "🚀 開啟網站",
                            "uri": url
                        },
                        "style": "primary",
                        "color": "#00B900",
                        "height": "sm"
                    }
                ],
                "paddingAll": "20px"
            }
        }

    # 一般操作成功訊息
    return {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "✅ 操作成功",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#ffffff",
                    "align": "center"
                }
            ],
            "backgroundColor": "#00B900",
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"模組：{module_name}",
                    "size": "sm",
                    "color": "#666666",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": f"操作：{operation}",
                    "size": "sm",
                    "color": "#666666",
                    "margin": "sm"
                },
                {
                    "type": "text",
                    "text": "操作已成功執行",
                    "size": "md",
                    "color": "#333333",
                    "weight": "bold",
                    "margin": "md"
                }
            ],
            "paddingAll": "20px"
        }
    }

def create_operation_error_message(module_name: str, operation: str, error: str) -> dict:
    """創建操作錯誤訊息"""
    return {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "❌ 操作失敗",
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
                    "text": f"模組：{module_name}",
                    "size": "sm",
                    "color": "#666666",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": f"操作：{operation}",
                    "size": "sm",
                    "color": "#666666",
                    "margin": "sm"
                },
                {
                    "type": "text",
                    "text": f"錯誤：{error}",
                    "size": "sm",
                    "color": "#E74C3C",
                    "wrap": True,
                    "margin": "md"
                }
            ],
            "paddingAll": "20px"
        }
    }

# 為了兼容性，保留原有的條件
if __name__ == "__main__":
    # 本地開發時
    app.run(debug=True, port=5000)