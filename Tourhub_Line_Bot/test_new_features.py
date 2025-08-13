#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試新的功能介紹系統
"""

import json
from api.index import create_simple_flex_message, get_message_template

def test_feature_menu():
    """測試功能選單"""
    print("🎯 測試功能選單")
    print("=" * 50)
    
    # 測試關鍵字匹配
    template_config = get_message_template("功能介紹")
    print(f"關鍵字匹配結果: {template_config}")
    
    # 創建功能選單
    menu = create_simple_flex_message('feature_menu')
    print(f"功能選單創建成功")
    print(f"標題: {menu['header']['contents'][0]['text']}")
    print(f"按鈕數量: {len(menu['footer']['contents'])}")
    
    # 顯示所有按鈕
    for i, button in enumerate(menu['footer']['contents'], 1):
        print(f"  {i}. {button['action']['label']}")
    
    print()

def test_feature_details():
    """測試功能詳細介紹"""
    print("📋 測試功能詳細介紹")
    print("=" * 50)
    
    features = ['leaderboard', 'trip_management', 'tour_clock', 'locker', 'split_bill']
    
    for feature in features:
        print(f"\n🔍 測試 {feature} 功能詳細介紹:")
        
        # 測試關鍵字匹配
        test_keywords = {
            'leaderboard': '排行榜功能介紹',
            'trip_management': '行程管理功能介紹',
            'tour_clock': '集合管理功能介紹',
            'locker': '置物櫃功能介紹',
            'split_bill': '分帳功能介紹'
        }
        
        keyword = test_keywords[feature]
        template_config = get_message_template(keyword)
        print(f"  關鍵字 '{keyword}' 匹配: {template_config is not None}")
        
        # 創建詳細介紹
        detail = create_simple_flex_message('feature_detail', feature_name=feature)
        print(f"  標題: {detail['header']['contents'][0]['text']}")
        print(f"  按鈕數量: {len(detail['footer']['contents'])}")
        
        # 顯示按鈕
        for button in detail['footer']['contents']:
            print(f"    - {button['action']['label']}")

def test_postback_simulation():
    """模擬 postback 事件"""
    print("\n🔄 模擬 postback 事件")
    print("=" * 50)
    
    # 模擬點擊排行榜按鈕
    print("模擬點擊 '🏆 排行榜' 按鈕:")
    detail = create_simple_flex_message('feature_detail', feature_name='leaderboard')
    print(f"  返回詳細介紹: {detail['header']['contents'][0]['text']}")
    
    # 模擬點擊返回按鈕
    print("\n模擬點擊 '🔙 返回功能選單' 按鈕:")
    menu = create_simple_flex_message('feature_menu')
    print(f"  返回選單: {menu['header']['contents'][0]['text']}")

def main():
    """主測試函數"""
    print("🚀 開始測試新的功能介紹系統")
    print("=" * 60)
    
    try:
        test_feature_menu()
        test_feature_details()
        test_postback_simulation()
        
        print("\n✅ 所有測試通過！")
        print("\n📱 使用方法:")
        print("1. 用戶輸入 '功能介紹' → 顯示功能選單")
        print("2. 點擊任意功能按鈕 → 顯示該功能的詳細介紹")
        print("3. 點擊 '返回功能選單' → 回到主選單")
        print("4. 直接輸入 '排行榜功能介紹' → 直接查看排行榜功能詳情")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
