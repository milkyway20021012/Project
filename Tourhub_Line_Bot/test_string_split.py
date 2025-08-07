#!/usr/bin/env python3
"""
測試字串分割問題
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_string_split():
    """測試字串分割"""
    
    # 模擬從資料庫獲取的格式化字串
    test_string = "2025年08月15日 星期五\n10:00 - 18:00\n札幌市區・大通公園"
    
    logger.info(f"原始字串: {repr(test_string)}")
    logger.info(f"字串長度: {len(test_string)}")
    
    # 測試分割
    parts = test_string.split('\n')
    logger.info(f"分割結果: {parts}")
    logger.info(f"分割後長度: {len(parts)}")
    
    for i, part in enumerate(parts):
        logger.info(f"  部分 {i}: {repr(part)}")
    
    # 測試實際的資料庫函數
    logger.info("\n=== 測試實際函數 ===")
    try:
        from api.database_utils import get_leaderboard_rank_details
        
        rank_data = get_leaderboard_rank_details(1)
        if rank_data and rank_data.get('itinerary_list'):
            first_item = rank_data['itinerary_list'][0]
            logger.info(f"第一個項目: {repr(first_item)}")
            
            parts = first_item.split('\n')
            logger.info(f"分割結果: {parts}")
            logger.info(f"分割後長度: {len(parts)}")
            
            # 檢查是否包含換行符
            if '\n' in first_item:
                logger.info("✅ 包含換行符")
            else:
                logger.warning("❌ 不包含換行符")
                
            # 嘗試其他分割方式
            import re
            parts_re = re.split(r'[\n\r]+', first_item)
            logger.info(f"正則分割結果: {parts_re}")
            
    except Exception as e:
        logger.error(f"測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_string_split()
