"""
分頁系統模組
"""

import logging

logger = logging.getLogger(__name__)

def create_paginated_leaderboard(rank, page=1):
    """創建分頁的排行榜詳細資訊"""
    from api.web_scraper import scrape_leaderboard_data
    
    # 獲取資料
    leaderboard_data = scrape_leaderboard_data()
    data = leaderboard_data.get(str(rank))
    
    if not data:
        return None
    
    # 分頁邏輯
    if page == 1:
        # 第一頁：基本資訊
        return {
            "type": "bubble",
            "size": "giga",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": data.get("rank_title", data["title"]),
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
                        "type": "text",
                        "text": data['title'],
                        "weight": "bold",
                        "size": "md",
                        "color": "#333333",
                        "marginBottom": "md"
                    },
                    {
                        "type": "text",
                        "text": f"目的地：{data['destination']}",
                        "size": "sm",
                        "color": "#555555",
                        "marginBottom": "sm"
                    },
                    {
                        "type": "text",
                        "text": f"行程天數：{data['duration']}",
                        "size": "sm",
                        "color": "#555555",
                        "marginBottom": "md"
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
                            "label": "查看詳細行程 📋",
                            "data": f"action=leaderboard_page&rank={rank}&page=2"
                        },
                        "style": "primary",
                        "color": data["color"],
                        "height": "sm"
                    }
                ],
                "paddingAll": "20px"
            }
        }
    
    elif page == 2:
        # 第二頁：詳細行程
        from api.web_scraper import scrape_trip_details
        trip_data = scrape_trip_details(int(rank))
        
        if not trip_data:
            return create_no_content_page(rank, "詳細行程")
        
        return {
            "type": "bubble",
            "size": "giga",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"{trip_data['rank_title']} 詳細行程",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#ffffff",
                        "align": "center"
                    }
                ],
                "backgroundColor": trip_data["color"],
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
                                "text": trip_data["itinerary"],
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
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "返回基本資訊 ⬅️",
                            "data": f"action=leaderboard_page&rank={rank}&page=1"
                        },
                        "style": "secondary",
                        "height": "sm"
                    }
                ],
                "paddingAll": "20px"
            }
        }
    
    return None

def create_paginated_itinerary(rank, page=1):
    """創建分頁的詳細行程"""
    from api.web_scraper import scrape_trip_details
    
    trip_data = scrape_trip_details(int(rank))
    if not trip_data:
        return create_no_content_page(rank, "詳細行程")
    
    # 將行程分割成多頁
    itinerary_lines = trip_data["itinerary_list"]
    items_per_page = 3  # 每頁顯示3個行程項目
    total_pages = (len(itinerary_lines) + items_per_page - 1) // items_per_page
    
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(itinerary_lines))
    page_items = itinerary_lines[start_idx:end_idx]
    
    # 創建頁面內容
    page_content = "\n\n".join(page_items)
    
    # 創建導航按鈕
    footer_buttons = []
    
    if page > 1:
        footer_buttons.append({
            "type": "button",
            "action": {
                "type": "postback",
                "label": "上一頁 ⬅️",
                "data": f"action=itinerary_page&rank={rank}&page={page-1}"
            },
            "style": "secondary",
            "height": "sm",
            "flex": 1
        })
    
    if page < total_pages:
        footer_buttons.append({
            "type": "button",
            "action": {
                "type": "postback",
                "label": "下一頁 ➡️",
                "data": f"action=itinerary_page&rank={rank}&page={page+1}"
            },
            "style": "primary",
            "color": trip_data["color"],
            "height": "sm",
            "flex": 1
        })
    
    # 如果只有一個按鈕，調整佈局
    footer_layout = "horizontal" if len(footer_buttons) > 1 else "vertical"
    if len(footer_buttons) == 1:
        footer_buttons[0].pop("flex", None)
    
    return {
        "type": "bubble",
        "size": "giga",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"{trip_data['rank_title']} 詳細行程",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#ffffff",
                    "align": "center"
                },
                {
                    "type": "text",
                    "text": f"第 {page} 頁 / 共 {total_pages} 頁",
                    "size": "sm",
                    "color": "#ffffff",
                    "align": "center",
                    "margin": "sm"
                }
            ],
            "backgroundColor": trip_data["color"],
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
                            "text": page_content,
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
            "layout": footer_layout,
            "contents": footer_buttons,
            "paddingAll": "20px",
            "spacing": "sm"
        } if footer_buttons else None
    }

def create_no_content_page(rank, content_type):
    """創建無內容頁面"""
    rank_titles = {1: "🥇 第一名", 2: "🥈 第二名", 3: "🥉 第三名", 4: "🏅 第四名", 5: "🎖️ 第五名"}
    rank_colors = {1: "#FFD700", 2: "#C0C0C0", 3: "#CD7F32", 4: "#4ECDC4", 5: "#FF6B9D"}
    
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"抱歉，{rank_titles.get(rank, f'第{rank}名')}的{content_type}暫時無法提供。",
                    "wrap": True,
                    "color": "#666666",
                    "align": "center"
                }
            ],
            "paddingAll": "20px"
        }
    }
