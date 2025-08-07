#!/usr/bin/env python3
"""
最終功能測試
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_new_features():
    """測試新功能"""
    print("=== 測試新功能 ===")
    
    # 測試關鍵字匹配
    from api.config import KEYWORD_MAPPINGS
    
    test_messages = [
        ("集合", "tour_clock"),
        ("東京行程", "tokyo_trips"),
        ("大阪旅遊", "osaka_trips"),
        ("功能介紹", "help")
    ]
    
    print("1. 關鍵字匹配測試:")
    for message, expected in test_messages:
        found = False
        for mapping_key, mapping in KEYWORD_MAPPINGS.items():
            if any(keyword in message for keyword in mapping["keywords"]):
                if mapping_key == expected:
                    print(f"✅ '{message}' -> {mapping_key}")
                    found = True
                    break
        if not found:
            print(f"❌ '{message}' -> 未找到或不匹配")
    
    # 測試 TourClock Flex Message
    print("\n2. TourClock Flex Message 測試:")
    try:
        from api.flex_templates import create_optimized_flex_message
        from api.config import MESSAGE_TEMPLATES
        
        template_data = MESSAGE_TEMPLATES["features"]["tour_clock"]
        flex_message = create_optimized_flex_message("feature", **template_data)
        
        if flex_message:
            print("✅ TourClock Flex Message 創建成功")
            # 檢查 URL
            button_uri = flex_message.get('footer', {}).get('contents', [{}])[0].get('action', {}).get('uri', '')
            if 'tourclock-dvf2.vercel.app' in button_uri:
                print("✅ TourClock URL 正確")
            else:
                print(f"❌ TourClock URL 錯誤: {button_uri}")
        else:
            print("❌ TourClock Flex Message 創建失敗")
    except Exception as e:
        print(f"❌ TourClock 測試失敗: {e}")
    
    # 測試地區行程查詢
    print("\n3. 地區行程查詢測試:")
    try:
        from api.database_utils import get_trips_by_location
        
        test_locations = ["東京", "大阪"]
        for location in test_locations:
            trips = get_trips_by_location(location, 3)
            print(f"✅ {location}: 找到 {len(trips)} 個行程")
            
            # 測試 Flex Message 生成
            flex_message = create_optimized_flex_message("location_trips", 
                trips=trips, location=location)
            
            if flex_message:
                print(f"✅ {location} Flex Message 創建成功")
            else:
                print(f"❌ {location} Flex Message 創建失敗")
                
    except Exception as e:
        print(f"❌ 地區行程查詢測試失敗: {e}")
    
    # 測試空數據處理
    print("\n4. 空數據處理測試:")
    try:
        flex_message = create_optimized_flex_message("location_trips", 
            trips=[], location="測試地區")
        
        if flex_message and 'error' in str(flex_message).lower():
            print("✅ 空數據錯誤訊息正確")
        else:
            print("❌ 空數據處理錯誤")
    except Exception as e:
        print(f"❌ 空數據測試失敗: {e}")

def test_performance():
    """測試性能"""
    print("\n=== 性能測試 ===")
    
    try:
        import time
        from api.advanced_cache import get_cache_stats
        
        # 獲取緩存統計
        stats = get_cache_stats()
        print(f"緩存命中率: {stats.get('hit_rate', 0):.2%}")
        print(f"總請求數: {stats.get('total_requests', 0)}")
        
        # 測試查詢速度
        from api.database_utils import get_leaderboard_from_database
        
        start_time = time.time()
        leaderboard = get_leaderboard_from_database()
        query_time = time.time() - start_time
        
        print(f"排行榜查詢時間: {query_time:.3f}s")
        if query_time < 1.0:
            print("✅ 查詢速度良好")
        else:
            print("⚠️  查詢速度較慢")
            
    except Exception as e:
        print(f"❌ 性能測試失敗: {e}")

if __name__ == "__main__":
    test_new_features()
    test_performance()
    print("\n測試完成！")
