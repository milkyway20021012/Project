#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試完整的集合功能
包括時間解析、地點解析、Flex Message 生成和提醒模擬
"""

import sys
import os
import json
import re
from datetime import datetime, timedelta

# 添加 api 目錄到路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from config import TIME_PATTERNS, MEETING_TIME_PATTERN
from vercel_meeting_manager import meeting_manager

def parse_time(user_message):
    """解析各種時間格式"""
    
    # 優先處理上午/下午/晚上/凌晨 (冒號格式) - 例如：下午2:35
    am_pm_colon_match = re.search(TIME_PATTERNS["am_pm_colon"], user_message)
    if am_pm_colon_match:
        period = am_pm_colon_match.group(1)
        hour = int(am_pm_colon_match.group(2))
        minute = am_pm_colon_match.group(3)
        
        # 轉換為24小時制
        if period == "下午" and hour != 12:
            hour += 12
        elif period == "晚上" and hour != 12:
            hour += 12
        elif period == "凌晨" and hour == 12:
            hour = 0
        elif period == "上午" and hour == 12:
            hour = 0
        
        return f"{hour:02d}:{minute.zfill(2)}"
    
    # 處理上午/下午/晚上/凌晨 (點分格式) - 例如：下午2點35分
    am_pm_match = re.search(TIME_PATTERNS["am_pm"], user_message)
    if am_pm_match:
        period = am_pm_match.group(1)
        hour = int(am_pm_match.group(2))
        minute = am_pm_match.group(3)
        
        # 轉換為24小時制
        if period == "下午" and hour != 12:
            hour += 12
        elif period == "晚上" and hour != 12:
            hour += 12
        elif period == "凌晨" and hour == 12:
            hour = 0
        elif period == "上午" and hour == 12:
            hour = 0
        
        return f"{hour:02d}:{minute.zfill(2)}"
    
    # 處理上午/下午/晚上/凌晨 (簡化格式) - 例如：晚上7點
    am_pm_simple_match = re.search(TIME_PATTERNS["am_pm_simple"], user_message)
    if am_pm_simple_match:
        period = am_pm_simple_match.group(1)
        hour = int(am_pm_simple_match.group(2))
        
        # 轉換為24小時制
        if period == "下午" and hour != 12:
            hour += 12
        elif period == "晚上" and hour != 12:
            hour += 12
        elif period == "凌晨" and hour == 12:
            hour = 0
        elif period == "上午" and hour == 12:
            hour = 0
        
        return f"{hour:02d}:00"
    
    # 處理小數點格式 - 例如：2.35
    decimal_time_match = re.search(TIME_PATTERNS["decimal_time"], user_message)
    if decimal_time_match:
        hour = decimal_time_match.group(1)
        minute = decimal_time_match.group(2)
        return f"{hour.zfill(2)}:{minute.zfill(2)}"
    
    # 標準時間格式 14:30
    time_match = re.search(TIME_PATTERNS["standard"], user_message)
    if time_match:
        return time_match.group(1)
    
    return None

def parse_location(user_message):
    """解析集合地點"""
    # 預設地點列表
    common_locations = [
        "東京鐵塔", "淺草寺", "新宿車站", "澀谷", "銀座", "秋葉原", "原宿", "池袋", "台場", "築地市場",
        "上野公園", "阿美橫町", "大阪城", "道頓堀", "心齋橋", "環球影城", "天保山", "海遊館", "梅田",
        "通天閣", "新世界", "金閣寺", "龍安寺", "二条城", "清水寺", "地主神社", "祇園", "伏見稻荷大社"
    ]
    
    # 優先檢查預設地點列表
    for location in common_locations:
        if location in user_message:
            return location
    
    # 使用正則表達式提取地點 - 改進版本
    location_patterns = [
        # 匹配時間後面的地點 + 集合動詞
        r'(?:\d{1,2}[:.]\d{2}|[上下晚凌][午上]\d{1,2}[點:]?\d{0,2}分?)\s*([\u4e00-\u9fa5A-Za-z0-9]+?)\s*(集合|見面|碰面|會合)',
        # 匹配地點 + 集合動詞
        r'([\u4e00-\u9fa5A-Za-z0-9]{2,8})\s*(集合|見面|碰面|會合)',
        # 匹配帶有地標後綴的地點
        r'([\u4e00-\u9fa5A-Za-z0-9]{2,8})(車站|寺|公園|廣場|商場|大樓|塔|橋|市場|通|町|村|城|館|園|山|湖|溫泉)'
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, user_message)
        if match:
            location = match.group(1).strip()
            # 過濾掉數字和時間相關詞彙
            if not re.match(r'^\d+$', location) and location not in ['上午', '下午', '晚上', '凌晨']:
                if len(location) >= 2:
                    return location
    
    return None

def test_complete_functionality():
    """測試完整功能"""
    print("=== TourHub Line Bot 完整功能測試 ===\n")
    
    test_cases = [
        "下午2:35 淺草寺集合",
        "14:30 新宿車站見面", 
        "晚上7點 銀座碰面",
        "2.35 澀谷集合",
        "上午10:00 東京鐵塔集合",
        "下午3點半 原宿見面"
    ]
    
    for i, test_message in enumerate(test_cases, 1):
        print(f"--- 測試 {i}: {test_message} ---")
        
        # 檢查是否匹配集合模式
        is_meeting = bool(re.search(MEETING_TIME_PATTERN, test_message))
        print(f"✓ 匹配集合模式: {is_meeting}")
        
        if is_meeting:
            # 解析時間和地點
            meeting_time = parse_time(test_message)
            meeting_location = parse_location(test_message)
            
            print(f"✓ 解析時間: {meeting_time}")
            print(f"✓ 解析地點: {meeting_location}")
            
            if meeting_time and meeting_location:
                # 創建集合
                success, message, meeting_id = meeting_manager.create_meeting(
                    user_id=f"test_user_{i}",
                    meeting_time=meeting_time,
                    meeting_location=meeting_location
                )
                
                print(f"✓ 創建集合: {success}")
                print(f"✓ 回應訊息: {message}")
                print(f"✓ 集合ID: {meeting_id}")
                
                if success:
                    # 模擬提醒時間表
                    reminder_schedule = meeting_manager.simulate_reminder_schedule(
                        meeting_time, meeting_location
                    )
                    
                    if reminder_schedule:
                        print("✓ 提醒時間表:")
                        for reminder in reminder_schedule.get("reminders", []):
                            print(f"   🔔 {reminder['time']} - {reminder['message']}")
                
                print("✅ 測試通過")
            else:
                print("❌ 解析失敗")
        else:
            print("❌ 不匹配集合模式")
        
        print("-" * 60)

def test_edge_cases():
    """測試邊界情況"""
    print("\n=== 邊界情況測試 ===\n")
    
    edge_cases = [
        "明天下午2:35 淺草寺集合",  # 包含日期
        "2點35分在新宿車站集合",    # 不同格式
        "澀谷14:30見面",           # 地點在前
        "集合時間下午3點地點銀座",   # 混合格式
        "無效訊息測試",             # 無效輸入
    ]
    
    for i, test_message in enumerate(edge_cases, 1):
        print(f"邊界測試 {i}: {test_message}")
        
        meeting_time = parse_time(test_message)
        meeting_location = parse_location(test_message)
        
        print(f"  時間: {meeting_time or '未識別'}")
        print(f"  地點: {meeting_location or '未識別'}")
        
        if meeting_time and meeting_location:
            print("  結果: ✅ 解析成功")
        else:
            print("  結果: ❌ 解析失敗")
        
        print()

if __name__ == "__main__":
    test_complete_functionality()
    test_edge_cases()
