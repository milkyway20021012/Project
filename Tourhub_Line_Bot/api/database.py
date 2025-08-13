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

# 收藏功能：資料庫持久化
def ensure_user_favorites_table_exists(connection):
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_favorites (
                id INT AUTO_INCREMENT PRIMARY KEY,
                line_user_id VARCHAR(128) NOT NULL,
                rank INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uniq_user_rank (line_user_id, rank)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        cursor.close()
        return True
    except Exception as e:
        logger.error(f"建立 user_favorites 表失敗: {e}")
        return False

def add_user_favorite_db(line_user_id: str, rank: int) -> bool:
    """新增收藏，若已存在則回傳 False"""
    try:
        connection = get_database_connection()
        if not connection:
            return False
        if not ensure_user_favorites_table_exists(connection):
            return False

        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO user_favorites (line_user_id, rank)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE rank = VALUES(rank)
                """,
                (line_user_id, int(rank))
            )
            inserted = cursor.rowcount == 1  # 1 表示新插入；2 可能是更新，但我們視為已存在
        finally:
            cursor.close()
            connection.close()

        return inserted
    except Exception as e:
        logger.error(f"新增收藏失敗: {e}")
        return False

def get_user_favorites_db(line_user_id: str):
    """取得使用者收藏的名次列表（升冪排序）"""
    try:
        connection = get_database_connection()
        if not connection:
            return []
        if not ensure_user_favorites_table_exists(connection):
            return []

        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT rank FROM user_favorites
                WHERE line_user_id = %s
                ORDER BY rank ASC
                """,
                (line_user_id,)
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()
            connection.close()

        return [int(r[0]) for r in rows]
    except Exception as e:
        logger.error(f"取得收藏清單失敗: {e}")
        return []
