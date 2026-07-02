import time
import threading
from typing import Optional

class TokenBucket:
    """
    Implements a thread-safe token bucket rate limiter.

    Tokens are added to the bucket at a fixed 'rate' (tokens per second), 
    up to a maximum 'capacity'.
    """
    def __init__(self, rate: float, capacity: float):
        if rate <= 0 or capacity < 0:
            raise ValueError("Rate must be positive and capacity non-negative.")

        self.rate = rate          # Tokens added per second (R)
        self.capacity = capacity  # Maximum number of tokens (C)
        
        # Current state variables
        self._tokens = capacity   # Initial tokens are set to full capacity
        self._last_fill_time = time.monotonic() # Time of the last access
        
        # Synchronization mechanism
        self._lock = threading.Lock()

    def _fill(self):
        """Internal method to calculate and fill tokens based on elapsed time."""
        now = time.monotonic()
        time_elapsed = now - self._last_fill_time
        
        # Calculate tokens added since last check
        tokens_to_add = time_elapsed * self.rate
        
        # Update token count, ensuring it does not exceed capacity
        self._tokens = min(self._tokens + tokens_to_add, self.capacity)
        
        # Update the last fill time
        self._last_fill_time = now

    def allow(self, amount: float = 1.0) -> bool:
        """
        Attempts to consume 'amount' tokens.

        Returns True if successful (tokens consumed), False otherwise (rate limited).
        """
        if amount <= 0:
            return True # No cost for zero or negative amounts

        with self._lock:
            self._fill()  # Update token count first
            
            if self._tokens >= amount:
                # Consume tokens and update state
                self._tokens -= amount
                return True
            else:
                return False

    def retry_after(self, amount: float = 1.0) -> float:
        """
        Calculates the time (in seconds) until 'amount' of tokens are available.

        Returns 0.0 if enough tokens are already available now.
        """
        if amount <= 0:
            return 0.0

        with self._lock:
            # Ensure token count is up-to-date before calculating wait time
            self._fill()
            
            available = self._tokens
            needed = amount - available
            
            if needed <= 0:
                # Enough tokens are already present or overshot (shouldn't happen)
                return 0.0
            
            # Time required to generate the 'needed' tokens at the current rate
            time_wait = needed / self.rate
            return time_wait

def run_demo():
    """Runs a test demonstration of the TokenBucket."""
    print("--- Running Token Bucket Demo ---")
    
    # Setup: Rate of 5 tokens/sec, Capacity of 10 tokens
    LIMITER = TokenBucket(rate=5.0, capacity=10.0)

    # --- Test Case 1: Initial consumption (within capacity) ---
    print("\n[Test 1] Testing initial bursts (Capacity: 10)")
    allowed_burst = 8.0
    if LIMITER.allow(allowed_burst):
        print(f"  SUCCESS: Allowed burst of {allowed_burst} tokens.")
    else:
        print("  FAILURE: Should have allowed the initial burst.")

    # Current tokens remaining should be around 2.0
    assert LIMITER._tokens < 3.0 and LIMITER._tokens >= 0.0, "Token count mismatch after burst."


    # --- Test Case 2: Immediate Rate Limit Hit ---
    print("\n[Test 2] Testing immediate limit hit.")
    test_amount = 5.0
    if not LIMITER.allow(test_amount):
        print(f"  SUCCESS: Correctly blocked request requiring {test_amount} tokens (rate limited).")
    else:
        print("  FAILURE: Should have blocked the request.")

    # --- Test Case 3: Wait and Retry ---
    print("\n[Test 3] Waiting for rate limit recovery...")
    wait_time = 0.6 # Wait for about (5 - current) / 5 seconds, so wait > 0.2s
    
    start_time = time.monotonic()
    # Sleep to simulate time passing
    time.sleep(wait_time) 
    end_time = time.monotonic()

    if LIMITER.allow(test_amount):
        print("  FAILURE: Should still be rate limited after sleeping.")
    else:
        # Check if the calculated retry time is accurate
        retry = LIMITER.retry_after(test_amount)
        print(f"  SUCCESS: Blocked again (Need {test_amount} tokens). Recommended wait: {retry:.3f}s.")

    # Assert that waiting for required amount of tokens actually makes it possible
    required_wait_time = 1.0 # Wait enough time to ensure recovery
    if LIMITER.allow(test_amount):
        print("  FAILURE: Should still be blocked after sufficient wait time.")
    else:
        # Now simulate waiting long enough (more than required)
        initial_tokens_for_retry = 2.0 # Rough estimation before long sleep
        expected_wait = (5.0 - initial_tokens_for_retry) / 5.0 + 0.1 # Ensure we overshoot the wait time
        print(f"  [Simulated] Sleeping for {required_wait_time} seconds...")
        start_time = time.monotonic()
        time.sleep(required_wait_time)
        end_time = time.monotonic()

        if LIMITER.allow(test_amount):
            print("  SUCCESS: Request allowed after waiting long enough.")
        else:
            print("  FAILURE: Failed to allow request after sufficient wait time.")


if __name__ == "__main__":
    run_demo()