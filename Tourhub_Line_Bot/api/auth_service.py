#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統一認證服務
提供 API 端點供各網站驗證 Line Bot 用戶
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from .unified_user_manager import user_manager

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建 Flask 應用
app = Flask(__name__)
CORS(app)  # 允許跨域請求

@app.route('/api/auth/verify-token', methods=['POST'])
def verify_unified_token():
    """驗證統一認證 Token"""
    try:
        data = request.json
        if not data:
            return jsonify({'valid': False, 'error': '無效的請求格式'}), 400
        
        line_user_id = data.get('line_user_id')
        unified_token = data.get('unified_token')
        
        if not line_user_id or not unified_token:
            return jsonify({'valid': False, 'error': '缺少必要參數'}), 400
        
        logger.info(f"🔐 驗證 Token: {line_user_id}")
        
        # 驗證 Token
        user = user_manager.get_or_create_user(line_user_id)
        if user and user.get('unified_token') == unified_token:
            logger.info(f"✅ Token 驗證成功: {line_user_id}")
            return jsonify({
                'valid': True,
                'user_id': user['id'],
                'line_user_id': line_user_id,
                'display_name': user.get('display_name'),
                'verified_at': datetime.now().isoformat()
            })
        
        logger.warning(f"❌ Token 驗證失敗: {line_user_id}")
        return jsonify({'valid': False, 'error': 'Token 無效'}), 401
        
    except Exception as e:
        logger.error(f"💥 Token 驗證錯誤: {e}")
        return jsonify({'valid': False, 'error': '服務器錯誤'}), 500

@app.route('/api/auth/get-user', methods=['POST'])
def get_user_info():
    """獲取用戶資訊"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': '無效的請求格式'}), 400
        
        line_user_id = data.get('line_user_id')
        if not line_user_id:
            return jsonify({'success': False, 'error': '缺少 line_user_id'}), 400
        
        logger.info(f"👤 獲取用戶資訊: {line_user_id}")
        
        user = user_manager.get_or_create_user(line_user_id)
        if user:
            logger.info(f"✅ 用戶資訊獲取成功: {line_user_id}")
            return jsonify({
                'success': True,
                'user': {
                    'id': user['id'],
                    'line_user_id': line_user_id,
                    'display_name': user.get('display_name'),
                    'unified_token': user['unified_token'],
                    'is_verified': user.get('is_verified', True),
                    'last_login_at': user.get('last_login_at').isoformat() if user.get('last_login_at') else None,
                    'created_at': user.get('created_at').isoformat() if user.get('created_at') else None
                }
            })
        
        logger.warning(f"❌ 用戶不存在: {line_user_id}")
        return jsonify({'success': False, 'error': '用戶不存在'}), 404
        
    except Exception as e:
        logger.error(f"💥 獲取用戶資訊錯誤: {e}")
        return jsonify({'success': False, 'error': '服務器錯誤'}), 500

@app.route('/api/auth/refresh-token', methods=['POST'])
def refresh_unified_token():
    """刷新統一認證 Token"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': '無效的請求格式'}), 400
        
        line_user_id = data.get('line_user_id')
        old_token = data.get('old_token')
        
        if not line_user_id or not old_token:
            return jsonify({'success': False, 'error': '缺少必要參數'}), 400
        
        logger.info(f"🔄 刷新 Token: {line_user_id}")
        
        # 驗證舊 Token
        user = user_manager.get_or_create_user(line_user_id)
        if not user or user.get('unified_token') != old_token:
            return jsonify({'success': False, 'error': '舊 Token 無效'}), 401
        
        # 生成新 Token
        new_token = user_manager.generate_unified_token(line_user_id)
        
        # 更新資料庫
        connection = user_manager.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute(
                    "UPDATE unified_users SET unified_token = %s, last_login_at = %s WHERE id = %s",
                    (new_token, datetime.now(), user['id'])
                )
                connection.commit()
                
                logger.info(f"✅ Token 刷新成功: {line_user_id}")
                return jsonify({
                    'success': True,
                    'new_token': new_token,
                    'refreshed_at': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"💥 Token 刷新資料庫錯誤: {e}")
                return jsonify({'success': False, 'error': '資料庫錯誤'}), 500
            finally:
                cursor.close()
                connection.close()
        
        return jsonify({'success': False, 'error': '資料庫連接失敗'}), 500
        
    except Exception as e:
        logger.error(f"💥 Token 刷新錯誤: {e}")
        return jsonify({'success': False, 'error': '服務器錯誤'}), 500

@app.route('/api/auth/health', methods=['GET'])
def health_check():
    """健康檢查端點"""
    return jsonify({
        'status': 'healthy',
        'service': 'TourHub Auth Service',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/auth/stats', methods=['GET'])
def get_stats():
    """獲取統計資訊"""
    try:
        connection = user_manager.get_connection()
        if not connection:
            return jsonify({'error': '資料庫連接失敗'}), 500
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # 統計用戶數量
            cursor.execute("SELECT COUNT(*) as total_users FROM unified_users")
            total_users = cursor.fetchone()['total_users']
            
            # 統計今日活躍用戶
            cursor.execute("""
                SELECT COUNT(*) as active_today 
                FROM unified_users 
                WHERE DATE(last_login_at) = CURDATE()
            """)
            active_today = cursor.fetchone()['active_today']
            
            # 統計綁定數量
            cursor.execute("SELECT COUNT(*) as total_bindings FROM user_website_bindings WHERE is_active = TRUE")
            total_bindings = cursor.fetchone()['total_bindings']
            
            return jsonify({
                'total_users': total_users,
                'active_today': active_today,
                'total_bindings': total_bindings,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"💥 統計查詢錯誤: {e}")
            return jsonify({'error': '查詢錯誤'}), 500
        finally:
            cursor.close()
            connection.close()
            
    except Exception as e:
        logger.error(f"💥 統計錯誤: {e}")
        return jsonify({'error': '服務器錯誤'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    
    logger.info(f"🚀 啟動統一認證服務，端口: {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
