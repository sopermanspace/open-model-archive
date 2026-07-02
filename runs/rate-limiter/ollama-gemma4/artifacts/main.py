import time
import threading
from typing import ClassVar, Optional

class TokenBucket:
    """
    A thread-safe implementation of a token bucket rate limiter.
    """
    def __init__(self, rate: float, capacity: float):
        """
        Initializes the token bucket.

        Args:
            rate (float): The refill rate in tokens per second.
            capacity (float): The maximum number of tokens the bucket can hold.
        """
        if rate <= 0 or capacity <= 0:
            raise ValueError("Rate and Capacity must be positive.")

        self._rate: ClassVar[float] = rate  # Tokens added per second
        self._capacity: ClassVar[float] = capacity
        
        # Current number of tokens in the bucket
        self._tokens: float = capacity
        
        # Time when the token count was last calculated/refilled (in seconds)
        self._last_time: ClassVar[float] = time.monotonic()
        
        # Lock for thread safety
        self._lock: threading.Lock = threading.Lock()

    def _refill(self, now: float):
        """Internal method to update token count based on elapsed time."""
        elapsed_time = now - self._last_time
        if elapsed_time < 0:
            # Should not happen if clock monotonic is used correctly, but good safeguard
            return

        tokens_to_add = elapsed_time * self._rate
        self._tokens = min(self._capacity, self._tokens + tokens_to_add)
        self._last_time = now

    def allow(self, amount: float = 1.0) -> bool:
        """
        Attempts to consume tokens. Updates the token count if successful.

        Args:
            amount (float): The number of tokens required for this request.

        Returns:
            bool: True if enough tokens were available and consumed, False otherwise.
        """
        if amount <= 0:
            return True # Edge case: zero requirement always succeeds
        
        with self._lock:
            now = time.monotonic()
            self._refill(now)

            if self._tokens >= amount:
                self._tokens -= amount
                # print(f"  [SUCCESS] Tokens remaining: {self._tokens:.2f}") # Debugging helper
                return True
            else:
                # print(f"  [FAIL] Not enough tokens. Available: {self._tokens:.2f}, Required: {amount:.2f}") # Debugging helper
                return False

    def retry_after(self, amount: float = 1.0) -> float:
        """
        Calculates the time (in seconds) until 'amount' tokens are expected to be available.

        Args:
            amount (float): The number of tokens required.

        Returns:
            float: Seconds to wait. Returns 0.0 if enough tokens are already available.
        """
        if amount <= 0:
            return 0.0

        with self._lock:
            now = time.monotonic()
            self._refill(now) # Ensure the current state is up-to-date

            tokens_needed = amount - self._tokens
            
            if tokens_needed <= 0:
                return 0.0  # Already enough tokens
            
            # Time needed = Tokens needed / Rate (tokens/second)
            time_needed = tokens_needed / self._rate
            return time_needed

def worker(limiter: TokenBucket, thread_id: int, attempts: list):
    """Worker function for testing thread safety."""
    print(f"Thread {thread_id}: Starting burst.")
    for i in range(10):
        time.sleep(0.05) # Simulate network delay
        if limiter.allow():
            attempts[thread_id].append("Allowed")
        else:
            attempts[thread_id].append("Blocked")

def main_demo():
    """Minimal demonstration and assertion checks."""
    print("\n--- TokenBucket Demonstration ---")

    # Scenario 1: Basic test (High rate, high capacity)
    RATE = 5.0  # 5 tokens/second
    CAPACITY = 10.0
    limiter_basic = TokenBucket(rate=RATE, capacity=CAPACITY)
    print(f"\n[Scenario 1] Rate={RATE}/s, Capacity={CAPACITY}. Testing burst.")

    # Consume tokens until it fails (should fail around 10 attempts total)
    allowed_count = 0
    for i in range(15):
        if limiter_basic.allow():
            allowed_count += 1
            print(f"Request {i+1}: Allowed.")
        else:
            print(f"Request {i+1}: Blocked.")

    assert allowed_count >= int(CAPACITY), "Initial burst failure: Should allow at least CAPACITY requests."

    # Scenario 2: Rate limiting test (Low rate, low capacity)
    RATE_SLOW = 0.5 # 0.5 tokens/second (1 token every 2 seconds)
    CAPACITY_SMALL = 2.0
    limiter_slow = TokenBucket(rate=RATE_SLOW, capacity=CAPACITY_SMALL)
    print(f"\n[Scenario 2] Rate={RATE_SLOW}/s, Capacity={CAPACITY_SMALL}. Testing wait.")

    # 1. Allow initial burst (2 tokens)
    assert limiter_slow.allow() is True
    allowed = 1
    assert limiter_slow.allow() is True
    allowed += 1
    print(f"Initial Burst: Allowed {allowed} requests.")

    # 2. Check retry time for a single token (requires > 0 tokens)
    wait_time = limiter_slow.retry_after(amount=1.0)
    print(f"Waiting time needed for 1 token: {wait_time:.3f} seconds (Expected ~2.0s).")
    # Allow a small tolerance due to system timing
    assert wait_time > 1.5 and wait_time < 2.5, "Retry after calculation incorrect."

    # 3. Wait for refill and re-check allow status
    print("Waiting 2.2 seconds...")
    time.sleep(2.2) # Should be enough time to generate at least one token (0.5 * 2.2 = 1.1 tokens)

    if limiter_slow.allow():
        print("Request after waiting: Allowed.")
        assert True
    else:
        raise AssertionError("Expected token refill, but request was blocked.")


# --- Thread Safety Demo ---
def main_thread_demo():
    """Demonstrates thread safety."""
    # Limiter configured to allow 10 tokens total over time at a rate of 2/s.
    SHARED_LIMITER = TokenBucket(rate=2.0, capacity=10.0)
    num_threads = 5
    attempts: list[list[str]] = [[] for _ in range(num_threads)]

    print("\n[Scenario 3] Thread Safety Test (Shared Resource)")
    print("Running multiple threads concurrently accessing the same limiter...")

    # Create and start threads
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(SHARED_LIMITER, i, attempts))
        threads.append(t)
        t.start()

    # Wait for all threads to complete
    for t in threads:
        t.join()

    # Verification check
    total_allowed = sum(1 for attempt in attempts for status in attempt if status == "Allowed")
    print(f"\n--- Results ---")
    print(f"Total Requests Attempted per thread (approx): {num_threads * 10}")
    print(f"Total Allowed Requests across all threads: {total_allowed}")
    
    # Since the capacity is only 10, even with refills, the burst capability should limit access greatly.
    # We assert that a high number of requests were processed but that the mechanism didn't crash or allow unlimited access due to race conditions.
    assert total_allowed <= 30, "The token counter seems corrupted (too many tokens allowed)."


if __name__ == "__main__":
    main_demo()
    main_thread_demo()