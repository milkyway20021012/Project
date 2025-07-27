#!/usr/bin/env python3
"""
OpenAI API 金鑰測試腳本
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

def test_api_key():
    """測試 OpenAI API 金鑰"""
    
    # 載入環境變數
    load_dotenv()
    
    # 獲取 API 金鑰
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ 錯誤：找不到 OPENAI_API_KEY 環境變數")
        return False
    
    print(f"🔑 API 金鑰格式：{api_key[:20]}...")
    
    # 檢查金鑰格式
    if api_key.startswith('sk-proj-'):
        print("⚠️  警告：檢測到舊格式的 API 金鑰 (sk-proj-...)")
        print("   建議：請前往 https://platform.openai.com/account/api-keys 獲取新的金鑰")
        print("   新金鑰應該以 'sk-' 開頭")
    
    try:
        # 創建 OpenAI 客戶端
        client = OpenAI(api_key=api_key)
        
        # 測試 API 調用
        print("🔄 正在測試 API 連接...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        
        print("✅ API 測試成功！")
        print(f"📝 回應：{response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ API 測試失敗：{str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 OpenAI API 金鑰測試")
    print("=" * 40)
    
    success = test_api_key()
    
    print("=" * 40)
    if success:
        print("🎉 您的 API 金鑰工作正常！")
    else:
        print("�� 請檢查您的 API 金鑰設定") 