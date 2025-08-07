#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
統一用戶管理系統
處理LINE用戶綁定、統一認證和多網站操作代理
"""

import os
import json
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import logging

# 設置日誌
logger = logging.getLogger(__name__)

# 嘗試導入MySQL連接器
try:
    import mysql.connector
    from mysql.connector import Error
    MYSQL_AVAILABLE = True
    logger.info("MySQL connector imported successfully")
except ImportError:
    MYSQL_AVAILABLE = False
    logger.warning("MySQL connector not available")

class UnifiedUserManager:
    """統一用戶管理器"""
    
    def __init__(self):
        self.db_config = {
            'host': os.environ.get('DB_HOST', 'localhost'),
            'database': os.environ.get('DB_NAME', 'tourhub'),
            'user': os.environ.get('DB_USER', 'root'),
            'password': os.environ.get('DB_PASSWORD', ''),
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci',
            'autocommit': True
        }
    
    def get_database_connection(self):
        """獲取資料庫連接"""
        if not MYSQL_AVAILABLE:
            logger.error("MySQL connector not available")
            return None
        
        try:
            connection = mysql.connector.connect(**self.db_config)
            if connection.is_connected():
                return connection
        except Error as e:
            logger.error(f"資料庫連接失敗: {e}")
        return None
    
    def generate_unified_token(self, line_user_id: str) -> str:
        """生成統一認證Token"""
        timestamp = str(int(datetime.now().timestamp()))
        random_string = secrets.token_urlsafe(32)
        raw_token = f"{line_user_id}:{timestamp}:{random_string}"
        return hashlib.sha256(raw_token.encode()).hexdigest()
    
    def create_or_update_user(self, line_user_id: str, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """創建或更新統一用戶"""
        if not MYSQL_AVAILABLE:
            logger.warning("MySQL not available, cannot create user")
            return None
        
        try:
            connection = self.get_database_connection()
            if not connection:
                return None
            
            cursor = connection.cursor(dictionary=True)
            
            # 檢查用戶是否已存在
            check_query = "SELECT * FROM unified_users WHERE line_user_id = %s"
            cursor.execute(check_query, (line_user_id,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                # 更新現有用戶
                update_query = """
                UPDATE unified_users 
                SET display_name = %s, picture_url = %s, last_login_at = %s, updated_at = %s
                WHERE line_user_id = %s
                """
                cursor.execute(update_query, (
                    profile_data.get('displayName'),
                    profile_data.get('pictureUrl'),
                    datetime.now(),
                    datetime.now(),
                    line_user_id
                ))
                
                user_data = existing_user.copy()
                user_data.update({
                    'display_name': profile_data.get('displayName'),
                    'picture_url': profile_data.get('pictureUrl'),
                    'last_login_at': datetime.now()
                })
                
            else:
                # 創建新用戶
                unified_token = self.generate_unified_token(line_user_id)
                
                insert_query = """
                INSERT INTO unified_users 
                (line_user_id, display_name, picture_url, unified_token, last_login_at)
                VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (
                    line_user_id,
                    profile_data.get('displayName'),
                    profile_data.get('pictureUrl'),
                    unified_token,
                    datetime.now()
                ))
                
                user_id = cursor.lastrowid
                user_data = {
                    'id': user_id,
                    'line_user_id': line_user_id,
                    'display_name': profile_data.get('displayName'),
                    'picture_url': profile_data.get('pictureUrl'),
                    'unified_token': unified_token,
                    'is_verified': False,
                    'status': 'active',
                    'created_at': datetime.now(),
                    'last_login_at': datetime.now()
                }
            
            cursor.close()
            connection.close()
            
            logger.info(f"用戶 {line_user_id} 創建/更新成功")
            return user_data
            
        except Error as e:
            logger.error(f"創建/更新用戶失敗: {e}")
            return None
    
    def get_user_by_line_id(self, line_user_id: str) -> Optional[Dict[str, Any]]:
        """根據LINE ID獲取用戶資料"""
        if not MYSQL_AVAILABLE:
            return None
        
        try:
            connection = self.get_database_connection()
            if not connection:
                return None
            
            cursor = connection.cursor(dictionary=True)
            query = "SELECT * FROM unified_users WHERE line_user_id = %s AND status = 'active'"
            cursor.execute(query, (line_user_id,))
            user = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            return user
            
        except Error as e:
            logger.error(f"獲取用戶資料失敗: {e}")
            return None
    
    def get_user_website_bindings(self, line_user_id: str) -> List[Dict[str, Any]]:
        """獲取用戶的網站綁定列表"""
        if not MYSQL_AVAILABLE:
            return []
        
        try:
            connection = self.get_database_connection()
            if not connection:
                return []
            
            cursor = connection.cursor(dictionary=True)
            query = """
            SELECT uwb.*, wm.module_name, wm.module_display_name, wm.base_url
            FROM user_website_bindings uwb
            JOIN unified_users uu ON uwb.unified_user_id = uu.id
            JOIN website_modules wm ON uwb.module_id = wm.id
            WHERE uu.line_user_id = %s AND uwb.is_active = TRUE AND wm.is_active = TRUE
            ORDER BY uwb.created_at DESC
            """
            cursor.execute(query, (line_user_id,))
            bindings = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            return bindings
            
        except Error as e:
            logger.error(f"獲取用戶網站綁定失敗: {e}")
            return []
    
    def get_available_modules(self) -> List[Dict[str, Any]]:
        """獲取可用的網站模組列表"""
        if not MYSQL_AVAILABLE:
            return []
        
        try:
            connection = self.get_database_connection()
            if not connection:
                return []
            
            cursor = connection.cursor(dictionary=True)
            query = "SELECT * FROM website_modules WHERE is_active = TRUE ORDER BY module_display_name"
            cursor.execute(query)
            modules = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            return modules
            
        except Error as e:
            logger.error(f"獲取網站模組列表失敗: {e}")
            return []
    
    def log_user_operation(self, line_user_id: str, operation_type: str, 
                          module_name: str = None, operation_data: Dict = None, 
                          result_status: str = 'pending', error_message: str = None) -> bool:
        """記錄用戶操作日誌"""
        if not MYSQL_AVAILABLE:
            return False
        
        try:
            connection = self.get_database_connection()
            if not connection:
                return False
            
            cursor = connection.cursor(dictionary=True)
            
            # 獲取用戶ID和模組ID
            user_query = "SELECT id FROM unified_users WHERE line_user_id = %s"
            cursor.execute(user_query, (line_user_id,))
            user_result = cursor.fetchone()
            
            if not user_result:
                return False
            
            unified_user_id = user_result['id']
            module_id = None
            
            if module_name:
                module_query = "SELECT id FROM website_modules WHERE module_name = %s"
                cursor.execute(module_query, (module_name,))
                module_result = cursor.fetchone()
                if module_result:
                    module_id = module_result['id']
            
            # 插入操作日誌
            log_query = """
            INSERT INTO user_operation_logs 
            (unified_user_id, module_id, operation_type, operation_data, result_status, error_message)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(log_query, (
                unified_user_id,
                module_id,
                operation_type,
                json.dumps(operation_data) if operation_data else None,
                result_status,
                error_message
            ))
            
            cursor.close()
            connection.close()
            
            return True
            
        except Error as e:
            logger.error(f"記錄用戶操作失敗: {e}")
            return False

# 創建全局實例
unified_user_manager = UnifiedUserManager()
