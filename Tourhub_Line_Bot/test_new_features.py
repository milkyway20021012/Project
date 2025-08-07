#!/usr/bin/env python3
"""
測試新功能腳本
測試集合功能和地區行程查詢功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.config import KEYWORD_MAPPINGS, MESSAGE_TEMPLATES
from api.flex_templates import create_optimized_flex_message
from api.database_utils import get_trips_by_location
import json

def test_keyword_mappings():
    """測試關鍵字映射"""
    print("=== 測試關鍵字映射 ===")
    
    # 測試集合功能關鍵字
    test_keywords = [
        "集合",
        "東京",
        "大阪行程",
        "功能介紹"
    ]
    
    for keyword in test_keywords:
        found = False
        for mapping_key, mapping in KEYWORD_MAPPINGS.items():
            if keyword in mapping["keywords"]:
                print(f"✅ 關鍵字 '{keyword}' -> {mapping_key} ({mapping['template']})")
                found = True
                break
        
        if not found:
            print(f"❌ 關鍵字 '{keyword}' 未找到映射")
    
    print()

def test_tour_clock_feature():
    """測試 TourClock 集合功能"""
    print("=== 測試 TourClock 集合功能 ===")
    
    try:
        # 獲取 TourClock 模板數據
        template_data = MESSAGE_TEMPLATES["features"]["tour_clock"]
        print(f"✅ TourClock 模板數據: {template_data}")
        
        # 創建 Flex Message
        flex_message = create_optimized_flex_message("feature", **template_data)
        
        if flex_message:
            print("✅ TourClock Flex Message 創建成功")
            print(f"標題: {flex_message.get('header', {}).get('contents', [{}])[0].get('text', 'N/A')}")
            
            # 檢查 URL
            footer_contents = flex_message.get('footer', {}).get('contents', [])
            if footer_contents:
                button = footer_contents[0]
                url = button.get('action', {}).get('uri', '')
                if 'tourclock-dvf2.vercel.app' in url:
                    print("✅ TourClock URL 正確")
                else:
                    print(f"❌ TourClock URL 錯誤: {url}")
            
        else:
            print("❌ TourClock Flex Message 創建失敗")
            
    except Exception as e:
        print(f"❌ TourClock 功能測試失敗: {e}")
    
    print()

def test_location_trips():
    """測試地區行程查詢功能"""
    print("=== 測試地區行程查詢功能 ===")
    
    test_locations = ["東京", "大阪", "京都"]
    
    for location in test_locations:
        try:
            print(f"測試 {location} 行程查詢...")
            
            # 獲取行程數據
            trips = get_trips_by_location(location, 5)
            print(f"✅ 找到 {len(trips)} 個 {location} 行程")
            
            if trips:
                # 顯示前3個行程的基本信息
                for i, trip in enumerate(trips[:3], 1):
                    print(f"  {i}. {trip.get('title', 'N/A')} - {trip.get('duration', 'N/A')}")
                
                # 創建 Flex Message
                flex_message = create_optimized_flex_message("location_trips", 
                    trips=trips, location=location)
                
                if flex_message:
                    print(f"✅ {location} Flex Message 創建成功")
                    
                    # 檢查標題
                    header_text = flex_message.get('header', {}).get('contents', [{}])[0].get('text', '')
                    if location in header_text:
                        print(f"✅ 標題包含地區名稱: {header_text}")
                    else:
                        print(f"❌ 標題不包含地區名稱: {header_text}")
                    
                    # 檢查行程內容
                    body_contents = flex_message.get('body', {}).get('contents', [])
                    if body_contents:
                        print(f"✅ 包含 {len(body_contents)} 個行程項目")
                    else:
                        print("❌ 沒有行程內容")
                        
                else:
                    print(f"❌ {location} Flex Message 創建失敗")
            else:
                print(f"⚠️  {location} 沒有找到行程數據")
                
                # 測試空數據的 Flex Message
                flex_message = create_optimized_flex_message("location_trips", 
                    trips=[], location=location)
                
                if flex_message and 'error' in str(flex_message):
                    print(f"✅ {location} 空數據錯誤訊息正確")
                else:
                    print(f"❌ {location} 空數據處理錯誤")
                    
        except Exception as e:
            print(f"❌ {location} 行程查詢測試失敗: {e}")
        
        print()

def test_keyword_recognition():
    """測試關鍵字識別邏輯"""
    print("=== 測試關鍵字識別邏輯 ===")
    
    test_messages = [
        "集合",
        "集合時間",
        "東京行程",
        "東京相關",
        "大阪旅遊",
        "京都景點",
        "沖繩推薦",
        "北海道行程",
        "功能介紹",
        "不相關的訊息"
    ]
    
    for message in test_messages:
        matched_config = None
        
        # 模擬關鍵字匹配邏輯
        for mapping_key, mapping in KEYWORD_MAPPINGS.items():
            for keyword in mapping["keywords"]:
                if keyword in message:
                    matched_config = mapping
                    matched_config["feature_name"] = mapping_key
                    break
            if matched_config:
                break
        
        if matched_config:
            template = matched_config.get("template", "unknown")
            location = matched_config.get("location", "")
            print(f"✅ '{message}' -> {template}" + (f" ({location})" if location else ""))
        else:
            print(f"❌ '{message}' -> 無匹配")
    
    print()

def main():
    """主測試函數"""
    print("開始測試新功能...\n")
    
    # 測試關鍵字映射
    test_keyword_mappings()
    
    # 測試 TourClock 功能
    test_tour_clock_feature()
    
    # 測試地區行程查詢
    test_location_trips()
    
    # 測試關鍵字識別
    test_keyword_recognition()
    
    print("測試完成！")

if __name__ == "__main__":
    main()
