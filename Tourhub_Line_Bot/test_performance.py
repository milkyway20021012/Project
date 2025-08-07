#!/usr/bin/env python3
"""
性能測試腳本 - 測試優化後的響應速度
"""

import time
import logging
import statistics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def measure_time(func, *args, **kwargs):
    """測量函數執行時間"""
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    return result, (end_time - start_time) * 1000  # 返回毫秒

def test_keyword_matching_performance():
    """測試關鍵字匹配性能"""
    logger.info("=== 測試關鍵字匹配性能 ===")
    
    try:
        from api.index import get_message_template
        
        test_messages = [
            "第一名詳細行程",
            "第二名詳細行程", 
            "第三名詳細行程",
            "排行榜",
            "冠軍詳細行程",
            "top1詳細",
            "不存在的關鍵字"
        ]
        
        times = []
        
        for message in test_messages:
            _, exec_time = measure_time(get_message_template, message)
            times.append(exec_time)
            logger.info(f"'{message}': {exec_time:.2f}ms")
        
        avg_time = statistics.mean(times)
        max_time = max(times)
        min_time = min(times)
        
        logger.info(f"關鍵字匹配性能統計:")
        logger.info(f"  平均時間: {avg_time:.2f}ms")
        logger.info(f"  最大時間: {max_time:.2f}ms")
        logger.info(f"  最小時間: {min_time:.2f}ms")
        
        return avg_time
        
    except Exception as e:
        logger.error(f"關鍵字匹配測試失敗: {e}")
        return None

def test_cache_performance():
    """測試緩存性能"""
    logger.info("=== 測試緩存性能 ===")
    
    try:
        from api.index import get_cached_rank_details
        
        # 第一次調用（冷緩存）
        _, cold_time = measure_time(get_cached_rank_details, 1)
        logger.info(f"冷緩存調用: {cold_time:.2f}ms")
        
        # 第二次調用（熱緩存）
        _, hot_time = measure_time(get_cached_rank_details, 1)
        logger.info(f"熱緩存調用: {hot_time:.2f}ms")
        
        # 計算緩存效果
        if cold_time > 0:
            speedup = cold_time / hot_time if hot_time > 0 else float('inf')
            logger.info(f"緩存加速比: {speedup:.2f}x")
        
        return cold_time, hot_time
        
    except Exception as e:
        logger.error(f"緩存性能測試失敗: {e}")
        return None, None

def test_database_query_performance():
    """測試資料庫查詢性能"""
    logger.info("=== 測試資料庫查詢性能 ===")
    
    try:
        from api.database_utils import get_leaderboard_from_database, get_leaderboard_rank_details
        
        # 測試排行榜查詢
        _, leaderboard_time = measure_time(get_leaderboard_from_database)
        logger.info(f"排行榜查詢: {leaderboard_time:.2f}ms")
        
        # 測試詳細行程查詢
        _, details_time = measure_time(get_leaderboard_rank_details, 1)
        logger.info(f"詳細行程查詢: {details_time:.2f}ms")
        
        return leaderboard_time, details_time
        
    except Exception as e:
        logger.error(f"資料庫查詢測試失敗: {e}")
        return None, None

def test_flex_message_creation():
    """測試 Flex Message 創建性能"""
    logger.info("=== 測試 Flex Message 創建性能 ===")
    
    try:
        from api.index import create_flex_message, get_cached_rank_details
        
        # 獲取測試資料
        rank_data = get_cached_rank_details(1)
        if not rank_data:
            logger.warning("無法獲取測試資料")
            return None
        
        # 測試 Flex Message 創建
        _, creation_time = measure_time(create_flex_message, "leaderboard_details", rank_data=rank_data)
        logger.info(f"Flex Message 創建: {creation_time:.2f}ms")
        
        return creation_time
        
    except Exception as e:
        logger.error(f"Flex Message 創建測試失敗: {e}")
        return None

def run_comprehensive_test():
    """運行綜合性能測試"""
    logger.info("=== 綜合性能測試 ===")
    
    try:
        from api.index import get_message_template, get_cached_rank_details, create_flex_message
        
        # 模擬完整的用戶請求處理流程
        test_message = "第一名詳細行程"
        
        start_time = time.time()
        
        # 1. 關鍵字匹配
        template_config = get_message_template(test_message)
        
        # 2. 獲取資料
        if template_config and template_config["template"] == "leaderboard_details":
            rank = int(template_config["rank"])
            rank_data = get_cached_rank_details(rank)
            
            # 3. 創建 Flex Message
            if rank_data:
                flex_message = create_flex_message("leaderboard_details", rank_data=rank_data)
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000
        
        logger.info(f"完整請求處理時間: {total_time:.2f}ms")
        
        # 性能評估
        if total_time < 100:
            logger.info("🚀 性能優秀 (< 100ms)")
        elif total_time < 300:
            logger.info("✅ 性能良好 (< 300ms)")
        elif total_time < 500:
            logger.info("⚠️  性能一般 (< 500ms)")
        else:
            logger.warning("❌ 性能需要改進 (> 500ms)")
        
        return total_time
        
    except Exception as e:
        logger.error(f"綜合測試失敗: {e}")
        return None

if __name__ == "__main__":
    logger.info("🚀 開始性能測試...")
    
    # 運行各項測試
    keyword_time = test_keyword_matching_performance()
    cold_time, hot_time = test_cache_performance()
    db_leaderboard_time, db_details_time = test_database_query_performance()
    flex_time = test_flex_message_creation()
    total_time = run_comprehensive_test()
    
    # 總結報告
    logger.info("\n" + "="*50)
    logger.info("📊 性能測試總結報告")
    logger.info("="*50)
    
    if keyword_time:
        logger.info(f"關鍵字匹配平均時間: {keyword_time:.2f}ms")
    
    if cold_time and hot_time:
        logger.info(f"緩存效果: {cold_time:.2f}ms -> {hot_time:.2f}ms")
    
    if db_leaderboard_time:
        logger.info(f"資料庫查詢時間: {db_leaderboard_time:.2f}ms")
    
    if flex_time:
        logger.info(f"Flex Message 創建: {flex_time:.2f}ms")
    
    if total_time:
        logger.info(f"完整請求處理: {total_time:.2f}ms")
    
    logger.info("🎉 性能測試完成！")
