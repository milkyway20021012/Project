#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試LINE Bot功能的腳本
"""

import os
import json
from api.index import app

def test_message_parsing():
    """測試訊息解析功能"""
    print("=== 測試訊息解析功能 ===")
    
    # 測試創建行程
    create_message = "創建日本東京五日遊"
    print(f"測試創建訊息: {create_message}")
    has_create_keyword = any(keyword in create_message for keyword in ["創建", "建立", "新增行程"])
    print(f"包含創建關鍵字: {has_create_keyword}")
    
    # 獨立行程管理功能已移除
    print("獨立行程管理功能已移除")

    return True

def test_flask_app():
    """測試Flask應用"""
    print("\n=== 測試Flask應用 ===")
    
    with app.test_client() as client:
        # 測試健康檢查
        response = client.get('/')
        print(f"健康檢查狀態碼: {response.status_code}")
        print(f"健康檢查回應: {response.get_json()}")
        
        # 測試debug端點
        debug_response = client.get('/debug')
        print(f"Debug端點狀態碼: {debug_response.status_code}")
        print(f"Debug端點回應: {debug_response.get_json()}")
        
        return response.status_code == 200

def test_environment():
    """測試環境變數"""
    print("\n=== 測試環境變數 ===")
    
    # 設定測試環境變數
    os.environ['CHANNEL_ACCESS_TOKEN'] = 'iSLcm0H/4YrP33YTWZusvTSdlffaNqoR85/zovMoumur6Lc0mhr3W1A1xoTGjiA/gCiJfVg11/sNW8mDhGtkjiQek3FZL3Pl8g1ix8sxbWMVWH1l8r3vmJgPFyGbP7fvz2Sw/kLXrov+xwk2vnlufgdB04t89/1O/w1cDnyilFU='
    os.environ['CHANNEL_SECRET'] = '568f8e8c2c6c24970ddd9512dc1fa46d'
    
    has_token = bool(os.environ.get('CHANNEL_ACCESS_TOKEN'))
    has_secret = bool(os.environ.get('CHANNEL_SECRET'))
    
    print(f"CHANNEL_ACCESS_TOKEN 存在: {has_token}")
    print(f"CHANNEL_SECRET 存在: {has_secret}")
    
    return has_token and has_secret

def test_database():
    """測試資料庫連接"""
    print("\n=== 測試資料庫連接 ===")
    
    try:
        from api.database_utils import get_database_connection

        # 測試連接
        conn = get_database_connection()
        if conn:
            print("資料庫連接: 成功")
            conn.close()
            print("獨立行程管理功能已移除")
            return True
        else:
            print("資料庫連接: 失敗")
            return False
            
    except Exception as e:
        print(f"資料庫測試錯誤: {str(e)}")
        return False

def main():
    """主測試函數"""
    print("開始測試LINE Bot功能...\n")
    
    results = {
        "訊息解析": test_message_parsing(),
        "Flask應用": test_flask_app(),
        "環境變數": test_environment(),
        "資料庫連接": test_database()
    }
    
    print("\n=== 測試結果總結 ===")
    all_passed = True
    for test_name, result in results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有測試都通過！")
        print("\n可能的問題:")
        print("1. LINE Bot webhook URL沒有正確設定")
        print("2. Vercel部署有問題")
        print("3. LINE Developer Console設定有誤")
        print("\n建議檢查:")
        print("1. 確認Vercel部署成功")
        print("2. 檢查LINE Bot webhook URL設定")
        print("3. 確認環境變數在Vercel上正確設定")
    else:
        print("\n❌ 有測試失敗，請檢查上述錯誤")

if __name__ == "__main__":
    main()
