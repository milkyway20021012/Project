"""
數據庫優化腳本
用於創建索引、優化查詢性能
"""

import logging
from .database_utils import get_database_connection

logger = logging.getLogger(__name__)

def create_performance_indexes():
    """創建性能優化索引"""
    
    indexes = [
        # line_trips 表索引
        {
            "table": "line_trips",
            "name": "idx_area_title",
            "columns": ["area", "title"],
            "description": "優化地區和標題查詢"
        },
        {
            "table": "line_trips", 
            "name": "idx_line_user_id",
            "columns": ["line_user_id"],
            "description": "優化用戶行程查詢"
        },
        {
            "table": "line_trips",
            "name": "idx_created_by_line_user", 
            "columns": ["created_by_line_user"],
            "description": "優化創建者查詢"
        },
        
        # trip_stats 表索引
        {
            "table": "trip_stats",
            "name": "idx_popularity_score",
            "columns": ["popularity_score DESC", "favorite_count DESC", "share_count DESC"],
            "description": "優化排行榜查詢"
        },
        {
            "table": "trip_stats",
            "name": "idx_trip_id_stats",
            "columns": ["trip_id"],
            "description": "優化統計數據關聯"
        },
        
        # line_trip_details 表索引
        {
            "table": "line_trip_details",
            "name": "idx_trip_date_time",
            "columns": ["trip_id", "date", "start_time"],
            "description": "優化行程詳細查詢"
        },
        {
            "table": "line_trip_details",
            "name": "idx_trip_id_details",
            "columns": ["trip_id"],
            "description": "優化行程詳細關聯"
        }
    ]
    
    try:
        with get_database_connection() as connection:
            if not connection:
                logger.error("無法連接到數據庫")
                return False
                
            cursor = connection.cursor()
            success_count = 0
            
            for index in indexes:
                try:
                    # 檢查索引是否已存在
                    check_query = """
                    SELECT COUNT(*) as count
                    FROM information_schema.statistics 
                    WHERE table_schema = DATABASE() 
                        AND table_name = %s 
                        AND index_name = %s
                    """
                    
                    cursor.execute(check_query, (index["table"], index["name"]))
                    result = cursor.fetchone()
                    
                    if result and result[0] > 0:
                        logger.info(f"索引 {index['name']} 已存在，跳過創建")
                        continue
                    
                    # 創建索引
                    columns_str = ", ".join(index["columns"])
                    create_query = f"""
                    CREATE INDEX {index['name']} 
                    ON {index['table']} ({columns_str})
                    """
                    
                    cursor.execute(create_query)
                    success_count += 1
                    logger.info(f"成功創建索引: {index['name']} - {index['description']}")
                    
                except Exception as e:
                    logger.warning(f"創建索引 {index['name']} 失敗: {e}")
                    continue
            
            cursor.close()
            logger.info(f"索引優化完成，成功創建 {success_count} 個索引")
            return True
            
    except Exception as e:
        logger.error(f"數據庫索引優化失敗: {e}")
        return False

def analyze_table_performance():
    """分析表性能"""
    
    try:
        with get_database_connection() as connection:
            if not connection:
                return
                
            cursor = connection.cursor(dictionary=True)
            
            # 分析主要表的統計信息
            tables = ["line_trips", "trip_stats", "line_trip_details"]
            
            for table in tables:
                try:
                    # 獲取表統計信息
                    stats_query = f"""
                    SELECT 
                        table_name,
                        table_rows,
                        data_length,
                        index_length,
                        (data_length + index_length) as total_size
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE() 
                        AND table_name = %s
                    """
                    
                    cursor.execute(stats_query, (table,))
                    stats = cursor.fetchone()
                    
                    if stats:
                        logger.info(f"表 {table} 統計:")
                        logger.info(f"  行數: {stats['table_rows']}")
                        logger.info(f"  數據大小: {stats['data_length']} bytes")
                        logger.info(f"  索引大小: {stats['index_length']} bytes")
                        logger.info(f"  總大小: {stats['total_size']} bytes")
                        
                except Exception as e:
                    logger.warning(f"分析表 {table} 失敗: {e}")
            
            cursor.close()
            
    except Exception as e:
        logger.error(f"性能分析失敗: {e}")

def optimize_database_settings():
    """優化數據庫設置"""
    
    optimizations = [
        "SET SESSION query_cache_type = ON",
        "SET SESSION query_cache_size = 1048576",  # 1MB
        "SET SESSION sort_buffer_size = 2097152",   # 2MB
        "SET SESSION read_buffer_size = 131072",    # 128KB
    ]
    
    try:
        with get_database_connection() as connection:
            if not connection:
                return False
                
            cursor = connection.cursor()
            
            for optimization in optimizations:
                try:
                    cursor.execute(optimization)
                    logger.info(f"應用優化設置: {optimization}")
                except Exception as e:
                    logger.warning(f"優化設置失敗: {optimization} - {e}")
            
            cursor.close()
            return True
            
    except Exception as e:
        logger.error(f"數據庫設置優化失敗: {e}")
        return False

def run_database_optimization():
    """運行完整的數據庫優化"""
    logger.info("開始數據庫優化...")
    
    # 分析當前性能
    analyze_table_performance()
    
    # 創建索引
    create_performance_indexes()
    
    # 優化設置
    optimize_database_settings()
    
    logger.info("數據庫優化完成")

if __name__ == "__main__":
    run_database_optimization()
