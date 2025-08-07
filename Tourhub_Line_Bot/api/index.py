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

# 導入網頁爬蟲功能
from api.web_scraper import (
    scrape_leaderboard_data,
    scrape_trip_details
)

# 導入分頁功能
from api.pagination import (
    create_paginated_leaderboard,
    create_paginated_itinerary
)

# 導入資料庫功能（作為備用）
try:
    from api.database import (
        get_leaderboard_data,
        get_trips_by_location
    )
except ImportError:
    logger.warning("資料庫模組導入失敗，將只使用網頁爬蟲")

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
from linebot.v3.webhooks import MessageEvent, TextMessageContent, PostbackEvent

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
        # 使用分頁系統顯示排行榜詳細資料
        rank = kwargs.get('rank', '1')
        page = kwargs.get('page', 1)

        return create_paginated_leaderboard(int(rank), page)

    elif template_type == "leaderboard_list":
        # 排行榜列表模板 - 從網站抓取資料
        leaderboard_data = scrape_leaderboard_data()

        # 如果網站抓取失敗，使用配置文件的備用資料
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
                                    "text": data.get('title', data.get('destination', '未知行程')),
                                    "size": "xs",
                                    "color": "#666666",
                                    "marginTop": "xs",
                                    "wrap": True
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
        # 動態獲取詳細行程，並優化顯示格式
        rank = kwargs.get('rank', '1')
        rank_int = int(rank)

        # 從網站抓取詳細行程
        from api.web_scraper import scrape_trip_details
        data = scrape_trip_details(rank_int)

        if not data:
            # 如果沒有詳細行程，顯示提示訊息
            rank_titles = {1: "🥇 第一名", 2: "🥈 第二名", 3: "🥉 第三名", 4: "🏅 第四名", 5: "🎖️ 第五名"}
            return {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"抱歉，{rank_titles.get(rank_int, f'第{rank_int}名')}的詳細行程安排暫時無法提供。",
                            "wrap": True,
                            "color": "#666666",
                            "align": "center"
                        }
                    ],
                    "paddingAll": "20px"
                }
            }

        # 優化行程格式 - 簡化顯示
        def format_itinerary(itinerary_text):
            """格式化行程文本，使其更簡潔"""
            if not itinerary_text:
                return "行程安排待更新"

            lines = itinerary_text.split('\n')
            formatted_lines = []

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 簡化日期格式
                if '年' in line and '月' in line and '日' in line:
                    # 將 "2025年08月15日 (星期五)" 簡化為 "8/15 (五)"
                    import re
                    date_match = re.search(r'(\d+)年(\d+)月(\d+)日.*?\((.*?)\)', line)
                    if date_match:
                        month = int(date_match.group(2))
                        day = int(date_match.group(3))
                        weekday = date_match.group(4).replace('星期', '')
                        formatted_lines.append(f"📅 {month}/{day} ({weekday})")
                        continue

                # 簡化時間和地點
                if ':' in line and '-' in line:
                    # 時間行
                    formatted_lines.append(f"🕐 {line}")
                elif line and not line.startswith('Day'):
                    # 地點行
                    formatted_lines.append(f"📍 {line}")

            # 限制行數，避免內容過長
            if len(formatted_lines) > 20:
                formatted_lines = formatted_lines[:20]
                formatted_lines.append("...")
                formatted_lines.append("💡 完整行程請查看網站")

            return '\n'.join(formatted_lines)

        formatted_itinerary = format_itinerary(data.get("itinerary", ""))

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
                                "text": formatted_itinerary,
                                "size": "sm",
                                "color": "#333333",
                                "wrap": True,
                                "lineSpacing": "sm"
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
                        "text": "💡 完整行程資訊請查看 TourHub 網站",
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
    logger.info("📥 收到 callback 請求")

    if not line_handler:
        logger.error("❌ Line handler 未設定")
        return "Bot not configured", 500

    try:
        signature = request.headers.get('X-Line-Signature')
        if not signature:
            logger.error("❌ 缺少 X-Line-Signature")
            abort(400)

        body = request.get_data(as_text=True)
        logger.info(f"📥 收到請求 body 長度: {len(body)}")

        line_handler.handle(body, signature)
        logger.info("✅ Callback 處理完成")
        return 'OK'

    except InvalidSignatureError:
        logger.error("❌ 無效的簽名")
        abort(400)
    except Exception as e:
        logger.error(f"❌ Callback 錯誤: {str(e)}")
        import traceback
        logger.error(f"❌ 錯誤詳情: {traceback.format_exc()}")
        return "Internal error", 500

# 訊息處理
if line_handler:
    @line_handler.add(MessageEvent, message=TextMessageContent)
    def handle_message(event):
        try:
            user_message = event.message.text
            logger.info(f"🔍 收到訊息: '{user_message}'")
            logger.info(f"🔍 訊息長度: {len(user_message)}")
            logger.info(f"🔍 訊息類型: {type(user_message)}")

            # 檢查模板匹配
            template_config = get_message_template(user_message)

            if template_config:
                logger.info(f"✅ 匹配到模板: {template_config['template']}, rank: {template_config.get('rank', 'N/A')}")

                # 創建 Flex Message
                if template_config["template"] == "feature":
                    flex_message = create_simple_flex_message(
                        "feature",
                        feature_name=template_config["feature_name"]
                    )
                elif template_config["template"] == "leaderboard":
                    logger.info(f"🔧 創建 leaderboard Flex Message, rank: {template_config['rank']}")
                    flex_message = create_simple_flex_message(
                        "leaderboard",
                        rank=template_config["rank"]
                    )
                    logger.info(f"🔧 leaderboard Flex Message 創建結果: {bool(flex_message)}")
                elif template_config["template"] == "leaderboard_list":
                    logger.info(f"🔧 創建 leaderboard_list Flex Message")
                    flex_message = create_simple_flex_message("leaderboard_list")
                    logger.info(f"🔧 leaderboard_list Flex Message 創建結果: {bool(flex_message)}")
                elif template_config["template"] == "leaderboard_details":
                    logger.info(f"🔧 創建 leaderboard_details Flex Message, rank: {template_config['rank']}")
                    flex_message = create_simple_flex_message(
                        "leaderboard_details",
                        rank=template_config["rank"]
                    )
                    logger.info(f"🔧 leaderboard_details Flex Message 創建結果: {bool(flex_message)}")
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
                logger.info("❌ 沒有匹配的模板，使用預設回應")
                flex_message = create_simple_flex_message("default")

            # 發送消息
            logger.info(f"📤 準備發送訊息，Flex Message 存在: {bool(flex_message)}")
            if flex_message:
                logger.info(f"📤 Flex Message 類型: {flex_message.get('type', 'N/A')}")

            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[FlexMessage(alt_text="TourHub Bot", contents=FlexContainer.from_dict(flex_message))]
                    )
                )
                logger.info("✅ 訊息發送成功")
                
        except Exception as e:
            logger.error(f"❌ 處理訊息錯誤: {str(e)}")
            import traceback
            logger.error(f"❌ 錯誤詳情: {traceback.format_exc()}")

            # 嘗試發送錯誤訊息給用戶
            try:
                error_message = create_simple_flex_message("default")
                with ApiClient(configuration) as api_client:
                    line_bot_api = MessagingApi(api_client)
                    line_bot_api.reply_message_with_http_info(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[FlexMessage(alt_text="TourHub Bot Error", contents=FlexContainer.from_dict(error_message))]
                        )
                    )
                    logger.info("🔧 錯誤回應發送成功")
            except Exception as send_error:
                logger.error(f"❌ 發送錯誤回應也失敗: {send_error}")

    # Postback 事件處理（分頁按鈕）
    @line_handler.add(PostbackEvent)
    def handle_postback(event):
        try:
            postback_data = event.postback.data
            logger.info(f"🔍 收到 postback: {postback_data}")

            # 解析 postback 資料
            params = {}
            for param in postback_data.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value

            action = params.get('action')
            rank = params.get('rank', '1')
            page = int(params.get('page', '1'))

            logger.info(f"🔧 Postback 參數: action={action}, rank={rank}, page={page}")

            flex_message = None

            if action == 'leaderboard_page':
                # 排行榜分頁
                flex_message = create_paginated_leaderboard(int(rank), page)
            elif action == 'itinerary_page':
                # 詳細行程分頁
                flex_message = create_paginated_itinerary(int(rank), page)

            if flex_message:
                logger.info(f"📤 準備發送分頁回應")
                with ApiClient(configuration) as api_client:
                    line_bot_api = MessagingApi(api_client)
                    line_bot_api.reply_message_with_http_info(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[FlexMessage(alt_text="TourHub Bot", contents=FlexContainer.from_dict(flex_message))]
                        )
                    )
                    logger.info("✅ 分頁回應發送成功")
            else:
                logger.error("❌ 無法創建分頁回應")

        except Exception as e:
            logger.error(f"❌ 處理 postback 錯誤: {str(e)}")
            import traceback
            logger.error(f"❌ 錯誤詳情: {traceback.format_exc()}")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
