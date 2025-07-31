#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TourHub Line Bot 集合功能使用示例
展示如何處理用戶輸入並生成 Flex Message
"""

import sys
import os
import json
import re
from datetime import datetime, timedelta

# 添加 api 目錄到路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from config import TIME_PATTERNS, MEETING_TIME_PATTERN, MESSAGE_TEMPLATES

def parse_time(user_message):
    """解析各種時間格式"""
    
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
    
    # 處理小數點格式 - 例如：2.35
    decimal_time_match = re.search(TIME_PATTERNS["decimal_time"], user_message)
    if decimal_time_match:
        hour = decimal_time_match.group(1)
        minute = decimal_time_match.group(2)
        return f"{hour.zfill(2)}:{minute.zfill(2)}"
    
    # 處理上午/下午/晚上/凌晨 (簡化格式) - 例如：晚上7點
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
        elif period == "上午" and hour == 12:
            hour = 0

        return f"{hour:02d}:00"

    # 標準時間格式 14:30
    time_match = re.search(TIME_PATTERNS["standard"], user_message)
    if time_match:
        return time_match.group(1)

    return None

def parse_location(user_message):
    """解析集合地點"""
    # 預設地點列表
    common_locations = [
        "東京鐵塔", "淺草寺", "新宿車站", "澀谷", "銀座", "秋葉原", "原宿", "池袋", "台場", "築地市場",
        "上野公園", "阿美橫町", "大阪城", "道頓堀", "心齋橋", "環球影城", "天保山", "海遊館", "梅田",
        "通天閣", "新世界", "金閣寺", "龍安寺", "二条城", "清水寺", "地主神社", "祇園", "伏見稻荷大社"
    ]

    # 優先檢查預設地點列表
    for location in common_locations:
        if location in user_message:
            return location

    # 使用正則表達式提取地點 - 改進版本
    location_patterns = [
        # 匹配時間後面的地點 + 集合動詞
        r'(?:\d{1,2}[:.]\d{2}|[上下晚凌][午上]\d{1,2}[點:]?\d{0,2}分?)\s*([\u4e00-\u9fa5A-Za-z0-9]+?)\s*(集合|見面|碰面|會合)',
        # 匹配地點 + 集合動詞
        r'([\u4e00-\u9fa5A-Za-z0-9]{2,8})\s*(集合|見面|碰面|會合)',
        # 匹配帶有地標後綴的地點
        r'([\u4e00-\u9fa5A-Za-z0-9]{2,8})(車站|寺|公園|廣場|商場|大樓|塔|橋|市場|通|町|村|城|館|園|山|湖|溫泉)'
    ]

    for pattern in location_patterns:
        match = re.search(pattern, user_message)
        if match:
            location = match.group(1).strip()
            # 過濾掉數字和時間相關詞彙
            if not re.match(r'^\d+$', location) and location not in ['上午', '下午', '晚上', '凌晨']:
                if len(location) >= 2:
                    return location

    return None

def create_meeting_success_flex_message(meeting_time, meeting_location, meeting_id=None):
    """創建集合設定成功的 Flex Message"""
    template = MESSAGE_TEMPLATES["meeting_success"]
    
    # 計算提醒時間
    try:
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
                        {"type": "text", "text": f"狀態：{template['status_success']}", "size": "sm", "color": template["status_success_color"], "flex": 1, "marginStart": "md"}
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

def process_meeting_message(user_message):
    """處理集合訊息"""
    print(f"處理用戶訊息: {user_message}")
    
    # 檢查是否匹配集合模式
    if not re.search(MEETING_TIME_PATTERN, user_message):
        print("❌ 不匹配集合模式")
        return None
    
    # 解析時間和地點
    meeting_time = parse_time(user_message)
    meeting_location = parse_location(user_message)
    
    print(f"解析結果:")
    print(f"  時間: {meeting_time}")
    print(f"  地點: {meeting_location}")
    
    if meeting_time and meeting_location:
        # 生成 Flex Message
        flex_message = create_meeting_success_flex_message(meeting_time, meeting_location)
        print("✅ 成功生成 Flex Message")
        return flex_message
    else:
        print("❌ 解析失敗")
        return None

def main():
    """主函數 - 示例用法"""
    print("=== TourHub Line Bot 集合功能示例 ===\n")
    
    # 測試案例
    test_messages = [
        "下午2:35 淺草寺集合",
        "14:30 新宿車站見面",
        "晚上7點 銀座碰面",
        "2.35 澀谷集合"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"--- 測試 {i} ---")
        flex_message = process_meeting_message(message)
        
        if flex_message:
            # 保存 Flex Message 到文件
            filename = f"flex_message_example_{i}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(flex_message, f, ensure_ascii=False, indent=2)
            print(f"💾 Flex Message 已保存到 {filename}")
        
        print()

if __name__ == "__main__":
    main()
