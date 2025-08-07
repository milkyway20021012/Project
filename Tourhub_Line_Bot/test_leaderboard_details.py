#!/usr/bin/env python3
"""
測試排行榜詳細行程功能
"""

import sys
import logging
from api.config import KEYWORD_MAPPINGS
from api.index import get_message_template

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_keyword_matching():
    """測試關鍵字匹配"""
    test_messages = [
        "第一名詳細行程",
        "第一名行程",
        "冠軍詳細行程",
        "排行榜第一名詳細",
        "第二名詳細行程",
        "第三名行程",
        "top1詳細",
        "Top1詳細"
    ]
    
    logger.info("=== 測試關鍵字匹配 ===")
    for message in test_messages:
        template_config = get_message_template(message)
        if template_config:
            logger.info(f"✅ '{message}' -> {template_config['template']} (rank: {template_config.get('rank', 'N/A')})")
        else:
            logger.warning(f"❌ '{message}' -> 無匹配")

def test_database_function():
    """測試資料庫函數"""
    logger.info("=== 測試資料庫函數 ===")
    try:
        from api.database_utils import get_leaderboard_rank_details, MYSQL_AVAILABLE
        
        if not MYSQL_AVAILABLE:
            logger.warning("⚠️  MySQL 不可用，跳過資料庫測試")
            return
        
        # 測試獲取第一名詳細行程
        rank_data = get_leaderboard_rank_details(1)
        if rank_data:
            logger.info("✅ 成功獲取第一名詳細行程")
            logger.info(f"   - 行程ID: {rank_data.get('trip_id')}")
            logger.info(f"   - 標題: {rank_data.get('title')}")
            logger.info(f"   - 地區: {rank_data.get('area')}")
            logger.info(f"   - 天數: {rank_data.get('duration')}")
            logger.info(f"   - 人氣分數: {rank_data.get('popularity_score')}")
            logger.info(f"   - 行程安排: {len(rank_data.get('itinerary_list', []))} 個項目")
        else:
            logger.warning("⚠️  無法獲取第一名詳細行程（可能沒有資料）")
            
    except Exception as e:
        logger.error(f"❌ 資料庫測試失敗: {e}")

def test_flex_message_creation():
    """測試 Flex Message 創建"""
    logger.info("=== 測試 Flex Message 創建 ===")
    try:
        from api.index import create_flex_message
        from api.database_utils import get_leaderboard_rank_details, MYSQL_AVAILABLE
        
        if not MYSQL_AVAILABLE:
            logger.warning("⚠️  MySQL 不可用，使用模擬資料測試")
            # 使用模擬資料
            mock_data = {
                "trip_id": 1,
                "rank": 1,
                "rank_title": "🥇 第一名",
                "title": "測試行程",
                "description": "精彩的測試行程",
                "area": "測試地區",
                "duration": "3天",
                "popularity_score": 95.5,
                "favorite_count": 100,
                "share_count": 50,
                "view_count": 1000,
                "itinerary": "Day 1: 測試景點A\nDay 2: 測試景點B\nDay 3: 測試景點C",
                "itinerary_list": [
                    "Day 1: 測試景點A (09:00 - 17:00)",
                    "Day 2: 測試景點B (10:00 - 16:00)",
                    "Day 3: 測試景點C (08:00 - 18:00)"
                ]
            }
            rank_data = mock_data
        else:
            rank_data = get_leaderboard_rank_details(1)
        
        if rank_data:
            flex_message = create_flex_message("leaderboard_details", rank_data=rank_data)
            if flex_message and flex_message.get("type") == "bubble":
                logger.info("✅ 成功創建 Flex Message")
                logger.info(f"   - 類型: {flex_message.get('type')}")
                logger.info(f"   - 大小: {flex_message.get('size')}")
                logger.info(f"   - 有標題: {'header' in flex_message}")
                logger.info(f"   - 有內容: {'body' in flex_message}")
                logger.info(f"   - 有按鈕: {'footer' in flex_message}")
            else:
                logger.error("❌ Flex Message 格式不正確")
        else:
            logger.warning("⚠️  無資料可測試 Flex Message")
            
    except Exception as e:
        logger.error(f"❌ Flex Message 測試失敗: {e}")

if __name__ == "__main__":
    logger.info("=== 排行榜詳細行程功能測試 ===")
    
    test_keyword_matching()
    test_database_function()
    test_flex_message_creation()
    
    logger.info("🎉 測試完成！")
