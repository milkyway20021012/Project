#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
多網站API代理系統
代理用戶對不同網站模組的操作
"""

import os
import json
import requests
from typing import Optional, Dict, Any, List
import logging

from .unified_user_manager import unified_user_manager

logger = logging.getLogger(__name__)

class WebsiteProxy:
    """網站API代理器"""
    
    def __init__(self):
        self.timeout = 30
        self.default_headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'TourHub-LineBot/1.0'
        }
    
    def execute_operation(self, line_user_id: str, module_name: str, 
                         operation: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """執行用戶操作"""
        try:
            # 獲取用戶資料
            user_data = unified_user_manager.get_user_by_line_id(line_user_id)
            if not user_data:
                return {
                    'success': False,
                    'error': 'User not found or not authenticated',
                    'error_code': 'USER_NOT_FOUND'
                }
            
            # 獲取網站模組資訊
            modules = unified_user_manager.get_available_modules()
            target_module = next((m for m in modules if m['module_name'] == module_name), None)
            
            if not target_module:
                return {
                    'success': False,
                    'error': f'Module {module_name} not found',
                    'error_code': 'MODULE_NOT_FOUND'
                }
            
            # 記錄操作開始
            unified_user_manager.log_user_operation(
                line_user_id=line_user_id,
                operation_type=f'{module_name}_{operation}',
                module_name=module_name,
                operation_data=data,
                result_status='pending'
            )
            
            # 根據模組執行相應操作
            result = self._execute_module_operation(
                user_data, target_module, operation, data
            )
            
            # 記錄操作結果
            unified_user_manager.log_user_operation(
                line_user_id=line_user_id,
                operation_type=f'{module_name}_{operation}',
                module_name=module_name,
                operation_data=data,
                result_status='success' if result.get('success') else 'failed',
                error_message=result.get('error') if not result.get('success') else None
            )
            
            return result
            
        except Exception as e:
            logger.error(f"執行操作失敗: {e}")
            
            # 記錄錯誤
            unified_user_manager.log_user_operation(
                line_user_id=line_user_id,
                operation_type=f'{module_name}_{operation}',
                module_name=module_name,
                operation_data=data,
                result_status='failed',
                error_message=str(e)
            )
            
            return {
                'success': False,
                'error': str(e),
                'error_code': 'EXECUTION_ERROR'
            }
    
    def _execute_module_operation(self, user_data: Dict[str, Any], 
                                 module: Dict[str, Any], operation: str, 
                                 data: Dict[str, Any] = None) -> Dict[str, Any]:
        """執行特定模組操作"""
        module_name = module['module_name']
        base_url = module['base_url']
        
        # 根據不同模組執行不同操作
        if module_name == 'tourhub_leaderboard':
            return self._execute_leaderboard_operation(user_data, base_url, operation, data)
        elif module_name == 'trip_management':
            return self._execute_trip_management_operation(user_data, base_url, operation, data)
        elif module_name == 'tour_clock':
            return self._execute_tour_clock_operation(user_data, base_url, operation, data)
        elif module_name == 'locker_finder':
            return self._execute_locker_finder_operation(user_data, base_url, operation, data)
        elif module_name == 'bill_split':
            return self._execute_bill_split_operation(user_data, base_url, operation, data)
        else:
            return self._execute_generic_operation(user_data, base_url, operation, data)
    
    def _execute_leaderboard_operation(self, user_data: Dict[str, Any], base_url: str,
                                      operation: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """執行排行榜操作"""
        if operation == 'view_leaderboard':
            # 直接跳轉到排行榜網站
            return {
                'success': True,
                'data': {
                    'action': 'redirect',
                    'url': base_url,
                    'message': '正在為您開啟排行榜頁面...'
                }
            }
        elif operation == 'get_top_trips':
            # 獲取熱門行程（如果有API的話）
            return self._make_request('GET', f"{base_url}/api/top-trips")
        else:
            return {'success': False, 'error': f'Unknown operation: {operation}'}

    def _execute_trip_management_operation(self, user_data: Dict[str, Any], base_url: str,
                                          operation: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """執行行程管理操作"""
        # 構建帶有用戶認證的URL
        auth_params = f"?unified_token={user_data['unified_token']}"

        if operation == 'manage_trips':
            return {
                'success': True,
                'data': {
                    'action': 'redirect',
                    'url': f"{base_url}{auth_params}",
                    'message': '正在為您開啟行程管理頁面...'
                }
            }
        elif operation == 'create_new_trip':
            return {
                'success': True,
                'data': {
                    'action': 'redirect',
                    'url': f"{base_url}/create{auth_params}",
                    'message': '正在為您開啟新建行程頁面...'
                }
            }
        else:
            return {'success': False, 'error': f'Unknown operation: {operation}'}

    def _execute_tour_clock_operation(self, user_data: Dict[str, Any], base_url: str,
                                     operation: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """執行集合管理操作"""
        auth_params = f"?unified_token={user_data['unified_token']}"

        if operation == 'manage_meetings':
            return {
                'success': True,
                'data': {
                    'action': 'redirect',
                    'url': f"{base_url}{auth_params}",
                    'message': '正在為您開啟集合管理頁面...'
                }
            }
        elif operation == 'create_meeting':
            return {
                'success': True,
                'data': {
                    'action': 'redirect',
                    'url': f"{base_url}/create{auth_params}",
                    'message': '正在為您開啟新建集合頁面...'
                }
            }
        else:
            return {'success': False, 'error': f'Unknown operation: {operation}'}

    def _execute_locker_finder_operation(self, user_data: Dict[str, Any], base_url: str,
                                        operation: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """執行置物櫃查找操作"""
        if operation == 'find_lockers':
            return {
                'success': True,
                'data': {
                    'action': 'redirect',
                    'url': base_url,
                    'message': '正在為您開啟置物櫃查找頁面...'
                }
            }
        elif operation == 'search_by_location':
            location = data.get('location') if data else ''
            return {
                'success': True,
                'data': {
                    'action': 'redirect',
                    'url': f"{base_url}?location={location}",
                    'message': f'正在為您搜尋{location}的置物櫃...'
                }
            }
        else:
            return {'success': False, 'error': f'Unknown operation: {operation}'}

    def _execute_bill_split_operation(self, user_data: Dict[str, Any], base_url: str,
                                     operation: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """執行分帳系統操作"""
        auth_params = f"?unified_token={user_data['unified_token']}"

        if operation == 'manage_bills':
            return {
                'success': True,
                'data': {
                    'action': 'redirect',
                    'url': f"{base_url}{auth_params}",
                    'message': '正在為您開啟分帳管理頁面...'
                }
            }
        elif operation == 'create_bill':
            return {
                'success': True,
                'data': {
                    'action': 'redirect',
                    'url': f"{base_url}/create{auth_params}",
                    'message': '正在為您開啟新建分帳頁面...'
                }
            }
        else:
            return {'success': False, 'error': f'Unknown operation: {operation}'}
    
    def _execute_generic_operation(self, user_data: Dict[str, Any], base_url: str, 
                                  operation: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """執行通用操作"""
        headers = self.default_headers.copy()
        headers['Authorization'] = f"Bearer {user_data['unified_token']}"
        
        # 通用API路徑
        api_path = f"{base_url}/api/{operation}"
        
        # 根據數據決定HTTP方法
        if data:
            return self._make_request('POST', api_path, headers=headers, json=data)
        else:
            return self._make_request('GET', api_path, headers=headers)
    
    def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """發送HTTP請求"""
        try:
            response = requests.request(method, url, timeout=self.timeout, **kwargs)
            
            # 記錄請求資訊
            logger.info(f"API Request: {method} {url} - Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    return {
                        'success': True,
                        'data': response.json(),
                        'status_code': response.status_code
                    }
                except json.JSONDecodeError:
                    return {
                        'success': True,
                        'data': response.text,
                        'status_code': response.status_code
                    }
            else:
                error_message = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_message = error_data.get('message', error_message)
                except:
                    pass
                
                return {
                    'success': False,
                    'error': error_message,
                    'status_code': response.status_code,
                    'error_code': 'HTTP_ERROR'
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timeout',
                'error_code': 'TIMEOUT'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Connection error',
                'error_code': 'CONNECTION_ERROR'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_code': 'REQUEST_ERROR'
            }
    
    def get_user_operations_summary(self, line_user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """獲取用戶操作摘要"""
        # 這裡可以從資料庫獲取用戶最近的操作記錄
        # 暫時返回空列表，實際實現時需要查詢 user_operation_logs 表
        return []

# 創建全局實例
website_proxy = WebsiteProxy()
