#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統一用戶管理系統
處理 Line 用戶的身份驗證和跨網站操作
"""

import os
import json
import uuid
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import mysql.connector
import requests

logger = logging.getLogger(__name__)

class UnifiedUserManager:
    def __init__(self):
        self.db_config = {
            'host': os.environ.get('MYSQL_HOST', 'trip.mysql.database.azure.com'),
            'user': os.environ.get('MYSQL_USER', 'b1129005'),
            'password': os.environ.get('MYSQL_PASSWORD', 'Anderson3663'),
            'database': os.environ.get('MYSQL_DB', 'tourhub'),
            'port': int(os.environ.get('MYSQL_PORT', 3306)),
            'ssl_disabled': False,
            'autocommit': True
        }
    
    def get_connection(self):
        """獲取資料庫連接"""
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"資料庫連接失敗: {e}")
            return None
    
    def get_or_create_user(self, line_user_id: str, display_name: str = None, picture_url: str = None) -> Optional[Dict]:
        """獲取或創建統一用戶"""
        connection = self.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # 檢查用戶是否存在
            cursor.execute(
                "SELECT * FROM unified_users WHERE line_user_id = %s",
                (line_user_id,)
            )
            user = cursor.fetchone()
            
            if user:
                # 更新最後登入時間
                cursor.execute(
                    "UPDATE unified_users SET last_login_at = %s WHERE id = %s",
                    (datetime.now(), user['id'])
                )
                logger.info(f"用戶 {line_user_id} 登入成功")
                return user
            
            # 創建新用戶
            unified_token = self.generate_unified_token(line_user_id)
            cursor.execute("""
                INSERT INTO unified_users 
                (line_user_id, display_name, picture_url, unified_token, is_verified, last_login_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (line_user_id, display_name, picture_url, unified_token, True, datetime.now()))
            
            user_id = cursor.lastrowid
            
            # 獲取新創建的用戶
            cursor.execute("SELECT * FROM unified_users WHERE id = %s", (user_id,))
            new_user = cursor.fetchone()
            
            logger.info(f"新用戶 {line_user_id} 創建成功")
            return new_user
            
        except Exception as e:
            logger.error(f"用戶管理錯誤: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    
    def generate_unified_token(self, line_user_id: str) -> str:
        """生成統一認證 Token"""
        timestamp = str(int(datetime.now().timestamp()))
        random_uuid = str(uuid.uuid4())
        raw_string = f"{line_user_id}:{timestamp}:{random_uuid}"
        return hashlib.sha256(raw_string.encode()).hexdigest()
    
    def bind_website(self, user_id: int, module_name: str, external_data: Dict = None) -> bool:
        """綁定用戶到網站模組"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # 獲取模組 ID
            cursor.execute("SELECT id FROM website_modules WHERE module_name = %s", (module_name,))
            module = cursor.fetchone()
            
            if not module:
                logger.error(f"模組 {module_name} 不存在")
                return False
            
            module_id = module['id']
            
            # 檢查是否已經綁定
            cursor.execute("""
                SELECT id FROM user_website_bindings 
                WHERE unified_user_id = %s AND module_id = %s
            """, (user_id, module_id))
            
            existing_binding = cursor.fetchone()
            
            if existing_binding:
                # 更新現有綁定
                cursor.execute("""
                    UPDATE user_website_bindings 
                    SET binding_data = %s, is_active = TRUE, updated_at = %s
                    WHERE id = %s
                """, (json.dumps(external_data or {}), datetime.now(), existing_binding['id']))
            else:
                # 創建新綁定
                cursor.execute("""
                    INSERT INTO user_website_bindings 
                    (unified_user_id, module_id, binding_data, is_active)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, module_id, json.dumps(external_data or {}), True))
            
            logger.info(f"用戶 {user_id} 成功綁定到模組 {module_name}")
            return True
            
        except Exception as e:
            logger.error(f"網站綁定錯誤: {e}")
            return False
        finally:
            cursor.close()
            connection.close()
    
    def get_user_bindings(self, user_id: int) -> Dict[str, Any]:
        """獲取用戶的所有網站綁定"""
        connection = self.get_connection()
        if not connection:
            return {}
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT wm.module_name, wm.module_display_name, wm.base_url,
                       uwb.binding_data, uwb.is_active, uwb.created_at
                FROM user_website_bindings uwb
                JOIN website_modules wm ON uwb.module_id = wm.id
                WHERE uwb.unified_user_id = %s AND uwb.is_active = TRUE
            """, (user_id,))
            
            bindings = cursor.fetchall()
            
            result = {}
            for binding in bindings:
                result[binding['module_name']] = {
                    'display_name': binding['module_display_name'],
                    'base_url': binding['base_url'],
                    'binding_data': json.loads(binding['binding_data'] or '{}'),
                    'created_at': binding['created_at']
                }
            
            return result
            
        except Exception as e:
            logger.error(f"獲取用戶綁定錯誤: {e}")
            return {}
        finally:
            cursor.close()
            connection.close()
    
    def log_operation(self, user_id: int, operation_type: str, operation_data: Dict, 
                     module_name: str = None, result_status: str = 'pending') -> bool:
        """記錄用戶操作"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            module_id = None
            if module_name:
                cursor.execute("SELECT id FROM website_modules WHERE module_name = %s", (module_name,))
                module = cursor.fetchone()
                if module:
                    module_id = module[0]
            
            cursor.execute("""
                INSERT INTO user_operation_logs 
                (unified_user_id, module_id, operation_type, operation_data, result_status)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, module_id, operation_type, json.dumps(operation_data), result_status))
            
            return True
            
        except Exception as e:
            logger.error(f"操作日誌記錄錯誤: {e}")
            return False
        finally:
            cursor.close()
            connection.close()

# 全局實例
user_manager = UnifiedUserManager()
