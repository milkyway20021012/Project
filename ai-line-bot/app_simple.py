#!/usr/bin/env python3
"""
簡化版本的 LINE Bot 應用程式
用於診斷 Vercel 部署問題
"""

import os
import time
from flask import Flask, request, jsonify

# 初始化 Flask
app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    """首頁端點"""
    try:
        return jsonify({
            "message": "✅ LINE Bot on Vercel is running.",
            "timestamp": time.time(),
            "status": "ok"
        })
    except Exception as e:
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e),
            "timestamp": time.time()
        }), 500

@app.route("/test", methods=["GET"])
def test():
    """測試端點"""
    try:
        return jsonify({
            "status": "ok",
            "message": "測試端點正常運作",
            "timestamp": time.time()
        })
    except Exception as e:
        return jsonify({
            "error": "Test Error",
            "message": str(e),
            "timestamp": time.time()
        }), 500

@app.route("/health", methods=["GET"])
def health():
    """健康檢查端點"""
    try:
        # 檢查環境變數
        env_vars = {
            "CHANNEL_ACCESS_TOKEN": bool(os.getenv('CHANNEL_ACCESS_TOKEN')),
            "CHANNEL_SECRET": bool(os.getenv('CHANNEL_SECRET')),
            "OPENAI_API_KEY": bool(os.getenv('OPENAI_API_KEY'))
        }
        
        return jsonify({
            "status": "healthy",
            "timestamp": time.time(),
            "environment": "production",
            "environment_variables": env_vars,
            "all_vars_set": all(env_vars.values())
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }), 500

@app.route("/debug", methods=["GET"])
def debug():
    """調試端點"""
    try:
        import sys
        import platform
        
        return jsonify({
            "python_version": sys.version,
            "platform": platform.platform(),
            "environment_variables": {
                "CHANNEL_ACCESS_TOKEN": "已設定" if os.getenv('CHANNEL_ACCESS_TOKEN') else "未設定",
                "CHANNEL_SECRET": "已設定" if os.getenv('CHANNEL_SECRET') else "未設定",
                "OPENAI_API_KEY": "已設定" if os.getenv('OPENAI_API_KEY') else "未設定"
            },
            "timestamp": time.time()
        })
    except Exception as e:
        return jsonify({
            "error": "Debug Error",
            "message": str(e),
            "timestamp": time.time()
        }), 500

# 錯誤處理
@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal Server Error",
        "message": "應用程式發生內部錯誤",
        "timestamp": time.time()
    }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({
        "error": "Application Error",
        "message": str(e),
        "timestamp": time.time()
    }), 500

if __name__ == "__main__":
    app.run(debug=False, port=8080) 