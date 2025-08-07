#!/usr/bin/env python3
"""
基本功能測試
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_environment():
    """測試環境配置"""
    print("=== 環境配置測試 ===")
    
    # 加載環境變數
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ 環境變數文件加載成功")
    except Exception as e:
        print(f"❌ 環境變數文件加載失敗: {e}")
        return False
    
    # 檢查關鍵環境變數
    channel_token = os.environ.get('CHANNEL_ACCESS_TOKEN')
    channel_secret = os.environ.get('CHANNEL_SECRET')
    
    if channel_token and channel_secret:
        print("✅ LINE Bot 環境變數已設定")
        return True
    else:
        print("❌ LINE Bot 環境變數未設定")
        return False

def test_basic_imports():
    """測試基本導入"""
    print("\n=== 基本導入測試 ===")
    
    try:
        from api.config import KEYWORD_MAPPINGS, MESSAGE_TEMPLATES
        print("✅ 配置文件導入成功")
    except Exception as e:
        print(f"❌ 配置文件導入失敗: {e}")
        return False
    
    try:
        from api.flex_templates import create_optimized_flex_message
        print("✅ Flex 模板導入成功")
    except Exception as e:
        print(f"❌ Flex 模板導入失敗: {e}")
        return False
    
    return True

def test_keyword_matching():
    """測試關鍵字匹配"""
    print("\n=== 關鍵字匹配測試 ===")
    
    try:
        from api.config import KEYWORD_MAPPINGS
        
        test_cases = [
            ("集合", "tour_clock"),
            ("東京", "tokyo_trips"),
            ("功能介紹", "help")
        ]
        
        for message, expected in test_cases:
            found = False
            for mapping_key, mapping in KEYWORD_MAPPINGS.items():
                if any(keyword in message for keyword in mapping["keywords"]):
                    if mapping_key == expected:
                        print(f"✅ '{message}' -> {mapping_key}")
                        found = True
                        break
            
            if not found:
                print(f"❌ '{message}' -> 匹配失敗")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 關鍵字匹配測試失敗: {e}")
        return False

def test_flex_message():
    """測試 Flex Message 生成"""
    print("\n=== Flex Message 測試 ===")
    
    try:
        from api.flex_templates import create_optimized_flex_message
        from api.config import MESSAGE_TEMPLATES
        
        # 測試 TourClock
        template_data = MESSAGE_TEMPLATES["features"]["tour_clock"]
        flex_message = create_optimized_flex_message("feature", **template_data)
        
        if flex_message and flex_message.get('type') == 'bubble':
            print("✅ TourClock Flex Message 生成成功")
        else:
            print("❌ TourClock Flex Message 生成失敗")
            return False
        
        # 測試地區行程（使用樣本數據）
        sample_trips = [
            {
                "id": "1",
                "title": "測試行程",
                "duration": "3天",
                "highlights": "測試景點",
                "area": "測試地區",
                "trip_id": 1
            }
        ]
        
        flex_message = create_optimized_flex_message("location_trips", 
            trips=sample_trips, location="測試地區")
        
        if flex_message and flex_message.get('type') == 'bubble':
            print("✅ 地區行程 Flex Message 生成成功")
        else:
            print("❌ 地區行程 Flex Message 生成失敗")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Flex Message 測試失敗: {e}")
        return False

def test_line_bot_config():
    """測試 LINE Bot 配置（不啟動完整系統）"""
    print("\n=== LINE Bot 配置測試 ===")
    
    try:
        from linebot.v3 import WebhookHandler
        from linebot.v3.messaging import Configuration
        
        channel_token = os.environ.get('CHANNEL_ACCESS_TOKEN')
        channel_secret = os.environ.get('CHANNEL_SECRET')
        
        if channel_token and channel_secret:
            configuration = Configuration(access_token=channel_token)
            line_handler = WebhookHandler(channel_secret)
            print("✅ LINE Bot 配置創建成功")
            return True
        else:
            print("❌ LINE Bot 環境變數缺失")
            return False
            
    except Exception as e:
        print(f"❌ LINE Bot 配置測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("開始基本功能測試...\n")
    
    tests = [
        test_environment,
        test_basic_imports,
        test_keyword_matching,
        test_flex_message,
        test_line_bot_config
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"測試結果: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有基本功能正常！")
        print("\n建議:")
        print("1. 如果要測試完整功能，請確保數據庫連接正常")
        print("2. 部署到 Vercel 時，記得設定環境變數")
        print("3. 新功能（集合和地區行程查詢）已準備就緒")
    else:
        print("⚠️  部分功能有問題，請檢查上述錯誤")

if __name__ == "__main__":
    main()
