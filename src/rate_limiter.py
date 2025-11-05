"""
Rate Limiting System
Prevents hitting API limits
"""

import time
from collections import deque
from threading import Lock

class RateLimiter:
    def __init__(self, max_requests_per_minute: int = 60):
        self.max_rpm = max_requests_per_minute
        self.request_times = deque()
        self.lock = Lock()
    
    def wait_if_needed(self) -> float:
        with self.lock:
            now = time.time()
            
            # Clean old requests
            while self.request_times and self.request_times[0] < now - 60:
                self.request_times.popleft()
            
            # Check if at limit
            if len(self.request_times) >= self.max_rpm:
                oldest = self.request_times[0]
                sleep_time = 60 - (now - oldest) + 0.1
                print(f"⏳ Rate limit: waiting {sleep_time:.1f}s...")
                time.sleep(sleep_time)
                wait_duration = sleep_time
            else:
                wait_duration = 0.0
            
            self.request_times.append(now)
            return wait_duration
