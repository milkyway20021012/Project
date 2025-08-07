"""
高級緩存系統
實施多層緩存、智能預熱、LRU 淘汰策略
"""

import time
import threading
import logging
from typing import Any, Dict, Optional, Callable
from collections import OrderedDict
from functools import wraps
import hashlib
import json

logger = logging.getLogger(__name__)

class LRUCache:
    """LRU (Least Recently Used) 緩存實現"""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.timestamps = {}
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key in self.cache:
                # 移動到末尾（最近使用）
                value = self.cache.pop(key)
                self.cache[key] = value
                self.timestamps[key] = time.time()
                return value
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        with self.lock:
            if key in self.cache:
                self.cache.pop(key)
            elif len(self.cache) >= self.max_size:
                # 移除最舊的項目
                oldest_key = next(iter(self.cache))
                self.cache.pop(oldest_key)
                self.timestamps.pop(oldest_key, None)
            
            self.cache[key] = value
            self.timestamps[key] = time.time() + ttl
    
    def is_expired(self, key: str) -> bool:
        return key in self.timestamps and time.time() > self.timestamps[key]
    
    def delete(self, key: str) -> None:
        with self.lock:
            self.cache.pop(key, None)
            self.timestamps.pop(key, None)
    
    def clear(self) -> None:
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
    
    def size(self) -> int:
        return len(self.cache)

class MultiLevelCache:
    """多層緩存系統"""
    
    def __init__(self):
        # L1: 熱點數據緩存（小容量，快速訪問）
        self.l1_cache = LRUCache(max_size=50)
        
        # L2: 一般數據緩存（中等容量）
        self.l2_cache = LRUCache(max_size=200)
        
        # L3: 冷數據緩存（大容量）
        self.l3_cache = LRUCache(max_size=500)
        
        self.hit_counts = {"l1": 0, "l2": 0, "l3": 0, "miss": 0}
        self.lock = threading.RLock()
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """生成緩存鍵"""
        key_data = {
            "func": func_name,
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """從多層緩存中獲取數據"""
        with self.lock:
            # 檢查 L1 緩存
            if not self.l1_cache.is_expired(key):
                value = self.l1_cache.get(key)
                if value is not None:
                    self.hit_counts["l1"] += 1
                    return value
            
            # 檢查 L2 緩存
            if not self.l2_cache.is_expired(key):
                value = self.l2_cache.get(key)
                if value is not None:
                    self.hit_counts["l2"] += 1
                    # 提升到 L1
                    self.l1_cache.set(key, value, ttl=300)
                    return value
            
            # 檢查 L3 緩存
            if not self.l3_cache.is_expired(key):
                value = self.l3_cache.get(key)
                if value is not None:
                    self.hit_counts["l3"] += 1
                    # 提升到 L2
                    self.l2_cache.set(key, value, ttl=600)
                    return value
            
            self.hit_counts["miss"] += 1
            return None
    
    def set(self, key: str, value: Any, level: str = "l2", ttl: int = 300) -> None:
        """設置緩存數據"""
        with self.lock:
            if level == "l1":
                self.l1_cache.set(key, value, ttl)
            elif level == "l2":
                self.l2_cache.set(key, value, ttl)
            elif level == "l3":
                self.l3_cache.set(key, value, ttl)
    
    def delete(self, key: str) -> None:
        """刪除緩存數據"""
        with self.lock:
            self.l1_cache.delete(key)
            self.l2_cache.delete(key)
            self.l3_cache.delete(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取緩存統計信息"""
        total_hits = sum(self.hit_counts.values())
        if total_hits == 0:
            return {"hit_rate": 0, "details": self.hit_counts}
        
        hit_rate = (total_hits - self.hit_counts["miss"]) / total_hits
        return {
            "hit_rate": hit_rate,
            "total_requests": total_hits,
            "details": self.hit_counts.copy(),
            "cache_sizes": {
                "l1": self.l1_cache.size(),
                "l2": self.l2_cache.size(),
                "l3": self.l3_cache.size()
            }
        }

# 全局緩存實例
_global_cache = MultiLevelCache()

def cached(ttl: int = 300, level: str = "l2", key_func: Optional[Callable] = None):
    """緩存裝飾器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成緩存鍵
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = _global_cache._generate_key(func.__name__, args, kwargs)
            
            # 嘗試從緩存獲取
            cached_result = _global_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"緩存命中: {func.__name__}")
                return cached_result
            
            # 執行函數並緩存結果
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # 根據執行時間決定緩存級別
            if execution_time > 1.0:  # 超過1秒的查詢放入L1
                cache_level = "l1"
                cache_ttl = ttl * 2
            elif execution_time > 0.5:  # 超過0.5秒的查詢放入L2
                cache_level = "l2"
                cache_ttl = ttl
            else:  # 快速查詢放入L3
                cache_level = "l3"
                cache_ttl = ttl // 2
            
            _global_cache.set(cache_key, result, cache_level, cache_ttl)
            logger.debug(f"緩存設置: {func.__name__} -> {cache_level}, 執行時間: {execution_time:.3f}s")
            
            return result
        return wrapper
    return decorator

def warm_up_cache_advanced():
    """高級緩存預熱"""
    logger.info("開始高級緩存預熱...")
    
    try:
        # 預熱排行榜數據
        from .database_utils import get_leaderboard_from_database
        leaderboard_data = get_leaderboard_from_database()
        if leaderboard_data:
            cache_key = _global_cache._generate_key("get_leaderboard_from_database", (), {})
            _global_cache.set(cache_key, leaderboard_data, "l1", 600)
            logger.info("排行榜數據預熱完成")
        
        # 預熱熱門地區數據
        from .database_utils import get_trips_by_location
        popular_locations = ["東京", "大阪", "京都", "沖繩", "北海道"]
        
        for location in popular_locations:
            try:
                trips = get_trips_by_location(location, 5)
                if trips:
                    cache_key = _global_cache._generate_key("get_trips_by_location", (location, 5), {})
                    _global_cache.set(cache_key, trips, "l2", 300)
                    logger.info(f"{location} 行程數據預熱完成")
            except Exception as e:
                logger.warning(f"預熱 {location} 數據失敗: {e}")
        
        # 預熱前5名詳細數據
        from .database_utils import get_leaderboard_rank_details
        for rank in range(1, 6):
            try:
                rank_data = get_leaderboard_rank_details(rank)
                if rank_data:
                    cache_key = _global_cache._generate_key("get_leaderboard_rank_details", (rank,), {})
                    _global_cache.set(cache_key, rank_data, "l1", 900)
                    logger.info(f"第{rank}名詳細數據預熱完成")
            except Exception as e:
                logger.warning(f"預熱第{rank}名數據失敗: {e}")
        
        logger.info("高級緩存預熱完成")
        
    except Exception as e:
        logger.error(f"高級緩存預熱失敗: {e}")

def get_cache_stats():
    """獲取緩存統計信息"""
    return _global_cache.get_stats()

def clear_cache():
    """清空所有緩存"""
    _global_cache.l1_cache.clear()
    _global_cache.l2_cache.clear()
    _global_cache.l3_cache.clear()
    logger.info("所有緩存已清空")
