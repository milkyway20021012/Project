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
    FlexContainer,
    TextMessage
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

def create_optimized_flex_itinerary(data):
    """創建優化的 Flex Message 詳細行程"""
    try:
        # 處理行程詳細資料，分割成多個短文本
        itinerary_items = []

        if data.get("details"):
            for detail in data["details"][:6]:  # 限制最多6個項目
                # 處理日期
                date_text = ""
                if detail['date']:
                    date_obj = detail['date']
                    weekdays = ['一', '二', '三', '四', '五', '六', '日']
                    weekday = weekdays[date_obj.weekday()]
                    date_text = f"{date_obj.month}/{date_obj.day} ({weekday})"

                # 處理時間
                time_text = ""
                if detail['start_time'] and detail['end_time']:
                    start_time = str(detail['start_time'])[:5]  # HH:MM
                    end_time = str(detail['end_time'])[:5]
                    time_text = f"{start_time}-{end_time}"

                # 處理地點（移除特殊字符）
                location = detail['location'] or "未知地點"
                location = location.replace('・', '-')  # 替換特殊字符

                # 創建單個行程項目
                if date_text and time_text and location:
                    itinerary_items.extend([
                        {
                            "type": "text",
                            "text": f"📅 {date_text}",
                            "size": "sm",
                            "color": "#666666",
                            "margin": "md"
                        },
                        {
                            "type": "text",
                            "text": f"🕐 {time_text}",
                            "size": "sm",
                            "color": "#333333"
                        },
                        {
                            "type": "text",
                            "text": f"📍 {location}",
                            "size": "sm",
                            "color": "#333333",
                            "wrap": True
                        }
                    ])

                    # 限制項目數量，避免過長
                    if len(itinerary_items) >= 15:  # 5個行程 x 3行 = 15項
                        break

        # 如果沒有詳細資料，顯示提示
        if not itinerary_items:
            itinerary_items = [
                {
                    "type": "text",
                    "text": "暫無詳細行程安排",
                    "size": "sm",
                    "color": "#666666",
                    "align": "center"
                }
            ]

        # 添加查看更多提示
        if len(data.get("details", [])) > 6:
            itinerary_items.append({
                "type": "text",
                "text": "...",
                "size": "sm",
                "color": "#999999",
                "align": "center",
                "margin": "md"
            })

        # 清理標題中的特殊字符
        clean_title = data['title'].replace('・', '-') if data['title'] else f"第{data['rank']}名行程"
        clean_area = data['area'].replace('・', '-') if data['area'] else "未知地區"

        return {
            "type": "bubble",
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
                        "text": f"{clean_title} - {clean_area}",
                        "size": "sm",
                        "color": "#ffffff",
                        "align": "center",
                        "margin": "sm",
                        "wrap": True
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
                    }
                ] + itinerary_items,
                "paddingAll": "20px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "💡 完整行程請查看 TourHub 網站",
                        "size": "xs",
                        "color": "#666666",
                        "align": "center"
                    }
                ],
                "paddingAll": "15px"
            }
        }

    except Exception as e:
        logger.error(f"創建優化 Flex Message 失敗: {e}")
        # 返回簡單的錯誤訊息
        return {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"抱歉，第{data.get('rank', '?')}名的詳細行程暫時無法提供。",
                        "wrap": True,
                        "color": "#666666",
                        "align": "center"
                    }
                ],
                "paddingAll": "20px"
            }
        }

def create_text_itinerary_response(rank):
    """創建文字格式的詳細行程回應"""
    try:
        from api.database import get_database_connection
        connection = get_database_connection()
        if not connection:
            return f"抱歉，第{rank}名的詳細行程暫時無法提供。"

        cursor = connection.cursor(dictionary=True)

        # 查詢排行榜中指定排名的行程
        leaderboard_query = """
        SELECT
            t.trip_id,
            t.title,
            t.area
        FROM line_trips t
        LEFT JOIN trip_stats ts ON t.trip_id = ts.trip_id
        WHERE t.trip_id IS NOT NULL
        ORDER BY ts.popularity_score DESC, ts.favorite_count DESC, ts.share_count DESC
        LIMIT %s, 1
        """

        cursor.execute(leaderboard_query, (int(rank) - 1,))
        trip_data = cursor.fetchone()

        if not trip_data:
            cursor.close()
            connection.close()
            return f"抱歉，第{rank}名的行程資料暫時無法提供。"

        trip_id = trip_data['trip_id']

        # 查詢詳細行程安排
        details_query = """
        SELECT
            location,
            date,
            start_time,
            end_time
        FROM line_trip_details
        WHERE trip_id = %s
        ORDER BY date, start_time
        """

        cursor.execute(details_query, (trip_id,))
        details = cursor.fetchall()

        cursor.close()
        connection.close()

        # 組織文字回應
        rank_emojis = {1: "🥇", 2: "🥈", 3: "🥉", 4: "🏅", 5: "🎖️"}
        rank_emoji = rank_emojis.get(int(rank), "🎖️")

        response_lines = [
            f"{rank_emoji} 第{rank}名詳細行程",
            f"📍 {trip_data['title']} - {trip_data['area']}",
            "",
            "📅 行程安排："
        ]

        if details:
            for detail in details:
                # 處理日期
                if detail['date']:
                    date_obj = detail['date']
                    weekdays = ['一', '二', '三', '四', '五', '六', '日']
                    weekday = weekdays[date_obj.weekday()]
                    date_str = f"{date_obj.month}/{date_obj.day} ({weekday})"
                    response_lines.append(f"📅 {date_str}")

                # 處理時間和地點
                time_str = ""
                if detail['start_time'] and detail['end_time']:
                    start_time = str(detail['start_time'])
                    end_time = str(detail['end_time'])

                    # 簡化時間格式
                    if ':' in start_time and len(start_time) > 8:
                        start_time = start_time[:5]  # 取 HH:MM
                    if ':' in end_time and len(end_time) > 8:
                        end_time = end_time[:5]

                    time_str = f"{start_time} - {end_time}"
                elif detail['start_time']:
                    start_time = str(detail['start_time'])
                    if ':' in start_time and len(start_time) > 8:
                        start_time = start_time[:5]
                    time_str = start_time

                # 地點
                location = detail['location'] or "未知地點"

                # 組合時間和地點
                if time_str:
                    response_lines.append(f"🕐 {time_str}")
                    response_lines.append(f"📍 {location}")
                else:
                    response_lines.append(f"📍 {location}")

                response_lines.append("")  # 空行分隔
        else:
            response_lines.append("暫無詳細行程安排")

        # 移除最後的空行
        while response_lines and response_lines[-1] == "":
            response_lines.pop()

        # 添加結尾
        response_lines.append("")
        response_lines.append("💡 更多資訊請查看 TourHub 網站")

        return "\n".join(response_lines)

    except Exception as e:
        logger.error(f"創建文字行程回應失敗: {e}")
        return f"抱歉，第{rank}名的詳細行程暫時無法提供。"

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
        # 直接從資料庫獲取詳細行程
        rank = kwargs.get('rank', '1')
        rank_int = int(rank)

        # 直接從資料庫查詢詳細行程
        try:
            from api.database import get_database_connection
            connection = get_database_connection()
            if not connection:
                raise Exception("資料庫連接失敗")

            cursor = connection.cursor(dictionary=True)

            # 查詢排行榜中指定排名的行程
            leaderboard_query = """
            SELECT
                t.trip_id,
                t.title,
                t.area,
                t.start_date,
                t.end_date
            FROM line_trips t
            LEFT JOIN trip_stats ts ON t.trip_id = ts.trip_id
            WHERE t.trip_id IS NOT NULL
            ORDER BY ts.popularity_score DESC, ts.favorite_count DESC, ts.share_count DESC
            LIMIT %s, 1
            """

            cursor.execute(leaderboard_query, (rank_int - 1,))
            trip_data = cursor.fetchone()

            if not trip_data:
                cursor.close()
                connection.close()
                raise Exception(f"找不到第{rank_int}名的行程")

            trip_id = trip_data['trip_id']

            # 查詢詳細行程安排
            details_query = """
            SELECT
                location,
                date,
                start_time,
                end_time,
                description
            FROM line_trip_details
            WHERE trip_id = %s
            ORDER BY date, start_time
            """

            cursor.execute(details_query, (trip_id,))
            details = cursor.fetchall()

            cursor.close()
            connection.close()

            # 組織資料
            rank_titles = {1: "🥇 第一名", 2: "🥈 第二名", 3: "🥉 第三名", 4: "🏅 第四名", 5: "🎖️ 第五名"}
            rank_colors = {1: "#FFD700", 2: "#C0C0C0", 3: "#CD7F32", 4: "#4ECDC4", 5: "#FF6B9D"}

            data = {
                "trip_id": trip_data['trip_id'],
                "rank": rank_int,
                "rank_title": rank_titles.get(rank_int, f"🎖️ 第{rank_int}名"),
                "title": trip_data['title'] or f"第{rank_int}名行程",
                "color": rank_colors.get(rank_int, "#9B59B6"),
                "area": trip_data['area'] or "未知地區",
                "details": details
            }

        except Exception as e:
            logger.error(f"資料庫查詢失敗: {e}")
            data = None

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

        # 格式化資料庫的詳細行程資料
        def format_database_itinerary(details):
            """格式化資料庫的行程詳細資料"""
            if not details:
                return "暫無詳細行程安排"

            formatted_lines = []

            for detail in details:
                # 處理日期
                if detail['date']:
                    date_obj = detail['date']
                    weekdays = ['一', '二', '三', '四', '五', '六', '日']
                    weekday = weekdays[date_obj.weekday()]
                    date_str = f"📅 {date_obj.month}/{date_obj.day} ({weekday})"
                    formatted_lines.append(date_str)

                # 處理時間和地點
                time_str = ""
                if detail['start_time'] and detail['end_time']:
                    start_time = str(detail['start_time'])
                    end_time = str(detail['end_time'])

                    # 如果是 timedelta 格式，轉換為時間格式
                    if ':' in start_time and len(start_time) > 8:
                        start_time = start_time[:8]  # 取 HH:MM:SS
                    if ':' in end_time and len(end_time) > 8:
                        end_time = end_time[:8]

                    time_str = f"🕐 {start_time} - {end_time}"
                elif detail['start_time']:
                    start_time = str(detail['start_time'])
                    if ':' in start_time and len(start_time) > 8:
                        start_time = start_time[:8]
                    time_str = f"🕐 {start_time}"

                # 地點
                location = detail['location'] or "未知地點"
                location_str = f"📍 {location}"

                # 添加時間和地點
                if time_str:
                    formatted_lines.append(f"{time_str} {location}")
                else:
                    formatted_lines.append(location_str)

                # 添加空行分隔
                formatted_lines.append("")

            # 移除最後的空行
            if formatted_lines and formatted_lines[-1] == "":
                formatted_lines.pop()

            # 限制行數，避免內容過長
            if len(formatted_lines) > 25:
                formatted_lines = formatted_lines[:25]
                formatted_lines.append("...")
                formatted_lines.append("💡 完整行程請查看 TourHub 網站")

            return '\n'.join(formatted_lines)

        # 創建優化的 Flex Message 結構
        return create_optimized_flex_itinerary(data)

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
                    logger.info(f"🔧 創建 leaderboard_details 優化 Flex Message, rank: {template_config['rank']}")
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
