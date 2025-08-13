import mysql.connector
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def get_database_connection():
    """建立資料庫連接"""
    try:
        connection = mysql.connector.connect(
            host=os.environ.get('MYSQL_HOST', 'trip.mysql.database.azure.com'),
            user=os.environ.get('MYSQL_USER', 'b1129005'),
            password=os.environ.get('MYSQL_PASSWORD', 'Anderson3663'),
            database=os.environ.get('MYSQL_DB', 'tourhub'),
            port=int(os.environ.get('MYSQL_PORT', 3306)),
            ssl_disabled=False,
            autocommit=True
        )
        logger.info("資料庫連接成功")
        return connection
    except Exception as e:
        logger.error(f"資料庫連接失敗: {e}")
        return None

## 已移除未使用的 get_leaderboard_data 函式

## 已移除未使用的 get_trip_details 函式

def get_trips_by_location(location):
    """根據地區獲取行程列表"""
    try:
        connection = get_database_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        query = """
        SELECT 
            t.trip_id,
            t.title,
            t.description,
            t.area,
            DATEDIFF(t.end_date, t.start_date) + 1 as duration_days,
            COALESCE(ts.favorite_count, 0) as favorite_count,
            COALESCE(ts.popularity_score, 0) as popularity_score
        FROM line_trips t
        LEFT JOIN trip_stats ts ON t.trip_id = ts.trip_id
        WHERE t.area LIKE %s
        ORDER BY ts.popularity_score DESC, ts.favorite_count DESC
        LIMIT 5
        """
        
        cursor.execute(query, (f"%{location}%",))
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        
        trips = []
        for trip in results:
            trips.append({
                "id": trip['trip_id'],
                "title": trip['title'],
                "duration": f"{trip['duration_days']}天{trip['duration_days']-1}夜" if trip['duration_days'] > 1 else "1天",
                "description": trip['description'] or "精彩行程",
                "highlights": trip['description'] or f"{trip['area']}精彩景點",
                "favorite_count": trip['favorite_count']
            })
        
        logger.info(f"成功獲取 {location} 地區 {len(trips)} 筆行程資料")
        return trips

    except Exception as e:
        logger.error(f"獲取地區行程失敗: {e}")
        return []

## 已移除未使用的 get_leaderboard_rank_details 函式

## 已移除未使用的 get_simple_itinerary_by_rank 函式
