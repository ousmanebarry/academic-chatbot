import time
import asyncio
import logging
from typing import Dict, Any, List
from collections import defaultdict, deque
from functools import wraps

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Performance monitoring and optimization utilities"""
    
    def __init__(self):
        self.metrics = defaultdict(deque)
        self.request_times = deque(maxlen=1000)
        self.active_requests = 0
        self.max_concurrent_requests = 100
        
    def track_request_time(self, duration_ms: float):
        """Track request timing"""
        self.request_times.append(duration_ms)
        
    def get_average_response_time(self) -> float:
        """Get average response time"""
        if not self.request_times:
            return 0.0
        return sum(self.request_times) / len(self.request_times)
    
    def get_p95_response_time(self) -> float:
        """Get 95th percentile response time"""
        if not self.request_times:
            return 0.0
        sorted_times = sorted(self.request_times)
        index = int(0.95 * len(sorted_times))
        return sorted_times[index]
    
    async def limit_concurrent_requests(self):
        """Rate limiting for concurrent requests"""
        if self.active_requests >= self.max_concurrent_requests:
            await asyncio.sleep(0.1)
            return await self.limit_concurrent_requests()
        
        self.active_requests += 1
        return True
    
    def release_request(self):
        """Release a request slot"""
        self.active_requests = max(0, self.active_requests - 1)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        return {
            "average_response_time": self.get_average_response_time(),
            "p95_response_time": self.get_p95_response_time(),
            "active_requests": self.active_requests,
            "total_requests": len(self.request_times),
            "performance_status": "healthy" if self.get_average_response_time() < 200 else "degraded"
        }

# Global performance monitor
monitor = PerformanceMonitor()

def performance_tracking(func):
    """Decorator to track function performance"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            # await monitor.limit_concurrent_requests()
            result = await func(*args, **kwargs)
            return result
        finally:
            duration_ms = (time.time() - start_time) * 1000
            monitor.track_request_time(duration_ms)
            # monitor.release_request()
    
    return wrapper
