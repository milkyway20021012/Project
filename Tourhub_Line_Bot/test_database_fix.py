#!/usr/bin/env python3
"""
測試數據庫修復
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_functions():
    """測試數據庫函數"""
    print("=== 測試數據庫函數 ===")
    
    try:
        # 測試連接池初始化
        from api.database_utils import initialize_connection_pool
        if initialize_connection_pool():
            print("✅ 數據庫連接池初始化成功")
        else:
            print("❌ 數據庫連接池初始化失敗")
            return
        
        # 測試排行榜查詢
        from api.database_utils import get_leaderboard_from_database
        leaderboard = get_leaderboard_from_database()
        if leaderboard:
            print(f"✅ 排行榜查詢成功，獲取 {len(leaderboard)} 條數據")
        else:
            print("❌ 排行榜查詢失敗")
        
        # 測試排行榜詳細查詢
        from api.database_utils import get_leaderboard_rank_details
        for rank in range(1, 4):  # 測試前3名
            try:
                rank_data = get_leaderboard_rank_details(rank)
                if rank_data:
                    print(f"✅ 第{rank}名詳細查詢成功: {rank_data.get('title', 'N/A')}")
                else:
                    print(f"⚠️  第{rank}名詳細查詢無數據")
            except Exception as e:
                print(f"❌ 第{rank}名詳細查詢失敗: {e}")
        
        # 測試地區行程查詢
        from api.database_utils import get_trips_by_location
        test_locations = ["東京", "大阪"]
        for location in test_locations:
            try:
                trips = get_trips_by_location(location, 3)
                print(f"✅ {location} 行程查詢成功，獲取 {len(trips)} 條數據")
            except Exception as e:
                print(f"❌ {location} 行程查詢失敗: {e}")
                
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    test_database_functions()
