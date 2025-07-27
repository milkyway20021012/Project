#!/usr/bin/env python3
"""
簡化的 Vercel 部署診斷工具
"""

import os
import sys

def check_files():
    """檢查必要檔案"""
    print("🔍 檢查必要檔案...")
    
    required_files = [
        'app.py',
        'vercel.json', 
        'requirements.txt'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️  缺少檔案: {', '.join(missing_files)}")
        return False
    else:
        print("\n✅ 所有必要檔案都存在")
        return True

def check_requirements():
    """檢查 requirements.txt 內容"""
    print("\n🔍 檢查 requirements.txt...")
    
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt 不存在")
        return False
    
    with open('requirements.txt', 'r') as f:
        content = f.read()
    
    required_packages = [
        'flask',
        'line-bot-sdk', 
        'python-dotenv',
        'openai'
    ]
    
    missing_packages = []
    for package in required_packages:
        if package in content:
            print(f"✅ {package}")
        else:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  缺少套件: {', '.join(missing_packages)}")
        return False
    else:
        print("\n✅ 所有必要套件都在 requirements.txt 中")
        return True

def check_vercel_config():
    """檢查 vercel.json 配置"""
    print("\n🔍 檢查 vercel.json...")
    
    if not os.path.exists('vercel.json'):
        print("❌ vercel.json 不存在")
        return False
    
    try:
        with open('vercel.json', 'r') as f:
            content = f.read()
        
        if '"@vercel/python"' in content:
            print("✅ Python runtime 配置正確")
        else:
            print("❌ Python runtime 配置有問題")
            return False
        
        if '"app.py"' in content:
            print("✅ 主檔案配置正確")
        else:
            print("❌ 主檔案配置有問題")
            return False
        
        print("✅ vercel.json 配置看起來正確")
        return True
        
    except Exception as e:
        print(f"❌ 讀取 vercel.json 時發生錯誤: {e}")
        return False

def main():
    """主函數"""
    print("🚀 Vercel 部署診斷工具")
    print("=" * 50)
    
    files_ok = check_files()
    req_ok = check_requirements()
    config_ok = check_vercel_config()
    
    print("\n" + "=" * 50)
    print("📊 診斷結果:")
    
    if all([files_ok, req_ok, config_ok]):
        print("✅ 本地配置看起來沒問題！")
        print("\n💡 如果仍然遇到 500 錯誤，請檢查：")
        print("1. Vercel 環境變數設定：")
        print("   - CHANNEL_ACCESS_TOKEN")
        print("   - CHANNEL_SECRET") 
        print("   - OPENAI_API_KEY")
        print("2. 前往 Vercel Dashboard → 專案 → Settings → Environment Variables")
        print("3. 確保所有環境變數都已正確設定")
        print("4. 重新部署專案")
    else:
        print("❌ 發現配置問題，請修復後重新部署")
        
        if not files_ok:
            print("\n🔧 檔案問題解決方案：")
            print("確保專案根目錄包含：app.py, vercel.json, requirements.txt")
        
        if not req_ok:
            print("\n🔧 依賴問題解決方案：")
            print("檢查 requirements.txt 是否包含所有必要套件")
        
        if not config_ok:
            print("\n🔧 配置問題解決方案：")
            print("檢查 vercel.json 是否正確配置")

if __name__ == "__main__":
    main() 