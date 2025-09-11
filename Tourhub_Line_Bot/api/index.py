from flask import Flask, request, abort
import os
import logging
import re

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全域 Flex Message 現代化主題系統
THEME_PRIMARY_BLUE = "#2563EB"      # 現代藍色（主要按鈕/header）
THEME_SECONDARY_BLUE = "#3B82F6"    # 次要藍色（hover狀態）
THEME_LIGHT_BLUE_BG = "#EFF6FF"     # 淺藍背景（卡片背景）
THEME_ACCENT_BLUE = "#1D4ED8"       # 強調藍色（重要元素）
THEME_TEXT_PRIMARY = "#1F2937"      # 主要文字深灰藍
THEME_TEXT_SECONDARY = "#6B7280"    # 次要文字
THEME_TEXT_MUTED = "#9CA3AF"        # 靜音文字
THEME_SUCCESS = "#10B981"           # 成功綠色
THEME_WARNING = "#F59E0B"           # 警告橙色
THEME_ERROR = "#EF4444"             # 錯誤紅色
THEME_BORDER = "#E5E7EB"            # 邊框顏色

def apply_modern_theme(payload):
    """套用現代化主題到 Flex Message dict
    - 統一的色彩系統
    - 改善的視覺層次
    - 更好的可讀性
    """
    if payload is None:
        return payload

    def _transform(node, parent_key=None):
        if isinstance(node, dict):
            # 統一替換舊的橘色系統
            if node.get('backgroundColor') == '#FFA500':
                node['backgroundColor'] = THEME_PRIMARY_BLUE
            
            # header 區塊統一使用主色調
            if node.get('type') == 'box' and parent_key == 'header':
                if node.get('backgroundColor') not in [THEME_PRIMARY_BLUE, THEME_ACCENT_BLUE]:
                    node['backgroundColor'] = THEME_PRIMARY_BLUE

            # 按鈕顏色優化
            if node.get('type') == 'button':
                style = node.get('style')
                if style == 'primary':
                    # 根據功能類型使用不同顏色
                    current_color = node.get('color', '')
                    if current_color in ['#FF6B6B', '#E74C3C']:  # 排行榜
                        node['color'] = THEME_ERROR
                    elif current_color in ['#4ECDC4', '#2ECC71']:  # 行程管理/成功
                        node['color'] = THEME_SUCCESS
                    elif current_color in ['#FFA500', '#F59E0B']:  # 置物櫃/警告
                        node['color'] = THEME_WARNING
                    elif current_color in ['#9B59B6', '#6C5CE7']:  # TourClock/功能說明
                        node['color'] = THEME_ACCENT_BLUE
                    else:
                        node['color'] = THEME_PRIMARY_BLUE
                elif style == 'secondary':
                    node.setdefault('color', THEME_TEXT_SECONDARY)

            # 文字顏色優化
            if node.get('type') == 'text':
                if parent_key == 'header':
                    node['color'] = '#ffffff'
                else:
                    current = node.get('color')
                    if current in (None, '#333333', '#222222', '#000000'):
                        node['color'] = THEME_TEXT_PRIMARY
                    elif current in ('#666666', '#777777', '#888888', '#555555'):
                        node['color'] = THEME_TEXT_SECONDARY
                    elif current == '#999999':
                        node['color'] = THEME_TEXT_MUTED

            # 遞迴處理子節點
            for k, v in list(node.items()):
                node[k] = _transform(v, parent_key=k)
            return node
        elif isinstance(node, list):
            return [_transform(child, parent_key=parent_key) for child in node]
        else:
            return node

    return _transform(payload)

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
    scrape_leaderboard_data
)

# 導入分頁功能
from api.pagination import (
    create_paginated_leaderboard,
    create_paginated_itinerary
)

import importlib

# 導入內容創建功能（若不存在則降級為無操作）
class _NoopContentCreator:
    def parse_and_create(self, user_message, line_user_id):
        return None

try:
    content_creator = importlib.import_module('api.content_creator').content_creator
except Exception:
    content_creator = _NoopContentCreator()

# 導入資料庫功能（作為備用）
try:
    from api.database import (
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
    PushMessageRequest,
    FlexMessage,
    FlexContainer
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, PostbackEvent, LocationMessageContent

# 建立 Flask app
app = Flask(__name__)

# 收藏功能：優先寫入資料庫，失敗則回退記憶體
USER_FAVORITES = {}

def _get_user_favorites_memory(line_user_id):
    favorites = USER_FAVORITES.get(line_user_id)
    if favorites is None:
        favorites = set()
        USER_FAVORITES[line_user_id] = favorites
    return favorites

def add_favorite(line_user_id, rank_int):
    try:
        # 先嘗試存 DB
        try:
            from api.database import add_user_favorite_db
            inserted = add_user_favorite_db(line_user_id, int(rank_int))
            if inserted:
                return True
        except Exception:
            pass

        # 回退記憶體
        favorites = _get_user_favorites_memory(line_user_id)
        before_size = len(favorites)
        favorites.add(int(rank_int))
        return len(favorites) > before_size
    except Exception:
        return False

def remove_favorite(line_user_id, rank_int):
    try:
        # 先嘗試 DB
        try:
            from api.database import remove_user_favorite_db
            removed = remove_user_favorite_db(line_user_id, int(rank_int))
            if removed:
                return True
        except Exception:
            pass
        # 回退記憶體
        favorites = _get_user_favorites_memory(line_user_id)
        if int(rank_int) in favorites:
            favorites.remove(int(rank_int))
            return True
        return False
    except Exception:
        return False

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

def parse_rank_request(user_message):
    """解析用戶輸入是否為要求排行榜第 n 名或其詳細行程
    支援：
    - 排行榜第5名 / 第5名
    - 第5名詳細行程 / 排行榜第5名詳細行程
    - top 3 / Top3 / TOP 3 詳細行程
    返回: (template_type, rank_int) 或 None
    """
    try:
        text = (user_message or '').strip()
        is_detail = '詳細' in text

        # 1) 中文「第n名」樣式（可帶「排行榜」前綴，可帶「詳細行程」後綴）
        m = re.search(r'(?:排行榜)?第\s*(\d+)\s*名', text)
        if m:
            rank = int(m.group(1))
            return ("leaderboard_details" if is_detail else "leaderboard", rank)

        # 2) 英文 Top n 樣式（top3, top 3, TOP 3...）
        m = re.search(r'(?i)\btop\s*(\d+)\b', text)
        if m:
            rank = int(m.group(1))
            return ("leaderboard_details" if is_detail else "leaderboard", rank)

        return None
    except Exception:
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
                            "color": THEME_TEXT_SECONDARY,
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
                            "color": THEME_TEXT_PRIMARY,
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
                            "color": THEME_TEXT_MUTED,
                    "align": "center",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": f"完整行程共 {total_days} 天，以上僅顯示前 6 天",
                    "size": "xs",
                            "color": THEME_TEXT_MUTED,
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
                        "text": "📋 行程安排",
                        "weight": "bold",
                        "size": "md",
                        "color": THEME_TEXT_PRIMARY,
                        "marginBottom": "lg"
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
                        "color": THEME_TEXT_SECONDARY,
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

## 已移除未使用的 create_text_itinerary_response 函式











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
                        "color": THEME_SUCCESS,
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

def create_user_account_info(line_user_id):
    """創建用戶帳號資訊"""
    try:
        user_manager = importlib.import_module('api.unified_user_manager').user_manager
    except Exception:
        return create_error_message("用戶管理功能暫不可用")

    # 獲取用戶資訊
    user = user_manager.get_or_create_user(line_user_id)
    if not user:
        return create_error_message("無法獲取用戶資訊")

    # 獲取綁定資訊
    bindings = user_manager.get_user_bindings(user['id'])

    # 格式化時間
    last_login = user.get('last_login_at')
    if last_login:
        last_login_str = last_login.strftime('%Y-%m-%d %H:%M')
    else:
        last_login_str = "首次使用"

    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "👤 我的帳號資訊",
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
                    "text": f"🆔 用戶 ID: {user['id']}",
                    "size": "sm",
                    "color": "#666666",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": f"📱 Line ID: {line_user_id[:10]}...",
                    "size": "sm",
                    "color": "#666666",
                    "margin": "sm"
                },
                {
                    "type": "text",
                    "text": f"⏰ 最後登入: {last_login_str}",
                    "size": "sm",
                    "color": "#666666",
                    "margin": "sm"
                },
                {
                    "type": "text",
                    "text": f"🔗 已綁定服務: {len(bindings)}/5",
                    "size": "sm",
                    "color": "#666666",
                    "margin": "sm"
                },
                {
                    "type": "text",
                    "text": f"✅ 帳號狀態: {user.get('status', 'active').upper()}",
                    "size": "sm",
                    "color": "#2ECC71",
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
                        "label": "🔗 查看綁定狀態",
                        "data": "action=binding_status"
                    },
                    "style": "primary",
                    "color": THEME_ACCENT_BLUE,
                    "height": "sm"
                },
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "🔄 重新綁定服務",
                        "data": "action=rebind_confirm"
                    },
                    "style": "secondary",
                    "height": "sm",
                    "margin": "sm"
                }
            ],
            "paddingAll": "20px"
        }
    }

def create_binding_status(line_user_id):
    """創建綁定狀態資訊"""
    try:
        user_manager = importlib.import_module('api.unified_user_manager').user_manager
    except Exception:
        return create_error_message("綁定管理功能暫不可用")

    # 獲取用戶資訊
    user = user_manager.get_or_create_user(line_user_id)
    if not user:
        return create_error_message("無法獲取用戶資訊")

    # 獲取綁定資訊
    bindings = user_manager.get_user_bindings(user['id'])

    # 預定義的服務列表
    services = [
        {"name": "tourhub_leaderboard", "display": "🏆 排行榜"},
        {"name": "trip_management", "display": "🗓️ 行程管理"},
        {"name": "tour_clock", "display": "⏰ 集合管理"},
        {"name": "locker_finder", "display": "🛅 置物櫃"},
        {"name": "bill_split", "display": "💰 分帳系統"}
    ]

    # 創建服務狀態列表
    service_contents = []
    for service in services:
        is_bound = service["name"] in bindings
        status_icon = "✅" if is_bound else "❌"
        status_text = "已綁定" if is_bound else "未綁定"

        service_contents.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": service["display"],
                    "size": "sm",
                    "color": "#333333",
                    "flex": 3
                },
                {
                    "type": "text",
                    "text": f"{status_icon} {status_text}",
                    "size": "sm",
                    "color": "#2ECC71" if is_bound else "#E74C3C",
                    "align": "end",
                    "flex": 2
                }
            ],
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
                    "text": "🔗 服務綁定狀態",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#ffffff",
                    "align": "center"
                }
            ],
            "backgroundColor": THEME_SUCCESS,
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"綁定狀態總覽 ({len(bindings)}/5)",
                    "size": "md",
                    "color": THEME_TEXT_PRIMARY,
                    "margin": "md",
                    "weight": "bold"
                },
                {
                    "type": "separator",
                    "margin": "lg"
                }
            ] + service_contents,
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
                        "label": "🔄 重新綁定所有服務",
                        "data": "action=rebind_all"
                    },
                    "style": "primary",
                    "color": THEME_SUCCESS,
                    "height": "sm"
                }
            ],
            "paddingAll": "20px"
        }
    }

def create_rebind_confirm():
    """創建重新綁定確認"""
    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🔄 重新綁定確認",
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
                    "text": "⚠️ 重新綁定將會：",
                    "size": "md",
                    "color": "#555555",
                    "margin": "md",
                    "weight": "bold"
                },
                {
                    "type": "text",
                    "text": "• 重新建立與所有服務的連接\n• 刷新您的認證 Token\n• 確保所有功能正常運作",
                    "size": "sm",
                    "color": "#666666",
                    "wrap": True,
                    "margin": "md"
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "💡 通常在以下情況需要重新綁定：",
                    "size": "sm",
                    "color": "#333333",
                    "weight": "bold",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "• 功能使用異常\n• 無法創建內容\n• 跳轉網站失敗",
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
                        "type": "postback",
                        "label": "✅ 確認重新綁定",
                        "data": "action=rebind_execute"
                    },
                    "style": "primary",
                    "color": "#F39C12",
                    "height": "sm"
                },
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "❌ 取消",
                        "data": "action=back_to_menu"
                    },
                    "style": "secondary",
                    "height": "sm",
                    "margin": "sm"
                }
            ],
            "paddingAll": "20px"
        }
    }

def execute_rebind(line_user_id):
    """執行重新綁定"""
    try:
        user_manager = importlib.import_module('api.unified_user_manager').user_manager
    except Exception:
        return create_error_message("重新綁定功能暫不可用")

    try:
        # 獲取用戶
        user = user_manager.get_or_create_user(line_user_id)
        if not user:
            return create_error_message("無法獲取用戶資訊")

        # 重新綁定所有服務
        services = ['trip_management', 'tour_clock', 'locker_finder', 'bill_split', 'tourhub_leaderboard']
        success_count = 0

        for service in services:
            if user_manager.bind_website(user['id'], service):
                success_count += 1

        # 記錄重新綁定操作
        user_manager.log_operation(
            user['id'],
            'rebind_services',
            {'services': services, 'success_count': success_count},
            result_status='success' if success_count == len(services) else 'partial'
        )

        if success_count == len(services):
            return {
                "type": "bubble",
                "size": "kilo",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "✅ 重新綁定成功",
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
                            "text": f"🎉 已成功重新綁定 {success_count} 個服務！",
                            "size": "md",
                            "color": THEME_TEXT_PRIMARY,
                            "margin": "md",
                            "weight": "bold"
                        },
                        {
                            "type": "text",
                            "text": "• 🏆 排行榜\n• 🗓️ 行程管理\n• ⏰ 集合管理\n• 🛅 置物櫃\n• 💰 分帳系統",
                            "size": "sm",
                            "color": THEME_TEXT_SECONDARY,
                            "wrap": True,
                            "margin": "md"
                        },
                        {
                            "type": "separator",
                            "margin": "lg"
                        },
                        {
                            "type": "text",
                            "text": "💡 現在您可以正常使用所有功能了！",
                            "size": "sm",
                            "color": THEME_SUCCESS,
                            "wrap": True,
                            "margin": "lg"
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
                                "label": "🎯 返回功能選單",
                                "data": "action=back_to_menu"
                            },
                            "style": "primary",
                            "color": THEME_SUCCESS,
                            "height": "sm"
                        }
                    ],
                    "paddingAll": "20px"
                }
            }
        else:
            return create_error_message(f"重新綁定部分成功 ({success_count}/{len(services)})")

    except Exception as e:
        logger.error(f"重新綁定失敗: {e}")
        return create_error_message("重新綁定失敗，請稍後再試")

def create_error_message(error_text):
    """創建錯誤訊息"""
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
                    "color": THEME_ERROR,
                    "align": "center"
                }
            ],
            "paddingAll": "20px"
        }
    }

def create_quick_reply_menu():
    """創建快速回覆選單"""
    return {
        "type": "bubble",
        "size": "giga",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🎯 TourHub 快速選單",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#ffffff",
                    "align": "center"
                },
                {
                    "type": "text",
                    "text": "選擇您需要的功能，開始您的完美旅程",
                    "size": "sm",
                    "color": "#E0E7FF",
                    "align": "center",
                    "margin": "sm",
                    "wrap": True
                }
            ],
            "backgroundColor": THEME_PRIMARY_BLUE,
            "paddingAll": "24px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                # 第一行：排行榜相關
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "🏆 排行榜",
                                "data": "action=quick_reply&type=leaderboard_list"
                            },
                            "style": "primary",
                            "color": THEME_PRIMARY_BLUE,
                            "height": "sm",
                            "flex": 1,
                            "margin": "sm"
                        },
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "🥇 第一名",
                                "data": "action=quick_reply&type=leaderboard&rank=1"
                            },
                            "style": "primary",
                            "color": THEME_PRIMARY_BLUE,
                            "height": "sm",
                            "flex": 1,
                            "margin": "sm"
                        }
                    ],
                    "spacing": "lg",
                    "marginBottom": "lg"
                },
                
                # 第二行：行程管理
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "🗓️ 行程管理",
                                "data": "action=quick_reply&type=trip_management"
                            },
                            "style": "primary",
                            "color": THEME_PRIMARY_BLUE,
                            "height": "sm",
                            "flex": 1,
                            "margin": "sm"
                        },
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "⏰ 集合管理",
                                "data": "action=quick_reply&type=tour_clock"
                            },
                            "style": "primary",
                            "color": THEME_PRIMARY_BLUE,
                            "height": "sm",
                            "flex": 1,
                            "margin": "sm"
                        }
                    ],
                    "spacing": "lg",
                    "marginBottom": "lg"
                },
                
                # 第三行：實用工具
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "🛅 置物櫃",
                                "data": "action=quick_reply&type=locker"
                            },
                            "style": "primary",
                            "color": THEME_PRIMARY_BLUE,
                            "height": "sm",
                            "flex": 1,
                            "margin": "sm"
                        },
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "💰 分帳工具",
                                "data": "action=quick_reply&type=split_bill"
                            },
                            "style": "primary",
                            "color": THEME_PRIMARY_BLUE,
                            "height": "sm",
                            "flex": 1,
                            "margin": "sm"
                        }
                    ],
                    "spacing": "lg",
                    "marginBottom": "lg"
                },
                
                # 第四行：個人功能
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "❤️ 我的收藏",
                                "data": "action=quick_reply&type=my_favorites"
                            },
                            "style": "primary",
                            "color": THEME_PRIMARY_BLUE,
                            "height": "sm",
                            "flex": 1,
                            "margin": "sm"
                        }
                    ],
                    "spacing": "lg",
                    "marginBottom": "lg"
                },
                
                # 分隔線
                {
                    "type": "separator",
                    "margin": "xxl"
                },
                
                # 第五行：幫助和設定
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "❓ 功能說明",
                                "data": "action=quick_reply&type=help"
                            },
                            "style": "primary",
                            "color": THEME_PRIMARY_BLUE,
                            "height": "sm",
                            "flex": 1,
                            "margin": "sm"
                        }
                    ],
                    "spacing": "lg"
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
                    "text": "💡 提示：您也可以直接輸入文字來使用功能",
                    "size": "xs",
                    "color": THEME_TEXT_SECONDARY,
                    "align": "center",
                    "wrap": True
                }
            ],
            "paddingAll": "15px"
        }
    }

def handle_quick_reply(params, line_user_id):
    """處理快速回覆"""
    if params is None:
        params = {}
    reply_type = params.get('type')
    rank = params.get('rank', '1')
    
    if reply_type == 'leaderboard_list':
        return create_simple_flex_message("leaderboard_list")
    elif reply_type == 'leaderboard':
        return create_simple_flex_message("leaderboard", rank=rank)
    elif reply_type == 'trip_management':
        return create_simple_flex_message("feature", feature_name="trip_management")
    elif reply_type == 'tour_clock':
        return create_simple_flex_message("feature", feature_name="tour_clock")
    elif reply_type == 'locker':
        return create_simple_flex_message("feature", feature_name="locker")
    elif reply_type == 'split_bill':
        return create_simple_flex_message("feature", feature_name="split_bill")
    elif reply_type == 'my_favorites':
        return create_simple_flex_message("my_favorites", line_user_id=line_user_id)
    elif reply_type == 'help':
        return create_simple_flex_message("feature_menu")
    elif reply_type == 'quick_reply_menu':
        return create_quick_reply_menu()
    else:
        return create_simple_flex_message("default")

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
                            "color": THEME_TEXT_PRIMARY,
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
            {"name": "💰 分帳工具", "data": "action=feature_detail&feature=split_bill"}
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



    elif template_type == "creation_help":
        return create_creation_help()


    elif template_type == "rebind_confirm":
        return create_rebind_confirm()

    elif template_type == "quick_reply_menu":
        return create_quick_reply_menu()

    elif template_type == "leaderboard":
        # 使用分頁系統顯示排行榜詳細資料
        rank = kwargs.get('rank', '1')
        page = kwargs.get('page', 1)

        return create_paginated_leaderboard(int(rank), page)

    elif template_type == "leaderboard_list":
        # 排行榜列表模板 - 僅從網站抓取資料（無模擬回退）
        leaderboard_data = scrape_leaderboard_data()

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
                                    "color": THEME_TEXT_SECONDARY,
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

    elif template_type == "leaderboard_top10":
        # 以 carousel 顯示前10名（來源：資料庫）
        rank_colors = {1: "#FFD700", 2: "#C0C0C0", 3: "#CD7F32", 4: "#4ECDC4", 5: "#FF6B9D"}
        try:
            from api.database import get_database_connection
            connection = get_database_connection()
            results = []
            if connection:
                cursor = connection.cursor(dictionary=True)
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
                LIMIT 10
                """
                cursor.execute(leaderboard_query)
                results = cursor.fetchall() or []
                cursor.close()
                connection.close()
        except Exception as e:
            logger.error(f"查詢 Top10 失敗: {e}")
            results = []

        def build_duration_days(row):
            try:
                if row.get('start_date') and row.get('end_date'):
                    days = (row['end_date'] - row['start_date']).days + 1
                    return f"{days}天{days-1}夜" if days and days > 1 else "1天"
            except Exception:
                return ""
            return ""

        bubbles = []
        for rank in range(1, 11):
            idx = rank - 1
            if idx < len(results):
                row = results[idx]
                color = rank_colors.get(rank, "#6C5CE7")
                title = row.get('title') or f"第{rank}名行程"
                destination = row.get('area') or ""
                duration = build_duration_days(row)

                body_contents = [
                    {"type": "text", "text": title, "weight": "bold", "size": "md", "color": "#333333", "wrap": True}
                ]
                if destination:
                    body_contents.append({"type": "text", "text": f"目的地：{destination}", "size": "sm", "color": "#555555", "margin": "md"})
                if duration:
                    body_contents.append({"type": "text", "text": f"行程天數：{duration}", "size": "sm", "color": "#555555"})

                footer_buttons = [
                    {"type": "button", "action": {"type": "postback", "label": "查看詳細行程 📋", "data": f"action=leaderboard_page&rank={rank}&page=2"}, "style": "primary", "color": color, "height": "sm"},
                    {"type": "button", "action": {"type": "postback", "label": "加入收藏 ❤️", "data": f"action=favorite_add&rank={rank}"}, "style": "secondary", "height": "sm", "margin": "sm"}
                ]

                bubbles.append({
                    "type": "bubble",
                    "size": "kilo",
                    "header": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": f"🏆 第{rank}名", "weight": "bold", "size": "lg", "color": "#ffffff", "align": "center"}
                        ],
                        "backgroundColor": color,
                        "paddingAll": "20px"
                    },
                    "body": {"type": "box", "layout": "vertical", "contents": body_contents, "paddingAll": "20px"},
                    "footer": {"type": "box", "layout": "vertical", "contents": footer_buttons, "paddingAll": "20px"}
                })
            else:
                color = rank_colors.get(rank, "#6C5CE7")
                bubbles.append({
                    "type": "bubble",
                    "size": "kilo",
                    "header": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": f"🏆 第{rank}名", "weight": "bold", "size": "lg", "color": "#ffffff", "align": "center"}
                        ],
                        "backgroundColor": color,
                        "paddingAll": "20px"
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": "無行程內容", "align": "center", "color": "#666666"}
                        ],
                        "paddingAll": "20px"
                    }
                })

        return {"type": "carousel", "contents": bubbles}

    elif template_type == "my_favorites":
        # 顯示使用者收藏的排行榜名次
        line_user_id = kwargs.get('line_user_id')
        favorites = []
        if line_user_id:
            # 先試 DB，再回退記憶體
            try:
                from api.database import get_user_favorites_db
                favorites = get_user_favorites_db(line_user_id)
                if not favorites:
                    favorites = sorted(list(_get_user_favorites_memory(line_user_id)))
            except Exception:
                favorites = sorted(list(_get_user_favorites_memory(line_user_id)))
        if not favorites:
            return {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "您尚未收藏任何行程名次", "align": "center", "color": "#666666", "wrap": True},
                        {"type": "text", "text": "在排行榜卡片點『加入收藏』即可新增", "size": "xs", "align": "center", "color": "#888888", "margin": "md"}
                    ],
                    "paddingAll": "20px"
                }
            }

        # 將收藏的名次轉成 carousel 卡片（每張附移除收藏）
        bubbles = []
        for rank in favorites[:10]:
            sub = create_simple_flex_message("leaderboard", rank=str(rank))
            if sub and sub.get('type') == 'bubble':
                # 附加一個移除收藏按鈕
                sub = dict(sub)  # 淺拷貝
                footer = sub.get('footer') or {"type": "box", "layout": "vertical", "contents": [], "paddingAll": "20px"}
                contents = footer.get('contents', [])
                # 在「我的收藏」清單中，不顯示「加入收藏」按鈕
                filtered_contents = []
                for c in contents:
                    try:
                        action = c.get('action', {})
                        data = action.get('data', '') if isinstance(action, dict) else ''
                        if isinstance(c, dict) and isinstance(action, dict) and isinstance(data, str):
                            if 'action=favorite_add' in data:
                                continue
                    except Exception:
                        pass
                    filtered_contents.append(c)
                contents = filtered_contents
                contents.append({
                    "type": "button",
                    "action": {"type": "postback", "label": "移除收藏 🗑️", "data": f"action=favorite_remove&rank={rank}"},
                    "style": "secondary",
                    "height": "sm",
                    "margin": "sm"
                })
                footer['contents'] = contents
                sub['footer'] = footer
                bubbles.append(sub)
        if not bubbles:
            return {
                "type": "bubble",
                "body": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "暫無有效收藏可顯示", "align": "center", "color": "#666666"}]}
            }
        return {"type": "carousel", "contents": bubbles}

    elif template_type == "locker_nearby_prompt":
        return {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "請分享您目前位置，以尋找附近的置物櫃", "wrap": True, "align": "center", "color": "#555555"}
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
                            "color": THEME_TEXT_SECONDARY,
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

        # 若無資料，回傳提示訊息
        if not trips:
            return {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"抱歉，暫無 {location} 的行程資料",
                            "wrap": True,
                            "color": THEME_TEXT_SECONDARY,
                            "align": "center"
                        }
                    ],
                    "paddingAll": "20px"
                }
            }

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

    # 預設回應：說明情況並提供快速選單
    return {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🤔 需要幫助嗎？",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#ffffff",
                    "align": "center"
                }
            ],
            "backgroundColor": THEME_PRIMARY_BLUE,
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "抱歉，我不太理解您的意思。",
                    "size": "md",
                    "color": THEME_TEXT_PRIMARY,
                    "wrap": True,
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "您可以參考以下快速選單了解所有可用功能，或直接輸入功能名稱來使用。",
                    "size": "sm",
                    "color": THEME_TEXT_SECONDARY,
                    "wrap": True,
                    "margin": "sm"
                }
            ],
            "paddingAll": "24px"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "🎯 查看快速選單",
                        "data": "action=quick_reply&type=quick_reply_menu"
                    },
                    "style": "primary",
                    "color": THEME_PRIMARY_BLUE,
                    "height": "sm"
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

            # 先檢查是否為第 n 名的快速查詢
            parsed = parse_rank_request(user_message)
            if parsed:
                template_key, rank = parsed
                if template_key == "leaderboard":
                    flex_message = create_simple_flex_message("leaderboard", rank=str(rank))
                else:
                    flex_message = create_simple_flex_message("leaderboard_details", rank=str(rank))

                with ApiClient(configuration) as api_client:
                    line_bot_api = MessagingApi(api_client)
                    themed = apply_modern_theme(flex_message)
                    line_bot_api.reply_message_with_http_info(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[FlexMessage(alt_text="TourHub 排行榜", contents=FlexContainer.from_dict(themed))]
                        )
                    )
                return

            # 再檢查是否為內容創建指令
            creation_result = content_creator.parse_and_create(user_message, line_user_id)
            if creation_result:
                response_message = create_creation_response(creation_result)

                with ApiClient(configuration) as api_client:
                    line_bot_api = MessagingApi(api_client)
                    themed = apply_modern_theme(response_message)
                    line_bot_api.reply_message_with_http_info(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[FlexMessage(alt_text="內容創建結果", contents=FlexContainer.from_dict(themed))]
                        )
                    )
                    logger.info("✅ 內容創建結果發送成功")
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

                elif template_config["template"] == "creation_help":
                    flex_message = create_simple_flex_message("creation_help")
                elif template_config["template"] == "user_account":
                    flex_message = create_simple_flex_message("user_account", line_user_id=line_user_id)
                elif template_config["template"] == "binding_status":
                    flex_message = create_simple_flex_message("binding_status", line_user_id=line_user_id)
                elif template_config["template"] == "rebind_confirm":
                    flex_message = create_simple_flex_message("rebind_confirm")
                elif template_config["template"] == "my_favorites":
                    flex_message = create_simple_flex_message("my_favorites", line_user_id=line_user_id)
                elif template_config["template"] == "leaderboard_top10":
                    flex_message = create_simple_flex_message("leaderboard_top10")
                elif template_config["template"] == "locker_nearby_prompt":
                    flex_message = create_simple_flex_message("locker_nearby_prompt")
                elif template_config["template"] == "quick_reply_menu":
                    flex_message = create_simple_flex_message("quick_reply_menu")
                else:
                    # 預設回應
                    flex_message = create_simple_flex_message("default")
            else:
                logger.info("❌ 沒有匹配的模板，使用預設回應")
                flex_message = create_simple_flex_message("default")

            # 發送消息（統一套用藍白主題）
            logger.info(f"📤 準備發送訊息，Flex Message 存在: {bool(flex_message)}")
            if flex_message:
                logger.info(f"📤 Flex Message 類型: {flex_message.get('type', 'N/A')}")

            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                themed = apply_modern_theme(flex_message)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[FlexMessage(alt_text="TourHub Bot", contents=FlexContainer.from_dict(themed))]
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

    # 位置訊息處理（附近置物櫃）
    @line_handler.add(MessageEvent, message=LocationMessageContent)
    def handle_location(event):
        try:
            latitude = getattr(event.message, 'latitude', None)
            longitude = getattr(event.message, 'longitude', None)
            logger.info(f"📍 收到位置: lat={latitude}, lng={longitude}")

            # 使用 locker_service 查詢真實資料
            try:
                from api.locker_service import fetch_nearby_lockers, build_lockers_carousel, store_user_locker_session
                lockers = fetch_nearby_lockers(latitude, longitude)
                # 存儲用戶會話數據
                line_user_id = event.source.user_id if hasattr(event.source, 'user_id') else 'unknown'
                store_user_locker_session(line_user_id, lockers)
                # 顯示第一個置物櫃
                flex_message = build_lockers_carousel(lockers, 0)
            except Exception as e:
                logger.error(f"locker_service 失敗，改回 mock: {e}")
                # 最後回退：一張提示卡
                flex_message = {
                    "type": "bubble",
                    "body": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "暫時無法取得附近置物櫃，稍後再試", "align": "center", "color": "#666666"}], "paddingAll": "20px"}
                }

            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                themed = apply_modern_theme(flex_message)
                response = line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[FlexMessage(alt_text="附近置物櫃", contents=FlexContainer.from_dict(themed))]
                    )
                )
                # 獲取消息ID並更新會話
                if hasattr(response, 'headers') and 'x-line-request-id' in response.headers:
                    message_id = response.headers['x-line-request-id']
                    from api.locker_service import store_user_locker_session
                    store_user_locker_session(line_user_id, lockers, message_id)
                logger.info("✅ 附近置物櫃回覆成功")
        except Exception as e:
            logger.error(f"❌ 處理位置訊息錯誤: {str(e)}")

    # Postback 事件處理（分頁按鈕／收藏）
    @line_handler.add(PostbackEvent)
    def handle_postback(event):
        try:
            postback_data = event.postback.data
            logger.info(f"🔍 收到 postback: {postback_data}")

            # 獲取用戶 ID
            line_user_id = event.source.user_id if hasattr(event.source, 'user_id') else 'unknown'

            # 解析 postback 資料
            params = {}
            for param in postback_data.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value

            action = params.get('action')
            rank = params.get('rank', '1')
            page = int(params.get('page', '1'))

            logger.info(f"🔧 Postback 參數: action={action}, rank={rank}, page={page}, user={line_user_id}")

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
            elif action == 'binding_status':
                # 查看綁定狀態
                logger.info(f"🔧 查看綁定狀態")
                flex_message = create_simple_flex_message("binding_status", line_user_id=line_user_id)
            elif action == 'rebind_confirm':
                # 重新綁定確認
                logger.info(f"🔧 重新綁定確認")
                flex_message = create_simple_flex_message("rebind_confirm")
            elif action == 'rebind_execute' or action == 'rebind_all':
                # 執行重新綁定
                logger.info(f"🔧 執行重新綁定")
                flex_message = execute_rebind(line_user_id)
            elif action == 'locker_next':
                # 置物櫃分頁處理 - 使用push_message更新現有消息
                try:
                    from api.locker_service import build_locker_with_pagination, get_user_message_id
                    current_index = int(params.get('index', 0))
                    logger.info(f"🔧 置物櫃分頁: index={current_index}, user={line_user_id}")
                    
                    # 構建新的Flex Message
                    flex_message = build_locker_with_pagination(line_user_id, current_index)
                    
                    # 使用push_message更新現有消息
                    with ApiClient(configuration) as api_client:
                        line_bot_api = MessagingApi(api_client)
                        
                        # 發送新的Flex Message來替換舊的
                        themed = apply_modern_theme(flex_message)
                        line_bot_api.push_message_with_http_info(
                            PushMessageRequest(
                                to=line_user_id,
                                messages=[FlexMessage(alt_text="附近置物櫃", contents=FlexContainer.from_dict(themed))]
                            )
                        )
                        logger.info("✅ 置物櫃分頁更新成功")
                    
                    # 不返回flex_message，因為已經直接發送了
                    return
                    
                except Exception as e:
                    logger.error(f"❌ 置物櫃分頁處理失敗: {e}")
                    flex_message = create_simple_flex_message("default")
            elif action == 'favorite_add':
                # 加入收藏（排行榜名次）
                try:
                    added = add_favorite(line_user_id, int(rank))
                    if added:
                        notice = f"已加入收藏：第{rank}名"
                    else:
                        notice = f"已在收藏：第{rank}名"
                except Exception:
                    notice = "加入收藏失敗"

                # 回傳簡短通知卡
                flex_message = {
                    "type": "bubble",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": notice, "wrap": True, "align": "center", "color": "#555555"},
                            {"type": "separator", "margin": "lg"},
                            {"type": "text", "text": "輸入『我的收藏』查看清單", "size": "xs", "align": "center", "color": "#888888", "margin": "md"}
                        ],
                        "paddingAll": "20px"
                    }
                }
            elif action == 'favorite_remove':
                # 取消收藏
                try:
                    removed = remove_favorite(line_user_id, int(rank))
                    if removed:
                        notice = f"已移除收藏：第{rank}名"
                    else:
                        notice = f"收藏內沒有：第{rank}名"
                except Exception:
                    notice = "移除收藏失敗"

                flex_message = {
                    "type": "bubble",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": notice, "wrap": True, "align": "center", "color": "#555555"},
                            {"type": "separator", "margin": "lg"},
                            {"type": "text", "text": "輸入『我的收藏』查看清單", "size": "xs", "align": "center", "color": "#888888", "margin": "md"}
                        ],
                        "paddingAll": "20px"
                    }
                }
            elif action == 'quick_reply':
                # 快速回覆處理
                logger.info(f"🔧 處理快速回覆: {params}")
                flex_message = handle_quick_reply(params, line_user_id)


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
