import time
import threading


class TokenBucket:
    """
    Thread-safe token bucket rate limiter.

    Parameters
    ----------
    rate : float
        Tokens added to the bucket per second.
    capacity : float
        Maximum number of tokens the bucket can hold.
    """

    def __init__(self, rate: float, capacity: float) -> None:
        if rate <= 0:
            raise ValueError("rate must be positive")
        if capacity <= 0:
            raise ValueError("capacity must be positive")

        self.rate = float(rate)
        self.capacity = float(capacity)
        self._tokens = float(capacity)
        self._last_update = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> float:
        now = time.monotonic()
        elapsed = now - self._last_update
        self._last_update = now
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        return self._tokens

    def allow(self, amount: float = 1.0) -> bool:
        """
        Attempt to consume ``amount`` tokens.

        Returns True if the request is allowed, False otherwise.
        """
        if amount <= 0:
            return True

        with self._lock:
            self._refill()
            if self._tokens >= amount:
                self._tokens -= amount
                return True
            return False

    def retry_after(self, amount: float = 1.0) -> float:
        """
        Return the number of seconds until ``amount`` tokens are available.
        Returns 0.0 if the request can be allowed immediately.
        """
        if amount <= 0:
            return 0.0

        with self._lock:
            self._refill()
            if self._tokens >= amount:
                return 0.0
            deficit = amount - self._tokens
            return deficit / self.rate


if __name__ == "__main__":
    import math

    bucket = TokenBucket(rate=10.0, capacity=10.0)

    assert bucket.allow(10.0) is True
    assert bucket.allow(1.0) is False
    assert math.isclose(bucket.retry_after(1.0), 0.1, rel_tol=1e-9)

    time.sleep(0.15)
    assert bucket.allow(1.0) is True

    # Ensure retry_after drops to 0 when tokens are available.
    full_bucket = TokenBucket(rate=100.0, capacity=100.0)
    assert full_bucket.retry_after(50.0) == 0.0
    assert full_bucket.allow(50.0) is True