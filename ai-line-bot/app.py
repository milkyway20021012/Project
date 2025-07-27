import os
import asyncio
import time
from functools import lru_cache
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
from openai import OpenAI
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# LINE 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
line_handler = WebhookHandler(LINE_CHANNEL_SECRET)

# OpenAI GPT 設定
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# 初始化 Flask
app = Flask(__name__)

# 簡單的快取機制
response_cache = {}

@app.route("/", methods=["GET"])
def index():
    return "✅ LINE Bot on Vercel is running."

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)

    print("📩 Received callback from LINE")
    print("📦 Body:", body)

    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        print("❌ Invalid Signature")
        abort(400)

    return 'OK'

@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print("✅ webhook message received")
    process_text_message(event)

def get_cached_response(user_text):
    """檢查快取中是否有相同的回應"""
    return response_cache.get(user_text)

def cache_response(user_text, response):
    """快取回應"""
    if len(response_cache) > 100:  # 限制快取大小
        response_cache.clear()
    response_cache[user_text] = response

def process_text_message(event):
    user_text = event.message.text.strip()
    user_id = event.source.user_id

    # 快速回覆常見問題
    quick_responses = {
        "排行榜": "📊 此功能尚未完善，敬請期待後續更新！",
        "你好": "👋 你好！我是您的智慧助理，有什麼可以幫助您的嗎？",
        "幫助": "🤖 我可以回答您的問題、提供資訊，或與您聊天。請直接輸入您的問題！",
        "hi": "👋 Hi! 我是您的智慧助理，有什麼可以幫助您的嗎？",
        "hello": "👋 Hello! 我是您的智慧助理，有什麼可以幫助您的嗎？",
        "謝謝": "😊 不客氣！很高興能幫助到您！",
        "再見": "👋 再見！有需要隨時找我聊天喔！"
    }
    
    # 檢查是否有快速回覆
    if user_text in quick_responses:
        reply_text = quick_responses[user_text]
    else:
        # 檢查快取
        cached_response = get_cached_response(user_text)
        if cached_response:
            reply_text = cached_response
            print("✅ 使用快取回應")
        else:
            try:
                # 優化的 OpenAI API 調用
                start_time = time.time()
                response = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",  # 可以改為 gpt-3.5-turbo-16k 或 gpt-4-turbo
                    messages=[
                        {"role": "system", "content": "你是 LINE 機器人中的智慧助理，請簡潔明瞭地回答問題，回應長度控制在100字以內。"},
                        {"role": "user", "content": user_text}
                    ],
                    max_tokens=100,  # 進一步限制回應長度以提高速度
                    temperature=0.5,  # 降低創造性以提高一致性
                    timeout=8,  # 縮短超時時間
                    stream=False  # 關閉串流以獲得完整回應
                )
                reply_text = response.choices[0].message.content.strip()
                end_time = time.time()
                print(f"⏱️ API 回應時間：{end_time - start_time:.2f}秒")
                
                # 快取回應
                cache_response(user_text, reply_text)
                
            except Exception as e:
                print(f"⚠️ OpenAI API 錯誤：{str(e)}")
                reply_text = "抱歉，我現在無法回應，請稍後再試。"

    try:
        line_bot_api.push_message(user_id, TextSendMessage(text=reply_text))
    except Exception as e:
        print("⚠️ 推送回覆訊息失敗：", e)

# 本地測試
if __name__ == "__main__":
    app.run(port=8080)
