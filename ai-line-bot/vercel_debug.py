#!/usr/bin/env python3
"""
Vercel 部署診斷工具
用於檢查環境變數和配置問題
"""

import os
import sys
from dotenv import load_dotenv

def check_environment():
    """檢查環境變數設定"""
    print("🔍 檢查環境變數...")
    
    # 載入 .env 檔案（如果存在）
    load_dotenv()
    
    # 檢查必要的環境變數
    required_vars = [
        'CHANNEL_ACCESS_TOKEN',
        'CHANNEL_SECRET', 
        'OPENAI_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * min(len(value), 10)}...")
        else:
            print(f"❌ {var}: 未設定")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  缺少環境變數: {', '.join(missing_vars)}")
        print("請在 Vercel 專案設定中添加這些環境變數")
        return False
    else:
        print("\n✅ 所有環境變數都已正確設定")
        return True

def check_vercel_config():
    """檢查 Vercel 配置"""
    print("\n🔍 檢查 Vercel 配置...")
    
    # 檢查 vercel.json
    if os.path.exists('vercel.json'):
        print("✅ vercel.json 檔案存在")
    else:
        print("❌ vercel.json 檔案不存在")
        return False
    
    # 檢查 requirements.txt
    if os.path.exists('requirements.txt'):
        print("✅ requirements.txt 檔案存在")
    else:
        print("❌ requirements.txt 檔案不存在")
        return False
    
    # 檢查 app.py
    if os.path.exists('app.py'):
        print("✅ app.py 檔案存在")
    else:
        print("❌ app.py 檔案不存在")
        return False
    
    return True

def check_dependencies():
    """檢查依賴套件"""
    print("\n🔍 檢查依賴套件...")
    
    required_packages = [
        'flask',
        'line-bot-sdk',
        'python-dotenv',
        'openai'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  缺少套件: {', '.join(missing_packages)}")
        return False
    else:
        print("\n✅ 所有依賴套件都已安裝")
        return True

def main():
    """主函數"""
    print("🚀 Vercel 部署診斷工具")
    print("=" * 50)
    
    env_ok = check_environment()
    config_ok = check_vercel_config()
    deps_ok = check_dependencies()
    
    print("\n" + "=" * 50)
    print("📊 診斷結果:")
    
    if all([env_ok, config_ok, deps_ok]):
        print("✅ 所有檢查都通過！您的配置看起來沒問題。")
        print("\n💡 如果仍然遇到 500 錯誤，請檢查：")
        print("1. Vercel 函數日誌中的具體錯誤訊息")
        print("2. LINE Bot 的 Webhook URL 設定")
        print("3. API 金鑰的有效性")
    else:
        print("❌ 發現問題，請修復後重新部署")
        
        if not env_ok:
            print("\n🔧 環境變數問題解決方案：")
            print("1. 前往 Vercel Dashboard")
            print("2. 選擇您的專案")
            print("3. 進入 Settings → Environment Variables")
            print("4. 添加以下環境變數：")
            print("   - CHANNEL_ACCESS_TOKEN")
            print("   - CHANNEL_SECRET") 
            print("   - OPENAI_API_KEY")
        
        if not config_ok:
            print("\n🔧 配置問題解決方案：")
            print("確保專案根目錄包含：vercel.json, requirements.txt, app.py")
        
        if not deps_ok:
            print("\n🔧 依賴問題解決方案：")
            print("檢查 requirements.txt 是否包含所有必要套件")

if __name__ == "__main__":
    main() 