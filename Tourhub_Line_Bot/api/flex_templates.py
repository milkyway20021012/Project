"""
優化的 Flex Message 模板系統
預編譯模板、減少動態生成開銷
"""

import json
import logging
from typing import Dict, Any, Optional
from string import Template
from .advanced_cache import cached

logger = logging.getLogger(__name__)

class FlexTemplateEngine:
    """Flex Message 模板引擎"""
    
    def __init__(self):
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """加載預編譯模板"""
        
        # 排行榜模板
        self.templates['leaderboard'] = {
            "type": "bubble",
            "size": "giga",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "${title}",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#ffffff",
                        "align": "center"
                    }
                ],
                "backgroundColor": "${color}",
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
                            {"type": "text", "text": "目的地：${destination}", "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
                        ],
                        "marginBottom": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "📅", "size": "md", "flex": 0},
                            {"type": "text", "text": "行程天數：${duration}", "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
                        ],
                        "marginBottom": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "👥", "size": "md", "flex": 0},
                            {"type": "text", "text": "參與人數：${participants}", "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
                        ],
                        "marginBottom": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": "💡", "size": "md", "flex": 0},
                            {"type": "text", "text": "特色：${feature}", "size": "sm", "color": "#555555", "flex": 1, "marginStart": "md"}
                        ],
                        "marginBottom": "md"
                    },
                    {"type": "separator", "margin": "md"},
                    {"type": "text", "text": "📋 詳細行程", "weight": "bold", "size": "md", "color": "#555555", "margin": "md"},
                    {"type": "text", "text": "${itinerary}", "size": "xs", "color": "#888888", "wrap": True, "margin": "sm"}
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
                        "color": "${color}",
                        "height": "sm"
                    }
                ],
                "paddingAll": "20px"
            }
        }
        
        # 功能介紹模板
        self.templates['feature'] = {
            "type": "bubble",
            "size": "kilo",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "${title}",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#ffffff",
                        "align": "center"
                    }
                ],
                "backgroundColor": "${color}",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "${description}",
                        "size": "md",
                        "color": "#555555",
                        "align": "center",
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": "${sub_description}",
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
                            "label": "${button_text}",
                            "uri": "${url}"
                        },
                        "style": "primary",
                        "color": "${color}",
                        "height": "sm"
                    }
                ],
                "paddingAll": "20px"
            }
        }
        
        # 行程列表模板
        self.templates['trip_list'] = {
            "type": "bubble",
            "size": "giga",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🗺️ ${location} 行程推薦",
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
                "contents": "${trip_contents}",
                "paddingAll": "20px"
            }
        }
        
        # 錯誤訊息模板
        self.templates['error'] = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "${message}",
                        "wrap": True,
                        "color": "#666666"
                    }
                ],
                "paddingAll": "20px"
            }
        }

        # 地區行程列表模板（簡化版本，不使用字符串替換）
        self.templates['location_trips'] = {
            "type": "bubble",
            "size": "giga",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🗺️ ${location} 行程推薦",
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
                "contents": [],  # 將在運行時填充
                "paddingAll": "20px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "💡 點擊「查看詳情」了解完整行程安排",
                        "size": "xs",
                        "color": "#666666",
                        "align": "center",
                        "wrap": True
                    }
                ],
                "paddingAll": "20px"
            }
        }
        
        logger.info(f"已加載 {len(self.templates)} 個 Flex Message 模板")
    
    @cached(ttl=3600, level="l1")  # 模板渲染結果緩存1小時
    def render_template(self, template_name: str, **kwargs) -> Optional[Dict[str, Any]]:
        """渲染模板"""
        if template_name not in self.templates:
            logger.error(f"模板 {template_name} 不存在")
            return None
        
        try:
            # 獲取模板
            template = self.templates[template_name]
            
            # 轉換為JSON字符串進行替換
            template_str = json.dumps(template)
            
            # 使用 Template 進行安全的字符串替換
            template_obj = Template(template_str)
            
            # 執行替換
            rendered_str = template_obj.safe_substitute(**kwargs)
            
            # 轉換回字典
            rendered_template = json.loads(rendered_str)
            
            return rendered_template
            
        except Exception as e:
            logger.error(f"模板渲染失敗: {template_name} - {e}")
            return None
    
    def create_trip_item(self, trip: Dict[str, Any]) -> Dict[str, Any]:
        """創建行程項目（優化版本）"""
        return {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": trip.get("title", "未知行程"),
                            "weight": "bold",
                            "size": "sm",
                            "color": "#555555"
                        },
                        {
                            "type": "text",
                            "text": f"⏰ {trip.get('duration', '未知')}",
                            "size": "xs",
                            "color": "#888888",
                            "marginTop": "sm"
                        },
                        {
                            "type": "text",
                            "text": f"📍 {trip.get('highlights', '精彩行程')}",
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
                        "data": f"trip_detail:{trip.get('id', '')}"
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
        }

# 全局模板引擎實例
_template_engine = FlexTemplateEngine()

def render_flex_message(template_name: str, **kwargs) -> Optional[Dict[str, Any]]:
    """渲染 Flex Message"""
    return _template_engine.render_template(template_name, **kwargs)

def create_optimized_flex_message(template_type: str, **kwargs) -> Dict[str, Any]:
    """創建優化的 Flex Message"""

    if template_type == "leaderboard":
        return render_flex_message("leaderboard", **kwargs)

    elif template_type == "feature":
        return render_flex_message("feature", **kwargs)

    elif template_type == "trip_list" or template_type == "location_trips":
        # 處理行程列表的特殊邏輯
        trips = kwargs.get('trips', [])
        location = kwargs.get('location', '未知地區')

        if not trips:
            # 沒有找到行程時的訊息
            return render_flex_message("error",
                message=f"抱歉，目前沒有找到 {location} 相關的行程。請嘗試其他地區或稍後再試。"
            )

        # 創建基礎模板
        base_template = _template_engine.templates['location_trips'].copy()

        # 替換標題中的地區名稱
        base_template['header']['contents'][0]['text'] = f"🗺️ {location} 行程推薦"

        # 創建行程內容
        trip_contents = []
        for trip in trips[:5]:  # 最多5個行程
            trip_item = _template_engine.create_trip_item(trip)
            trip_contents.append(trip_item)

        # 設置行程內容
        base_template['body']['contents'] = trip_contents

        return base_template

    else:
        # 默認錯誤訊息
        return render_flex_message("error",
            message="抱歉，我不太理解您的訊息。請嘗試輸入「功能介紹」查看可用功能。"
        )
