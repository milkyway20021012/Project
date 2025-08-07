#!/usr/bin/env python3
"""
測試資料庫中的實際資料格式
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_details():
    """測試資料庫中的詳細行程資料格式"""
    logger.info("=== 測試資料庫詳細行程格式 ===")
    
    try:
        from api.database_utils import get_database_connection, MYSQL_AVAILABLE
        
        if not MYSQL_AVAILABLE:
            logger.warning("⚠️  MySQL 不可用")
            return
        
        connection = get_database_connection()
        if not connection:
            logger.error("❌ 無法連接資料庫")
            return
        
        cursor = connection.cursor(dictionary=True)
        
        # 先獲取排行榜第一名的 trip_id
        leaderboard_query = """
        SELECT 
            t.trip_id,
            t.title,
            t.area
        FROM line_trips t
        LEFT JOIN trip_stats ts ON t.trip_id = ts.trip_id
        WHERE t.trip_id IS NOT NULL
        ORDER BY ts.popularity_score DESC, ts.favorite_count DESC, ts.share_count DESC
        LIMIT 1
        """
        
        cursor.execute(leaderboard_query)
        trip_data = cursor.fetchone()
        
        if not trip_data:
            logger.error("❌ 找不到排行榜資料")
            return
        
        trip_id = trip_data.get('trip_id')
        logger.info(f"第一名行程: {trip_data.get('title')} (ID: {trip_id})")
        
        # 查詢詳細行程
        detail_query = """
        SELECT 
            location,
            date,
            start_time,
            end_time,
            description
        FROM line_trip_details
        WHERE trip_id = %s
        ORDER BY date, start_time
        LIMIT 5
        """
        
        cursor.execute(detail_query, (trip_id,))
        details = cursor.fetchall()
        
        logger.info(f"找到 {len(details)} 筆詳細行程資料:")
        
        for i, detail in enumerate(details, 1):
            logger.info(f"  項目 {i}:")
            logger.info(f"    - location: {detail.get('location')} (type: {type(detail.get('location'))})")
            logger.info(f"    - date: {detail.get('date')} (type: {type(detail.get('date'))})")
            logger.info(f"    - start_time: {detail.get('start_time')} (type: {type(detail.get('start_time'))})")
            logger.info(f"    - end_time: {detail.get('end_time')} (type: {type(detail.get('end_time'))})")
            logger.info(f"    - description: {detail.get('description')}")
        
        cursor.close()
        connection.close()
        
        # 測試格式化函數
        logger.info("\n=== 測試格式化結果 ===")
        from api.database_utils import get_leaderboard_rank_details
        
        rank_data = get_leaderboard_rank_details(1)
        if rank_data:
            logger.info(f"格式化後的行程列表:")
            for i, item in enumerate(rank_data.get('itinerary_list', []), 1):
                logger.info(f"  項目 {i}: {repr(item)}")
                logger.info(f"    分割後: {item.split('\\n')}")
        
    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database_details()
