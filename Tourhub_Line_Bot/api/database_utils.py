import logging
from typing import Dict, List, Any
from datetime import datetime

# 嘗試導入 MySQL 連接器，如果失敗則記錄錯誤
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("MySQL connector imported successfully")
except ImportError as e:
    MYSQL_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import MySQL connector: {e}")
    logger.warning("Database functionality will be disabled")

import os

# 資料庫連接配置
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'trip.mysql.database.azure.com'),
    'user': os.getenv('MYSQL_USER', 'b1129005'),
    'password': os.getenv('MYSQL_PASSWORD', 'Anderson3663'),
    'database': os.getenv('MYSQL_DB', 'tourhub'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'ssl_disabled': False
}

def get_database_connection():
    """獲取資料庫連接"""
    if not MYSQL_AVAILABLE:
        logger.warning("MySQL connector not available, cannot connect to database")
        return None

    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        logger.error(f"資料庫連接失敗: {e}")
        return None

def get_leaderboard_from_database():
    """從資料庫獲取排行榜資料"""
    try:
        connection = get_database_connection()
        if not connection:
            return {}
        
        cursor = connection.cursor(dictionary=True)
        
        # 查詢排行榜資料 - 根據收藏數、分享數、查看數排序
        query = """
        SELECT 
            t.trip_id,
            t.title,
            t.description,
            t.area,
            t.start_date,
            t.end_date,
            ts.favorite_count,
            ts.share_count,
            ts.view_count,
            ts.popularity_score,
            DATEDIFF(t.end_date, t.start_date) + 1 as duration_days
        FROM line_trips t
        LEFT JOIN trip_stats ts ON t.trip_id = ts.trip_id
        WHERE t.trip_id IS NOT NULL
        ORDER BY ts.popularity_score DESC, ts.favorite_count DESC, ts.share_count DESC
        LIMIT 5
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        
        # 轉換為排行榜格式
        leaderboard_data = {}
        for index, row in enumerate(results, 1):
            # 計算行程天數
            duration_days = row.get('duration_days', 1)
            duration_text = f"{duration_days}天"
            
            # 計算參與人數（這裡用收藏數作為參考）
            favorite_count = row.get('favorite_count', 0) or 0
            participants = favorite_count + 1
            
            # 構建行程特色描述
            area = row.get('area', '未知地區')
            description = row.get('description', '精彩行程')
            
            # 構建詳細行程（這裡可以進一步查詢trip_detail表）
            itinerary = f"Day 1: {area}精彩行程\nDay 2: 更多精彩景點\nDay 3: 完美收官"
            
            # 根據排名設定顏色
            colors = ["#FFD700", "#C0C0C0", "#CD7F32", "#4ECDC4", "#FF6B9D"]
            color = colors[index - 1] if index <= len(colors) else "#9B59B6"
            
            leaderboard_data[str(index)] = {
                "title": f"{['🥇', '🥈', '🥉', '🏅', '🎖️'][index-1]} 排行榜第{index}名" if index <= 5 else f"🎖️ 排行榜第{index}名",
                "color": color,
                "destination": area,
                "duration": duration_text,
                "participants": f"{participants}人",
                "feature": description,
                "itinerary": itinerary,
                "trip_id": row.get('trip_id'),
                "favorite_count": row.get('favorite_count', 0) or 0,
                "share_count": row.get('share_count', 0) or 0,
                "view_count": row.get('view_count', 0) or 0,
                "popularity_score": float(row.get('popularity_score', 0) or 0)
            }
        
        logger.info(f"成功從資料庫獲取 {len(leaderboard_data)} 條排行榜資料")
        return leaderboard_data
        
    except Exception as e:
        logger.error(f"從資料庫獲取排行榜資料失敗: {e}")
        return {}

def get_trips_by_location(location: str, limit: int = 5):
    """根據地區查詢行程列表"""
    try:
        connection = get_database_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        # 查詢指定地區的行程
        query = """
        SELECT 
            t.trip_id,
            t.title,
            t.description,
            t.area,
            t.start_date,
            t.end_date,
            DATEDIFF(t.end_date, t.start_date) + 1 as duration_days
        FROM line_trips t
        WHERE t.area LIKE %s
        ORDER BY t.trip_id DESC
        LIMIT %s
        """
        
        cursor.execute(query, (f"%{location}%", limit))
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        
        # 轉換為行程列表格式
        trips = []
        for row in results:
            trips.append({
                "id": str(row.get('trip_id')),
                "title": row.get('title', '未知行程'),
                "duration": f"{row.get('duration_days', 1)}天",
                "highlights": row.get('description', '精彩行程'),
                "area": row.get('area', '未知地區'),
                "trip_id": row.get('trip_id')
            })
        
        logger.info(f"找到 {len(trips)} 筆 {location} 相關行程")
        return trips
        
    except Exception as e:
        logger.error(f"查詢地區行程失敗: {e}")
        return []

def get_trip_details_by_id(trip_id: int):
    """根據行程ID獲取詳細行程資訊"""
    try:
        connection = get_database_connection()
        if not connection:
            return None
        
        cursor = connection.cursor(dictionary=True)
        
        # 查詢行程基本資訊
        trip_query = """
        SELECT 
            t.trip_id,
            t.title,
            t.description,
            t.area,
            t.start_date,
            t.end_date,
            DATEDIFF(t.end_date, t.start_date) + 1 as duration_days
        FROM line_trips t
        WHERE t.trip_id = %s
        """
        
        cursor.execute(trip_query, (trip_id,))
        trip_data = cursor.fetchone()
        
        if not trip_data:
            cursor.close()
            connection.close()
            return None
        
        # 查詢詳細行程安排
        detail_query = """
        SELECT 
            location,
            date,
            start_time,
            end_time
        FROM line_trip_details
        WHERE trip_id = %s
        ORDER BY date, start_time
        """
        
        cursor.execute(detail_query, (trip_id,))
        details = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        # 構建詳細行程
        itinerary_parts = []
        for i, detail in enumerate(details, 1):
            location = detail.get('location', '未知地點')
            date = detail.get('date')
            start_time = detail.get('start_time', '')
            end_time = detail.get('end_time', '')
            
            time_text = f"{start_time} - {end_time}" if start_time and end_time else ""
            itinerary_parts.append(f"Day {i}: {location} {time_text}")
        
        # 如果沒有詳細行程，使用預設
        if not itinerary_parts:
            itinerary_parts = [
                f"Day 1: {trip_data.get('area', '未知地區')}精彩行程",
                "Day 2: 更多精彩景點",
                "Day 3: 完美收官"
            ]
        
        return {
            "trip_id": trip_data.get('trip_id'),
            "title": trip_data.get('title', '未知行程'),
            "description": trip_data.get('description', '精彩行程'),
            "area": trip_data.get('area', '未知地區'),
            "duration": f"{trip_data.get('duration_days', 1)}天",
            "itinerary": "\n".join(itinerary_parts)
        }
        
    except Exception as e:
        logger.error(f"獲取行程詳細資訊失敗: {e}")
        return None

def get_leaderboard_rank_details(rank: int = 1):
    """獲取排行榜指定排名的詳細行程資訊"""
    if not MYSQL_AVAILABLE:
        logger.warning("MySQL connector not available, cannot get leaderboard rank details")
        return None

    try:
        connection = get_database_connection()
        if not connection:
            return None

        cursor = connection.cursor(dictionary=True)

        # 查詢排行榜資料，獲取指定排名的行程
        leaderboard_query = """
        SELECT
            t.trip_id,
            t.title,
            t.description,
            t.area,
            t.start_date,
            t.end_date,
            ts.favorite_count,
            ts.share_count,
            ts.view_count,
            ts.popularity_score,
            DATEDIFF(t.end_date, t.start_date) + 1 as duration_days
        FROM line_trips t
        LEFT JOIN trip_stats ts ON t.trip_id = ts.trip_id
        WHERE t.trip_id IS NOT NULL
        ORDER BY ts.popularity_score DESC, ts.favorite_count DESC, ts.share_count DESC
        LIMIT %s, 1
        """

        cursor.execute(leaderboard_query, (rank - 1,))  # rank-1 因為 LIMIT 是從 0 開始
        trip_data = cursor.fetchone()

        if not trip_data:
            cursor.close()
            connection.close()
            return None

        trip_id = trip_data.get('trip_id')

        # 查詢詳細行程安排
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
        """

        cursor.execute(detail_query, (trip_id,))
        details = cursor.fetchall()

        cursor.close()
        connection.close()

        # 構建詳細行程
        itinerary_parts = []
        current_day = 1
        last_date = None

        for detail in details:
            location = detail.get('location', '未知地點')
            date = detail.get('date')
            start_time = detail.get('start_time', '')
            end_time = detail.get('end_time', '')
            description = detail.get('description', '')

            # 檢查是否是新的一天
            if date != last_date:
                if last_date is not None:
                    current_day += 1
                last_date = date

            # 格式化時間
            time_text = ""
            if start_time and end_time:
                time_text = f" ({start_time} - {end_time})"
            elif start_time:
                time_text = f" ({start_time})"

            # 添加描述
            desc_text = f" - {description}" if description else ""

            itinerary_parts.append(f"Day {current_day}: {location}{time_text}{desc_text}")

        # 如果沒有詳細行程，使用預設
        if not itinerary_parts:
            duration_days = trip_data.get('duration_days', 1)
            area = trip_data.get('area', '未知地區')
            for day in range(1, duration_days + 1):
                if day == 1:
                    itinerary_parts.append(f"Day {day}: {area} 精彩行程開始")
                elif day == duration_days:
                    itinerary_parts.append(f"Day {day}: {area} 完美收官")
                else:
                    itinerary_parts.append(f"Day {day}: {area} 更多精彩景點")

        # 計算排名標題
        rank_titles = {1: "🥇 第一名", 2: "🥈 第二名", 3: "🥉 第三名", 4: "🏅 第四名", 5: "🎖️ 第五名"}
        rank_title = rank_titles.get(rank, f"🎖️ 第{rank}名")

        return {
            "trip_id": trip_data.get('trip_id'),
            "rank": rank,
            "rank_title": rank_title,
            "title": trip_data.get('title', '未知行程'),
            "description": trip_data.get('description', '精彩行程'),
            "area": trip_data.get('area', '未知地區'),
            "duration": f"{trip_data.get('duration_days', 1)}天",
            "start_date": str(trip_data.get('start_date', '')),
            "end_date": str(trip_data.get('end_date', '')),
            "favorite_count": trip_data.get('favorite_count', 0) or 0,
            "share_count": trip_data.get('share_count', 0) or 0,
            "view_count": trip_data.get('view_count', 0) or 0,
            "popularity_score": float(trip_data.get('popularity_score', 0) or 0),
            "itinerary": "\n".join(itinerary_parts),
            "itinerary_list": itinerary_parts
        }

    except Exception as e:
        logger.error(f"獲取排行榜第{rank}名詳細行程失敗: {e}")
        return None