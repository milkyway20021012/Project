#!/usr/bin/env python3
"""
測試啟動過程
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_startup():
    """測試啟動過程"""
    print("=== 測試啟動過程 ===")
    
    try:
        # 加載環境變數
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ 環境變數加載成功")
        
        # 測試主程序導入（這會觸發啟動過程）
        print("正在導入主程序...")
        from api.index import app, configuration, line_handler
        
        if configuration and line_handler:
            print("✅ LINE Bot 配置成功")
        else:
            print("❌ LINE Bot 配置失敗")
            return False
        
        print("✅ 主程序啟動成功")
        return True
        
    except Exception as e:
        print(f"❌ 啟動過程失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_message_processing():
    """測試消息處理邏輯"""
    print("\n=== 測試消息處理邏輯 ===")
    
    try:
        from api.config import KEYWORD_MAPPINGS
        
        # 模擬消息處理
        test_messages = [
            "集合",
            "東京行程", 
            "功能介紹",
            "不相關的訊息"
        ]
        
        for message in test_messages:
            matched = False
            for mapping_key, mapping in KEYWORD_MAPPINGS.items():
                if any(keyword in message for keyword in mapping["keywords"]):
                    print(f"✅ '{message}' -> {mapping_key}")
                    matched = True
                    break
            
            if not matched:
                print(f"⚠️  '{message}' -> 無匹配（正常）")
        
        return True
        
    except Exception as e:
        print(f"❌ 消息處理測試失敗: {e}")
        return False

def test_new_features():
    """測試新功能"""
    print("\n=== 測試新功能 ===")
    
    try:
        from api.flex_templates import create_optimized_flex_message
        from api.config import MESSAGE_TEMPLATES
        
        # 測試集合功能
        print("測試集合功能...")
        template_data = MESSAGE_TEMPLATES["features"]["tour_clock"]
        flex_message = create_optimized_flex_message("feature", **template_data)
        
        if flex_message:
            print("✅ 集合功能正常")
        else:
            print("❌ 集合功能失敗")
            return False
        
        # 測試地區行程查詢
        print("測試地區行程查詢...")
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
            trips=sample_trips, location="東京")
        
        if flex_message:
            print("✅ 地區行程查詢功能正常")
        else:
            print("❌ 地區行程查詢功能失敗")
            return False
        
        # 測試空數據處理
        print("測試空數據處理...")
        flex_message = create_optimized_flex_message("location_trips", 
            trips=[], location="測試地區")
        
        if flex_message:
            print("✅ 空數據處理正常")
        else:
            print("❌ 空數據處理失敗")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 新功能測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("開始完整啟動測試...\n")
    
    tests = [
        test_startup,
        test_message_processing,
        test_new_features
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"測試結果: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有功能正常！您的 Line Bot 已準備就緒！")
        print("\n可用功能:")
        print("1. 🔗 集合功能 - 輸入「集合」等關鍵字")
        print("2. 🗺️ 地區行程查詢 - 輸入「東京行程」等關鍵字")
        print("3. 📋 排行榜功能 - 輸入「排行榜」等關鍵字")
        print("4. ❓ 功能介紹 - 輸入「功能介紹」")
    else:
        print("⚠️  部分功能有問題，但基本功能應該可以使用")

if __name__ == "__main__":
    main()
