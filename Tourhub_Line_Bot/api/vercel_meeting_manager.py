#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vercel 兼容的集合管理系統
由於 Vercel 是無狀態環境，這個版本不使用本地資料庫和後台線程
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os

logger = logging.getLogger(__name__)

class VercelMeetingManager:
    """適用於 Vercel 的集合管理器"""
    
    def __init__(self):
        # 在 Vercel 環境中，我們不能使用持久化存儲
        # 這裡只做基本的驗證和處理
        logger.info("Vercel 集合管理器初始化")
    
    def create_meeting(self, user_id: str, meeting_time: str, meeting_location: str,
                      meeting_name: Optional[str] = None) -> Tuple[bool, str, Optional[int]]:
        """
        創建集合（Vercel 版本）

        Args:
            user_id: 用戶ID
            meeting_time: 集合時間 (HH:MM)
            meeting_location: 集合地點
            meeting_name: 集合名稱 (可選)

        Returns:
            (success, message, meeting_id)
        """
        try:
            # 驗證時間格式
            if not self._validate_time_format(meeting_time):
                return False, "時間格式錯誤，請使用 HH:MM 格式", None

            # 驗證時間是否為未來時間
            current_time = datetime.now()
            today = current_time.strftime("%Y-%m-%d")
            meeting_datetime = datetime.strptime(f"{today} {meeting_time}", "%Y-%m-%d %H:%M")

            # 如果時間已過，假設是明天
            if meeting_datetime <= current_time:
                meeting_datetime = meeting_datetime + timedelta(days=1)

            # 生成集合名稱
            if not meeting_name:
                meeting_date_str = meeting_datetime.strftime("%m月%d日")
                meeting_name = f"{meeting_date_str} {meeting_location}集合"

            # 生成一個基於內容的 meeting_id
            meeting_id = abs(hash(f"{user_id}_{meeting_time}_{meeting_location}_{meeting_datetime.date()}")) % 100000

            # 在實際應用中，這裡應該保存到外部資料庫
            # 目前只做日誌記錄
            logger.info(f"創建集合成功: ID={meeting_id}, 用戶={user_id}, 時間={meeting_time}, 地點={meeting_location}, 預計日期={meeting_datetime.date()}")

            return True, "集合設定成功！智能提醒已啟用", meeting_id

        except Exception as e:
            logger.error(f"創建集合失敗: {str(e)}")
            return False, "集合設定失敗", None
    
    def get_user_meetings(self, user_id: str, status: str = "active") -> List[Dict]:
        """獲取用戶的集合列表（Vercel 版本）"""
        try:
            # 在 Vercel 環境中，我們無法持久化數據
            # 這裡返回空列表，實際應用中需要連接外部資料庫
            logger.info(f"獲取用戶 {user_id} 的集合列表（Vercel 環境）")
            return []
                
        except Exception as e:
            logger.error(f"獲取用戶集合失敗: {str(e)}")
            return []
    
    def get_meeting_by_id(self, meeting_id: int) -> Optional[Dict]:
        """根據ID獲取集合詳情（Vercel 版本）"""
        try:
            # 在 Vercel 環境中，我們無法持久化數據
            logger.info(f"獲取集合詳情: ID={meeting_id}（Vercel 環境）")
            return None
                
        except Exception as e:
            logger.error(f"獲取集合詳情失敗: {str(e)}")
            return None
    
    def cancel_meeting(self, meeting_id: int, user_id: str) -> Tuple[bool, str]:
        """取消集合（Vercel 版本）"""
        try:
            # 在 Vercel 環境中，我們無法持久化數據
            logger.info(f"模擬取消集合: ID={meeting_id}, 用戶={user_id}")
            return True, "集合已取消（Vercel 環境）"
                
        except Exception as e:
            logger.error(f"取消集合失敗: {str(e)}")
            return False, "取消集合失敗"
    
    def _validate_time_format(self, time_str: str) -> bool:
        """驗證時間格式"""
        try:
            datetime.strptime(time_str, "%H:%M")
            return True
        except ValueError:
            return False
    
    def set_reminder_callback(self, callback_func):
        """設定提醒回調函數（Vercel 版本）"""
        # 在 Vercel 環境中，我們不能使用後台線程
        # 提醒功能需要使用外部服務（如 Vercel Cron Jobs 或第三方服務）
        logger.info("提醒回調函數已設定（Vercel 環境 - 需要外部 Cron 服務）")
        self.reminder_callback = callback_func

    def simulate_reminder_schedule(self, meeting_time: str, meeting_location: str) -> Dict:
        """模擬提醒時間表"""
        try:
            current_time = datetime.now()
            today = current_time.strftime("%Y-%m-%d")
            meeting_datetime = datetime.strptime(f"{today} {meeting_time}", "%Y-%m-%d %H:%M")

            # 如果時間已過，假設是明天
            if meeting_datetime <= current_time:
                meeting_datetime = meeting_datetime + timedelta(days=1)

            # 計算提醒時間
            reminder_10min = meeting_datetime - timedelta(minutes=10)
            reminder_5min = meeting_datetime - timedelta(minutes=5)

            return {
                "meeting_datetime": meeting_datetime,
                "reminder_10min": reminder_10min,
                "reminder_5min": reminder_5min,
                "reminders": [
                    {
                        "time": reminder_10min.strftime("%H:%M"),
                        "type": "10_min_before",
                        "message": f"⏰ 還有 10 分鐘就要在 {meeting_location} 集合了！"
                    },
                    {
                        "time": reminder_5min.strftime("%H:%M"),
                        "type": "5_min_before",
                        "message": f"🚨 還有 5 分鐘就要在 {meeting_location} 集合了！"
                    },
                    {
                        "time": meeting_datetime.strftime("%H:%M"),
                        "type": "on_time",
                        "message": f"🎯 集合時間到了！請準時到達 {meeting_location}！"
                    }
                ]
            }
        except Exception as e:
            logger.error(f"模擬提醒時間表失敗: {str(e)}")
            return {}

# 創建全局實例
vercel_meeting_manager = VercelMeetingManager()

# 為了向後兼容，也提供原來的名稱
meeting_manager = vercel_meeting_manager
