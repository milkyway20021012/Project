import mysql.connector
import pymysql
import json
from typing import Dict, List, Any

# 資料庫連接配置
DB_CONFIG = {
    'host': 'trip.mysql.database.azure.com',
    'user': 'b1129005',
    'password': 'Anderson3663',
    'database': 'tourhub',
    'port': 3306,
    'ssl_disabled': False
}

def connect_to_database():
    """連接到MySQL資料庫"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        print("✅ 成功連接到資料庫")
        return connection
    except Exception as e:
        print(f"❌ 連接資料庫失敗: {e}")
        return None

def get_all_tables(connection):
    """獲取所有資料表"""
    try:
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        cursor.close()
        return tables
    except Exception as e:
        print(f"❌ 獲取資料表失敗: {e}")
        return []

def get_table_structure(connection, table_name):
    """獲取資料表結構"""
    try:
        cursor = connection.cursor()
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        cursor.close()
        return columns
    except Exception as e:
        print(f"❌ 獲取表結構失敗: {e}")
        return []

def get_sample_data(connection, table_name, limit=5):
    """獲取範例資料"""
    try:
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        
        # 轉換為字典格式
        data = []
        for row in rows:
            data.append(dict(zip(columns, row)))
        return data
    except Exception as e:
        print(f"❌ 獲取範例資料失敗: {e}")
        return []

def analyze_database():
    """分析整個資料庫"""
    print("🔍 開始分析資料庫...")
    
    connection = connect_to_database()
    if not connection:
        return
    
    # 獲取所有資料表
    tables = get_all_tables(connection)
    print(f"\n📋 找到 {len(tables)} 個資料表:")
    for table in tables:
        print(f"  - {table}")
    
    # 分析每個資料表
    database_info = {}
    for table in tables:
        print(f"\n🔍 分析資料表: {table}")
        
        # 獲取表結構
        structure = get_table_structure(connection, table)
        print(f"  欄位數量: {len(structure)}")
        for col in structure:
            print(f"    - {col[0]} ({col[1]}) {col[2]} {col[3]} {col[4]} {col[5]}")
        
        # 獲取範例資料
        sample_data = get_sample_data(connection, table, 3)
        print(f"  範例資料數量: {len(sample_data)}")
        
        database_info[table] = {
            'structure': structure,
            'sample_data': sample_data
        }
    
    connection.close()
    
    # 保存分析結果
    with open('database_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(database_info, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n✅ 分析完成，結果已保存到 database_analysis.json")
    return database_info

if __name__ == "__main__":
    analyze_database() 