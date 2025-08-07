#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試路由是否正確設定
"""

from api.index import app

def test_routes():
    """測試所有路由"""
    print("🔍 檢查應用程式路由")
    print("=" * 50)
    
    # 獲取所有路由
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'rule': rule.rule
        })
    
    print(f"📋 找到 {len(routes)} 個路由:")
    for route in routes:
        methods = ', '.join([m for m in route['methods'] if m not in ['HEAD', 'OPTIONS']])
        print(f"   {route['rule']:30} [{methods:15}] → {route['endpoint']}")
    
    # 特別檢查關鍵路由
    key_routes = [
        '/auth/line/callback',
        '/api/verify-token',
        '/callback',
        '/',
        '/debug'
    ]
    
    print(f"\n🎯 檢查關鍵路由:")
    for key_route in key_routes:
        found = any(route['rule'] == key_route for route in routes)
        status = "✅ 存在" if found else "❌ 不存在"
        print(f"   {key_route:30} {status}")

def test_line_login_callback():
    """測試LINE Login回調函數"""
    print(f"\n🔐 測試LINE Login回調函數")
    print("=" * 50)
    
    try:
        from api.index import line_login_callback
        print("✅ line_login_callback 函數存在")
        
        # 檢查函數是否可調用
        if callable(line_login_callback):
            print("✅ 函數可調用")
        else:
            print("❌ 函數不可調用")
            
    except ImportError as e:
        print(f"❌ 無法導入 line_login_callback: {e}")
    except Exception as e:
        print(f"❌ 其他錯誤: {e}")

def test_verify_token_endpoint():
    """測試Token驗證端點"""
    print(f"\n🔑 測試Token驗證端點")
    print("=" * 50)
    
    try:
        from api.index import verify_unified_token
        print("✅ verify_unified_token 函數存在")
        
        if callable(verify_unified_token):
            print("✅ 函數可調用")
        else:
            print("❌ 函數不可調用")
            
    except ImportError as e:
        print(f"❌ 無法導入 verify_unified_token: {e}")
    except Exception as e:
        print(f"❌ 其他錯誤: {e}")

def test_app_configuration():
    """測試應用程式配置"""
    print(f"\n⚙️ 測試應用程式配置")
    print("=" * 50)
    
    print(f"Flask應用名稱: {app.name}")
    print(f"Debug模式: {app.debug}")
    print(f"測試模式: {app.testing}")
    
    # 檢查重要的配置
    if hasattr(app, 'url_map'):
        print("✅ URL映射正常")
    else:
        print("❌ URL映射異常")

def simulate_callback_request():
    """模擬回調請求"""
    print(f"\n🧪 模擬回調請求")
    print("=" * 50)
    
    try:
        with app.test_client() as client:
            # 測試GET請求到回調端點
            response = client.get('/auth/line/callback')
            print(f"GET /auth/line/callback:")
            print(f"   狀態碼: {response.status_code}")
            print(f"   回應: {response.get_data(as_text=True)[:100]}...")
            
            # 測試帶參數的請求
            response = client.get('/auth/line/callback?code=test&state=test')
            print(f"\nGET /auth/line/callback?code=test&state=test:")
            print(f"   狀態碼: {response.status_code}")
            print(f"   回應: {response.get_data(as_text=True)[:100]}...")
            
    except Exception as e:
        print(f"❌ 模擬請求失敗: {e}")

def main():
    """主函數"""
    print("🚀 LINE Bot 路由診斷工具")
    print("=" * 60)
    
    # 測試路由
    test_routes()
    
    # 測試LINE Login回調
    test_line_login_callback()
    
    # 測試Token驗證端點
    test_verify_token_endpoint()
    
    # 測試應用程式配置
    test_app_configuration()
    
    # 模擬回調請求
    simulate_callback_request()
    
    print("\n" + "=" * 60)
    print("🎯 診斷完成")
    print("\n💡 如果 /auth/line/callback 路由不存在，請檢查：")
    print("1. 代碼是否正確推送到 GitHub")
    print("2. Vercel 是否成功部署最新版本")
    print("3. 部署日誌中是否有錯誤")

if __name__ == "__main__":
    main()
