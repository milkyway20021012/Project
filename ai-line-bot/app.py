import os
import asyncio
import time
import logging
from functools import lru_cache
from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
from openai import OpenAI
from dotenv import load_dotenv

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 載入環境變數
load_dotenv()

# 檢查環境變數
def check_environment():
    """檢查必要的環境變數"""
    required_vars = {
        'CHANNEL_ACCESS_TOKEN': os.getenv('CHANNEL_ACCESS_TOKEN'),
        'CHANNEL_SECRET': os.getenv('CHANNEL_SECRET'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY')
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        logger.error(f"缺少環境變數: {missing_vars}")
        return False
    
    logger.info("所有環境變數都已正確設定")
    return True

# LINE 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    logger.error("LINE Bot 環境變數未設定")
else:
    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
    line_handler = WebhookHandler(LINE_CHANNEL_SECRET)
    logger.info("LINE Bot 初始化成功")

# OpenAI GPT 設定
openai_api_key = os.getenv('OPENAI_API_KEY')
if openai_api_key:
    openai_client = OpenAI(api_key=openai_api_key)
    logger.info("OpenAI 客戶端初始化成功")
else:
    logger.error("OpenAI API 金鑰未設定")
    openai_client = None

# 初始化 Flask
app = Flask(__name__)

# 設定 Flask 錯誤處理
@app.errorhandler(500)
def internal_error(error):
    """處理 500 錯誤"""
    logger.error(f"500 錯誤: {error}")
    return jsonify({
        "error": "Internal Server Error",
        "message": "應用程式發生內部錯誤",
        "timestamp": time.time()
    }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """處理所有未捕獲的異常"""
    logger.error(f"未捕獲的異常: {str(e)}")
    return jsonify({
        "error": "Application Error",
        "message": str(e),
        "timestamp": time.time()
    }), 500

# 簡單的快取機制
response_cache = {}

@app.route("/", methods=["GET"])
def index():
    """首頁端點"""
    try:
        # 檢查環境變數
        env_status = check_environment()
        
        return jsonify({
            "message": "✅ LINE Bot on Vercel is running.",
            "environment_ok": env_status,
            "timestamp": time.time()
        })
    except Exception as e:
        logger.error(f"首頁端點錯誤: {str(e)}")
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500

@app.route("/test", methods=["GET"])
def test():
    """簡單測試端點"""
    try:
        return jsonify({
            "status": "ok",
            "message": "測試端點正常運作",
            "timestamp": time.time()
        })
    except Exception as e:
        logger.error(f"測試端點錯誤: {str(e)}")
        return jsonify({
            "error": "Test Error",
            "message": str(e)
        }), 500

@app.route("/health", methods=["GET"])
def health():
    """健康檢查端點"""
    try:
        # 基本檢查
        basic_status = {
            "app_loaded": True,
            "timestamp": time.time(),
            "environment": "production"
        }
        
        # 嘗試檢查環境變數（不讓它導致整個端點失敗）
        try:
            env_status = check_environment()
            basic_status["environment_ok"] = env_status
            basic_status["environment_variables"] = {
                "line_token_set": bool(LINE_CHANNEL_ACCESS_TOKEN),
                "line_secret_set": bool(LINE_CHANNEL_SECRET),
                "openai_key_set": bool(openai_api_key)
            }
        except Exception as env_error:
            logger.error(f"環境變數檢查錯誤: {str(env_error)}")
            basic_status["environment_ok"] = False
            basic_status["environment_error"] = str(env_error)
        
        return jsonify(basic_status)
    except Exception as e:
        logger.error(f"健康檢查錯誤: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }), 500

@app.route("/callback", methods=['POST'])
def callback():
    """LINE Webhook 回調端點"""
    try:
        signature = request.headers.get('X-Line-Signature', '')
        body = request.get_data(as_text=True)

        logger.info("📩 Received callback from LINE")
        logger.info(f"📦 Body length: {len(body)}")

        # 檢查 LINE Bot 是否已初始化
        if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
            logger.error("LINE Bot 未正確初始化")
            return jsonify({"error": "LINE Bot not configured"}), 500

        try:
            line_handler.handle(body, signature)
            logger.info("✅ LINE webhook 處理成功")
            return 'OK'
        except InvalidSignatureError:
            logger.error("❌ Invalid Signature")
            return jsonify({"error": "Invalid signature"}), 400
        except Exception as e:
            logger.error(f"❌ LINE webhook 處理錯誤: {str(e)}")
            return jsonify({"error": str(e)}), 500
            
    except Exception as e:
        logger.error(f"❌ Callback 端點錯誤: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """處理文字訊息"""
    try:
        logger.info("✅ webhook message received")
        process_text_message(event)
    except Exception as e:
        logger.error(f"❌ 處理訊息錯誤: {str(e)}")
        # 嘗試發送錯誤訊息給用戶
        try:
            if 'line_bot_api' in globals():
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="抱歉，處理您的訊息時發生錯誤，請稍後再試。")
                )
        except Exception as reply_error:
            logger.error(f"❌ 發送錯誤回覆失敗: {str(reply_error)}")

def get_cached_response(user_text):
    """檢查快取中是否有相同的回應"""
    return response_cache.get(user_text)

def cache_response(user_text, response):
    """快取回應"""
    if len(response_cache) > 100:  # 限制快取大小
        response_cache.clear()
    response_cache[user_text] = response

def process_text_message(event):
    """處理文字訊息"""
    user_text = event.message.text.strip()
    user_id = event.source.user_id
    
    # 調試資訊
    logger.info(f"🔍 處理訊息：{user_text}")
    logger.info(f"🔑 API 金鑰狀態：{'已設定' if os.getenv('OPENAI_API_KEY') else '未設定'}")
    if os.getenv('OPENAI_API_KEY'):
        logger.info(f"🔑 API 金鑰格式：{os.getenv('OPENAI_API_KEY')[:20]}...")

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
        logger.info("✅ 使用快速回覆")
    else:
        # 檢查快取
        cached_response = get_cached_response(user_text)
        if cached_response:
            reply_text = cached_response
            logger.info("✅ 使用快取回應")
        else:
            # 檢查 OpenAI 客戶端是否可用
            if not openai_client:
                logger.error("OpenAI 客戶端未初始化")
                reply_text = "抱歉，AI 服務暫時無法使用，請稍後再試。"
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
                    logger.info(f"⏱️ API 回應時間：{end_time - start_time:.2f}秒")
                    
                    # 快取回應
                    cache_response(user_text, reply_text)
                    
                except Exception as e:
                    logger.error(f"⚠️ OpenAI API 錯誤：{str(e)}")
                    logger.error(f"🔍 錯誤詳情：{type(e).__name__}")
                    # 更詳細的錯誤處理
                    if "invalid_api_key" in str(e).lower():
                        reply_text = "抱歉，API 金鑰設定有問題，請聯繫管理員。"
                    elif "rate_limit" in str(e).lower():
                        reply_text = "抱歉，API 使用量已達上限，請稍後再試。"
                    elif "timeout" in str(e).lower():
                        reply_text = "抱歉，回應超時，請稍後再試。"
                    else:
                        reply_text = "抱歉，我現在無法回應，請稍後再試。"

    try:
        line_bot_api.push_message(user_id, TextSendMessage(text=reply_text))
        logger.info("✅ 訊息發送成功")
    except Exception as e:
        logger.error(f"⚠️ 推送回覆訊息失敗：{str(e)}")
        # 嘗試使用 reply_message 作為備用方案
        try:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )
            logger.info("✅ 使用 reply_message 發送成功")
        except Exception as reply_error:
            logger.error(f"❌ reply_message 也失敗：{str(reply_error)}")

# 本地測試
if __name__ == "__main__":
    app.run(port=8080)

# Vercel 部署所需
app.debug = False
