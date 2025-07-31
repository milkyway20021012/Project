#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
集合解析功能測試
測試各種時間和地點解析功能
"""

import re
import sys
import os

# 添加 api 目錄到路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from api.config import TIME_PATTERNS, MEETING_LOCATIONS, MEETING_TIME_PATTERN

def parse_time(user_message):
    """解析各種時間格式"""
    from datetime import datetime
    
    # 優先處理上午/下午/晚上/凌晨 (完整格式) - 例如：下午2:35
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
        
        return f"{hour:02d}:{minute.zfill(2)}"
    
    # 處理上午/下午/晚上/凌晨 (簡化格式) - 例如：下午2點
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
        
        return f"{hour:02d}:00"
    
    # 處理 "點半" 或 "點30分"
    natural_time_match = re.search(TIME_PATTERNS["natural_time"], user_message)
    if natural_time_match:
        hour = natural_time_match.group(1) or natural_time_match.group(2)
        return f"{hour.zfill(2)}:30"
    
    # 中文時間格式 2點30分
    chinese_time = re.search(TIME_PATTERNS["chinese"], user_message)
    if chinese_time:
        hour = chinese_time.group(1)
        minute = chinese_time.group(2)
        return f"{hour.zfill(2)}:{minute.zfill(2)}"
    
    # 簡化中文時間格式 2點
    simple_chinese_time = re.search(TIME_PATTERNS["simple_chinese"], user_message)
    if simple_chinese_time:
        hour = simple_chinese_time.group(1)
        return f"{hour.zfill(2)}:00"
    
    # 標準時間格式 14:30 (最後處理，避免與上午/下午格式衝突)
    time_match = re.search(TIME_PATTERNS["standard"], user_message)
    if time_match:
        return time_match.group(1)
    
    # 處理冒號格式但沒有前後文的情況
    colon_time_match = re.search(TIME_PATTERNS["time_with_colon"], user_message)
    if colon_time_match:
        hour = colon_time_match.group(1)
        minute = colon_time_match.group(2)
        return f"{hour.zfill(2)}:{minute.zfill(2)}"
    
    return None

def parse_location(user_message):
    """解析集合地點"""
    # 優先檢查預設地點列表
    for location in MEETING_LOCATIONS:
        if location in user_message:
            return location
    
    # 模糊比對預設地點
    for location in MEETING_LOCATIONS:
        if any(word in user_message for word in location.split()):
            return location
    
    # 使用正則表達式提取地點
    # 匹配 "在/到/約在/集合於/見面於 + 地點" 的格式
    location_patterns = [
        r'(在|到|約在|集合於|見面於|於)([\u4e00-\u9fa5A-Za-z0-9\s]+?)(集合|見面|碰面|會合|$|\s|，|,|。|！|！)',
        r'([\u4e00-\u9fa5A-Za-z0-9\s]+?)(集合|見面|碰面|會合)',
        r'集合.*?([\u4e00-\u9fa5A-Za-z0-9\s]+?)(\s|，|,|。|！|！|$)',
        r'([\u4e00-\u9fa5A-Za-z0-9\s]{2,10})(車站|寺|公園|廣場|商場|大樓|塔|橋|市場|通|町|村|城|館|園|山|湖|溫泉)'
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, user_message)
        if match:
            location = match.group(1) if '集合' not in match.group(1) else match.group(2)
            # 清理地點名稱
            location = location.strip()
            if len(location) >= 2:  # 至少2個字符
                return location
    
    # 如果還是找不到，嘗試提取中文地名
    chinese_location_match = re.search(r'([\u4e00-\u9fa5]{2,10})', user_message)
    if chinese_location_match:
        return chinese_location_match.group(1)
    
    return None

def test_meeting_parsing():
    """測試集合解析功能"""
    
    test_cases = [
        # 時間測試案例
        "下午2:35 淺草寺集合",
        "14:30 新宿車站見面",
        "2點35分 澀谷集合",
        "下午3點 銀座碰面",
        "晚上7點30分 秋葉原集合",
        "上午10點 原宿見面",
        "3點半 池袋集合",
        "下午2點 台場碰面",
        "14:35 築地市場集合",
        "晚上8點 上野公園見面",
        
        # 地點測試案例
        "下午2:35 東京鐵塔集合",
        "14:30 大阪城見面",
        "3點 道頓堀集合",
        "晚上7點 心齋橋碰面",
        "下午4點 環球影城集合",
        "2點30分 天保山見面",
        "晚上6點 海遊館集合",
        "下午1點 梅田碰面",
        "15:30 通天閣集合",
        "晚上9點 新世界見面",
        
        # 複雜案例
        "明天下午2:35 淺草寺集合",
        "今天14:30 新宿車站見面",
        "下午2點35分 澀谷集合",
        "晚上7點半 銀座碰面",
        "上午10點30分 秋葉原集合",
        "下午3點 原宿見面",
        "14:35 池袋集合",
        "晚上8點 台場碰面",
        "下午4點30分 築地市場集合",
        "上午11點 上野公園見面"
    ]
    
    print("🔍 集合解析功能測試")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 測試案例 {i}: {test_case}")
        
        # 檢查是否包含集合關鍵字
        is_meeting = bool(re.search(MEETING_TIME_PATTERN, test_case))
        print(f"  集合關鍵字: {'✅' if is_meeting else '❌'}")
        
        # 解析時間
        time_result = parse_time(test_case)
        print(f"  時間解析: {time_result if time_result else '❌ 未識別'}")
        
        # 解析地點
        location_result = parse_location(test_case)
        print(f"  地點解析: {location_result if location_result else '❌ 未識別'}")
        
        # 總結
        if time_result and location_result:
            print(f"  ✅ 完整解析: {time_result} @ {location_result}")
        elif time_result:
            print(f"  ⚠️  部分解析: 時間={time_result}, 地點未識別")
        elif location_result:
            print(f"  ⚠️  部分解析: 地點={location_result}, 時間未識別")
        else:
            print(f"  ❌ 解析失敗")

def test_specific_cases():
    """測試特定案例"""
    print("\n🎯 特定案例測試")
    print("=" * 50)
    
    specific_cases = [
        "下午2:35 淺草寺集合",  # 您的原始需求
        "2:35 淺草寺集合",
        "下午2點35分 淺草寺集合",
        "14:35 淺草寺集合",
        "下午2點半 淺草寺集合",
        "2點半 淺草寺集合",
        "下午2:30 淺草寺集合",
        "淺草寺 下午2:35集合",
        "集合 下午2:35 淺草寺",
        "約在下午2:35 淺草寺集合"
    ]
    
    for test_case in specific_cases:
        print(f"\n📝 測試: {test_case}")
        time_result = parse_time(test_case)
        location_result = parse_location(test_case)
        print(f"  時間: {time_result}")
        print(f"  地點: {location_result}")
        
        if time_result == "14:35" and location_result == "淺草寺":
            print("  ✅ 完美匹配您的需求！")
        else:
            print("  ❌ 不完全匹配")

if __name__ == "__main__":
    test_meeting_parsing()
    test_specific_cases()
    
    print("\n🎉 測試完成！")
    print("\n💡 使用說明:")
    print("1. 支援的時間格式: 下午2:35, 14:35, 2點35分, 下午2點半等")
    print("2. 支援的地點格式: 淺草寺, 新宿車站, 澀谷等")
    print("3. 支援的集合關鍵字: 集合, 見面, 碰面, 會合等")
    print("4. 範例: '下午2:35 淺草寺集合' 會自動解析並設定到 TourClock") 