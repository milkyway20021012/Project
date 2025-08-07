#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自動設定統一綁定系統資料庫
"""

import os
import sys
from api.database_utils import get_database_connection

def setup_unified_database():
    """設定統一綁定系統資料庫表格"""
    print("🗄️ 開始設定統一綁定系統資料庫...")
    print("=" * 60)
    
    # 獲取資料庫連接
    connection = get_database_connection()
    if not connection:
        print("❌ 無法連接到資料庫")
        return False
    
    try:
        cursor = connection.cursor()
        
        # 讀取SQL腳本
        sql_file_path = "database/unified_user_system.sql"
        if not os.path.exists(sql_file_path):
            print(f"❌ 找不到SQL文件: {sql_file_path}")
            return False
        
        with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        # 分割SQL語句（以分號分隔）
        sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        print(f"📋 準備執行 {len(sql_statements)} 個SQL語句...")
        
        # 執行每個SQL語句
        for i, statement in enumerate(sql_statements, 1):
            try:
                print(f"   {i:2d}. 執行中...", end="")
                cursor.execute(statement)
                print(" ✅ 成功")
                
                # 如果是CREATE TABLE語句，顯示表名
                if statement.upper().startswith('CREATE TABLE'):
                    table_name = extract_table_name(statement)
                    if table_name:
                        print(f"       創建表格: {table_name}")
                
                # 如果是INSERT語句，顯示插入資訊
                elif statement.upper().startswith('INSERT INTO'):
                    table_name = extract_insert_table_name(statement)
                    if table_name:
                        print(f"       插入資料到: {table_name}")
                        
            except Exception as e:
                print(f" ❌ 失敗")
                print(f"       錯誤: {e}")
                print(f"       語句: {statement[:100]}...")
                continue
        
        # 提交變更
        connection.commit()
        print("\n✅ 資料庫設定完成！")
        
        # 驗證表格是否創建成功
        print("\n🔍 驗證表格創建狀況...")
        verify_tables(cursor)
        
        return True
        
    except Exception as e:
        print(f"❌ 設定過程中發生錯誤: {e}")
        return False
        
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def extract_table_name(create_statement):
    """從CREATE TABLE語句中提取表名"""
    try:
        # 尋找 "CREATE TABLE" 後的表名
        parts = create_statement.upper().split()
        if 'TABLE' in parts:
            table_index = parts.index('TABLE')
            if table_index + 1 < len(parts):
                table_name = parts[table_index + 1]
                # 移除 "IF NOT EXISTS" 等關鍵字
                if table_name in ['IF', 'NOT', 'EXISTS']:
                    if table_index + 4 < len(parts):
                        table_name = parts[table_index + 4]
                # 移除括號和其他符號
                table_name = table_name.replace('(', '').replace('`', '')
                return table_name
    except:
        pass
    return None

def extract_insert_table_name(insert_statement):
    """從INSERT語句中提取表名"""
    try:
        parts = insert_statement.upper().split()
        if 'INTO' in parts:
            into_index = parts.index('INTO')
            if into_index + 1 < len(parts):
                table_name = parts[into_index + 1]
                table_name = table_name.replace('(', '').replace('`', '')
                return table_name
    except:
        pass
    return None

def verify_tables(cursor):
    """驗證表格是否創建成功"""
    expected_tables = [
        'unified_users',
        'website_modules', 
        'user_website_bindings',
        'user_operation_logs',
        'system_configs'
    ]
    
    for table in expected_tables:
        try:
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            result = cursor.fetchone()
            if result:
                print(f"   ✅ {table}")
                
                # 檢查表格記錄數
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"       記錄數: {count}")
            else:
                print(f"   ❌ {table} - 表格不存在")
        except Exception as e:
            print(f"   ⚠️  {table} - 檢查失敗: {e}")

def check_website_modules():
    """檢查網站模組是否正確插入"""
    print("\n🌐 檢查網站模組配置...")
    
    connection = get_database_connection()
    if not connection:
        print("❌ 無法連接到資料庫")
        return
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT module_name, module_display_name, base_url FROM website_modules")
        modules = cursor.fetchall()
        
        if modules:
            print(f"   找到 {len(modules)} 個網站模組:")
            for module in modules:
                print(f"   📱 {module['module_display_name']}")
                print(f"      模組名: {module['module_name']}")
                print(f"      URL: {module['base_url']}")
                print()
        else:
            print("   ⚠️  沒有找到網站模組資料")
            
    except Exception as e:
        print(f"   ❌ 檢查失敗: {e}")
    finally:
        cursor.close()
        connection.close()

def main():
    """主函數"""
    print("🚀 TourHub統一綁定系統資料庫設定工具")
    print("=" * 60)
    
    # 檢查是否有資料庫連接
    print("🔍 檢查資料庫連接...")
    connection = get_database_connection()
    if not connection:
        print("❌ 無法連接到資料庫，請檢查連接設定")
        return
    else:
        print("✅ 資料庫連接正常")
        connection.close()
    
    # 設定資料庫
    success = setup_unified_database()
    
    if success:
        # 檢查網站模組
        check_website_modules()
        
        print("\n🎉 設定完成！")
        print("現在你可以：")
        print("1. 設定LINE Login環境變數")
        print("2. 部署到Vercel")
        print("3. 測試統一綁定功能")
    else:
        print("\n❌ 設定失敗，請檢查錯誤訊息")

if __name__ == "__main__":
    main()
