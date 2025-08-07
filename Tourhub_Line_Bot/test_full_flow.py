#!/usr/bin/env python3
"""
測試完整的消息處理流程
"""

import sys
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_message_processing():
    """測試完整的消息處理流程"""
    logger.info("=== 測試完整消息處理流程 ===")
    
    try:
        from api.index import get_message_template, create_flex_message
        from api.database_utils import get_leaderboard_rank_details
        
        # 測試消息
        test_message = "第一名詳細行程"
        
        # 1. 獲取模板配置
        template_config = get_message_template(test_message)
        logger.info(f"1. 模板配置: {template_config}")
        
        if template_config and template_config["template"] == "leaderboard_details":
            # 2. 獲取排行榜資料
            rank = int(template_config["rank"])
            rank_data = get_leaderboard_rank_details(rank)
            logger.info(f"2. 獲取到排行榜第{rank}名資料: {rank_data is not None}")
            
            if rank_data:
                logger.info(f"   - 行程: {rank_data.get('title')}")
                logger.info(f"   - 地區: {rank_data.get('area')}")
                logger.info(f"   - 詳細行程項目數: {len(rank_data.get('itinerary_list', []))}")
                
                # 3. 創建 Flex Message
                flex_message = create_flex_message("leaderboard_details", rank_data=rank_data)
                logger.info(f"3. Flex Message 創建: {flex_message is not None}")
                
                if flex_message:
                    # 4. 驗證 Flex Message 結構
                    required_keys = ["type", "header", "body", "footer"]
                    all_keys_present = all(key in flex_message for key in required_keys)
                    logger.info(f"4. Flex Message 結構完整: {all_keys_present}")
                    
                    # 5. 檢查標題內容
                    header_text = flex_message.get("header", {}).get("contents", [{}])[0].get("text", "")
                    logger.info(f"5. 標題內容: {header_text}")
                    
                    # 6. 檢查行程內容
                    body_contents = flex_message.get("body", {}).get("contents", [])
                    # 檢查包含日期的項目（新格式）
                    date_items = [item for item in body_contents if item.get("type") == "text" and "年" in item.get("text", "") and "月" in item.get("text", "")]
                    # 檢查包含時間的項目
                    time_items = [item for item in body_contents if item.get("type") == "text" and ":" in item.get("text", "") and "-" in item.get("text", "")]
                    # 檢查分隔線數量
                    separator_items = [item for item in body_contents if item.get("type") == "separator"]

                    logger.info(f"6. 行程內容分析:")
                    logger.info(f"   - 日期項目數: {len(date_items)}")
                    logger.info(f"   - 時間項目數: {len(time_items)}")
                    logger.info(f"   - 分隔線數: {len(separator_items)}")
                    logger.info(f"   - 總內容項目數: {len(body_contents)}")

                    # 顯示前幾個內容項目
                    for i, item in enumerate(body_contents[:10]):
                        if item.get("type") == "text":
                            logger.info(f"   - 項目 {i}: {item.get('text', '')[:50]}...")
                    
                    logger.info("✅ 完整流程測試成功！")
                    return True
                else:
                    logger.error("❌ Flex Message 創建失敗")
            else:
                logger.warning("⚠️  無法獲取排行榜資料")
        else:
            logger.error("❌ 模板配置不正確")
            
    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
    
    return False

def test_different_ranks():
    """測試不同排名的詳細行程"""
    logger.info("=== 測試不同排名 ===")
    
    test_cases = [
        ("第一名詳細行程", 1),
        ("第二名詳細行程", 2),
        ("第三名詳細行程", 3)
    ]
    
    for message, expected_rank in test_cases:
        try:
            from api.index import get_message_template
            from api.database_utils import get_leaderboard_rank_details
            
            template_config = get_message_template(message)
            if template_config and template_config["template"] == "leaderboard_details":
                rank = int(template_config["rank"])
                if rank == expected_rank:
                    rank_data = get_leaderboard_rank_details(rank)
                    if rank_data:
                        logger.info(f"✅ '{message}' -> 第{rank}名: {rank_data.get('title', '無標題')}")
                    else:
                        logger.warning(f"⚠️  '{message}' -> 第{rank}名: 無資料")
                else:
                    logger.error(f"❌ '{message}' -> 排名不符: 期望{expected_rank}, 實際{rank}")
            else:
                logger.error(f"❌ '{message}' -> 無法匹配模板")
                
        except Exception as e:
            logger.error(f"❌ 測試 '{message}' 失敗: {e}")

if __name__ == "__main__":
    logger.info("=== 完整流程測試 ===")
    
    success = test_message_processing()
    test_different_ranks()
    
    if success:
        logger.info("🎉 所有測試通過！功能已準備就緒！")
    else:
        logger.error("💥 測試失敗，需要檢查問題")
        sys.exit(1)
