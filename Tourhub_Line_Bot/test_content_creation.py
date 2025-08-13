#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試內容創建功能
"""

import json
from api.content_creator import content_creator
from api.index import create_creation_response, create_creation_help

def test_trip_creation():
    """測試行程創建"""
    print("🗓️ 測試行程創建功能")
    print("=" * 50)
    
    test_cases = [
        "創建東京三日遊行程",
        "建立北海道五日遊行程",
        "規劃大阪美食行程",
        "新增京都二日遊行程",
        "沖繩度假行程規劃"
    ]
    
    for test_case in test_cases:
        print(f"\n🔍 測試: {test_case}")
        result = content_creator.parse_and_create(test_case, "test_user_123")
        
        if result:
            print(f"  ✅ 解析成功")
            print(f"  📋 類型: {result['content_type']}")
            print(f"  📝 標題: {result.get('details', {}).get('title', 'N/A')}")
            print(f"  📍 地點: {result.get('details', {}).get('location', 'N/A')}")
            print(f"  📅 天數: {result.get('details', {}).get('days', 'N/A')}")
            print(f"  🎯 狀態: {result['type']}")
        else:
            print(f"  ❌ 解析失敗")

def test_meeting_creation():
    """測試集合創建"""
    print("\n⏰ 測試集合創建功能")
    print("=" * 50)
    
    test_cases = [
        "創建明天9點東京車站集合",
        "設定後天下午2點集合",
        "約今天晚上7點集合",
        "建立大阪城集合",
        "新增京都站集合時間"
    ]
    
    for test_case in test_cases:
        print(f"\n🔍 測試: {test_case}")
        result = content_creator.parse_and_create(test_case, "test_user_123")
        
        if result:
            print(f"  ✅ 解析成功")
            print(f"  📋 類型: {result['content_type']}")
            print(f"  📝 標題: {result.get('details', {}).get('title', 'N/A')}")
            print(f"  📍 地點: {result.get('details', {}).get('location', 'N/A')}")
            time_info = result.get('details', {}).get('time_info', {})
            if time_info:
                print(f"  ⏰ 時間: {time_info.get('description', 'N/A')}")
                if time_info.get('date'):
                    print(f"  📅 日期: {time_info['date']}")
                if time_info.get('time'):
                    print(f"  🕐 時刻: {time_info['time']}")
            print(f"  🎯 狀態: {result['type']}")
        else:
            print(f"  ❌ 解析失敗")

def test_bill_creation():
    """測試分帳創建"""
    print("\n💰 測試分帳創建功能")
    print("=" * 50)
    
    test_cases = [
        "創建東京旅遊分帳",
        "建立聚餐分帳",
        "新增購物分帳",
        "大阪美食AA制",
        "北海道旅行分帳管理"
    ]
    
    for test_case in test_cases:
        print(f"\n🔍 測試: {test_case}")
        result = content_creator.parse_and_create(test_case, "test_user_123")
        
        if result:
            print(f"  ✅ 解析成功")
            print(f"  📋 類型: {result['content_type']}")
            print(f"  📝 標題: {result.get('details', {}).get('title', 'N/A')}")
            print(f"  🎯 狀態: {result['type']}")
        else:
            print(f"  ❌ 解析失敗")

def test_response_creation():
    """測試回應訊息創建"""
    print("\n📱 測試回應訊息創建")
    print("=" * 50)
    
    # 測試成功回應
    success_result = {
        'type': 'success',
        'content_type': 'trip',
        'message': '✅ 行程「東京三日遊行程」創建成功！',
        'url': 'https://tripfrontend.vercel.app/trip/trip_20241213_143022',
        'details': {
            'title': '東京三日遊行程',
            'location': '東京',
            'days': 3
        }
    }
    
    print("🔍 測試成功回應:")
    response = create_creation_response(success_result)
    print(f"  ✅ 回應創建成功")
    print(f"  📋 標題: {response['header']['contents'][0]['text']}")
    print(f"  🎨 顏色: {response['header']['backgroundColor']}")
    print(f"  🔘 按鈕: {len(response.get('footer', {}).get('contents', []))}")
    
    # 測試失敗回應
    error_result = {
        'type': 'error',
        'content_type': 'trip',
        'message': '❌ 行程創建失敗：系統錯誤',
        'error': '網路連接失敗'
    }
    
    print("\n🔍 測試失敗回應:")
    response = create_creation_response(error_result)
    print(f"  ✅ 回應創建成功")
    print(f"  📋 標題: {response['header']['contents'][0]['text']}")
    print(f"  🎨 顏色: {response['header']['backgroundColor']}")
    print(f"  🔘 按鈕: {len(response.get('footer', {}).get('contents', []))}")

def test_creation_help():
    """測試創建說明"""
    print("\n📖 測試創建說明")
    print("=" * 50)
    
    help_message = create_creation_help()
    print(f"✅ 創建說明生成成功")
    print(f"📋 標題: {help_message['header']['contents'][0]['text']}")
    print(f"📝 內容區塊數: {len(help_message['body']['contents'])}")

def test_non_creation_messages():
    """測試非創建訊息"""
    print("\n❌ 測試非創建訊息")
    print("=" * 50)
    
    test_cases = [
        "功能介紹",
        "排行榜",
        "天氣查詢",
        "分帳 1000 3人",
        "你好"
    ]
    
    for test_case in test_cases:
        print(f"\n🔍 測試: {test_case}")
        result = content_creator.parse_and_create(test_case, "test_user_123")
        
        if result:
            print(f"  ⚠️ 意外匹配到創建功能")
        else:
            print(f"  ✅ 正確識別為非創建訊息")

def main():
    """主測試函數"""
    print("🚀 開始測試內容創建功能")
    print("=" * 60)
    
    try:
        test_trip_creation()
        test_meeting_creation()
        test_bill_creation()
        test_response_creation()
        test_creation_help()
        test_non_creation_messages()
        
        print("\n✅ 所有測試完成！")
        print("\n🎯 功能總結:")
        print("1. 🗓️ 行程創建 - 支援多種格式，自動解析地點和天數")
        print("2. ⏰ 集合創建 - 支援時間和地點解析")
        print("3. 💰 分帳創建 - 支援多種命名方式")
        print("4. 📱 回應訊息 - 成功/失敗狀態的美觀顯示")
        print("5. 📖 創建說明 - 完整的使用指南")
        
        print("\n📱 使用範例:")
        print("• 創建東京三日遊行程 → 自動創建到行程管理網站")
        print("• 設定明天9點東京車站集合 → 自動創建到集合管理網站")
        print("• 建立東京旅遊分帳 → 自動創建到分帳管理網站")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
