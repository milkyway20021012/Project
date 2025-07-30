import os
from api.database_utils import get_database_connection

def test_environment_variables():
    """測試環境變數設定"""
    print("🔍 檢查環境變數設定...")
    
    # 檢查資料庫環境變數
    db_vars = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_DB', 'MYSQL_PORT']
    for var in db_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: 未設定 (使用預設值)")
    
    # 檢查LINE Bot環境變數
    line_vars = ['LINE_CHANNEL_ACCESS_TOKEN', 'LINE_CHANNEL_SECRET']
    for var in line_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * len(value)} (已設定)")
        else:
            print(f"❌ {var}: 未設定")
    
    # 測試資料庫連接
    print("\n🔗 測試資料庫連接...")
    try:
        connection = get_database_connection()
        if connection:
            print("✅ 資料庫連接成功")
            connection.close()
        else:
            print("❌ 資料庫連接失敗")
    except Exception as e:
        print(f"❌ 資料庫連接錯誤: {e}")

if __name__ == "__main__":
    test_environment_variables() 