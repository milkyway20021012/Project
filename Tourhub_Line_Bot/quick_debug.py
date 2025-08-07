#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速診斷 not found 問題
"""

import os
from api.index import get_message_template, create_flex_message

def test_binding_flow():
    """測試完整的綁定流程"""
    print("🔍 診斷綁定流程問題")
    print("=" * 50)
    
    # 步驟1: 測試關鍵字匹配
    print("1. 測試關鍵字匹配...")
    template_config = get_message_template("綁定帳號")
    if template_config:
        print(f"   ✅ 關鍵字匹配成功: {template_config}")
    else:
        print("   ❌ 關鍵字匹配失敗")
        return False
    
    # 步驟2: 檢查環境變數
    print("\n2. 檢查LINE Login環境變數...")
    required_vars = [
        'LINE_LOGIN_CHANNEL_ID',
        'LINE_LOGIN_CHANNEL_SECRET',
        'LINE_LOGIN_REDIRECT_URI'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            print(f"   ✅ {var}: {value[:20]}...")
        else:
            print(f"   ❌ {var}: 未設定")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️ 缺少環境變數: {missing_vars}")
        print("這可能是導致 'not found' 的原因！")
        return False
    
    # 步驟3: 測試Flex Message創建
    print("\n3. 測試Flex Message創建...")
    try:
        flex_message = create_flex_message(
            "account_binding",
            line_user_id="test_user_123"
        )
        
        if flex_message:
            print("   ✅ Flex Message創建成功")
            
            # 檢查是否有綁定按鈕
            if 'footer' in flex_message:
                footer = flex_message['footer']
                if 'contents' in footer:
                    for content in footer['contents']:
                        if content.get('type') == 'button':
                            action = content.get('action', {})
                            if action.get('type') == 'uri':
                                uri = action.get('uri', '')
                                print(f"   🔗 綁定URL: {uri[:50]}...")
                                
                                # 檢查URL是否包含必要參數
                                if 'api.line.me/oauth2' in uri:
                                    print("   ✅ LINE Login URL格式正確")
                                else:
                                    print("   ❌ LINE Login URL格式錯誤")
                                    return False
            return True
        else:
            print("   ❌ Flex Message創建失敗")
            return False
            
    except Exception as e:
        print(f"   ❌ Flex Message創建異常: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_line_login_handler():
    """檢查LINE Login處理器"""
    print("\n🔐 檢查LINE Login處理器")
    print("=" * 50)
    
    try:
        from api.line_login_handler import line_login_handler
        
        # 檢查配置
        print(f"Channel ID: {line_login_handler.channel_id}")
        print(f"Channel Secret: {line_login_handler.channel_secret[:10] if line_login_handler.channel_secret else 'None'}...")
        print(f"Redirect URI: {line_login_handler.redirect_uri}")
        
        if not line_login_handler.channel_id:
            print("❌ LINE_LOGIN_CHANNEL_ID 未設定")
            return False
        
        if not line_login_handler.channel_secret:
            print("❌ LINE_LOGIN_CHANNEL_SECRET 未設定")
            return False
        
        if not line_login_handler.redirect_uri:
            print("❌ LINE_LOGIN_REDIRECT_URI 未設定")
            return False
        
        # 測試URL生成
        test_url = line_login_handler.generate_login_url("test_user")
        if test_url:
            print(f"✅ URL生成成功: {test_url[:80]}...")
            return True
        else:
            print("❌ URL生成失敗")
            return False
            
    except Exception as e:
        print(f"❌ LINE Login處理器錯誤: {e}")
        return False

def main():
    """主函數"""
    print("🚀 快速診斷 'not found' 問題")
    print("=" * 60)
    
    # 測試綁定流程
    binding_ok = test_binding_flow()
    
    # 檢查LINE Login處理器
    handler_ok = check_line_login_handler()
    
    print("\n" + "=" * 60)
    print("🎯 診斷結果")
    print("=" * 60)
    
    if binding_ok and handler_ok:
        print("✅ 本地測試正常")
        print("\n💡 'not found' 可能的原因：")
        print("1. Vercel環境變數未正確設定")
        print("2. 代碼未正確部署到Vercel")
        print("3. LINE Login Channel設定錯誤")
        
        print("\n🔧 建議檢查：")
        print("1. 在Vercel Dashboard檢查環境變數")
        print("2. 檢查最新部署是否成功")
        print("3. 確認LINE Login Callback URL設定")
    else:
        print("❌ 發現問題")
        print("\n🔧 需要修復：")
        if not binding_ok:
            print("- 綁定流程有問題")
        if not handler_ok:
            print("- LINE Login處理器有問題")

if __name__ == "__main__":
    main()
