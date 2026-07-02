import time
import threading

class TokenBucket:
    def __init__(self, rate: float, capacity: float) -> None:
        if rate <= 0:
            raise ValueError("Rate must be positive")
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
            
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.monotonic()
        self.lock = threading.Lock()

    def _refill(self, now: float) -> None:
        elapsed = now - self.last_update
        if elapsed > 0:
            new_tokens = elapsed * self.rate
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_update = now

    def allow(self, amount: float = 1.0) -> bool:
        if amount > self.capacity:
            return False
            
        with self.lock:
            now = time.monotonic()
            self._refill(now)
            
            if self.tokens >= amount:
                self.tokens -= amount
                return True
            return False

    def retry_after(self, amount: float = 1.0) -> float:
        if amount > self.capacity:
            return float('inf')
            
        with self.lock:
            now = time.monotonic()
            self._refill(now)
            
            if self.tokens >= amount:
                return 0.0
                
            missing_tokens = amount - self.tokens
            return missing_tokens / self.rate

if __name__ == "__main__":
    bucket = TokenBucket(rate=2.0, capacity=5.0)
    
    # Initially we have 5 tokens, we consume 5
    assert bucket.allow(3.0) is True
    assert bucket.allow(2.0) is True
    
    # The bucket should now be empty
    assert bucket.allow(1.0) is False
    
    # We need 1 token, rate is 2.0/s, so we need to wait 0.5s
    wait_time = bucket.retry_after(1.0)
    assert wait_time > 0.0 and wait_time <= 0.5
    
    # Wait for the token to replenish
    time.sleep(wait_time + 0.01)
    
    # We should now be able to consume 1 token
    assert bucket.allow(1.0) is True
    assert bucket.allow(10.0) is False