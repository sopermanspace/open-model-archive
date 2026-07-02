import threading
import time


class TokenBucket:
    """Thread-safe token bucket rate limiter."""

    def __init__(self, rate: float, capacity: float) -> None:
        if rate <= 0:
            raise ValueError("rate must be > 0")
        if capacity <= 0:
            raise ValueError("capacity must be > 0")

        self.rate: float = float(rate)
        self.capacity: float = float(capacity)
        self._tokens: float = float(capacity)
        self._last_update: float = time.monotonic()
        self._lock: threading.Lock = threading.Lock()

    def _replenish(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_update
        if elapsed:
            self._tokens = min(
                self.capacity, self._tokens + self.rate * elapsed
            )
            self._last_update = now

    def allow(self, amount: float = 1.0) -> bool:
        """Return True if the request is allowed, False if rate limited."""
        if amount <= 0:
            raise ValueError("amount must be > 0")

        with self._lock:
            self._replenish()
            if amount > self.capacity:
                return False
            if self._tokens >= amount:
                self._tokens -= amount
                return True
            return False

    def retry_after(self, amount: float = 1.0) -> float:
        """Seconds until `amount` tokens are available (0.0 if allowed now)."""
        if amount <= 0:
            raise ValueError("amount must be > 0")

        with self._lock:
            self._replenish()
            if amount > self.capacity:
                return float("inf")
            deficit = amount - self._tokens
            return 0.0 if deficit <= 0 else deficit / self.rate


if __name__ == "__main__":
    bucket = TokenBucket(rate=5.0, capacity=5.0)

    # A full bucket should allow the initial burst.
    assert bucket.allow(5.0) is True
    assert bucket.allow(1.0) is False

    # Should take ~0.2 seconds to accumulate one token.
    wait = bucket.retry_after(1.0)
    assert abs(wait - 0.2) < 0.01, wait

    time.sleep(wait + 0.05)
    assert bucket.allow(1.0) is True

    # Already has enough tokens for a tiny request.
    assert bucket.retry_after(0.1) == 0.0

    # Requests larger than the bucket capacity can never be satisfied.
    assert bucket.allow(100.0) is False
    assert bucket.retry_after(100.0) == float("inf")