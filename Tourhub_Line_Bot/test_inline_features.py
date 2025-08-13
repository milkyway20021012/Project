#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試新的內建功能
"""

import json
from api.index import create_simple_flex_message, get_message_template, calculate_split_bill

def test_split_bill_calculator():
    """測試分帳計算功能"""
    print("💰 測試分帳計算功能")
    print("=" * 50)
    
    test_cases = [
        "分帳 1000 3人",
        "AA 2500 5人",
        "分帳 800 4人",
        "AA 1500 2人",
        "分帳 999 3人"  # 測試小數點
    ]
    
    for test_case in test_cases:
        result = calculate_split_bill(test_case)
        print(f"輸入: {test_case}")
        if result:
            print(f"結果: {result.split('💰')[1].split('📝')[0].strip()}")
        else:
            print("結果: 無法識別")
        print()

def test_inline_features():
    """測試內建功能模板"""
    print("🛠️ 測試內建功能模板")
    print("=" * 50)
    
    features = [
        ("quick_split_calculator", "快速分帳計算器"),
        ("weather_inquiry", "天氣查詢"),
        ("currency_converter", "匯率換算"),
        ("travel_tips", "旅遊小貼士"),
        ("nearby_search", "附近景點搜尋")
    ]
    
    for template_type, name in features:
        print(f"\n🔍 測試 {name}:")
        try:
            flex_message = create_simple_flex_message(template_type)
            print(f"  ✅ 模板創建成功")
            print(f"  📋 標題: {flex_message['header']['contents'][0]['text']}")
            
            # 檢查是否有按鈕
            if 'footer' in flex_message:
                button_count = len(flex_message['footer']['contents'])
                print(f"  🔘 按鈕數量: {button_count}")
            else:
                print(f"  🔘 按鈕數量: 0")
                
        except Exception as e:
            print(f"  ❌ 創建失敗: {e}")

def test_keyword_matching():
    """測試關鍵字匹配"""
    print("\n🔍 測試關鍵字匹配")
    print("=" * 50)
    
    test_keywords = [
        ("快速分帳", "quick_split_calculator"),
        ("天氣查詢", "weather_inquiry"),
        ("匯率換算", "currency_converter"),
        ("旅遊小貼士", "travel_tips"),
        ("附近景點", "nearby_search"),
        ("分帳 1000 3人", None),  # 這個應該被分帳計算功能處理
    ]
    
    for keyword, expected_template in test_keywords:
        template_config = get_message_template(keyword)
        print(f"關鍵字: '{keyword}'")
        
        if template_config:
            actual_template = template_config.get('template')
            print(f"  匹配模板: {actual_template}")
            if expected_template and actual_template == expected_template:
                print(f"  ✅ 匹配正確")
            elif expected_template:
                print(f"  ❌ 預期: {expected_template}, 實際: {actual_template}")
            else:
                print(f"  ℹ️ 有匹配結果")
        else:
            if expected_template is None:
                print(f"  ✅ 正確無匹配（將由特殊處理）")
            else:
                print(f"  ❌ 預期匹配但無結果")
        print()

def test_enhanced_feature_menu():
    """測試增強的功能選單"""
    print("🎯 測試增強的功能選單")
    print("=" * 50)
    
    try:
        menu = create_simple_flex_message('feature_menu')
        print(f"✅ 功能選單創建成功")
        print(f"📋 標題: {menu['header']['contents'][0]['text']}")
        
        button_count = len(menu['footer']['contents'])
        print(f"🔘 總按鈕數量: {button_count}")
        
        print("\n📝 所有功能按鈕:")
        for i, button in enumerate(menu['footer']['contents'], 1):
            label = button['action']['label']
            data = button['action']['data']
            print(f"  {i:2d}. {label}")
            
            # 檢查是否為內建功能
            if 'inline_feature' in data:
                print(f"      🔧 內建功能")
            else:
                print(f"      🌐 外部功能")
        
    except Exception as e:
        print(f"❌ 功能選單創建失敗: {e}")

def main():
    """主測試函數"""
    print("🚀 開始測試 Line Bot 內建功能")
    print("=" * 60)
    
    try:
        test_split_bill_calculator()
        test_inline_features()
        test_keyword_matching()
        test_enhanced_feature_menu()
        
        print("\n✅ 所有測試完成！")
        print("\n📱 新增的內建功能:")
        print("1. 💰 快速分帳計算 - 直接在聊天中計算分帳")
        print("2. 🌤️ 天氣查詢 - 查詢旅遊地點天氣")
        print("3. 💱 匯率換算 - 即時匯率換算")
        print("4. 💡 旅遊小貼士 - 實用旅遊建議")
        print("5. 📍 附近景點 - 地點推薦功能")
        
        print("\n🎯 使用方式:")
        print("• 直接輸入: '分帳 1000 3人' → 立即計算結果")
        print("• 關鍵字查詢: '快速分帳' → 顯示計算器介面")
        print("• 功能選單: '功能介紹' → 選擇內建功能")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
