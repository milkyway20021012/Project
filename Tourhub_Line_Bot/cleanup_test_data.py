#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
清理所有測試資料
"""

from api.database_utils import get_database_connection

def cleanup_database_test_data():
    """清理資料庫中的測試資料"""
    print("🗄️ 清理資料庫測試資料")
    print("=" * 50)
    
    connection = get_database_connection()
    if not connection:
        print("❌ 無法連接到資料庫")
        return False
    
    try:
        cursor = connection.cursor()
        
        # 清理統一用戶系統的測試資料
        cleanup_queries = [
            # 清理用戶操作日誌中的測試資料
            "DELETE FROM user_operation_logs WHERE unified_user_id IN (SELECT id FROM unified_users WHERE line_user_id LIKE 'test_%')",
            
            # 清理用戶網站綁定中的測試資料
            "DELETE FROM user_website_bindings WHERE unified_user_id IN (SELECT id FROM unified_users WHERE line_user_id LIKE 'test_%')",
            
            # 清理測試用戶
            "DELETE FROM unified_users WHERE line_user_id LIKE 'test_%'",
            "DELETE FROM unified_users WHERE display_name LIKE '%測試%'",
            "DELETE FROM unified_users WHERE display_name LIKE '%test%'",
            
            # 清理可能的調試用戶
            "DELETE FROM unified_users WHERE line_user_id = 'debug_user'",
            "DELETE FROM unified_users WHERE line_user_id = 'mock_user'",
        ]
        
        total_deleted = 0
        
        for i, query in enumerate(cleanup_queries, 1):
            try:
                print(f"   {i}. 執行清理查詢...", end="")
                cursor.execute(query)
                deleted_count = cursor.rowcount
                total_deleted += deleted_count
                print(f" ✅ 刪除 {deleted_count} 筆記錄")
            except Exception as e:
                print(f" ❌ 失敗: {e}")
        
        # 提交變更
        connection.commit()
        
        print(f"\n✅ 資料庫清理完成，共刪除 {total_deleted} 筆測試記錄")
        
        # 顯示清理後的統計
        print("\n📊 清理後統計:")
        stats_queries = [
            ("統一用戶", "SELECT COUNT(*) FROM unified_users"),
            ("網站綁定", "SELECT COUNT(*) FROM user_website_bindings"), 
            ("操作日誌", "SELECT COUNT(*) FROM user_operation_logs"),
            ("網站模組", "SELECT COUNT(*) FROM website_modules"),
            ("系統配置", "SELECT COUNT(*) FROM system_configs")
        ]
        
        for name, query in stats_queries:
            try:
                cursor.execute(query)
                count = cursor.fetchone()[0]
                print(f"   {name}: {count} 筆記錄")
            except Exception as e:
                print(f"   {name}: 查詢失敗 - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 清理過程中發生錯誤: {e}")
        return False
        
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def cleanup_test_files():
    """清理測試文件"""
    print("\n📁 清理測試文件")
    print("=" * 50)
    
    import os
    
    # 要刪除的測試文件列表
    test_files = [
        "debug_keyword_matching.py",
        "test_bot_response.py", 
        "test_routes.py",
        "test_line_login_url.py",
        "test_website_operations.py",
        "verify_deployment_ready.py",
        "setup_unified_database.py",
        "cleanup_test_data.py"  # 包括這個文件本身
    ]
    
    deleted_files = []
    
    for file_name in test_files:
        if os.path.exists(file_name):
            try:
                os.remove(file_name)
                deleted_files.append(file_name)
                print(f"   ✅ 刪除: {file_name}")
            except Exception as e:
                print(f"   ❌ 無法刪除 {file_name}: {e}")
        else:
            print(f"   ⚪ 不存在: {file_name}")
    
    print(f"\n✅ 文件清理完成，共刪除 {len(deleted_files)} 個測試文件")
    
    return deleted_files

def cleanup_log_files():
    """清理日誌文件"""
    print("\n📋 清理日誌文件")
    print("=" * 50)
    
    import os
    import glob
    
    # 查找可能的日誌文件
    log_patterns = [
        "*.log",
        "logs/*.log",
        "debug*.txt",
        "test*.txt"
    ]
    
    deleted_logs = []
    
    for pattern in log_patterns:
        log_files = glob.glob(pattern)
        for log_file in log_files:
            try:
                os.remove(log_file)
                deleted_logs.append(log_file)
                print(f"   ✅ 刪除日誌: {log_file}")
            except Exception as e:
                print(f"   ❌ 無法刪除 {log_file}: {e}")
    
    if not deleted_logs:
        print("   ⚪ 沒有找到日誌文件")
    else:
        print(f"\n✅ 日誌清理完成，共刪除 {len(deleted_logs)} 個日誌文件")
    
    return deleted_logs

def main():
    """主函數"""
    print("🧹 TourHub 測試資料清理工具")
    print("=" * 60)
    
    # 清理資料庫測試資料
    db_success = cleanup_database_test_data()
    
    # 清理測試文件
    deleted_files = cleanup_test_files()
    
    # 清理日誌文件
    deleted_logs = cleanup_log_files()
    
    print("\n" + "=" * 60)
    print("🎯 清理完成總結")
    print("=" * 60)
    
    if db_success:
        print("✅ 資料庫測試資料清理成功")
    else:
        print("❌ 資料庫測試資料清理失敗")
    
    print(f"✅ 刪除 {len(deleted_files)} 個測試文件")
    print(f"✅ 刪除 {len(deleted_logs)} 個日誌文件")
    
    print("\n💡 建議接下來：")
    print("1. 檢查資料庫是否還有其他測試資料")
    print("2. 確認統一綁定系統正常運作")
    print("3. 進行實際用戶測試")
    
    print("\n⚠️  注意：這個清理腳本執行後會自動刪除自己")

if __name__ == "__main__":
    main()
