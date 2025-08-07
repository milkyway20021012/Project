"""
性能監控系統
實施響應時間監控、錯誤追蹤、性能指標收集
"""

import time
import threading
import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from functools import wraps
import statistics
import json

logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """性能指標收集器"""
    
    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples
        self.metrics = defaultdict(lambda: {
            'response_times': deque(maxlen=max_samples),
            'error_count': 0,
            'success_count': 0,
            'total_requests': 0,
            'last_error': None,
            'last_error_time': None
        })
        self.lock = threading.RLock()
        
        # 全局統計
        self.global_stats = {
            'start_time': time.time(),
            'total_requests': 0,
            'total_errors': 0,
            'avg_response_time': 0,
            'peak_response_time': 0,
            'min_response_time': float('inf')
        }
    
    def record_request(self, endpoint: str, response_time: float, success: bool = True, error: str = None):
        """記錄請求指標"""
        with self.lock:
            metric = self.metrics[endpoint]
            
            # 記錄響應時間
            metric['response_times'].append(response_time)
            metric['total_requests'] += 1
            
            # 記錄成功/失敗
            if success:
                metric['success_count'] += 1
            else:
                metric['error_count'] += 1
                metric['last_error'] = error
                metric['last_error_time'] = time.time()
            
            # 更新全局統計
            self.global_stats['total_requests'] += 1
            if not success:
                self.global_stats['total_errors'] += 1
            
            # 更新響應時間統計
            if response_time > self.global_stats['peak_response_time']:
                self.global_stats['peak_response_time'] = response_time
            
            if response_time < self.global_stats['min_response_time']:
                self.global_stats['min_response_time'] = response_time
            
            # 計算平均響應時間
            all_times = []
            for m in self.metrics.values():
                all_times.extend(list(m['response_times']))
            
            if all_times:
                self.global_stats['avg_response_time'] = statistics.mean(all_times)
    
    def get_endpoint_stats(self, endpoint: str) -> Dict[str, Any]:
        """獲取特定端點的統計信息"""
        with self.lock:
            if endpoint not in self.metrics:
                return {}
            
            metric = self.metrics[endpoint]
            response_times = list(metric['response_times'])
            
            if not response_times:
                return {
                    'endpoint': endpoint,
                    'total_requests': metric['total_requests'],
                    'success_count': metric['success_count'],
                    'error_count': metric['error_count'],
                    'error_rate': 0,
                    'avg_response_time': 0,
                    'min_response_time': 0,
                    'max_response_time': 0,
                    'p95_response_time': 0,
                    'last_error': metric['last_error'],
                    'last_error_time': metric['last_error_time']
                }
            
            # 計算統計指標
            avg_time = statistics.mean(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            p95_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max_time
            error_rate = metric['error_count'] / metric['total_requests'] if metric['total_requests'] > 0 else 0
            
            return {
                'endpoint': endpoint,
                'total_requests': metric['total_requests'],
                'success_count': metric['success_count'],
                'error_count': metric['error_count'],
                'error_rate': error_rate,
                'avg_response_time': avg_time,
                'min_response_time': min_time,
                'max_response_time': max_time,
                'p95_response_time': p95_time,
                'last_error': metric['last_error'],
                'last_error_time': metric['last_error_time']
            }
    
    def get_global_stats(self) -> Dict[str, Any]:
        """獲取全局統計信息"""
        with self.lock:
            uptime = time.time() - self.global_stats['start_time']
            
            return {
                'uptime_seconds': uptime,
                'total_requests': self.global_stats['total_requests'],
                'total_errors': self.global_stats['total_errors'],
                'error_rate': self.global_stats['total_errors'] / max(self.global_stats['total_requests'], 1),
                'avg_response_time': self.global_stats['avg_response_time'],
                'peak_response_time': self.global_stats['peak_response_time'],
                'min_response_time': self.global_stats['min_response_time'] if self.global_stats['min_response_time'] != float('inf') else 0,
                'requests_per_second': self.global_stats['total_requests'] / max(uptime, 1)
            }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """獲取所有統計信息"""
        with self.lock:
            endpoint_stats = {}
            for endpoint in self.metrics.keys():
                endpoint_stats[endpoint] = self.get_endpoint_stats(endpoint)
            
            return {
                'global': self.get_global_stats(),
                'endpoints': endpoint_stats
            }

# 全局性能監控實例
_performance_monitor = PerformanceMetrics()

def monitor_performance(endpoint_name: str = None):
    """性能監控裝飾器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 確定端點名稱
            endpoint = endpoint_name or func.__name__
            
            # 記錄開始時間
            start_time = time.time()
            success = True
            error_msg = None
            
            try:
                # 執行函數
                result = func(*args, **kwargs)
                return result
            
            except Exception as e:
                success = False
                error_msg = str(e)
                logger.error(f"性能監控捕獲錯誤 {endpoint}: {e}")
                raise
            
            finally:
                # 記錄性能指標
                response_time = time.time() - start_time
                _performance_monitor.record_request(endpoint, response_time, success, error_msg)
                
                # 記錄慢查詢
                if response_time > 2.0:  # 超過2秒的請求
                    logger.warning(f"慢查詢檢測: {endpoint} 耗時 {response_time:.3f}s")
        
        return wrapper
    return decorator

class HealthChecker:
    """健康檢查器"""
    
    def __init__(self):
        self.checks = {}
        self.lock = threading.RLock()
    
    def register_check(self, name: str, check_func: callable, timeout: float = 5.0):
        """註冊健康檢查"""
        with self.lock:
            self.checks[name] = {
                'func': check_func,
                'timeout': timeout,
                'last_check': None,
                'last_result': None,
                'last_error': None
            }
    
    def run_check(self, name: str) -> Dict[str, Any]:
        """運行單個健康檢查"""
        if name not in self.checks:
            return {'status': 'unknown', 'error': 'Check not found'}
        
        check = self.checks[name]
        start_time = time.time()
        
        try:
            # 執行檢查
            result = check['func']()
            response_time = time.time() - start_time
            
            # 更新檢查記錄
            with self.lock:
                check['last_check'] = time.time()
                check['last_result'] = 'healthy'
                check['last_error'] = None
            
            return {
                'status': 'healthy',
                'response_time': response_time,
                'details': result
            }
        
        except Exception as e:
            response_time = time.time() - start_time
            
            # 更新檢查記錄
            with self.lock:
                check['last_check'] = time.time()
                check['last_result'] = 'unhealthy'
                check['last_error'] = str(e)
            
            return {
                'status': 'unhealthy',
                'response_time': response_time,
                'error': str(e)
            }
    
    def run_all_checks(self) -> Dict[str, Any]:
        """運行所有健康檢查"""
        results = {}
        overall_status = 'healthy'
        
        for name in self.checks.keys():
            result = self.run_check(name)
            results[name] = result
            
            if result['status'] != 'healthy':
                overall_status = 'unhealthy'
        
        return {
            'overall_status': overall_status,
            'checks': results,
            'timestamp': time.time()
        }

# 全局健康檢查器
_health_checker = HealthChecker()

def register_health_check(name: str, timeout: float = 5.0):
    """健康檢查註冊裝飾器"""
    def decorator(func):
        _health_checker.register_check(name, func, timeout)
        return func
    return decorator

# 註冊基本健康檢查
@register_health_check('database')
def check_database_health():
    """檢查數據庫健康狀態"""
    try:
        from .database_utils import get_database_connection
        with get_database_connection() as connection:
            if connection:
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                return {'status': 'connected', 'test_query': 'passed'}
            else:
                raise Exception("無法獲取數據庫連接")
    except Exception as e:
        raise Exception(f"數據庫健康檢查失敗: {e}")

@register_health_check('cache')
def check_cache_health():
    """檢查緩存健康狀態"""
    try:
        from .advanced_cache import get_cache_stats
        stats = get_cache_stats()
        return {
            'hit_rate': stats.get('hit_rate', 0),
            'total_requests': stats.get('total_requests', 0)
        }
    except Exception as e:
        raise Exception(f"緩存健康檢查失敗: {e}")

def get_performance_stats():
    """獲取性能統計信息"""
    return _performance_monitor.get_all_stats()

def get_health_status():
    """獲取健康狀態"""
    return _health_checker.run_all_checks()
