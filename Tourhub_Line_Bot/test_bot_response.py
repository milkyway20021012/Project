#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試Bot回應功能
"""

import json
from api.index import get_message_template, create_flex_message

def test_binding_response():
    """測試綁定帳號回應"""
    print("🤖 測試Bot綁定帳號回應")
    print("=" * 50)
    
    test_message = "綁定帳號"
    test_user_id = "test_user_123"
    
    print(f"📝 測試訊息: '{test_message}'")
    print(f"👤 測試用戶ID: {test_user_id}")
    
    # 步驟1: 測試關鍵字匹配
    print("\n🔍 步驟1: 測試關鍵字匹配")
    template_config = get_message_template(test_message)
    if template_config:
        print(f"✅ 關鍵字匹配成功")
        print(f"   模板類型: {template_config.get('template')}")
    else:
        print(f"❌ 關鍵字匹配失敗")
        return False
    
    # 步驟2: 測試Flex Message創建
    print("\n💬 步驟2: 測試Flex Message創建")
    try:
        flex_message = create_flex_message(
            template_config["template"],
            line_user_id=test_user_id
        )
        
        if flex_message:
            print("✅ Flex Message創建成功")
            print(f"   類型: {flex_message.get('type')}")
            
            # 檢查是否有綁定按鈕
            if 'footer' in flex_message:
                footer_contents = flex_message['footer'].get('contents', [])
                for content in footer_contents:
                    if content.get('type') == 'button':
                        action = content.get('action', {})
                        if action.get('type') == 'uri':
                            print(f"   🔗 找到綁定按鈕: {action.get('label')}")
                            print(f"   🌐 綁定URL: {action.get('uri')}")
            
            return True
        else:
            print("❌ Flex Message創建失敗")
            return False
            
    except Exception as e:
        print(f"❌ Flex Message創建異常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_other_keywords():
    """測試其他關鍵字"""
    print("\n🧪 測試其他關鍵字")
    print("=" * 50)
    
    test_cases = [
        "功能介紹",
        "第一名", 
        "網站操作",
        "東京"
    ]
    
    for message in test_cases:
        print(f"\n📝 測試: '{message}'")
        template_config = get_message_template(message)
        if template_config:
            print(f"   ✅ 匹配成功 - 模板: {template_config.get('template')}")
        else:
            print(f"   ❌ 匹配失敗")

def simulate_line_webhook():
    """模擬LINE Webhook請求"""
    print("\n🔗 模擬LINE Webhook請求")
    print("=" * 50)
    
    # 模擬LINE Bot收到的訊息格式
    mock_event = {
        "type": "message",
        "message": {
            "type": "text",
            "text": "綁定帳號"
        },
        "source": {
            "type": "user",
            "userId": "test_user_123"
        },
        "replyToken": "mock_reply_token"
    }
    
    print("📨 模擬收到訊息:")
    print(json.dumps(mock_event, indent=2, ensure_ascii=False))
    
    # 提取訊息內容
    user_message = mock_event["message"]["text"]
    user_id = mock_event["source"]["userId"]
    
    print(f"\n🔍 處理訊息: '{user_message}'")
    print(f"👤 用戶ID: {user_id}")
    
    # 測試處理流程
    template_config = get_message_template(user_message)
    if template_config:
        print(f"✅ 找到匹配模板: {template_config.get('template')}")
        
        try:
            flex_message = create_flex_message(
                template_config["template"],
                line_user_id=user_id
            )
            
            if flex_message:
                print("✅ 準備發送Flex Message")
                print("📤 在實際環境中，這裡會調用LINE API發送訊息")
                return True
            else:
                print("❌ Flex Message創建失敗")
                return False
                
        except Exception as e:
            print(f"❌ 處理異常: {e}")
            return False
    else:
        print("❌ 沒有找到匹配的模板")
        return False

def main():
    """主函數"""
    print("🚀 LINE Bot回應測試")
    print("=" * 50)
    
    # 測試綁定回應
    success1 = test_binding_response()
    
    # 測試其他關鍵字
    test_other_keywords()
    
    # 模擬Webhook請求
    success2 = simulate_line_webhook()
    
    print("\n" + "=" * 50)
    print("🎯 測試結果總結")
    print(f"綁定功能測試: {'✅ 通過' if success1 else '❌ 失敗'}")
    print(f"Webhook模擬測試: {'✅ 通過' if success2 else '❌ 失敗'}")
    
    if success1 and success2:
        print("\n🎉 所有測試通過！")
        print("💡 如果LINE Bot仍然沒有回應，請檢查：")
        print("1. Vercel部署是否成功")
        print("2. LINE Bot Webhook URL是否正確")
        print("3. LINE Bot Channel設定是否正確")
        print("4. 環境變數是否正確設定")
    else:
        print("\n⚠️ 有測試失敗，請檢查上述錯誤訊息")

if __name__ == "__main__":
    main()
