#!/usr/bin/env python3
"""
Vercel 部署診斷腳本
"""

import os
import sys
from dotenv import load_dotenv

def check_environment():
    """檢查環境設定"""
    print("🔍 環境診斷")
    print("=" * 40)
    
    # 載入環境變數
    load_dotenv()
    
    # 檢查必要檔案
    required_files = ['app.py', 'requirements.txt', 'vercel.json']
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} - 存在")
        else:
            print(f"❌ {file} - 缺失")
    
    # 檢查環境變數
    env_vars = ['OPENAI_API_KEY', 'CHANNEL_ACCESS_TOKEN', 'CHANNEL_SECRET']
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var} - 已設定 ({value[:20]}...)")
        else:
            print(f"❌ {var} - 未設定")
    
    print()

def check_app_structure():
    """檢查應用程式結構"""
    print("📁 應用程式結構檢查")
    print("=" * 40)
    
    try:
        from app import app
        print("✅ Flask 應用程式載入成功")
        
        # 檢查路由
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(f"{rule.rule} ({', '.join(rule.methods)})")
        
        print("📋 可用路由：")
        for route in routes:
            print(f"  - {route}")
            
    except Exception as e:
        print(f"❌ 應用程式載入失敗：{str(e)}")
    
    print()

def check_dependencies():
    """檢查依賴套件"""
    print("📦 依賴套件檢查")
    print("=" * 40)
    
    required_packages = [
        'flask',
        'line-bot-sdk',
        'python-dotenv',
        'openai'
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} - 已安裝")
        except ImportError:
            print(f"❌ {package} - 未安裝")
    
    print()

def generate_deployment_info():
    """生成部署資訊"""
    print("🚀 部署資訊")
    print("=" * 40)
    
    print("📋 部署檢查清單：")
    print("1. 確保所有檔案已推送到 GitHub")
    print("2. 在 Vercel 中設定環境變數")
    print("3. 設定 LINE Bot Webhook URL")
    print("4. 測試部署 URL")
    
    print("\n🔗 測試 URL：")
    print("- 主頁：https://your-project.vercel.app/")
    print("- 健康檢查：https://your-project.vercel.app/health")
    print("- Webhook：https://your-project.vercel.app/callback")
    
    print("\n📊 監控位置：")
    print("- Vercel Dashboard → 專案 → Functions")
    print("- Vercel Dashboard → 專案 → Deployments")

if __name__ == "__main__":
    print("🧪 Vercel 部署診斷工具")
    print("=" * 50)
    
    check_environment()
    check_app_structure()
    check_dependencies()
    generate_deployment_info()
    
    print("=" * 50)
    print("🎯 診斷完成！請根據上述資訊進行部署。") 