#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
內容創建處理器
解析用戶輸入並創建對應的內容
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from .website_proxy import website_proxy

logger = logging.getLogger(__name__)

class ContentCreator:
    def __init__(self):
        self.patterns = {
            'create_trip': [
                r'創建(.+?)行程',
                r'建立(.+?)行程',
                r'新增(.+?)行程',
                r'規劃(.+?)行程',
                r'(.+?)行程規劃'
            ],
            'create_meeting': [
                r'創建(.+?)集合',
                r'建立(.+?)集合',
                r'設定(.+?)集合',
                r'(.+?)集合時間',
                r'約(.+?)集合'
            ],
            'create_bill': [
                r'創建(.+?)分帳',
                r'建立(.+?)分帳',
                r'新增(.+?)分帳',
                r'(.+?)分帳管理',
                r'(.+?)AA制'
            ]
        }
    
    def parse_and_create(self, user_message: str, line_user_id: str) -> Optional[Dict[str, Any]]:
        """解析用戶訊息並創建對應內容"""
        
        # 檢查是否為創建行程
        trip_info = self._parse_trip_creation(user_message)
        if trip_info:
            return self._create_trip_content(line_user_id, trip_info)
        
        # 檢查是否為創建集合
        meeting_info = self._parse_meeting_creation(user_message)
        if meeting_info:
            return self._create_meeting_content(line_user_id, meeting_info)
        
        # 檢查是否為創建分帳
        bill_info = self._parse_bill_creation(user_message)
        if bill_info:
            return self._create_bill_content(line_user_id, bill_info)
        
        return None
    
    def _parse_trip_creation(self, message: str) -> Optional[Dict[str, Any]]:
        """解析行程創建指令"""
        for pattern in self.patterns['create_trip']:
            match = re.search(pattern, message)
            if match:
                trip_name = match.group(1).strip()
                
                # 解析地點和天數
                location = self._extract_location(trip_name)
                days = self._extract_days(trip_name)
                
                return {
                    'title': trip_name,
                    'location': location,
                    'days': days,
                    'description': f'透過 Line Bot 創建的{trip_name}'
                }
        return None
    
    def _parse_meeting_creation(self, message: str) -> Optional[Dict[str, Any]]:
        """解析集合創建指令"""
        for pattern in self.patterns['create_meeting']:
            match = re.search(pattern, message)
            if match:
                meeting_name = match.group(1).strip()
                
                # 解析時間和地點
                time_info = self._extract_time(meeting_name)
                location = self._extract_location(meeting_name)
                
                return {
                    'title': meeting_name,
                    'location': location,
                    'time_info': time_info,
                    'description': f'透過 Line Bot 創建的{meeting_name}集合'
                }
        return None
    
    def _parse_bill_creation(self, message: str) -> Optional[Dict[str, Any]]:
        """解析分帳創建指令"""
        for pattern in self.patterns['create_bill']:
            match = re.search(pattern, message)
            if match:
                bill_name = match.group(1).strip()
                
                return {
                    'title': bill_name,
                    'description': f'透過 Line Bot 創建的{bill_name}分帳',
                    'currency': 'TWD'
                }
        return None
    
    def _extract_location(self, text: str) -> str:
        """提取地點資訊"""
        locations = ['東京', '大阪', '京都', '北海道', '沖繩', '奈良', '神戶', '橫濱', '名古屋', '福岡']
        for location in locations:
            if location in text:
                return location
        return '未指定地點'
    
    def _extract_days(self, text: str) -> int:
        """提取天數資訊"""
        day_patterns = [
            r'(\d+)天',
            r'(\d+)日',
            r'一日', r'二日', r'三日', r'四日', r'五日', r'六日', r'七日'
        ]
        
        for pattern in day_patterns:
            match = re.search(pattern, text)
            if match:
                if pattern in ['一日', '二日', '三日', '四日', '五日', '六日', '七日']:
                    day_map = {'一日': 1, '二日': 2, '三日': 3, '四日': 4, '五日': 5, '六日': 6, '七日': 7}
                    return day_map.get(match.group(0), 1)
                else:
                    return int(match.group(1))
        
        # 預設為 3 天
        return 3
    
    def _extract_time(self, text: str) -> Dict[str, Any]:
        """提取時間資訊"""
        time_patterns = [
            r'(\d{1,2}):(\d{2})',
            r'(\d{1,2})點',
            r'上午(\d{1,2})點',
            r'下午(\d{1,2})點',
            r'明天',
            r'後天',
            r'今天'
        ]
        
        result = {
            'date': None,
            'time': None,
            'description': '請稍後設定具體時間'
        }
        
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                if pattern == r'(\d{1,2}):(\d{2})':
                    result['time'] = f"{match.group(1)}:{match.group(2)}"
                elif pattern == r'(\d{1,2})點':
                    result['time'] = f"{match.group(1)}:00"
                elif pattern == r'上午(\d{1,2})點':
                    hour = int(match.group(1))
                    result['time'] = f"{hour:02d}:00"
                elif pattern == r'下午(\d{1,2})點':
                    hour = int(match.group(1)) + 12
                    result['time'] = f"{hour:02d}:00"
                elif pattern == '明天':
                    result['date'] = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                elif pattern == '後天':
                    result['date'] = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
                elif pattern == '今天':
                    result['date'] = datetime.now().strftime('%Y-%m-%d')
                break
        
        return result
    
    def _create_trip_content(self, line_user_id: str, trip_info: Dict[str, Any]) -> Dict[str, Any]:
        """創建行程內容"""
        try:
            result = website_proxy.create_trip(line_user_id, trip_info)
            
            if result['success']:
                return {
                    'type': 'success',
                    'content_type': 'trip',
                    'message': result['message'],
                    'url': result.get('url'),
                    'details': {
                        'title': trip_info['title'],
                        'location': trip_info['location'],
                        'days': trip_info['days']
                    }
                }
            else:
                return {
                    'type': 'error',
                    'content_type': 'trip',
                    'message': result['message'],
                    'error': result.get('error')
                }
                
        except Exception as e:
            logger.error(f"創建行程內容錯誤: {e}")
            return {
                'type': 'error',
                'content_type': 'trip',
                'message': '❌ 創建行程時發生錯誤，請稍後再試',
                'error': str(e)
            }
    
    def _create_meeting_content(self, line_user_id: str, meeting_info: Dict[str, Any]) -> Dict[str, Any]:
        """創建集合內容"""
        try:
            result = website_proxy.create_meeting(line_user_id, meeting_info)
            
            if result['success']:
                return {
                    'type': 'success',
                    'content_type': 'meeting',
                    'message': result['message'],
                    'url': result.get('url'),
                    'details': {
                        'title': meeting_info['title'],
                        'location': meeting_info['location'],
                        'time_info': meeting_info['time_info']
                    }
                }
            else:
                return {
                    'type': 'error',
                    'content_type': 'meeting',
                    'message': result['message'],
                    'error': result.get('error')
                }
                
        except Exception as e:
            logger.error(f"創建集合內容錯誤: {e}")
            return {
                'type': 'error',
                'content_type': 'meeting',
                'message': '❌ 創建集合時發生錯誤，請稍後再試',
                'error': str(e)
            }
    
    def _create_bill_content(self, line_user_id: str, bill_info: Dict[str, Any]) -> Dict[str, Any]:
        """創建分帳內容"""
        try:
            result = website_proxy.create_bill(line_user_id, bill_info)
            
            if result['success']:
                return {
                    'type': 'success',
                    'content_type': 'bill',
                    'message': result['message'],
                    'url': result.get('url'),
                    'details': {
                        'title': bill_info['title']
                    }
                }
            else:
                return {
                    'type': 'error',
                    'content_type': 'bill',
                    'message': result['message'],
                    'error': result.get('error')
                }
                
        except Exception as e:
            logger.error(f"創建分帳內容錯誤: {e}")
            return {
                'type': 'error',
                'content_type': 'bill',
                'message': '❌ 創建分帳時發生錯誤，請稍後再試',
                'error': str(e)
            }

# 全局實例
content_creator = ContentCreator()
