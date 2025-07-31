#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
本地集合管理系統
提供完整的集合設定、管理和提醒功能
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
import threading
import time
import os
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class MeetingManager:
    """集合管理器"""
    
    def __init__(self, db_path: str = "meetings.db"):
        self.db_path = db_path
        self.init_database()
        self.start_reminder_thread()
    
    def init_database(self):
        """初始化資料庫"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 創建集合表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS meetings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        meeting_name TEXT NOT NULL,
                        meeting_time TEXT NOT NULL,
                        meeting_location TEXT NOT NULL,
                        meeting_date TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'active',
                        reminder_10min_sent BOOLEAN DEFAULT FALSE,
                        reminder_5min_sent BOOLEAN DEFAULT FALSE,
                        reminder_on_time_sent BOOLEAN DEFAULT FALSE
                    )
                ''')
                
                # 創建提醒記錄表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS reminders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        meeting_id INTEGER,
                        reminder_type TEXT NOT NULL,
                        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (meeting_id) REFERENCES meetings (id)
                    )
                ''')
                
                conn.commit()
                logger.info("資料庫初始化完成")
                
        except Exception as e:
            logger.error(f"資料庫初始化失敗: {str(e)}")
    
    def create_meeting(self, user_id: str, meeting_time: str, meeting_location: str, 
                      meeting_name: Optional[str] = None) -> Tuple[bool, str, Optional[int]]:
        """
        創建集合
        
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
            
            # 生成集合名稱
            if not meeting_name:
                current_date = datetime.now().strftime("%m月%d日")
                meeting_name = f"{current_date} {meeting_location}集合"
            
            # 設定日期為今天
            meeting_date = datetime.now().strftime("%Y-%m-%d")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO meetings 
                    (user_id, meeting_name, meeting_time, meeting_location, meeting_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, meeting_name, meeting_time, meeting_location, meeting_date))
                
                meeting_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"成功創建集合: ID={meeting_id}, 時間={meeting_time}, 地點={meeting_location}")
                return True, "集合設定成功", meeting_id
                
        except Exception as e:
            logger.error(f"創建集合失敗: {str(e)}")
            return False, "集合設定失敗", None
    
    def get_user_meetings(self, user_id: str, status: str = "active") -> List[Dict]:
        """獲取用戶的集合列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, meeting_name, meeting_time, meeting_location, meeting_date, created_at
                    FROM meetings 
                    WHERE user_id = ? AND status = ?
                    ORDER BY meeting_date, meeting_time
                ''', (user_id, status))
                
                meetings = []
                for row in cursor.fetchall():
                    meetings.append({
                        "id": row[0],
                        "meeting_name": row[1],
                        "meeting_time": row[2],
                        "meeting_location": row[3],
                        "meeting_date": row[4],
                        "created_at": row[5]
                    })
                
                return meetings
                
        except Exception as e:
            logger.error(f"獲取用戶集合失敗: {str(e)}")
            return []
    
    def get_meeting_by_id(self, meeting_id: int) -> Optional[Dict]:
        """根據ID獲取集合詳情"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, user_id, meeting_name, meeting_time, meeting_location, 
                           meeting_date, created_at, status
                    FROM meetings 
                    WHERE id = ?
                ''', (meeting_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "user_id": row[1],
                        "meeting_name": row[2],
                        "meeting_time": row[3],
                        "meeting_location": row[4],
                        "meeting_date": row[5],
                        "created_at": row[6],
                        "status": row[7]
                    }
                return None
                
        except Exception as e:
            logger.error(f"獲取集合詳情失敗: {str(e)}")
            return None
    
    def cancel_meeting(self, meeting_id: int, user_id: str) -> Tuple[bool, str]:
        """取消集合"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE meetings 
                    SET status = 'cancelled' 
                    WHERE id = ? AND user_id = ?
                ''', (meeting_id, user_id))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"成功取消集合: ID={meeting_id}")
                    return True, "集合已取消"
                else:
                    return False, "找不到指定的集合或無權限取消"
                
        except Exception as e:
            logger.error(f"取消集合失敗: {str(e)}")
            return False, "取消集合失敗"
    
    def get_pending_reminders(self) -> List[Dict]:
        """獲取待發送的提醒"""
        try:
            current_time = datetime.now()
            current_date = current_time.strftime("%Y-%m-%d")
            current_time_str = current_time.strftime("%H:%M")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 獲取今天的活躍集合
                cursor.execute('''
                    SELECT id, user_id, meeting_name, meeting_time, meeting_location,
                           reminder_10min_sent, reminder_5min_sent, reminder_on_time_sent
                    FROM meetings 
                    WHERE meeting_date = ? AND status = 'active'
                ''', (current_date,))
                
                reminders = []
                for row in cursor.fetchall():
                    meeting_id, user_id, meeting_name, meeting_time, meeting_location, \
                    reminder_10min_sent, reminder_5min_sent, reminder_on_time_sent = row
                    
                    # 計算時間差
                    meeting_datetime = datetime.strptime(f"{current_date} {meeting_time}", "%Y-%m-%d %H:%M")
                    time_diff = meeting_datetime - current_time
                    minutes_diff = int(time_diff.total_seconds() / 60)
                    
                    # 檢查是否需要發送提醒
                    if minutes_diff == 10 and not reminder_10min_sent:
                        reminders.append({
                            "meeting_id": meeting_id,
                            "user_id": user_id,
                            "meeting_name": meeting_name,
                            "meeting_time": meeting_time,
                            "meeting_location": meeting_location,
                            "reminder_type": "10_min_before",
                            "message": f"⏰ 集合提醒：還有 10 分鐘就要在 {meeting_location} 集合了！"
                        })
                    
                    elif minutes_diff == 5 and not reminder_5min_sent:
                        reminders.append({
                            "meeting_id": meeting_id,
                            "user_id": user_id,
                            "meeting_name": meeting_name,
                            "meeting_time": meeting_time,
                            "meeting_location": meeting_location,
                            "reminder_type": "5_min_before",
                            "message": f"🚨 緊急提醒：還有 5 分鐘就要在 {meeting_location} 集合了！"
                        })
                    
                    elif minutes_diff == 0 and not reminder_on_time_sent:
                        reminders.append({
                            "meeting_id": meeting_id,
                            "user_id": user_id,
                            "meeting_name": meeting_name,
                            "meeting_time": meeting_time,
                            "meeting_location": meeting_location,
                            "reminder_type": "on_time",
                            "message": f"🎯 集合時間到了！請準時到達 {meeting_location}！"
                        })
                
                return reminders
                
        except Exception as e:
            logger.error(f"獲取待發送提醒失敗: {str(e)}")
            return []
    
    def mark_reminder_sent(self, meeting_id: int, reminder_type: str):
        """標記提醒已發送"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 更新提醒狀態
                if reminder_type == "10_min_before":
                    cursor.execute('''
                        UPDATE meetings 
                        SET reminder_10min_sent = TRUE 
                        WHERE id = ?
                    ''', (meeting_id,))
                elif reminder_type == "5_min_before":
                    cursor.execute('''
                        UPDATE meetings 
                        SET reminder_5min_sent = TRUE 
                        WHERE id = ?
                    ''', (meeting_id,))
                elif reminder_type == "on_time":
                    cursor.execute('''
                        UPDATE meetings 
                        SET reminder_on_time_sent = TRUE 
                        WHERE id = ?
                    ''', (meeting_id,))
                
                # 記錄提醒發送
                cursor.execute('''
                    INSERT INTO reminders (meeting_id, reminder_type)
                    VALUES (?, ?)
                ''', (meeting_id, reminder_type))
                
                conn.commit()
                logger.info(f"已標記提醒發送: 集合ID={meeting_id}, 類型={reminder_type}")
                
        except Exception as e:
            logger.error(f"標記提醒發送失敗: {str(e)}")
    
    def _validate_time_format(self, time_str: str) -> bool:
        """驗證時間格式"""
        try:
            datetime.strptime(time_str, "%H:%M")
            return True
        except ValueError:
            return False
    
    def start_reminder_thread(self):
        """啟動提醒線程"""
        def reminder_worker():
            while True:
                try:
                    # 獲取待發送的提醒
                    reminders = self.get_pending_reminders()

                    # 發送提醒到 LINE Bot
                    for reminder in reminders:
                        logger.info(f"需要發送提醒: {reminder}")

                        # 調用外部回調函數發送提醒
                        if hasattr(self, 'reminder_callback') and self.reminder_callback:
                            try:
                                self.reminder_callback(reminder)
                            except Exception as e:
                                logger.error(f"調用提醒回調失敗: {str(e)}")

                        # 標記為已發送
                        self.mark_reminder_sent(reminder["meeting_id"], reminder["reminder_type"])

                    # 每分鐘檢查一次
                    time.sleep(60)

                except Exception as e:
                    logger.error(f"提醒線程錯誤: {str(e)}")
                    time.sleep(60)

        # 啟動後台線程
        thread = threading.Thread(target=reminder_worker, daemon=True)
        thread.start()
        logger.info("提醒線程已啟動")

    def set_reminder_callback(self, callback_func):
        """設定提醒回調函數"""
        self.reminder_callback = callback_func
        logger.info("提醒回調函數已設定")
    
    def send_reminder_to_user(self, user_id: str, reminder_data: Dict):
        """發送提醒給用戶（由外部調用）"""
        try:
            # 這裡會由 LINE Bot 調用
            logger.info(f"發送提醒給用戶 {user_id}: {reminder_data}")
            return True
        except Exception as e:
            logger.error(f"發送提醒失敗: {str(e)}")
            return False

# 全局實例
meeting_manager = MeetingManager() 