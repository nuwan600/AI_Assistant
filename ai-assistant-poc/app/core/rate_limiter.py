from app.core.config import settings
import time
import asyncio
from fastapi import HTTPException, status

class TokenBucketRateLimiter:
    def __init__(self, capacity: int, fill_rate: float):
        self.capacity = capacity
        self.fill_rate = fill_rate
        self.user_buckets = {}
        self._lock = asyncio.Lock()

    async def check_rate_limit(self, user_id: str):
        async with self._lock:
            now = time.time()
            if user_id not in self.user_buckets:
                self.user_buckets[user_id] = {"tokens": self.capacity, "last_updated": now}

            bucket = self.user_buckets[user_id]
            elapsed = now - bucket["last_updated"]
            
            # Refill tokens
            bucket["tokens"] = min(self.capacity, bucket["tokens"] + elapsed * self.fill_rate)
            bucket["last_updated"] = now

            if bucket["tokens"] >= 1.0:
                bucket["tokens"] -= 1.0
                return True
            else:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Try again later."
                )

rate_limiter = TokenBucketRateLimiter(
    capacity=settings.RATE_LIMIT_TOKENS, 
    fill_rate=settings.RATE_LIMIT_FILL_RATE
)