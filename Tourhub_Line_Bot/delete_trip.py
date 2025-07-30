import mysql.connector
from api.database_utils import get_database_connection

def delete_trip_safely(trip_id):
    """安全地刪除行程及其相關資料"""
    try:
        connection = get_database_connection()
        if not connection:
            print("❌ 無法連接到資料庫")
            return False
        
        cursor = connection.cursor(dictionary=True)
        
        # 1. 先查看要刪除的行程資料
        print(f"🔍 查看行程 ID {trip_id} 的資料...")
        cursor.execute("SELECT * FROM line_trips WHERE trip_id = %s", (trip_id,))
        trip_data = cursor.fetchone()
        
        if not trip_data:
            print(f"❌ 找不到行程 ID {trip_id}")
            return False
        
        print("📋 要刪除的行程資料:")
        print(f"  標題: {trip_data.get('title')}")
        print(f"  地區: {trip_data.get('area')}")
        print(f"  開始日期: {trip_data.get('start_date')}")
        print(f"  結束日期: {trip_data.get('end_date')}")
        
        # 2. 查看相關資料數量
        print("\n📊 相關資料統計:")
        
        # 統計行程詳細資料
        cursor.execute("SELECT COUNT(*) as count FROM line_trip_details WHERE trip_id = %s", (trip_id,))
        detail_count = cursor.fetchone()['count']
        print(f"  行程詳細資料: {detail_count} 筆")
        
        # 統計收藏資料
        cursor.execute("SELECT COUNT(*) as count FROM user_favorites WHERE trip_id = %s", (trip_id,))
        favorite_count = cursor.fetchone()['count']
        print(f"  收藏記錄: {favorite_count} 筆")
        
        # 統計分享資料
        cursor.execute("SELECT COUNT(*) as count FROM user_shares WHERE trip_id = %s", (trip_id,))
        share_count = cursor.fetchone()['count']
        print(f"  分享記錄: {share_count} 筆")
        
        # 統計參與者資料（如果表存在）
        try:
            cursor.execute("SELECT COUNT(*) as count FROM trip_participants WHERE trip_id = %s", (trip_id,))
            participant_count = cursor.fetchone()['count']
            print(f"  參與者記錄: {participant_count} 筆")
        except:
            participant_count = 0
            print(f"  參與者記錄: 0 筆 (表不存在)")
        
        # 統計統計資料
        cursor.execute("SELECT COUNT(*) as count FROM trip_stats WHERE trip_id = %s", (trip_id,))
        stats_count = cursor.fetchone()['count']
        print(f"  統計資料: {stats_count} 筆")
        
        # 3. 確認刪除
        confirm = input(f"\n⚠️  確定要刪除行程 ID {trip_id} 及其所有相關資料嗎？(y/N): ")
        if confirm.lower() != 'y':
            print("❌ 取消刪除操作")
            return False
        
        # 4. 開始刪除相關資料
        print("\n🗑️  開始刪除相關資料...")
        
        # 刪除行程詳細資料
        if detail_count > 0:
            cursor.execute("DELETE FROM line_trip_details WHERE trip_id = %s", (trip_id,))
            print(f"✅ 已刪除 {detail_count} 筆行程詳細資料")
        
        # 刪除收藏記錄
        if favorite_count > 0:
            cursor.execute("DELETE FROM user_favorites WHERE trip_id = %s", (trip_id,))
            print(f"✅ 已刪除 {favorite_count} 筆收藏記錄")
        
        # 刪除分享記錄
        if share_count > 0:
            cursor.execute("DELETE FROM user_shares WHERE trip_id = %s", (trip_id,))
            print(f"✅ 已刪除 {share_count} 筆分享記錄")
        
        # 刪除參與者記錄（如果表存在）
        if participant_count > 0:
            try:
                cursor.execute("DELETE FROM trip_participants WHERE trip_id = %s", (trip_id,))
                print(f"✅ 已刪除 {participant_count} 筆參與者記錄")
            except:
                print(f"⚠️  跳過參與者記錄刪除（表不存在）")
        
        # 刪除統計資料
        if stats_count > 0:
            cursor.execute("DELETE FROM trip_stats WHERE trip_id = %s", (trip_id,))
            print(f"✅ 已刪除 {stats_count} 筆統計資料")
        
        # 最後刪除行程主資料
        cursor.execute("DELETE FROM line_trips WHERE trip_id = %s", (trip_id,))
        print(f"✅ 已刪除行程主資料")
        
        # 提交變更
        connection.commit()
        print(f"\n🎉 成功刪除行程 ID {trip_id} 及其所有相關資料！")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 刪除過程中發生錯誤: {e}")
        if connection:
            connection.rollback()
            connection.close()
        return False

if __name__ == "__main__":
    trip_id = input("請輸入要刪除的行程 ID: ")
    try:
        trip_id = int(trip_id)
        delete_trip_safely(trip_id)
    except ValueError:
        print("❌ 請輸入有效的行程 ID（數字）") 