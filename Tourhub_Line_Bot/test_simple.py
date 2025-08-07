#!/usr/bin/env python3
"""
簡單測試腳本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.config import KEYWORD_MAPPINGS, MESSAGE_TEMPLATES
from api.flex_templates import create_optimized_flex_message
import json

def test_tour_clock():
    """測試 TourClock 功能"""
    print("=== 測試 TourClock 功能 ===")
    
    try:
        template_data = MESSAGE_TEMPLATES["features"]["tour_clock"]
        flex_message = create_optimized_flex_message("feature", **template_data)
        
        if flex_message:
            print("✅ TourClock Flex Message 創建成功")
            print(json.dumps(flex_message, indent=2, ensure_ascii=False))
        else:
            print("❌ TourClock Flex Message 創建失敗")
            
    except Exception as e:
        print(f"❌ 錯誤: {e}")

def test_empty_trips():
    """測試空行程列表"""
    print("\n=== 測試空行程列表 ===")
    
    try:
        flex_message = create_optimized_flex_message("location_trips", 
            trips=[], location="京都")
        
        if flex_message:
            print("✅ 空行程 Flex Message 創建成功")
            print(json.dumps(flex_message, indent=2, ensure_ascii=False))
        else:
            print("❌ 空行程 Flex Message 創建失敗")
            
    except Exception as e:
        print(f"❌ 錯誤: {e}")

def test_sample_trips():
    """測試樣本行程"""
    print("\n=== 測試樣本行程 ===")
    
    sample_trips = [
        {
            "id": "1",
            "title": "東京三日遊",
            "duration": "3天",
            "highlights": "淺草寺、東京塔、銀座購物",
            "area": "東京",
            "trip_id": 1
        },
        {
            "id": "2", 
            "title": "東京美食之旅",
            "duration": "2天",
            "highlights": "築地市場、拉麵街、居酒屋體驗",
            "area": "東京",
            "trip_id": 2
        }
    ]
    
    try:
        flex_message = create_optimized_flex_message("location_trips", 
            trips=sample_trips, location="東京")
        
        if flex_message:
            print("✅ 樣本行程 Flex Message 創建成功")
            print(json.dumps(flex_message, indent=2, ensure_ascii=False))
        else:
            print("❌ 樣本行程 Flex Message 創建失敗")
            
    except Exception as e:
        print(f"❌ 錯誤: {e}")

if __name__ == "__main__":
    test_tour_clock()
    test_empty_trips()
    test_sample_trips()
