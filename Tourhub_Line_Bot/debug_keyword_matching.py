#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
診斷關鍵字匹配問題
"""

from api.index import get_message_template
from api.config import KEYWORD_MAPPINGS

def test_keyword_matching():
    """測試關鍵字匹配功能"""
    print("🔍 診斷關鍵字匹配問題")
    print("=" * 50)
    
    # 測試訊息
    test_messages = [
        "綁定帳號",
        "帳號綁定", 
        "登入",
        "login",
        "Login",
        "綁定",
        "帳號",
        "我的帳號",
        "個人資料",
        "網站操作",
        "功能介紹"
    ]
    
    print("📋 測試關鍵字匹配:")
    for message in test_messages:
        print(f"\n輸入: '{message}'")
        
        try:
            template_config = get_message_template(message)
            if template_config:
                print(f"  ✅ 匹配成功")
                print(f"     模板: {template_config.get('template')}")
                if 'feature_name' in template_config:
                    print(f"     功能: {template_config.get('feature_name')}")
                if 'rank' in template_config:
                    print(f"     排名: {template_config.get('rank')}")
            else:
                print(f"  ❌ 沒有匹配")
        except Exception as e:
            print(f"  ⚠️  錯誤: {e}")

def check_keyword_mappings():
    """檢查關鍵字映射配置"""
    print("\n🗂️ 檢查關鍵字映射配置:")
    print("=" * 50)
    
    for key, config in KEYWORD_MAPPINGS.items():
        print(f"\n📌 {key}:")
        print(f"   模板: {config.get('template')}")
        print(f"   關鍵字: {config.get('keywords')}")
        
        # 特別檢查綁定相關的配置
        if 'account_binding' in key or 'binding' in key.lower():
            print(f"   🔗 這是綁定相關配置")

def test_line_login_handler():
    """測試LINE Login處理器"""
    print("\n🔐 測試LINE Login處理器:")
    print("=" * 50)
    
    try:
        from api.line_login_handler import line_login_handler
        print("✅ LINE Login處理器導入成功")
        
        # 測試創建綁定訊息
        test_user_id = "test_user_123"
        print(f"🧪 測試創建綁定訊息 (用戶ID: {test_user_id})")
        
        binding_message = line_login_handler.create_binding_message(test_user_id)
        if binding_message:
            print("✅ 綁定訊息創建成功")
            print(f"   類型: {binding_message.get('type')}")
            if binding_message.get('header'):
                header_text = binding_message['header']['contents'][0].get('text', '')
                print(f"   標題: {header_text}")
        else:
            print("❌ 綁定訊息創建失敗")
            
    except Exception as e:
        print(f"❌ LINE Login處理器測試失敗: {e}")
        import traceback
        traceback.print_exc()

def test_unified_user_manager():
    """測試統一用戶管理器"""
    print("\n👤 測試統一用戶管理器:")
    print("=" * 50)
    
    try:
        from api.unified_user_manager import unified_user_manager
        print("✅ 統一用戶管理器導入成功")
        
        # 測試資料庫連接
        connection = unified_user_manager.get_database_connection()
        if connection:
            print("✅ 資料庫連接成功")
            connection.close()
        else:
            print("❌ 資料庫連接失敗")
            
        # 測試獲取可用模組
        modules = unified_user_manager.get_available_modules()
        print(f"📱 找到 {len(modules)} 個可用模組")
        for module in modules:
            print(f"   - {module.get('module_display_name')}")
            
    except Exception as e:
        print(f"❌ 統一用戶管理器測試失敗: {e}")
        import traceback
        traceback.print_exc()

def test_create_flex_message():
    """測試Flex Message創建"""
    print("\n💬 測試Flex Message創建:")
    print("=" * 50)
    
    try:
        from api.index import create_flex_message
        print("✅ create_flex_message函數導入成功")
        
        # 測試創建綁定訊息
        test_user_id = "test_user_123"
        print(f"🧪 測試創建account_binding模板")
        
        flex_message = create_flex_message(
            "account_binding",
            line_user_id=test_user_id
        )
        
        if flex_message:
            print("✅ account_binding Flex Message創建成功")
            print(f"   類型: {flex_message.get('type')}")
        else:
            print("❌ account_binding Flex Message創建失敗")
            
    except Exception as e:
        print(f"❌ Flex Message創建測試失敗: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函數"""
    print("🚀 LINE Bot綁定功能診斷工具")
    print("=" * 50)
    
    # 測試關鍵字匹配
    test_keyword_matching()
    
    # 檢查關鍵字映射
    check_keyword_mappings()
    
    # 測試LINE Login處理器
    test_line_login_handler()
    
    # 測試統一用戶管理器
    test_unified_user_manager()
    
    # 測試Flex Message創建
    test_create_flex_message()
    
    print("\n" + "=" * 50)
    print("🎯 診斷完成")
    print("\n💡 如果所有測試都通過，問題可能在於：")
    print("1. LINE Bot Webhook設定")
    print("2. 環境變數配置")
    print("3. Vercel部署狀態")
    print("4. LINE Bot Channel設定")

if __name__ == "__main__":
    main()
