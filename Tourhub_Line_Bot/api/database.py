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

def get_leaderboard_data():
    """獲取排行榜資料"""
    try:
        connection = get_database_connection()
        if not connection:
            return None
        
        cursor = connection.cursor(dictionary=True)
        
        # 查詢排行榜資料 - 根據人氣分數排序
        query = """
        SELECT 
            t.trip_id,
            t.title,
            t.description,
            t.area,
            t.start_date,
            t.end_date,
            DATEDIFF(t.end_date, t.start_date) + 1 as duration_days,
            COALESCE(ts.favorite_count, 0) as favorite_count,
            COALESCE(ts.share_count, 0) as share_count,
            COALESCE(ts.view_count, 0) as view_count,
            COALESCE(ts.popularity_score, 0) as popularity_score
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
        leaderboard = {}
        rank_colors = {1: "#FFD700", 2: "#C0C0C0", 3: "#CD7F32", 4: "#4ECDC4", 5: "#FF6B9D"}
        rank_titles = {1: "🥇 排行榜第一名", 2: "🥈 排行榜第二名", 3: "🥉 排行榜第三名", 
                      4: "🏅 排行榜第四名", 5: "🎖️ 排行榜第五名"}
        
        for i, trip in enumerate(results, 1):
            leaderboard[str(i)] = {
                "trip_id": trip['trip_id'],
                "title": rank_titles.get(i, f"🎖️ 排行榜第{i}名"),
                "color": rank_colors.get(i, "#9B59B6"),
                "destination": trip['area'] or "未知地區",
                "duration": f"{trip['duration_days']}天{trip['duration_days']-1}夜" if trip['duration_days'] > 1 else "1天",
                "participants": f"{trip['favorite_count']}人收藏",
                "feature": trip['description'] or "精彩行程",
                "itinerary": f"行程標題：{trip['title']}\n地區：{trip['area']}\n開始日期：{trip['start_date']}\n結束日期：{trip['end_date']}\n人氣分數：{trip['popularity_score']}",
                "favorite_count": trip['favorite_count'],
                "share_count": trip['share_count'],
                "view_count": trip['view_count'],
                "popularity_score": trip['popularity_score']
            }
        
        logger.info(f"成功獲取 {len(leaderboard)} 筆排行榜資料")
        return leaderboard
        
    except Exception as e:
        logger.error(f"獲取排行榜資料失敗: {e}")
        return None

def get_trip_details(trip_id):
    """獲取特定行程的詳細資料"""
    try:
        connection = get_database_connection()
        if not connection:
            return None
        
        cursor = connection.cursor(dictionary=True)
        
        # 查詢行程基本資料
        trip_query = """
        SELECT 
            t.trip_id,
            t.title,
            t.description,
            t.area,
            t.start_date,
            t.end_date,
            DATEDIFF(t.end_date, t.start_date) + 1 as duration_days,
            COALESCE(ts.favorite_count, 0) as favorite_count,
            COALESCE(ts.share_count, 0) as share_count,
            COALESCE(ts.view_count, 0) as view_count,
            COALESCE(ts.popularity_score, 0) as popularity_score
        FROM line_trips t
        LEFT JOIN trip_stats ts ON t.trip_id = ts.trip_id
        WHERE t.trip_id = %s
        """
        
        cursor.execute(trip_query, (trip_id,))
        trip_data = cursor.fetchone()
        
        if not trip_data:
            cursor.close()
            connection.close()
            return None
        
        # 查詢行程詳細安排
        details_query = """
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
        
        cursor.execute(details_query, (trip_id,))
        details = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        # 格式化詳細行程
        itinerary_parts = []
        for detail in details:
            date_str = detail['date'].strftime('%Y-%m-%d') if detail['date'] else "未知日期"
            time_str = ""
            if detail['start_time'] and detail['end_time']:
                start_time = str(detail['start_time'])[:5]
                end_time = str(detail['end_time'])[:5]
                time_str = f"{start_time}-{end_time}"
            elif detail['start_time']:
                time_str = str(detail['start_time'])[:5]
            
            location = detail['location'] or "未知地點"
            if time_str:
                itinerary_parts.append(f"{date_str} {time_str}: {location}")
            else:
                itinerary_parts.append(f"{date_str}: {location}")
        
        # 如果沒有詳細行程，使用基本資訊
        if not itinerary_parts:
            itinerary_parts.append(f"精彩的{trip_data['area']}之旅")
        
        result = {
            "trip_id": trip_data['trip_id'],
            "title": trip_data['title'],
            "description": trip_data['description'],
            "area": trip_data['area'],
            "duration": f"{trip_data['duration_days']}天{trip_data['duration_days']-1}夜" if trip_data['duration_days'] > 1 else "1天",
            "start_date": trip_data['start_date'].strftime('%Y-%m-%d') if trip_data['start_date'] else "",
            "end_date": trip_data['end_date'].strftime('%Y-%m-%d') if trip_data['end_date'] else "",
            "favorite_count": trip_data['favorite_count'],
            "share_count": trip_data['share_count'],
            "view_count": trip_data['view_count'],
            "popularity_score": trip_data['popularity_score'],
            "itinerary": "\n".join(itinerary_parts),
            "itinerary_list": itinerary_parts
        }
        
        logger.info(f"成功獲取行程 {trip_id} 的詳細資料")
        return result
        
    except Exception as e:
        logger.error(f"獲取行程詳細資料失敗: {e}")
        return None

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
