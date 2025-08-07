#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試實際網站操作功能
"""

from api.website_proxy import website_proxy
from api.unified_user_manager import unified_user_manager

def test_website_operations():
    """測試網站操作功能"""
    print("🧪 測試實際網站操作功能")
    print("=" * 50)
    
    # 模擬用戶資料
    mock_user_data = {
        'id': 1,
        'line_user_id': 'test_user_123',
        'display_name': '測試用戶',
        'unified_token': 'test_token_123',
        'is_verified': True
    }
    
    # 測試各個網站模組
    test_cases = [
        {
            'module': 'tourhub_leaderboard',
            'operation': 'view_leaderboard',
            'description': 'TourHub排行榜 - 查看排行榜'
        },
        {
            'module': 'trip_management',
            'operation': 'manage_trips',
            'description': '行程管理 - 管理我的行程'
        },
        {
            'module': 'tour_clock',
            'operation': 'manage_meetings',
            'description': '集合管理 - 管理集合時間'
        },
        {
            'module': 'locker_finder',
            'operation': 'find_lockers',
            'description': '置物櫃查找 - 查找置物櫃'
        },
        {
            'module': 'bill_split',
            'operation': 'manage_bills',
            'description': '分帳系統 - 管理分帳'
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 測試：{test_case['description']}")
        print(f"   模組：{test_case['module']}")
        print(f"   操作：{test_case['operation']}")
        
        try:
            # 直接調用網站代理的內部方法進行測試
            proxy = website_proxy
            
            # 模擬模組資料
            mock_module = {
                'module_name': test_case['module'],
                'base_url': get_module_url(test_case['module'])
            }
            
            # 執行操作
            result = proxy._execute_module_operation(
                mock_user_data, 
                mock_module, 
                test_case['operation']
            )
            
            if result.get('success'):
                print(f"   ✅ 成功")
                if result.get('data', {}).get('action') == 'redirect':
                    print(f"   🔗 跳轉URL: {result['data']['url']}")
                    print(f"   💬 訊息: {result['data']['message']}")
            else:
                print(f"   ❌ 失敗: {result.get('error')}")
                
        except Exception as e:
            print(f"   ⚠️  異常: {e}")
    
    print(f"\n{'=' * 50}")
    print("🎯 測試完成")

def get_module_url(module_name):
    """獲取模組URL"""
    urls = {
        'tourhub_leaderboard': 'https://tourhubashy.vercel.app',
        'trip_management': 'https://tripfrontend.vercel.app/linetrip',
        'tour_clock': 'https://tourclock-dvf2.vercel.app',
        'locker_finder': 'https://tripfrontend.vercel.app/linelocker',
        'bill_split': 'https://split-front-pearl.vercel.app'
    }
    return urls.get(module_name, '')

def test_module_operations_menu():
    """測試模組操作選單"""
    print("\n🧪 測試模組操作選單")
    print("=" * 50)
    
    from api.index import create_website_operation_menu
    
    modules = [
        'tourhub_leaderboard',
        'trip_management', 
        'tour_clock',
        'locker_finder',
        'bill_split'
    ]
    
    for module in modules:
        print(f"\n📋 測試模組：{module}")
        try:
            menu = create_website_operation_menu('test_user_123', module)
            
            if menu and menu.get('type') == 'bubble':
                print(f"   ✅ 選單創建成功")
                
                # 檢查操作按鈕
                body_contents = menu.get('body', {}).get('contents', [])
                button_count = len([c for c in body_contents if c.get('type') == 'button'])
                print(f"   🔘 操作按鈕數量: {button_count}")
                
                # 顯示操作選項
                for content in body_contents:
                    if content.get('type') == 'button':
                        label = content.get('action', {}).get('label', '')
                        data = content.get('action', {}).get('data', '')
                        print(f"      - {label} ({data})")
            else:
                print(f"   ❌ 選單創建失敗")
                
        except Exception as e:
            print(f"   ⚠️  異常: {e}")

if __name__ == "__main__":
    test_website_operations()
    test_module_operations_menu()
