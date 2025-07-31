#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試集合時間和地點解析功能
"""

import sys
import os
import re

# 添加 api 目錄到路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from config import TIME_PATTERNS, MEETING_TIME_PATTERN, MEETING_LOCATIONS

def parse_time(user_message):
    """解析各種時間格式"""
    from datetime import datetime
    
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
        elif period == "上午" and hour == 12:
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
    
    # 處理小數點格式 - 例如：2.35
    decimal_time_match = re.search(TIME_PATTERNS["decimal_time"], user_message)
    if decimal_time_match:
        hour = decimal_time_match.group(1)
        minute = decimal_time_match.group(2)
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

def test_parsing():
    """測試解析功能"""
    test_cases = [
        "下午2:35 淺草寺集合",
        "下午2點35分 淺草寺集合",
        "14:30 新宿車站見面",
        "晚上7點 銀座碰面",
        "上午10:00 東京鐵塔集合",
        "2.35 澀谷集合",
        "明天3點半 原宿見面",
        "凌晨1點 池袋集合",
        "下午12:00 台場集合",
        "上午12點 築地市場見面"
    ]
    
    print("=== 集合時間和地點解析測試 ===\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"測試 {i}: {test_case}")
        
        # 檢查是否匹配集合模式
        is_meeting = bool(re.search(MEETING_TIME_PATTERN, test_case))
        print(f"  匹配集合模式: {is_meeting}")
        
        # 解析時間
        meeting_time = parse_time(test_case)
        print(f"  解析時間: {meeting_time}")
        
        # 解析地點
        meeting_location = parse_location(test_case)
        print(f"  解析地點: {meeting_location}")
        
        # 判斷是否成功
        success = meeting_time and meeting_location
        print(f"  解析成功: {success}")
        print("-" * 50)

if __name__ == "__main__":
    test_parsing()
