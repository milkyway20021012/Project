#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
簡單的本地 Line Bot 集合管理系統
不依賴外部部署，直接在本地運行
"""

import os
import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, 
    FlexSendMessage, PostbackEvent
)
import re

app = Flask(__name__)

# Line Bot 設定 (請在這裡填入您的憑證)
CHANNEL_ACCESS_TOKEN = 'YOUR_CHANNEL_ACCESS_TOKEN'  # 請替換為您的 Token
CHANNEL_SECRET = 'YOUR_CHANNEL_SECRET'  # 請替換為您的 Secret

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 資料庫設定
DB_PATH = 'meetings.db'

def init_database():
    """初始化資料庫"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                meeting_name TEXT NOT NULL,
                meeting_time TEXT NOT NULL,
                meeting_location TEXT NOT NULL,
                meeting_date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active',
                reminder_10min_sent BOOLEAN DEFAULT FALSE,
                reminder_5min_sent BOOLEAN DEFAULT FALSE,
                reminder_on_time_sent BOOLEAN DEFAULT FALSE
            )
        ''')
        conn.commit()

# 時間解析模式
TIME_PATTERNS = {
    "am_pm": r'(上午|下午|晚上|凌晨)\s*(\d{1,2})[點:](\d{1,2})',
    "am_pm_simple": r'(上午|下午|晚上|凌晨)\s*(\d{1,2})',
    "natural_time": r'(\d{1,2})點半|(\d{1,2})點30分',
    "chinese": r'(\d{1,2})點(\d{1,2})分',
    "simple_chinese": r'(\d{1,2})點',
    "standard": r'(\d{1,2}:\d{2})',
    "time_with_colon": r'(\d{1,2}):(\d{1,2})'
}

# 集合關鍵字模式
MEETING_KEYWORDS = ['集合', '見面', '約', '約在', '在', '到', '見', '碰面', '會合']

def parse_time(user_message):
    """解析各種時間格式"""
    # 優先處理上午/下午/晚上/凌晨 (完整格式) - 例如：下午2:35
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
    
    # 標準時間格式 14:30
    time_match = re.search(TIME_PATTERNS["standard"], user_message)
    if time_match:
        return time_match.group(1)
    
    # 處理冒號格式
    colon_time_match = re.search(TIME_PATTERNS["time_with_colon"], user_message)
    if colon_time_match:
        hour = colon_time_match.group(1)
        minute = colon_time_match.group(2)
        return f"{hour.zfill(2)}:{minute.zfill(2)}"
    
    return None

def parse_location(user_message):
    """解析集合地點"""
    # 常見地點列表
    common_locations = [
        '淺草寺', '新宿車站', '澀谷', '銀座', '秋葉原', '原宿', '池袋', '台場',
        '築地市場', '上野公園', '東京鐵塔', '大阪城', '道頓堀', '心齋橋',
        '環球影城', '天保山', '海遊館', '梅田', '通天閣', '新世界'
    ]
    
    # 優先檢查預設地點列表
    for location in common_locations:
        if location in user_message:
            return location
    
    # 使用正則表達式提取地點
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
            location = location.strip()
            if len(location) >= 2:
                return location
    
    # 如果還是找不到，嘗試提取中文地名
    chinese_location_match = re.search(r'([\u4e00-\u9fa5]{2,10})', user_message)
    if chinese_location_match:
        return chinese_location_match.group(1)
    
    return None

def is_meeting_message(user_message):
    """檢查是否為集合訊息"""
    return any(keyword in user_message for keyword in MEETING_KEYWORDS)

def create_meeting_success_flex(meeting_time, meeting_location, meeting_id):
    """創建集合成功 Flex Message"""
    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "📍 集合設定成功",
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
                    "text": f"⏰ 時間：{meeting_time}",
                    "size": "md",
                    "color": "#27AE60",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": f"📍 地點：{meeting_location}",
                    "size": "md",
                    "color": "#27AE60",
                    "margin": "sm"
                },
                {
                    "type": "text",
                    "text": "✅ 智能提醒已啟用",
                    "size": "md",
                    "color": "#27AE60",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "• 集合前 10 分鐘提醒\n• 集合前 5 分鐘提醒\n• 集合時間到提醒",
                    "size": "sm",
                    "color": "#888888",
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
                        "label": "查看我的集合",
                        "data": "view_meetings"
                    },
                    "style": "primary",
                    "color": "#9B59B6",
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
                    "color": "#9B59B6",
                    "height": "sm",
                    "marginTop": "sm"
                }
            ],
            "paddingAll": "20px"
        }
    }

def create_meeting_list_flex(meetings):
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

def create_meeting(user_id, meeting_time, meeting_location):
    """創建集合"""
    try:
        # 生成集合名稱
        current_date = datetime.now().strftime("%m月%d日")
        meeting_name = f"{current_date} {meeting_location}集合"
        meeting_date = datetime.now().strftime("%Y-%m-%d")
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO meetings 
                (user_id, meeting_name, meeting_time, meeting_location, meeting_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, meeting_name, meeting_time, meeting_location, meeting_date))
            
            meeting_id = cursor.lastrowid
            conn.commit()
            
            return True, meeting_id
            
    except Exception as e:
        print(f"創建集合失敗: {str(e)}")
        return False, None

def get_user_meetings(user_id):
    """獲取用戶的集合列表"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, meeting_name, meeting_time, meeting_location, meeting_date
                FROM meetings 
                WHERE user_id = ? AND status = 'active'
                ORDER BY meeting_date, meeting_time
            ''', (user_id,))
            
            meetings = []
            for row in cursor.fetchall():
                meetings.append({
                    "id": row[0],
                    "meeting_name": row[1],
                    "meeting_time": row[2],
                    "meeting_location": row[3],
                    "meeting_date": row[4]
                })
            
            return meetings
            
    except Exception as e:
        print(f"獲取用戶集合失敗: {str(e)}")
        return []

def cancel_meeting(meeting_id, user_id):
    """取消集合"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE meetings 
                SET status = 'cancelled' 
                WHERE id = ? AND user_id = ?
            ''', (meeting_id, user_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                return True, "集合已取消"
            else:
                return False, "找不到指定的集合或無權限取消"
                
    except Exception as e:
        print(f"取消集合失敗: {str(e)}")
        return False, "取消集合失敗"

def get_pending_reminders():
    """獲取待發送的提醒"""
    try:
        current_time = datetime.now()
        current_date = current_time.strftime("%Y-%m-%d")
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, user_id, meeting_name, meeting_time, meeting_location,
                       reminder_10min_sent, reminder_5min_sent, reminder_on_time_sent
                FROM meetings 
                WHERE meeting_date = ? AND status = 'active'
            ''', (current_date,))
            
            reminders = []
            for row in cursor.fetchall():
                meeting_id, user_id, meeting_name, meeting_time, meeting_location, \
                reminder_10min_sent, reminder_5min_sent, reminder_on_time_sent = row
                
                # 計算時間差
                meeting_datetime = datetime.strptime(f"{current_date} {meeting_time}", "%Y-%m-%d %H:%M")
                time_diff = meeting_datetime - current_time
                minutes_diff = int(time_diff.total_seconds() / 60)
                
                # 檢查是否需要發送提醒
                if minutes_diff == 10 and not reminder_10min_sent:
                    reminders.append({
                        "meeting_id": meeting_id,
                        "user_id": user_id,
                        "meeting_name": meeting_name,
                        "meeting_time": meeting_time,
                        "meeting_location": meeting_location,
                        "reminder_type": "10_min_before",
                        "message": f"⏰ 集合提醒：還有 10 分鐘就要在 {meeting_location} 集合了！"
                    })
                
                elif minutes_diff == 5 and not reminder_5min_sent:
                    reminders.append({
                        "meeting_id": meeting_id,
                        "user_id": user_id,
                        "meeting_name": meeting_name,
                        "meeting_time": meeting_time,
                        "meeting_location": meeting_location,
                        "reminder_type": "5_min_before",
                        "message": f"🚨 緊急提醒：還有 5 分鐘就要在 {meeting_location} 集合了！"
                    })
                
                elif minutes_diff == 0 and not reminder_on_time_sent:
                    reminders.append({
                        "meeting_id": meeting_id,
                        "user_id": user_id,
                        "meeting_name": meeting_name,
                        "meeting_time": meeting_time,
                        "meeting_location": meeting_location,
                        "reminder_type": "on_time",
                        "message": f"🎯 集合時間到了！請準時到達 {meeting_location}！"
                    })
            
            return reminders
            
    except Exception as e:
        print(f"獲取待發送提醒失敗: {str(e)}")
        return []

def mark_reminder_sent(meeting_id, reminder_type):
    """標記提醒已發送"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 更新提醒狀態
            if reminder_type == "10_min_before":
                cursor.execute('UPDATE meetings SET reminder_10min_sent = TRUE WHERE id = ?', (meeting_id,))
            elif reminder_type == "5_min_before":
                cursor.execute('UPDATE meetings SET reminder_5min_sent = TRUE WHERE id = ?', (meeting_id,))
            elif reminder_type == "on_time":
                cursor.execute('UPDATE meetings SET reminder_on_time_sent = TRUE WHERE id = ?', (meeting_id,))
            
            conn.commit()
            
    except Exception as e:
        print(f"標記提醒發送失敗: {str(e)}")

def reminder_worker():
    """提醒工作線程"""
    while True:
        try:
            # 獲取待發送的提醒
            reminders = get_pending_reminders()
            
            # 發送提醒
            for reminder in reminders:
                try:
                    # 發送文字提醒
                    line_bot_api.push_message(
                        reminder["user_id"],
                        TextSendMessage(text=reminder["message"])
                    )
                    
                    # 標記為已發送
                    mark_reminder_sent(reminder["meeting_id"], reminder["reminder_type"])
                    
                    print(f"已發送提醒: {reminder['message']} 給用戶 {reminder['user_id']}")
                    
                except Exception as e:
                    print(f"發送提醒失敗: {str(e)}")
            
            # 每分鐘檢查一次
            time.sleep(60)
            
        except Exception as e:
            print(f"提醒線程錯誤: {str(e)}")
            time.sleep(60)

# Line Bot 事件處理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """處理文字訊息"""
    try:
        user_message = event.message.text
        user_id = event.source.user_id
        
        print(f"收到訊息: {user_message} 來自用戶: {user_id}")
        
        # 檢查是否為集合訊息
        if is_meeting_message(user_message):
            # 解析時間和地點
            meeting_time = parse_time(user_message)
            meeting_location = parse_location(user_message)
            
            if meeting_time and meeting_location:
                # 創建集合
                success, meeting_id = create_meeting(user_id, meeting_time, meeting_location)
                
                if success:
                    # 發送成功訊息
                    flex_message = create_meeting_success_flex(meeting_time, meeting_location, meeting_id)
                    line_bot_api.reply_message(
                        event.reply_token,
                        FlexSendMessage(alt_text="集合設定成功", contents=flex_message)
                    )
                    print(f"成功設定集合: {meeting_time} @ {meeting_location}")
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="❌ 集合設定失敗，請稍後再試")
                    )
                    
            elif meeting_time and not meeting_location:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"✅ 時間已識別：{meeting_time}\n❌ 地點未識別\n請明確指定集合地點，例如：淺草寺、新宿車站等")
                )
                
            elif meeting_location and not meeting_time:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"❌ 時間未識別\n✅ 地點已識別：{meeting_location}\n請明確指定集合時間，例如：下午2:35、14:35、2點35分等")
                )
                
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="📝 請輸入包含時間和地點的集合資訊，例如：\n• 下午2:35 淺草寺集合\n• 14:30 新宿車站見面\n• 2點35分 澀谷集合")
                )
        else:
            # 其他訊息
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="🤖 我是 TourHub Bot！\n\n💡 試試輸入：\n• 下午2:35 淺草寺集合\n• 14:30 新宿車站見面\n• 2點35分 澀谷集合")
            )
            
    except Exception as e:
        print(f"處理訊息錯誤: {str(e)}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ 處理訊息時發生錯誤，請稍後再試")
        )

@handler.add(PostbackEvent)
def handle_postback(event):
    """處理 Postback 事件"""
    try:
        postback_data = event.postback.data
        user_id = event.source.user_id
        
        if postback_data == "view_meetings":
            # 查看集合列表
            meetings = get_user_meetings(user_id)
            
            if meetings:
                flex_message = create_meeting_list_flex(meetings)
                line_bot_api.reply_message(
                    event.reply_token,
                    FlexSendMessage(alt_text="我的集合列表", contents=flex_message)
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="📝 目前沒有設定任何集合\n\n💡 試試輸入：\n• 下午2:35 淺草寺集合\n• 14:30 新宿車站見面")
                )
                
        elif postback_data.startswith("cancel_meeting:"):
            # 取消集合
            meeting_id = int(postback_data.split(":")[1])
            success, message = cancel_meeting(meeting_id, user_id)
            
            if success:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"✅ {message}")
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"❌ {message}")
                )
                
    except Exception as e:
        print(f"處理 Postback 錯誤: {str(e)}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ 處理操作時發生錯誤，請稍後再試")
        )

@app.route("/callback", methods=['POST'])
def callback():
    """Line Bot Webhook 端點"""
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

@app.route("/")
def health():
    """健康檢查端點"""
    return {"status": "running", "bot_configured": True}

if __name__ == "__main__":
    # 初始化資料庫
    init_database()
    
    # 啟動提醒線程
    reminder_thread = threading.Thread(target=reminder_worker, daemon=True)
    reminder_thread.start()
    
    print("🤖 TourHub Bot 已啟動！")
    print("📝 請在 Line Bot 中測試：下午2:35 淺草寺集合")
    
    # 啟動 Flask 應用
    app.run(host='0.0.0.0', port=5000, debug=True) 