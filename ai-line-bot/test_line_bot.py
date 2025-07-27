#!/usr/bin/env python3
"""
LINE Bot 功能測試腳本
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

def test_line_bot_functionality():
    """測試 LINE Bot 的核心功能"""
    
    # 載入環境變數
    load_dotenv()
    
    print("🧪 LINE Bot 功能測試")
    print("=" * 50)
    
    # 檢查環境變數
    api_key = os.getenv('OPENAI_API_KEY')
    channel_token = os.getenv('CHANNEL_ACCESS_TOKEN')
    channel_secret = os.getenv('CHANNEL_SECRET')
    
    print(f"🔑 OpenAI API 金鑰：{'✅ 已設定' if api_key else '❌ 未設定'}")
    print(f"🔑 LINE Channel Token：{'✅ 已設定' if channel_token else '❌ 未設定'}")
    print(f"🔑 LINE Channel Secret：{'✅ 已設定' if channel_secret else '❌ 未設定'}")
    
    if not api_key:
        print("❌ 錯誤：缺少 OpenAI API 金鑰")
        return False
    
    # 測試 OpenAI 客戶端
    try:
        print("\n🔄 測試 OpenAI 客戶端...")
        client = OpenAI(api_key=api_key)
        print("✅ OpenAI 客戶端創建成功")
        
        # 測試 API 調用
        print("🔄 測試 API 調用...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是 LINE 機器人中的智慧助理，請簡潔明瞭地回答問題，回應長度控制在100字以內。"},
                {"role": "user", "content": "你好"}
            ],
            max_tokens=100,
            temperature=0.5,
            timeout=8,
            stream=False
        )
        
        reply_text = response.choices[0].message.content.strip()
        print(f"✅ API 調用成功")
        print(f"📝 回應內容：{reply_text}")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗：{str(e)}")
        print(f"🔍 錯誤類型：{type(e).__name__}")
        return False

def test_quick_responses():
    """測試快速回覆功能"""
    
    print("\n🚀 測試快速回覆功能")
    print("-" * 30)
    
    quick_responses = {
        "排行榜": "📊 此功能尚未完善，敬請期待後續更新！",
        "你好": "👋 你好！我是您的智慧助理，有什麼可以幫助您的嗎？",
        "幫助": "🤖 我可以回答您的問題、提供資訊，或與您聊天。請直接輸入您的問題！",
        "hi": "👋 Hi! 我是您的智慧助理，有什麼可以幫助您的嗎？",
        "hello": "👋 Hello! 我是您的智慧助理，有什麼可以幫助您的嗎？",
        "謝謝": "😊 不客氣！很高興能幫助到您！",
        "再見": "👋 再見！有需要隨時找我聊天喔！"
    }
    
    test_messages = ["你好", "排行榜", "hi", "幫助"]
    
    for msg in test_messages:
        if msg in quick_responses:
            print(f"✅ '{msg}' -> {quick_responses[msg]}")
        else:
            print(f"❌ '{msg}' -> 需要 API 調用")
    
    return True

if __name__ == "__main__":
    success1 = test_line_bot_functionality()
    success2 = test_quick_responses()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("🎉 所有測試通過！您的 LINE Bot 應該可以正常工作。")
    else:
        print("🔧 部分測試失敗，請檢查設定。") 