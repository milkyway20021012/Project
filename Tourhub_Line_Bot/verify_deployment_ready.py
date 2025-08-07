#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
驗證部署準備狀態
"""

import os
import requests
from api.database_utils import get_database_connection

def check_environment_variables():
    """檢查環境變數"""
    print("🔧 檢查環境變數設定")
    print("=" * 50)
    
    required_vars = {
        'LINE Bot': [
            'CHANNEL_ACCESS_TOKEN',
            'CHANNEL_SECRET'
        ],
        'LINE Login': [
            'LINE_LOGIN_CHANNEL_ID',
            'LINE_LOGIN_CHANNEL_SECRET', 
            'LINE_LOGIN_REDIRECT_URI'
        ],
        'Database': [
            'MYSQL_HOST',
            'MYSQL_USER',
            'MYSQL_PASSWORD',
            'MYSQL_DB'
        ]
    }
    
    all_good = True
    
    for category, vars_list in required_vars.items():
        print(f"\n📋 {category}:")
        for var in vars_list:
            value = os.environ.get(var)
            if value:
                # 隱藏敏感資訊
                if 'PASSWORD' in var or 'SECRET' in var or 'TOKEN' in var:
                    display_value = f"{value[:8]}..." if len(value) > 8 else "***"
                else:
                    display_value = value
                print(f"   ✅ {var}: {display_value}")
            else:
                print(f"   ❌ {var}: 未設定")
                all_good = False
    
    return all_good

def check_database_connection():
    """檢查資料庫連接"""
    print("\n🗄️ 檢查資料庫連接")
    print("=" * 50)
    
    try:
        connection = get_database_connection()
        if connection:
            print("✅ 資料庫連接成功")
            
            # 檢查統一用戶系統表格
            cursor = connection.cursor()
            tables_to_check = [
                'unified_users',
                'website_modules',
                'user_website_bindings',
                'user_operation_logs',
                'system_configs'
            ]
            
            print("\n📊 檢查統一用戶系統表格:")
            for table in tables_to_check:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"   ✅ {table}: {count} 筆記錄")
                except Exception as e:
                    print(f"   ❌ {table}: 錯誤 - {e}")
                    return False
            
            cursor.close()
            connection.close()
            return True
        else:
            print("❌ 資料庫連接失敗")
            return False
    except Exception as e:
        print(f"❌ 資料庫連接異常: {e}")
        return False

def check_line_login_config():
    """檢查LINE Login配置"""
    print("\n🔐 檢查LINE Login配置")
    print("=" * 50)
    
    channel_id = os.environ.get('LINE_LOGIN_CHANNEL_ID')
    channel_secret = os.environ.get('LINE_LOGIN_CHANNEL_SECRET')
    redirect_uri = os.environ.get('LINE_LOGIN_REDIRECT_URI')
    
    if not channel_id:
        print("❌ LINE_LOGIN_CHANNEL_ID 未設定")
        return False
    
    if not channel_secret:
        print("❌ LINE_LOGIN_CHANNEL_SECRET 未設定")
        return False
    
    if not redirect_uri:
        print("❌ LINE_LOGIN_REDIRECT_URI 未設定")
        return False
    
    print(f"✅ Channel ID: {channel_id}")
    print(f"✅ Channel Secret: {channel_secret[:8]}...")
    print(f"✅ Redirect URI: {redirect_uri}")
    
    # 檢查回調URL格式
    if not redirect_uri.startswith('https://'):
        print("⚠️ 回調URL應該使用HTTPS")
        return False
    
    if not redirect_uri.endswith('/auth/line/callback'):
        print("⚠️ 回調URL應該以 /auth/line/callback 結尾")
        return False
    
    return True

def test_line_login_url_generation():
    """測試LINE Login URL生成"""
    print("\n🔗 測試LINE Login URL生成")
    print("=" * 50)
    
    try:
        from api.line_login_handler import line_login_handler
        
        test_user_id = "test_user_123"
        login_url = line_login_handler.generate_login_url(test_user_id)
        
        if login_url:
            print("✅ LINE Login URL生成成功")
            print(f"   URL: {login_url[:100]}...")
            
            # 檢查URL格式
            if 'api.line.me/oauth2/v2.1/authorize' in login_url:
                print("✅ URL格式正確")
                return True
            else:
                print("❌ URL格式不正確")
                return False
        else:
            print("❌ LINE Login URL生成失敗")
            return False
            
    except Exception as e:
        print(f"❌ LINE Login URL生成異常: {e}")
        return False

def check_vercel_deployment():
    """檢查Vercel部署狀態"""
    print("\n🚀 檢查Vercel部署建議")
    print("=" * 50)
    
    redirect_uri = os.environ.get('LINE_LOGIN_REDIRECT_URI')
    if redirect_uri:
        # 提取域名
        domain = redirect_uri.replace('https://', '').replace('/auth/line/callback', '')
        health_check_url = f"https://{domain}/"
        
        print(f"🌐 你的Vercel域名: {domain}")
        print(f"🔍 健康檢查URL: {health_check_url}")
        print(f"🔗 LINE Login回調URL: {redirect_uri}")
        
        print("\n📋 部署檢查清單:")
        print("   1. 確認代碼已推送到GitHub")
        print("   2. 確認Vercel已自動部署")
        print("   3. 確認部署狀態為成功")
        print("   4. 確認環境變數已在Vercel中設定")
        
        return True
    else:
        print("❌ 無法確定Vercel域名")
        return False

def main():
    """主函數"""
    print("🚀 TourHub統一綁定系統部署準備檢查")
    print("=" * 60)
    
    checks = [
        ("環境變數", check_environment_variables),
        ("資料庫連接", check_database_connection),
        ("LINE Login配置", check_line_login_config),
        ("LINE Login URL生成", test_line_login_url_generation),
        ("Vercel部署", check_vercel_deployment)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name}檢查異常: {e}")
            results.append((check_name, False))
    
    # 總結
    print("\n" + "=" * 60)
    print("🎯 檢查結果總結")
    print("=" * 60)
    
    all_passed = True
    for check_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{check_name:20} {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有檢查都通過！")
        print("💡 你現在可以：")
        print("1. 推送代碼到GitHub")
        print("2. 等待Vercel自動部署")
        print("3. 在LINE Bot中輸入「綁定帳號」測試")
    else:
        print("⚠️ 有檢查項目失敗")
        print("💡 請根據上述錯誤訊息進行修正")

if __name__ == "__main__":
    main()
