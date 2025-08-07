from flask import Flask, request, abort
import os
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加載環境變數
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("環境變數文件已加載")
except ImportError:
    logger.warning("python-dotenv 未安裝，跳過 .env 文件加載")
except Exception as e:
    logger.error(f"加載環境變數失敗: {e}")

# 導入配置文件
from api.config import (
    MESSAGE_TEMPLATES,
    KEYWORD_MAPPINGS
)

# 導入資料庫功能
from api.database import (
    get_leaderboard_data,
    get_trip_details,
    get_trips_by_location,
    get_leaderboard_rank_details,
    get_simple_itinerary_by_rank
)

# LINE Bot imports
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    FlexMessage,
    FlexContainer
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

# 建立 Flask app
app = Flask(__name__)

def get_message_template(user_message):
    """根據用戶消息獲取對應的模板配置"""
    # 按關鍵字長度排序，優先匹配更具體的關鍵字
    all_mappings = []

    for mapping_key, mapping in KEYWORD_MAPPINGS.items():
        for keyword in mapping["keywords"]:
            if keyword in user_message:
                all_mappings.append((len(keyword), mapping))

    # 如果有匹配，返回最長的關鍵字對應的模板
    if all_mappings:
        all_mappings.sort(key=lambda x: x[0], reverse=True)  # 按長度降序排列
        return all_mappings[0][1]

    return None

def create_simple_flex_message(template_type, **kwargs):
    """創建簡單的 Flex Message"""
    
    if template_type == "feature":
        feature_name = kwargs.get('feature_name')
        if feature_name in MESSAGE_TEMPLATES["features"]:
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
    
    elif template_type == "help":
        template = MESSAGE_TEMPLATES["help"]
        
        feature_contents = []
        for feature in template["features"]:
            feature_contents.append({
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
    
    elif template_type == "leaderboard":
        # 從資料庫獲取排行榜詳細資料
        rank = kwargs.get('rank', '1')
        rank_int = int(rank)

        # 嘗試從資料庫獲取詳細資料
        data = get_leaderboard_rank_details(rank_int)

        if not data:
            # 如果資料庫失敗，使用配置文件的備用資料
            from api.config import LEADERBOARD_DATA
            data = LEADERBOARD_DATA.get(rank, LEADERBOARD_DATA["1"])

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
                                {"type": "text", "text": "❤️", "size": "md", "flex": 0},
                                {"type": "text", "text": f"收藏數：{data.get('favorite_count', 0)}", "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
                            ],
                            "marginBottom": "sm"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "⭐", "size": "md", "flex": 0},
                                {"type": "text", "text": f"人氣分數：{data.get('popularity_score', 0):.2f}", "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
                            ],
                            "marginBottom": "md"
                        },
                        {"type": "separator", "margin": "md"},
                        {"type": "text", "text": "📋 詳細行程安排", "weight": "bold", "size": "md", "color": "#555555", "margin": "md"},
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": data.get("itinerary", "精彩行程安排"),
                                    "size": "xs",
                                    "color": "#666666",
                                    "wrap": True,
                                    "lineSpacing": "sm"
                                }
                            ],
                            "backgroundColor": "#f8f9fa",
                            "cornerRadius": "md",
                            "paddingAll": "md",
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

    elif template_type == "leaderboard_list":
        # 排行榜列表模板 - 從資料庫獲取資料
        leaderboard_data = get_leaderboard_data()

        # 如果資料庫失敗，使用配置文件的備用資料
        if not leaderboard_data:
            from api.config import LEADERBOARD_DATA
            leaderboard_data = LEADERBOARD_DATA

        # 創建排行榜項目
        leaderboard_contents = []

        # 根據排名順序顯示前5名
        for rank in range(1, 6):
            rank_str = str(rank)
            if rank_str in leaderboard_data:
                data = leaderboard_data[rank_str]

                # 根據排名設定圖標
                rank_icons = {1: "🥇", 2: "🥈", 3: "🥉", 4: "🏅", 5: "🎖️"}
                icon = rank_icons.get(rank, "🏆")

                leaderboard_contents.append({
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": f"{icon} 第{rank}名",
                                    "weight": "bold",
                                    "size": "sm",
                                    "color": data["color"]
                                },
                                {
                                    "type": "text",
                                    "text": data.get('destination', '未知目的地'),
                                    "size": "xs",
                                    "color": "#666666",
                                    "marginTop": "xs"
                                },
                                {
                                    "type": "text",
                                    "text": f"⏰ {data.get('duration', '未知天數')}",
                                    "size": "xs",
                                    "color": "#888888",
                                    "marginTop": "xs"
                                }
                            ],
                            "flex": 1
                        }
                    ],
                    "paddingAll": "sm",
                    "backgroundColor": "#f8f9fa",
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
                        "text": "🏆 TourHub 排行榜",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#ffffff",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": "熱門旅遊行程排名",
                        "size": "sm",
                        "color": "#ffffff",
                        "align": "center",
                        "margin": "sm"
                    }
                ],
                "backgroundColor": "#FF6B6B",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": leaderboard_contents,
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
                        "color": "#FF6B6B",
                        "height": "sm"
                    }
                ],
                "paddingAll": "20px"
            }
        }

    elif template_type == "leaderboard_details":
        # 排行榜詳細行程模板 - 只顯示純粹的行程安排
        rank = kwargs.get('rank', '1')
        rank_int = int(rank)

        # 從資料庫獲取簡潔的行程安排
        data = get_simple_itinerary_by_rank(rank_int)

        if not data:
            # 如果沒有詳細行程，顯示提示訊息
            return {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"抱歉，第{rank}名的詳細行程安排暫時無法提供。",
                            "wrap": True,
                            "color": "#666666",
                            "align": "center"
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
                        "text": f"{data['rank_title']} 詳細行程",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#ffffff",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": f"{data['title']} - {data['area']}",
                        "size": "sm",
                        "color": "#ffffff",
                        "align": "center",
                        "margin": "sm"
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
                        "type": "text",
                        "text": "📅 行程安排",
                        "weight": "bold",
                        "size": "md",
                        "color": "#555555",
                        "marginBottom": "md"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": data["itinerary"],
                                "size": "sm",
                                "color": "#333333",
                                "wrap": True,
                                "lineSpacing": "md"
                            }
                        ],
                        "backgroundColor": "#f8f9fa",
                        "cornerRadius": "md",
                        "paddingAll": "md"
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
                        "text": "💡 想了解更多資訊？輸入對應排名查看完整介紹",
                        "size": "xs",
                        "color": "#666666",
                        "align": "center",
                        "wrap": True
                    }
                ],
                "paddingAll": "20px"
            }
        }

    elif template_type == "location_trips":
        # 地區行程查詢模板 - 從資料庫獲取資料
        location = kwargs.get('location', '未知地區')

        # 從資料庫獲取地區行程資料
        trips = get_trips_by_location(location)

        # 如果沒有找到資料，使用模擬資料
        if not trips:
            trips = [
                {
                    "title": f"{location}經典三日遊",
                    "duration": "3天2夜",
                    "highlights": "經典景點深度遊覽",
                    "id": "sample_1"
                },
                {
                    "title": f"{location}美食文化之旅",
                    "duration": "4天3夜",
                    "highlights": "品嚐當地特色美食",
                    "id": "sample_2"
                },
                {
                    "title": f"{location}自然風光探索",
                    "duration": "5天4夜",
                    "highlights": "欣賞自然美景",
                    "id": "sample_3"
                }
            ]

        # 創建行程內容
        trip_contents = []
        for trip in trips:
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
                    },
                    {
                        "type": "text",
                        "text": "為您精選的熱門行程",
                        "size": "sm",
                        "color": "#ffffff",
                        "align": "center",
                        "margin": "sm"
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
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "💡 更多行程請訪問我們的網站",
                        "size": "xs",
                        "color": "#666666",
                        "align": "center",
                        "wrap": True
                    }
                ],
                "paddingAll": "20px"
            }
        }

    # 預設錯誤訊息
    return {
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

# 健康檢查 API
@app.route('/api/health')
def health():
    return {
        "status": "running",
        "bot_configured": configuration is not None
    }

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
            logger.info(f"收到訊息: {user_message}")
            
            # 檢查模板匹配
            template_config = get_message_template(user_message)
            
            if template_config:
                logger.info(f"匹配到模板: {template_config['template']}")

                # 創建 Flex Message
                if template_config["template"] == "feature":
                    flex_message = create_simple_flex_message(
                        "feature",
                        feature_name=template_config["feature_name"]
                    )
                elif template_config["template"] == "leaderboard":
                    flex_message = create_simple_flex_message(
                        "leaderboard",
                        rank=template_config["rank"]
                    )
                elif template_config["template"] == "leaderboard_list":
                    flex_message = create_simple_flex_message("leaderboard_list")
                elif template_config["template"] == "leaderboard_details":
                    flex_message = create_simple_flex_message(
                        "leaderboard_details",
                        rank=template_config["rank"]
                    )
                elif template_config["template"] == "location_trips":
                    flex_message = create_simple_flex_message(
                        "location_trips",
                        location=template_config["location"]
                    )
                elif template_config["template"] == "help":
                    flex_message = create_simple_flex_message("help")
                elif template_config["template"] == "tour_clock":
                    # TourClock 使用 feature 模板
                    flex_message = create_simple_flex_message(
                        "feature",
                        feature_name="tour_clock"
                    )
                else:
                    # 預設回應
                    flex_message = create_simple_flex_message("default")
            else:
                logger.info("沒有匹配的模板，使用預設回應")
                flex_message = create_simple_flex_message("default")

            # 發送消息
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[FlexMessage(alt_text="TourHub Bot", contents=FlexContainer.from_dict(flex_message))]
                    )
                )
                logger.info("訊息發送成功")
                
        except Exception as e:
            logger.error(f"處理訊息錯誤: {str(e)}")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
