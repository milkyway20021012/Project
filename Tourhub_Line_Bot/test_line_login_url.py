#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試LINE Login URL生成
"""

import os

def test_line_login_url():
    """測試LINE Login URL生成"""
    print("🔗 測試LINE Login URL生成")
    print("=" * 50)
    
    # 設定測試環境變數
    os.environ['LINE_LOGIN_CHANNEL_ID'] = 'test_channel_id'
    os.environ['LINE_LOGIN_CHANNEL_SECRET'] = 'test_channel_secret'
    os.environ['LINE_LOGIN_REDIRECT_URI'] = 'https://line-bot-theta-dun.vercel.app/auth/line/callback'
    
    try:
        from api.line_login_handler import line_login_handler
        
        test_user_id = "test_user_123"
        login_url = line_login_handler.generate_login_url(test_user_id)
        
        if login_url:
            print("✅ LINE Login URL生成成功")
            print(f"URL: {login_url}")
            
            # 檢查URL組成
            if 'api.line.me/oauth2/v2.1/authorize' in login_url:
                print("✅ 使用正確的LINE Login端點")
            else:
                print("❌ LINE Login端點不正確")
                
            if 'client_id=test_channel_id' in login_url:
                print("✅ Channel ID正確包含")
            else:
                print("❌ Channel ID未包含")
                
            if 'redirect_uri=https%3A//line-bot-theta-dun.vercel.app/auth/line/callback' in login_url:
                print("✅ Redirect URI正確包含")
            else:
                print("❌ Redirect URI不正確")
                print("   期望: https%3A//line-bot-theta-dun.vercel.app/auth/line/callback")
                
        else:
            print("❌ LINE Login URL生成失敗")
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

def check_environment_setup():
    """檢查環境設定"""
    print("\n🔧 檢查環境設定")
    print("=" * 50)
    
    required_vars = [
        'LINE_LOGIN_CHANNEL_ID',
        'LINE_LOGIN_CHANNEL_SECRET', 
        'LINE_LOGIN_REDIRECT_URI'
    ]
    
    print("需要在Vercel中設定的環境變數:")
    for var in required_vars:
        if var == 'LINE_LOGIN_REDIRECT_URI':
            print(f"   {var}=https://line-bot-theta-dun.vercel.app/auth/line/callback")
        else:
            print(f"   {var}=你的{var.lower()}")

def main():
    """主函數"""
    print("🚀 LINE Login URL 測試工具")
    print("=" * 60)
    
    test_line_login_url()
    check_environment_setup()
    
    print("\n" + "=" * 60)
    print("🎯 下一步操作:")
    print("1. 在LINE Developers Console設定正確的Callback URL")
    print("2. 在Vercel設定正確的環境變數")
    print("3. 重新測試綁定功能")

if __name__ == "__main__":
    main()
