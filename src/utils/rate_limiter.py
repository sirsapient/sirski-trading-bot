import asyncio
import time
from collections import defaultdict
from typing import Dict

class RateLimiter:
    """Rate limiter to prevent API abuse."""
    
    def __init__(self):
        self.call_times: Dict[str, list] = defaultdict(list)
        self.limits = {
            "solana_rpc": (100, 60),      # 100 calls per 60 seconds
            "base_rpc": (50, 60),         # 50 calls per 60 seconds  
            "jupiter_api": (200, 60),     # 200 calls per 60 seconds
            "uniswap_api": (100, 60),     # 100 calls per 60 seconds
        }
    
    async def wait_if_needed(self, api_name: str):
        """Wait if we're hitting rate limits."""
        if api_name not in self.limits:
            return
        
        max_calls, window = self.limits[api_name]
        now = time.time()
        
        # Remove old calls outside the window
        self.call_times[api_name] = [
            call_time for call_time in self.call_times[api_name] 
            if now - call_time < window
        ]
        
        # Check if we need to wait
        if len(self.call_times[api_name]) >= max_calls:
            sleep_time = self.call_times[api_name][0] + window - now
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        # Record this call
        self.call_times[api_name].append(now) 