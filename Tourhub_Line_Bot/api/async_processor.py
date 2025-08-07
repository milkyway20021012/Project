"""
異步處理系統
用於處理耗時的數據庫查詢和API調用
"""

import asyncio
import threading
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional
from functools import wraps
import queue

logger = logging.getLogger(__name__)

class AsyncProcessor:
    """異步處理器"""
    
    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.task_queue = queue.Queue()
        self.results = {}
        self.running = True
        
        # 啟動後台處理線程
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        
        logger.info(f"異步處理器已啟動，最大工作線程數: {max_workers}")
    
    def _worker(self):
        """後台工作線程"""
        while self.running:
            try:
                # 從隊列獲取任務
                if not self.task_queue.empty():
                    task = self.task_queue.get(timeout=1)
                    self._process_task(task)
                else:
                    time.sleep(0.1)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"異步處理器工作線程錯誤: {e}")
    
    def _process_task(self, task: Dict[str, Any]):
        """處理單個任務"""
        try:
            task_id = task['id']
            func = task['func']
            args = task.get('args', ())
            kwargs = task.get('kwargs', {})
            callback = task.get('callback')
            
            # 執行任務
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # 存儲結果
            self.results[task_id] = {
                'result': result,
                'execution_time': execution_time,
                'completed_at': time.time()
            }
            
            # 執行回調
            if callback:
                try:
                    callback(result)
                except Exception as e:
                    logger.error(f"任務回調執行失敗: {e}")
            
            logger.debug(f"異步任務 {task_id} 完成，耗時 {execution_time:.3f}s")
            
        except Exception as e:
            logger.error(f"異步任務處理失敗: {e}")
            self.results[task['id']] = {
                'error': str(e),
                'completed_at': time.time()
            }
    
    def submit_task(self, func: Callable, *args, callback: Optional[Callable] = None, **kwargs) -> str:
        """提交異步任務"""
        task_id = f"task_{int(time.time() * 1000)}_{id(func)}"
        
        task = {
            'id': task_id,
            'func': func,
            'args': args,
            'kwargs': kwargs,
            'callback': callback,
            'submitted_at': time.time()
        }
        
        self.task_queue.put(task)
        logger.debug(f"異步任務 {task_id} 已提交")
        
        return task_id
    
    def get_result(self, task_id: str, timeout: float = 5.0) -> Optional[Any]:
        """獲取任務結果"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if task_id in self.results:
                result_data = self.results.pop(task_id)
                if 'error' in result_data:
                    raise Exception(result_data['error'])
                return result_data['result']
            time.sleep(0.01)
        
        return None
    
    def batch_execute(self, tasks: List[Dict[str, Any]], timeout: float = 10.0) -> List[Any]:
        """批量執行任務"""
        futures = []
        
        for task in tasks:
            future = self.executor.submit(
                task['func'], 
                *task.get('args', ()), 
                **task.get('kwargs', {})
            )
            futures.append(future)
        
        results = []
        for future in as_completed(futures, timeout=timeout):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"批量任務執行失敗: {e}")
                results.append(None)
        
        return results
    
    def shutdown(self):
        """關閉異步處理器"""
        self.running = False
        self.executor.shutdown(wait=True)
        logger.info("異步處理器已關閉")

# 全局異步處理器實例
_async_processor = AsyncProcessor()

def async_task(timeout: float = 5.0):
    """異步任務裝飾器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 檢查是否需要異步執行
            if hasattr(threading.current_thread(), '_async_mode') and threading.current_thread()._async_mode:
                # 已在異步模式中，直接執行
                return func(*args, **kwargs)
            
            # 提交異步任務
            task_id = _async_processor.submit_task(func, *args, **kwargs)
            
            # 等待結果
            result = _async_processor.get_result(task_id, timeout)
            if result is None:
                logger.warning(f"異步任務 {func.__name__} 超時")
                # 超時時同步執行
                return func(*args, **kwargs)
            
            return result
        return wrapper
    return decorator

def preload_data():
    """預加載數據（異步）"""
    logger.info("開始異步預加載數據...")
    
    preload_tasks = [
        {
            'func': _preload_leaderboard,
            'args': (),
            'kwargs': {}
        },
        {
            'func': _preload_popular_locations,
            'args': (),
            'kwargs': {}
        },
        {
            'func': _preload_rank_details,
            'args': (),
            'kwargs': {}
        }
    ]
    
    try:
        results = _async_processor.batch_execute(preload_tasks, timeout=15.0)
        success_count = sum(1 for r in results if r is not None)
        logger.info(f"異步預加載完成，成功 {success_count}/{len(preload_tasks)} 個任務")
    except Exception as e:
        logger.error(f"異步預加載失敗: {e}")

def _preload_leaderboard():
    """預加載排行榜數據"""
    try:
        from .database_utils import get_leaderboard_from_database
        data = get_leaderboard_from_database()
        logger.info("排行榜數據預加載完成")
        return data
    except Exception as e:
        logger.error(f"排行榜數據預加載失敗: {e}")
        return None

def _preload_popular_locations():
    """預加載熱門地區數據"""
    try:
        from .database_utils import get_trips_by_location
        locations = ["東京", "大阪", "京都", "沖繩", "北海道"]
        
        for location in locations:
            get_trips_by_location(location, 5)
        
        logger.info("熱門地區數據預加載完成")
        return True
    except Exception as e:
        logger.error(f"熱門地區數據預加載失敗: {e}")
        return None

def _preload_rank_details():
    """預加載排行榜詳細數據"""
    try:
        from .database_utils import get_leaderboard_rank_details
        
        for rank in range(1, 6):
            get_leaderboard_rank_details(rank)
        
        logger.info("排行榜詳細數據預加載完成")
        return True
    except Exception as e:
        logger.error(f"排行榜詳細數據預加載失敗: {e}")
        return None

def get_processor_stats():
    """獲取處理器統計信息"""
    return {
        "max_workers": _async_processor.max_workers,
        "queue_size": _async_processor.task_queue.qsize(),
        "pending_results": len(_async_processor.results),
        "running": _async_processor.running
    }

# 在模塊關閉時清理資源
import atexit
atexit.register(_async_processor.shutdown)
