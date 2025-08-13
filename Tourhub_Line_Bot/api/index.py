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

# 導入內容創建功能
from api.content_creator import content_creator

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

                # 創建單個行程項目（移除所有 icon）
                if date_text and time_text and location:
                    itinerary_items.extend([
                        {
                            "type": "text",
                            "text": date_text,
                            "size": "sm",
                            "color": "#666666",
                            "margin": "md",
                            "weight": "bold"
                        },
                        {
                            "type": "text",
                            "text": time_text,
                            "size": "sm",
                            "color": "#333333"
                        },
                        {
                            "type": "text",
                            "text": location,
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

        # 添加行程長度提示
        total_days = len(data.get("details", []))
        if total_days > 6:
            itinerary_items.extend([
                {
                    "type": "text",
                    "text": "...",
                    "size": "sm",
                    "color": "#999999",
                    "align": "center",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": f"完整行程共 {total_days} 天，以上僅顯示前 6 天",
                    "size": "xs",
                    "color": "#999999",
                    "align": "center",
                    "wrap": True
                }
            ])

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
                        "text": "行程安排",
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
                        "text": "完整行程請查看 TourHub 網站",
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

def create_quick_split_calculator():
    """創建快速分帳計算器"""
    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "💰 快速分帳計算器",
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
                    "text": "請輸入以下格式來計算分帳：",
                    "size": "md",
                    "color": "#555555",
                    "wrap": True,
                    "margin": "md"
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "📝 格式範例：",
                    "weight": "bold",
                    "size": "sm",
                    "color": "#333333",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "• 分帳 1000 3人\n• 分帳 2500 5人\n• AA 800 4人",
                    "size": "sm",
                    "color": "#666666",
                    "wrap": True,
                    "margin": "sm"
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "💡 小提示：",
                    "weight": "bold",
                    "size": "sm",
                    "color": "#333333",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "輸入總金額和人數，我會自動幫您計算每人應付的金額！",
                    "size": "sm",
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
                    "type": "button",
                    "action": {
                        "type": "uri",
                        "label": "使用完整分帳工具",
                        "uri": "https://tripfrontend.vercel.app/linesplitbill"
                    },
                    "style": "primary",
                    "color": "#E74C3C",
                    "height": "sm"
                }
            ],
            "paddingAll": "20px"
        }
    }

def calculate_split_bill(message):
    """計算分帳金額"""
    import re

    # 匹配格式：分帳/AA + 金額 + 人數
    pattern = r'(?:分帳|AA|aa)\s*(\d+(?:\.\d+)?)\s*(\d+)(?:人)?'
    match = re.search(pattern, message)

    if match:
        amount = float(match.group(1))
        people = int(match.group(2))

        if people <= 0:
            return "❌ 人數必須大於 0"

        per_person = amount / people

        response = f"💰 分帳計算結果\n\n"
        response += f"💳 總金額：${amount:,.0f}\n"
        response += f"👥 分攤人數：{people}人\n"
        response += f"💵 每人應付：${per_person:,.0f}\n\n"

        if per_person != int(per_person):
            response += f"💡 精確金額：${per_person:.2f}\n\n"

        response += "📝 想要記錄更多費用？\n"
        response += "輸入「分帳工具」使用完整功能！"

        return response

    return None

def get_weather_info(location=None):
    """獲取天氣資訊（模擬）"""
    if not location:
        return {
            "type": "bubble",
            "size": "kilo",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🌤️ 天氣查詢",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#ffffff",
                        "align": "center"
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
                        "type": "text",
                        "text": "請輸入以下格式查詢天氣：",
                        "size": "md",
                        "color": "#555555",
                        "wrap": True,
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "lg"
                    },
                    {
                        "type": "text",
                        "text": "📝 格式範例：",
                        "weight": "bold",
                        "size": "sm",
                        "color": "#333333",
                        "margin": "lg"
                    },
                    {
                        "type": "text",
                        "text": "• 東京天氣\n• 大阪天氣\n• 京都天氣\n• 北海道天氣",
                        "size": "sm",
                        "color": "#666666",
                        "wrap": True,
                        "margin": "sm"
                    }
                ],
                "paddingAll": "20px"
            }
        }

def get_currency_converter():
    """獲取匯率換算工具"""
    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "💱 匯率換算",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#ffffff",
                    "align": "center"
                }
            ],
            "backgroundColor": "#F39C12",
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "請輸入以下格式進行換算：",
                    "size": "md",
                    "color": "#555555",
                    "wrap": True,
                    "margin": "md"
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "📝 格式範例：",
                    "weight": "bold",
                    "size": "sm",
                    "color": "#333333",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "• 1000台幣換日幣\n• 100美金換台幣\n• 5000日幣換台幣",
                    "size": "sm",
                    "color": "#666666",
                    "wrap": True,
                    "margin": "sm"
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "💡 支援幣別：",
                    "weight": "bold",
                    "size": "sm",
                    "color": "#333333",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "台幣 (TWD)、日幣 (JPY)、美金 (USD)、港幣 (HKD)",
                    "size": "sm",
                    "color": "#666666",
                    "wrap": True,
                    "margin": "sm"
                }
            ],
            "paddingAll": "20px"
        }
    }

def create_travel_tips():
    """創建旅遊小貼士"""
    tips = [
        "🎒 輕裝出行，只帶必需品",
        "📱 下載離線地圖和翻譯 App",
        "💳 準備多種付款方式",
        "🏥 購買旅遊保險",
        "📋 備份重要文件",
        "🌐 了解當地文化和禮儀",
        "💰 預留緊急備用金",
        "📞 記住緊急聯絡電話"
    ]

    tip_contents = []
    for tip in tips:
        tip_contents.append({
            "type": "text",
            "text": tip,
            "size": "sm",
            "color": "#666666",
            "wrap": True,
            "margin": "sm"
        })

    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "💡 旅遊小貼士",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#ffffff",
                    "align": "center"
                }
            ],
            "backgroundColor": "#2ECC71",
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "實用的旅遊建議：",
                    "size": "md",
                    "color": "#555555",
                    "wrap": True,
                    "margin": "md"
                },
                {
                    "type": "separator",
                    "margin": "lg"
                }
            ] + tip_contents,
            "paddingAll": "20px"
        }
    }

def create_nearby_search():
    """創建附近景點搜尋"""
    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "📍 附近景點搜尋",
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
                    "text": "請輸入地點來搜尋附近景點：",
                    "size": "md",
                    "color": "#555555",
                    "wrap": True,
                    "margin": "md"
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "📝 格式範例：",
                    "weight": "bold",
                    "size": "sm",
                    "color": "#333333",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "• 東京附近景點\n• 大阪附近推薦\n• 京都周邊景點",
                    "size": "sm",
                    "color": "#666666",
                    "wrap": True,
                    "margin": "sm"
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "💡 或者直接輸入地區名稱：",
                    "weight": "bold",
                    "size": "sm",
                    "color": "#333333",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "東京、大阪、京都、北海道、沖繩",
                    "size": "sm",
                    "color": "#666666",
                    "wrap": True,
                    "margin": "sm"
                }
            ],
            "paddingAll": "20px"
        }
    }

def create_creation_response(creation_result):
    """創建內容創建結果的回應訊息"""
    if creation_result['type'] == 'success':
        # 成功創建的回應
        content_type_names = {
            'trip': '行程',
            'meeting': '集合',
            'bill': '分帳'
        }

        content_name = content_type_names.get(creation_result['content_type'], '內容')

        return {
            "type": "bubble",
            "size": "kilo",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"✅ {content_name}創建成功",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#ffffff",
                        "align": "center"
                    }
                ],
                "backgroundColor": "#2ECC71",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": creation_result['message'],
                        "size": "md",
                        "color": "#555555",
                        "wrap": True,
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "lg"
                    },
                    {
                        "type": "text",
                        "text": "📋 詳細資訊：",
                        "weight": "bold",
                        "size": "sm",
                        "color": "#333333",
                        "margin": "lg"
                    }
                ] + _create_detail_contents(creation_result.get('details', {})),
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
                            "label": f"查看{content_name}",
                            "uri": creation_result.get('url', 'https://tripfrontend.vercel.app')
                        },
                        "style": "primary",
                        "color": "#2ECC71",
                        "height": "sm"
                    }
                ] if creation_result.get('url') else [],
                "paddingAll": "20px"
            }
        }
    else:
        # 創建失敗的回應
        return {
            "type": "bubble",
            "size": "kilo",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "❌ 創建失敗",
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
                        "text": creation_result['message'],
                        "size": "md",
                        "color": "#555555",
                        "wrap": True,
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "lg"
                    },
                    {
                        "type": "text",
                        "text": "💡 請檢查輸入格式或稍後再試",
                        "size": "sm",
                        "color": "#666666",
                        "wrap": True,
                        "margin": "lg"
                    }
                ],
                "paddingAll": "20px"
            }
        }

def _create_detail_contents(details):
    """創建詳細資訊內容"""
    contents = []

    if 'title' in details:
        contents.append({
            "type": "text",
            "text": f"📝 標題：{details['title']}",
            "size": "sm",
            "color": "#666666",
            "wrap": True,
            "margin": "sm"
        })

    if 'location' in details:
        contents.append({
            "type": "text",
            "text": f"📍 地點：{details['location']}",
            "size": "sm",
            "color": "#666666",
            "wrap": True,
            "margin": "sm"
        })

    if 'days' in details:
        contents.append({
            "type": "text",
            "text": f"📅 天數：{details['days']}天",
            "size": "sm",
            "color": "#666666",
            "wrap": True,
            "margin": "sm"
        })

    if 'time_info' in details and details['time_info']:
        time_info = details['time_info']
        time_text = "⏰ 時間：" + time_info.get('description', '請稍後設定')
        if time_info.get('date'):
            time_text += f" ({time_info['date']}"
            if time_info.get('time'):
                time_text += f" {time_info['time']}"
            time_text += ")"

        contents.append({
            "type": "text",
            "text": time_text,
            "size": "sm",
            "color": "#666666",
            "wrap": True,
            "margin": "sm"
        })

    return contents

def create_creation_help():
    """創建內容創建說明"""
    return {
        "type": "bubble",
        "size": "giga",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🚀 直接創建內容",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#ffffff",
                    "align": "center"
                }
            ],
            "backgroundColor": "#6C5CE7",
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "現在您可以直接在 Line 中創建內容到各個網站！",
                    "size": "md",
                    "color": "#555555",
                    "wrap": True,
                    "margin": "md"
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "🗓️ 創建行程",
                    "weight": "bold",
                    "size": "sm",
                    "color": "#333333",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "• 創建東京三日遊行程\n• 建立北海道五日遊行程\n• 規劃大阪美食行程",
                    "size": "sm",
                    "color": "#666666",
                    "wrap": True,
                    "margin": "sm"
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "⏰ 創建集合",
                    "weight": "bold",
                    "size": "sm",
                    "color": "#333333",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "• 創建明天9點東京車站集合\n• 設定後天下午2點集合\n• 約今天晚上7點集合",
                    "size": "sm",
                    "color": "#666666",
                    "wrap": True,
                    "margin": "sm"
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "💰 創建分帳",
                    "weight": "bold",
                    "size": "sm",
                    "color": "#333333",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "• 創建東京旅遊分帳\n• 建立聚餐分帳\n• 新增購物分帳",
                    "size": "sm",
                    "color": "#666666",
                    "wrap": True,
                    "margin": "sm"
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "💡 創建後會自動同步到對應網站，您可以點擊連結查看和編輯詳細內容！",
                    "size": "sm",
                    "color": "#2ECC71",
                    "wrap": True,
                    "margin": "lg"
                }
            ],
            "paddingAll": "20px"
        }
    }

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

    elif template_type == "feature_menu":
        template = MESSAGE_TEMPLATES["feature_menu"]

        # 創建功能按鈕
        feature_buttons = []
        features = [
            {"name": "🏆 排行榜", "data": "action=feature_detail&feature=leaderboard"},
            {"name": "🗓️ 行程管理", "data": "action=feature_detail&feature=trip_management"},
            {"name": "⏰ 集合", "data": "action=feature_detail&feature=tour_clock"},
            {"name": "🛅 置物櫃查找", "data": "action=feature_detail&feature=locker"},
            {"name": "💰 分帳工具", "data": "action=feature_detail&feature=split_bill"},
            {"name": "💰 快速分帳", "data": "action=inline_feature&feature=quick_split"},
            {"name": "🌤️ 天氣查詢", "data": "action=inline_feature&feature=weather"},
            {"name": "💱 匯率換算", "data": "action=inline_feature&feature=currency"},
            {"name": "💡 旅遊小貼士", "data": "action=inline_feature&feature=tips"},
            {"name": "📍 附近景點", "data": "action=inline_feature&feature=nearby"}
        ]

        for feature in features:
            feature_buttons.append({
                "type": "button",
                "action": {
                    "type": "postback",
                    "label": feature["name"],
                    "data": feature["data"]
                },
                "style": "secondary",
                "height": "sm",
                "margin": "sm"
            })

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
                        "wrap": True
                    }
                ],
                "paddingAll": "20px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": feature_buttons,
                "paddingAll": "20px"
            }
        }

    elif template_type == "feature_detail":
        feature_name = kwargs.get('feature_name')
        if feature_name in MESSAGE_TEMPLATES["feature_details"]:
            template = MESSAGE_TEMPLATES["feature_details"][feature_name]

            # 創建功能詳情內容
            detail_contents = []

            # 添加描述
            detail_contents.append({
                "type": "text",
                "text": template["description"],
                "size": "md",
                "color": "#555555",
                "wrap": True,
                "margin": "md"
            })

            # 添加功能特點
            detail_contents.append({
                "type": "separator",
                "margin": "lg"
            })
            detail_contents.append({
                "type": "text",
                "text": "✨ 功能特點",
                "weight": "bold",
                "size": "sm",
                "color": "#333333",
                "margin": "lg"
            })

            for detail in template["details"]:
                detail_contents.append({
                    "type": "text",
                    "text": detail,
                    "size": "sm",
                    "color": "#666666",
                    "wrap": True,
                    "margin": "sm"
                })

            # 添加使用步驟
            detail_contents.append({
                "type": "separator",
                "margin": "lg"
            })
            detail_contents.append({
                "type": "text",
                "text": "📋 使用方法",
                "weight": "bold",
                "size": "sm",
                "color": "#333333",
                "margin": "lg"
            })

            for step in template["usage_steps"]:
                detail_contents.append({
                    "type": "text",
                    "text": step,
                    "size": "sm",
                    "color": "#666666",
                    "wrap": True,
                    "margin": "sm"
                })

            # 創建按鈕
            footer_buttons = [
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
                },
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "🔙 返回功能選單",
                        "data": "action=back_to_menu"
                    },
                    "style": "secondary",
                    "height": "sm",
                    "margin": "sm"
                }
            ]

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
                    "contents": detail_contents,
                    "paddingAll": "20px"
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": footer_buttons,
                    "paddingAll": "20px"
                }
            }

    elif template_type == "quick_split_calculator":
        return create_quick_split_calculator()

    elif template_type == "weather_inquiry":
        return get_weather_info()

    elif template_type == "currency_converter":
        return get_currency_converter()

    elif template_type == "travel_tips":
        return create_travel_tips()

    elif template_type == "nearby_search":
        return create_nearby_search()

    elif template_type == "creation_help":
        return create_creation_help()

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

            # 獲取用戶 ID
            line_user_id = event.source.user_id if hasattr(event.source, 'user_id') else 'unknown'

            # 先檢查是否為內容創建指令
            creation_result = content_creator.parse_and_create(user_message, line_user_id)
            if creation_result:
                # 創建回應訊息
                response_message = create_creation_response(creation_result)

                with ApiClient(configuration) as api_client:
                    line_bot_api = MessagingApi(api_client)
                    line_bot_api.reply_message_with_http_info(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[FlexMessage(alt_text="內容創建結果", contents=FlexContainer.from_dict(response_message))]
                        )
                    )
                    logger.info("✅ 內容創建結果發送成功")
                return

            # 檢查是否為分帳計算
            split_result = calculate_split_bill(user_message)
            if split_result:
                # 直接發送文字回應
                with ApiClient(configuration) as api_client:
                    line_bot_api = MessagingApi(api_client)
                    line_bot_api.reply_message_with_http_info(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text=split_result)]
                        )
                    )
                    logger.info("✅ 分帳計算結果發送成功")
                return

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
                elif template_config["template"] == "feature_menu":
                    flex_message = create_simple_flex_message("feature_menu")
                elif template_config["template"] == "feature_detail":
                    flex_message = create_simple_flex_message(
                        "feature_detail",
                        feature_name=template_config["feature_name"]
                    )
                elif template_config["template"] == "tour_clock":
                    # TourClock 使用 feature 模板
                    flex_message = create_simple_flex_message(
                        "feature",
                        feature_name="tour_clock"
                    )
                elif template_config["template"] == "quick_split_calculator":
                    flex_message = create_simple_flex_message("quick_split_calculator")
                elif template_config["template"] == "weather_inquiry":
                    flex_message = create_simple_flex_message("weather_inquiry")
                elif template_config["template"] == "currency_converter":
                    flex_message = create_simple_flex_message("currency_converter")
                elif template_config["template"] == "travel_tips":
                    flex_message = create_simple_flex_message("travel_tips")
                elif template_config["template"] == "nearby_search":
                    flex_message = create_simple_flex_message("nearby_search")
                elif template_config["template"] == "creation_help":
                    flex_message = create_simple_flex_message("creation_help")
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
            elif action == 'feature_detail':
                # 功能詳細介紹
                feature = params.get('feature')
                if feature:
                    logger.info(f"🔧 創建功能詳細介紹: {feature}")
                    flex_message = create_simple_flex_message(
                        "feature_detail",
                        feature_name=feature
                    )
            elif action == 'back_to_menu':
                # 返回功能選單
                logger.info(f"🔧 返回功能選單")
                flex_message = create_simple_flex_message("feature_menu")
            elif action == 'inline_feature':
                # 內建功能
                feature = params.get('feature')
                logger.info(f"🔧 使用內建功能: {feature}")

                if feature == 'quick_split':
                    flex_message = create_simple_flex_message("quick_split_calculator")
                elif feature == 'weather':
                    flex_message = create_simple_flex_message("weather_inquiry")
                elif feature == 'currency':
                    flex_message = create_simple_flex_message("currency_converter")
                elif feature == 'tips':
                    flex_message = create_simple_flex_message("travel_tips")
                elif feature == 'nearby':
                    flex_message = create_simple_flex_message("nearby_search")

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
