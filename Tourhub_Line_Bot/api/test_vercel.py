#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vercel 測試版本 - 簡化的 Line Bot
用於診斷部署問題
"""

from flask import Flask, request, abort
import os
import logging
import re
from datetime import datetime, timedelta

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

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 建立 Flask app
app = Flask(__name__)

# 簡化的時間解析
def parse_time(user_message):
    """簡化的時間解析"""
    # 下午2:35 格式
    am_pm_match = re.search(r'(下午|上午|晚上|凌晨)\s*(\d{1,2})[:](\d{1,2})', user_message)
    if am_pm_match:
        period = am_pm_match.group(1)
        hour = int(am_pm_match.group(2))
        minute = am_pm_match.group(3)
        
        if period == "下午" and hour != 12:
            hour += 12
        elif period == "晚上" and hour != 12:
            hour += 12
        elif period == "凌晨" and hour == 12:
            hour = 0
        elif period == "上午" and hour == 12:
            hour = 0
        
        return f"{hour:02d}:{minute.zfill(2)}"
    
    # 標準格式 14:30
    time_match = re.search(r'(\d{1,2}:\d{2})', user_message)
    if time_match:
        return time_match.group(1)
    
    return None

# 簡化的地點解析
def parse_location(user_message):
    """簡化的地點解析"""
    common_locations = ["淺草寺", "新宿車站", "澀谷", "銀座", "秋葉原", "原宿", "池袋", "台場"]
    
    for location in common_locations:
        if location in user_message:
            return location
    
    # 簡單的正則匹配
    location_match = re.search(r'([\u4e00-\u9fa5]{2,8})\s*(集合|見面)', user_message)
    if location_match:
        return location_match.group(1)
    
    return None

# 簡化的 Flex Message
def create_simple_flex_message(meeting_time, meeting_location):
    """創建簡化的 Flex Message"""
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
                    "text": f"⏰ 集合時間：{meeting_time}",
                    "size": "md",
                    "color": "#555555",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": f"📍 集合地點：{meeting_location}",
                    "size": "md",
                    "color": "#555555",
                    "margin": "sm"
                },
                {
                    "type": "text",
                    "text": "✅ 集合設定完成！",
                    "weight": "bold",
                    "size": "sm",
                    "color": "#27AE60",
                    "align": "center",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "這是 Vercel 測試版本",
                    "size": "xs",
                    "color": "#888888",
                    "align": "center",
                    "margin": "sm"
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

# 健康檢查
@app.route('/')
def health():
    return {
        "status": "running",
        "bot_configured": configuration is not None,
        "version": "vercel_test_v1.0"
    }

# 除錯端點
@app.route('/debug')
def debug():
    return {
        "has_token": bool(CHANNEL_ACCESS_TOKEN),
        "has_secret": bool(CHANNEL_SECRET),
        "token_length": len(CHANNEL_ACCESS_TOKEN) if CHANNEL_ACCESS_TOKEN else 0,
        "environment": "vercel"
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
            
            # 檢查是否包含集合關鍵字
            if any(keyword in user_message for keyword in ["集合", "見面", "碰面"]):
                meeting_time = parse_time(user_message)
                meeting_location = parse_location(user_message)
                
                logger.info(f"解析結果 - 時間: {meeting_time}, 地點: {meeting_location}")
                
                if meeting_time and meeting_location:
                    # 創建 Flex Message
                    flex_message = create_simple_flex_message(meeting_time, meeting_location)
                    
                    with ApiClient(configuration) as api_client:
                        line_bot_api = MessagingApi(api_client)
                        line_bot_api.reply_message_with_http_info(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[FlexMessage(alt_text="集合設定", contents=FlexContainer.from_dict(flex_message))]
                            )
                        )
                    
                    logger.info("成功發送 Flex Message")
                else:
                    # 發送簡單文字回應
                    with ApiClient(configuration) as api_client:
                        line_bot_api = MessagingApi(api_client)
                        line_bot_api.reply_message_with_http_info(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[{
                                    "type": "text",
                                    "text": f"解析結果：\n時間: {meeting_time or '未識別'}\n地點: {meeting_location or '未識別'}\n\n請使用格式如：下午2:35 淺草寺集合"
                                }]
                            )
                        )
            else:
                # 回應測試訊息
                with ApiClient(configuration) as api_client:
                    line_bot_api = MessagingApi(api_client)
                    line_bot_api.reply_message_with_http_info(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[{
                                "type": "text",
                                "text": f"收到訊息: {user_message}\n\n這是 Vercel 測試版本。\n請嘗試輸入：下午2:35 淺草寺集合"
                            }]
                        )
                    )
                
        except Exception as e:
            logger.error(f"處理訊息錯誤: {str(e)}")

# Vercel 入口點
if __name__ == "__main__":
    app.run(debug=True, port=5000)
