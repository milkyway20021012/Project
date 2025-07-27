#!/usr/bin/env python3
"""
部署測試腳本
用於診斷 Vercel 部署問題
"""

import os
import sys

def check_files():
    """檢查必要檔案"""
    print("🔍 檢查部署檔案...")
    
    required_files = [
        'app.py',
        'vercel.json',
        'requirements.txt',
        'runtime.txt'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - 缺少")
            return False
    
    return True

def check_app_structure():
    """檢查應用程式結構"""
    print("\n🔍 檢查應用程式結構...")
    
    try:
        with open('app.py', 'r') as f:
            content = f.read()
        
        # 檢查必要的 Flask 元素
        checks = [
            ('from flask import', 'Flask 導入'),
            ('app = Flask', 'Flask 應用程式初始化'),
            ('@app.route', '路由裝飾器'),
            ('if __name__ == "__main__"', '主程式入口')
        ]
        
        for check, description in checks:
            if check in content:
                print(f"✅ {description}")
            else:
                print(f"❌ {description} - 缺少")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 讀取 app.py 時發生錯誤: {e}")
        return False

def check_vercel_config():
    """檢查 Vercel 配置"""
    print("\n🔍 檢查 Vercel 配置...")
    
    try:
        with open('vercel.json', 'r') as f:
            content = f.read()
        
        checks = [
            ('"@vercel/python"', 'Python runtime'),
            ('"app.py"', '主檔案配置'),
            ('"/(.*)"', '路由配置')
        ]
        
        for check, description in checks:
            if check in content:
                print(f"✅ {description}")
            else:
                print(f"❌ {description} - 缺少")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 讀取 vercel.json 時發生錯誤: {e}")
        return False

def main():
    """主函數"""
    print("🚀 Vercel 部署診斷工具")
    print("=" * 50)
    
    files_ok = check_files()
    app_ok = check_app_structure()
    config_ok = check_vercel_config()
    
    print("\n" + "=" * 50)
    print("📊 診斷結果:")
    
    if all([files_ok, app_ok, config_ok]):
        print("✅ 部署配置看起來正確！")
        print("\n💡 如果仍然遇到 404 錯誤，請檢查：")
        print("1. Vercel 部署是否成功完成")
        print("2. 函數是否正確構建")
        print("3. 路由是否正確配置")
        print("4. 嘗試訪問：https://your-project.vercel.app/")
    else:
        print("❌ 發現配置問題")
        
        if not files_ok:
            print("\n🔧 檔案問題：確保所有必要檔案都存在")
        
        if not app_ok:
            print("\n🔧 應用程式問題：檢查 app.py 結構")
        
        if not config_ok:
            print("\n🔧 配置問題：檢查 vercel.json 設定")

if __name__ == "__main__":
    main() 