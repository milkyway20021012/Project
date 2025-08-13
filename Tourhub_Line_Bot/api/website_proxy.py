#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
網站 API 代理系統
處理與各個網站的 API 交互
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime
from .unified_user_manager import user_manager

logger = logging.getLogger(__name__)

class WebsiteProxy:
    def __init__(self):
        self.website_configs = {
            'trip_management': {
                'base_url': 'https://tripfrontend.vercel.app',
                'api_endpoints': {
                    'create_trip': '/api/trips',
                    'get_trips': '/api/trips',
                    'update_trip': '/api/trips/{trip_id}',
                    'delete_trip': '/api/trips/{trip_id}'
                }
            },
            'tour_clock': {
                'base_url': 'https://tourclock-dvf2.vercel.app',
                'api_endpoints': {
                    'create_meeting': '/api/meetings',
                    'get_meetings': '/api/meetings',
                    'update_meeting': '/api/meetings/{meeting_id}'
                }
            },
            'bill_split': {
                'base_url': 'https://split-front-pearl.vercel.app',
                'api_endpoints': {
                    'create_bill': '/api/bills',
                    'get_bills': '/api/bills',
                    'add_expense': '/api/bills/{bill_id}/expenses'
                }
            },
            'locker_finder': {
                'base_url': 'https://tripfrontend.vercel.app',
                'api_endpoints': {
                    'search_lockers': '/api/lockers/search',
                    'book_locker': '/api/lockers/book'
                }
            }
        }
    
    def create_trip(self, line_user_id: str, trip_data: Dict[str, Any]) -> Dict[str, Any]:
        """創建行程"""
        try:
            # 獲取或創建用戶
            user = user_manager.get_or_create_user(line_user_id)
            if not user:
                return {'success': False, 'error': '用戶驗證失敗'}
            
            # 確保用戶綁定到行程管理模組
            user_manager.bind_website(user['id'], 'trip_management')
            
            # 記錄操作
            user_manager.log_operation(
                user['id'], 
                'create_trip', 
                trip_data, 
                'trip_management'
            )
            
            # 準備 API 請求數據
            api_data = {
                'line_user_id': line_user_id,
                'unified_token': user['unified_token'],
                'trip_data': trip_data,
                'created_via': 'line_bot'
            }
            
            # 調用網站 API（模擬）
            # 實際實現時需要根據各網站的 API 規格調整
            result = self._call_website_api('trip_management', 'create_trip', api_data)
            
            if result.get('success'):
                # 更新操作狀態
                user_manager.log_operation(
                    user['id'], 
                    'create_trip', 
                    {'trip_id': result.get('trip_id'), **trip_data}, 
                    'trip_management',
                    'success'
                )
                
                return {
                    'success': True,
                    'trip_id': result.get('trip_id'),
                    'message': f"✅ 行程「{trip_data.get('title', '未命名行程')}」創建成功！",
                    'url': f"{self.website_configs['trip_management']['base_url']}/trip/{result.get('trip_id')}"
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', '創建失敗'),
                    'message': f"❌ 行程創建失敗：{result.get('error', '未知錯誤')}"
                }
                
        except Exception as e:
            logger.error(f"創建行程錯誤: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "❌ 系統錯誤，請稍後再試"
            }
    
    def create_meeting(self, line_user_id: str, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """創建集合"""
        try:
            user = user_manager.get_or_create_user(line_user_id)
            if not user:
                return {'success': False, 'error': '用戶驗證失敗'}
            
            user_manager.bind_website(user['id'], 'tour_clock')
            user_manager.log_operation(user['id'], 'create_meeting', meeting_data, 'tour_clock')
            
            api_data = {
                'line_user_id': line_user_id,
                'unified_token': user['unified_token'],
                'meeting_data': meeting_data,
                'created_via': 'line_bot'
            }
            
            result = self._call_website_api('tour_clock', 'create_meeting', api_data)
            
            if result.get('success'):
                user_manager.log_operation(
                    user['id'], 
                    'create_meeting', 
                    {'meeting_id': result.get('meeting_id'), **meeting_data}, 
                    'tour_clock',
                    'success'
                )
                
                return {
                    'success': True,
                    'meeting_id': result.get('meeting_id'),
                    'message': f"✅ 集合「{meeting_data.get('title', '未命名集合')}」創建成功！",
                    'url': f"{self.website_configs['tour_clock']['base_url']}/meeting/{result.get('meeting_id')}"
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', '創建失敗'),
                    'message': f"❌ 集合創建失敗：{result.get('error', '未知錯誤')}"
                }
                
        except Exception as e:
            logger.error(f"創建集合錯誤: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "❌ 系統錯誤，請稍後再試"
            }
    
    def create_bill(self, line_user_id: str, bill_data: Dict[str, Any]) -> Dict[str, Any]:
        """創建分帳"""
        try:
            user = user_manager.get_or_create_user(line_user_id)
            if not user:
                return {'success': False, 'error': '用戶驗證失敗'}
            
            user_manager.bind_website(user['id'], 'bill_split')
            user_manager.log_operation(user['id'], 'create_bill', bill_data, 'bill_split')
            
            api_data = {
                'line_user_id': line_user_id,
                'unified_token': user['unified_token'],
                'bill_data': bill_data,
                'created_via': 'line_bot'
            }
            
            result = self._call_website_api('bill_split', 'create_bill', api_data)
            
            if result.get('success'):
                user_manager.log_operation(
                    user['id'], 
                    'create_bill', 
                    {'bill_id': result.get('bill_id'), **bill_data}, 
                    'bill_split',
                    'success'
                )
                
                return {
                    'success': True,
                    'bill_id': result.get('bill_id'),
                    'message': f"✅ 分帳「{bill_data.get('title', '未命名分帳')}」創建成功！",
                    'url': f"{self.website_configs['bill_split']['base_url']}/bill/{result.get('bill_id')}"
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', '創建失敗'),
                    'message': f"❌ 分帳創建失敗：{result.get('error', '未知錯誤')}"
                }
                
        except Exception as e:
            logger.error(f"創建分帳錯誤: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "❌ 系統錯誤，請稍後再試"
            }
    
    def _call_website_api(self, website: str, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """調用網站 API（模擬實現）"""
        # 這裡是模擬實現，實際需要根據各網站的 API 規格來實現
        
        # 模擬成功回應
        if website == 'trip_management' and endpoint == 'create_trip':
            return {
                'success': True,
                'trip_id': f"trip_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'message': '行程創建成功'
            }
        elif website == 'tour_clock' and endpoint == 'create_meeting':
            return {
                'success': True,
                'meeting_id': f"meeting_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'message': '集合創建成功'
            }
        elif website == 'bill_split' and endpoint == 'create_bill':
            return {
                'success': True,
                'bill_id': f"bill_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'message': '分帳創建成功'
            }
        
        # 實際實現示例（需要根據各網站 API 調整）
        """
        try:
            config = self.website_configs.get(website)
            if not config:
                return {'success': False, 'error': f'未知網站: {website}'}
            
            url = config['base_url'] + config['api_endpoints'][endpoint]
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {data.get('unified_token')}"
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'error': f'API 調用失敗: {response.status_code}'
                }
                
        except requests.RequestException as e:
            logger.error(f"API 調用錯誤: {e}")
            return {'success': False, 'error': f'網路錯誤: {str(e)}'}
        """
        
        return {'success': False, 'error': '功能開發中'}

# 全局實例
website_proxy = WebsiteProxy()
