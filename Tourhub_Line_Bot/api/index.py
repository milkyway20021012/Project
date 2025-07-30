from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import os

app = Flask(__name__)

# 把你自己的 LINE Secret 加上來
line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])

@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is working!"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        return str(e), 400

    return "OK", 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"你說的是：{msg}")
    )

# 這是讓 Vercel 執行 Flask 應用的關鍵
def handler(request, response):
    return app(request.environ, response.start_response)