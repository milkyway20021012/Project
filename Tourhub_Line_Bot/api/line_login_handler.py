#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LINE Login 綁定處理器
處理LINE Login授權流程和用戶綁定
"""

import os
import json
import requests
import secrets
from datetime import datetime
from urllib.parse import urlencode, parse_qs
from typing import Optional, Dict, Any, List
import logging

from .unified_user_manager import unified_user_manager

logger = logging.getLogger(__name__)

class LineLoginHandler:
    """LINE Login處理器"""
    
    def __init__(self):
        self.channel_id = os.environ.get('LINE_LOGIN_CHANNEL_ID')
        self.channel_secret = os.environ.get('LINE_LOGIN_CHANNEL_SECRET')
        self.redirect_uri = os.environ.get('LINE_LOGIN_REDIRECT_URI', 'https://line-bot-theta-dun.vercel.app/auth/line/callback')
        self.line_login_api_base = 'https://api.line.me/oauth2/v2.1'
        self.line_api_base = 'https://api.line.me/v2'
    
    def generate_login_url(self, line_user_id: str, state_data: Dict[str, Any] = None) -> str:
        """生成LINE Login授權URL"""
        if not self.channel_id:
            logger.error("LINE Login Channel ID not configured")
            # 臨時返回設定提示URL，而不是None
            return "https://line-bot-theta-dun.vercel.app/?setup=required"
        
        # 生成state參數（包含用戶ID和其他數據）
        state_info = {
            'line_user_id': line_user_id,
            'timestamp': str(int(datetime.now().timestamp())),
            'nonce': secrets.token_urlsafe(16)
        }
        if state_data:
            state_info.update(state_data)
        
        state = json.dumps(state_info)
        
        params = {
            'response_type': 'code',
            'client_id': self.channel_id,
            'redirect_uri': self.redirect_uri,
            'state': state,
            'scope': 'profile openid email',
            'nonce': secrets.token_urlsafe(16)
        }
        
        login_url = f"{self.line_login_api_base}/authorize?{urlencode(params)}"
        
        # 記錄操作
        unified_user_manager.log_user_operation(
            line_user_id=line_user_id,
            operation_type='line_login_start',
            operation_data={'redirect_uri': self.redirect_uri}
        )
        
        return login_url
    
    def handle_callback(self, code: str, state: str) -> Dict[str, Any]:
        """處理LINE Login回調"""
        try:
            # 解析state參數
            state_data = json.loads(state)
            line_user_id = state_data.get('line_user_id')
            
            if not line_user_id:
                return {'success': False, 'error': 'Invalid state parameter'}
            
            # 交換access token
            token_data = self._exchange_access_token(code)
            if not token_data:
                return {'success': False, 'error': 'Failed to exchange access token'}
            
            # 獲取用戶資料
            profile_data = self._get_user_profile(token_data['access_token'])
            if not profile_data:
                return {'success': False, 'error': 'Failed to get user profile'}
            
            # 創建或更新統一用戶
            user_data = unified_user_manager.create_or_update_user(line_user_id, profile_data)
            if not user_data:
                return {'success': False, 'error': 'Failed to create/update user'}
            
            # 記錄成功操作
            unified_user_manager.log_user_operation(
                line_user_id=line_user_id,
                operation_type='line_login_success',
                operation_data={
                    'profile': profile_data,
                    'token_info': {
                        'expires_in': token_data.get('expires_in'),
                        'scope': token_data.get('scope')
                    }
                },
                result_status='success'
            )
            
            return {
                'success': True,
                'user_data': user_data,
                'profile_data': profile_data,
                'unified_token': user_data.get('unified_token')
            }
            
        except Exception as e:
            logger.error(f"LINE Login callback處理失敗: {e}")
            if 'line_user_id' in locals():
                unified_user_manager.log_user_operation(
                    line_user_id=line_user_id,
                    operation_type='line_login_error',
                    result_status='failed',
                    error_message=str(e)
                )
            return {'success': False, 'error': str(e)}
    
    def _exchange_access_token(self, code: str) -> Optional[Dict[str, Any]]:
        """交換access token"""
        if not self.channel_secret:
            logger.error("LINE Login Channel Secret not configured")
            return None
        
        token_url = f"{self.line_login_api_base}/token"
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.channel_id,
            'client_secret': self.channel_secret
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            response = requests.post(token_url, data=data, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"交換access token失敗: {e}")
            return None
    
    def _get_user_profile(self, access_token: str) -> Optional[Dict[str, Any]]:
        """獲取用戶資料"""
        profile_url = f"{self.line_api_base}/profile"
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        try:
            response = requests.get(profile_url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"獲取用戶資料失敗: {e}")
            return None
    
    def create_binding_message(self, line_user_id: str) -> Dict[str, Any]:
        """創建綁定提示訊息"""
        # 檢查用戶是否已綁定
        user_data = unified_user_manager.get_user_by_line_id(line_user_id)
        bindings = unified_user_manager.get_user_website_bindings(line_user_id)
        available_modules = unified_user_manager.get_available_modules()
        
        if user_data and user_data.get('is_verified'):
            # 已綁定用戶 - 顯示綁定狀態
            return self._create_bound_user_message(user_data, bindings, available_modules)
        else:
            # 未綁定用戶 - 顯示綁定邀請
            return self._create_binding_invitation_message(line_user_id)
    
    def _create_binding_invitation_message(self, line_user_id: str) -> Dict[str, Any]:
        """創建綁定邀請訊息"""
        login_url = self.generate_login_url(line_user_id)
        
        return {
            "type": "bubble",
            "size": "giga",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🔗 帳號綁定",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#ffffff",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": "一次綁定，暢遊所有網站",
                        "size": "sm",
                        "color": "#ffffff",
                        "align": "center",
                        "margin": "sm"
                    }
                ],
                "backgroundColor": "#00B900",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🎯 綁定後您可以：",
                        "weight": "bold",
                        "size": "md",
                        "color": "#333333",
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": "• 無需重複登入各個網站\n• 統一管理所有帳號資料\n• 享受個人化服務體驗\n• 快速操作所有功能",
                        "size": "sm",
                        "color": "#666666",
                        "wrap": True,
                        "margin": "sm"
                    },
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": "🔒 安全保障",
                        "weight": "bold",
                        "size": "sm",
                        "color": "#00B900",
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": "使用LINE官方認證，資料安全有保障",
                        "size": "xs",
                        "color": "#888888",
                        "wrap": True,
                        "margin": "sm"
                    }
                ],
                "paddingAll": "20px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": "🔗 立即綁定帳號",
                            "uri": login_url
                        },
                        "style": "primary",
                        "color": "#00B900",
                        "height": "sm"
                    }
                ],
                "paddingAll": "20px"
            }
        }
    
    def _create_bound_user_message(self, user_data: Dict[str, Any], 
                                  bindings: List[Dict[str, Any]], 
                                  available_modules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """創建已綁定用戶訊息"""
        binding_contents = []
        
        for module in available_modules:
            is_bound = any(b['module_id'] == module['id'] for b in bindings)
            status_text = "✅ 已綁定" if is_bound else "⚪ 未綁定"
            status_color = "#00B900" if is_bound else "#999999"
            
            binding_contents.append({
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "text",
                        "text": module['module_display_name'],
                        "size": "sm",
                        "color": "#333333",
                        "flex": 1
                    },
                    {
                        "type": "text",
                        "text": status_text,
                        "size": "xs",
                        "color": status_color,
                        "align": "end"
                    }
                ],
                "marginBottom": "sm"
            })
        
        return {
            "type": "bubble",
            "size": "giga",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"👋 {user_data.get('display_name', '用戶')}",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#ffffff",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": "帳號已綁定成功",
                        "size": "sm",
                        "color": "#ffffff",
                        "align": "center",
                        "margin": "sm"
                    }
                ],
                "backgroundColor": "#00B900",
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🌐 網站綁定狀態",
                        "weight": "bold",
                        "size": "md",
                        "color": "#333333",
                        "margin": "md"
                    }
                ] + binding_contents,
                "paddingAll": "20px"
            }
        }

# 創建全局實例
line_login_handler = LineLoginHandler()
