import time
import threading

class TokenBucket:
    def __init__(self, rate: float, capacity: float) -> None:
        if rate <= 0 or capacity <= 0:
            raise ValueError("Rate and capacity must be greater than zero.")
        self.rate: float = rate
        self.capacity: float = capacity
        self.tokens: float = capacity
        self.last_refill: float = time.monotonic()
        self.lock: threading.Lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now

    def allow(self, amount: float = 1.0) -> bool:
        if amount > self.capacity:
            return False
            
        with self.lock:
            self._refill()
            if self.tokens >= amount:
                self.tokens -= amount
                return True
            return False

    def retry_after(self, amount: float = 1.0) -> float:
        if amount > self.capacity:
            return float('inf')
            
        with self.lock:
            self._refill()
            if self.tokens >= amount:
                return 0.0
            missing_tokens = amount - self.tokens
            return missing_tokens / self.rate

if __name__ == "__main__":
    bucket = TokenBucket(rate=2.0, capacity=5.0)
    
    # Initial capacity is 5.0, should allow 3.0 + 2.0
    assert bucket.allow(3.0) is True
    assert bucket.allow(2.0) is True
    
    # Now it should be near empty, so 1.0 will fail
    assert bucket.allow(1.0) is False
    
    # Needs 1 token, rate is 2/sec -> approx 0.5 seconds wait
    wait_time = bucket.retry_after(1.0)
    assert 0.4 < wait_time <= 0.5
    
    # Sleep to let bucket refill
    time.sleep(0.55)
    
    # Should now allow 1.0
    assert bucket.allow(1.0) is True
    
    print("All tests passed.")