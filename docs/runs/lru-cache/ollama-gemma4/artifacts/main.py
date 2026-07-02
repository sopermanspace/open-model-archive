from collections import OrderedDict
from typing import Any, Dict

class LRUCache:
    """
    Implements an LRU Cache using collections.OrderedDict to maintain 
    O(1) time complexity for both get and put operations.
    """

    def __init__(self, capacity: int):
        """
        Initializes the cache with a given capacity.
        Capacity must be a positive integer.
        """
        if capacity <= 0:
            raise ValueError("Capacity must be a positive integer.")
            
        self.capacity = capacity
        # OrderedDict stores key-value pairs and maintains insertion order.
        # We use it to track usage: MRU is at the end, LRU is at the start.
        self._cache: OrderedDict[int, int] = OrderedDict()

    def get(self, key: int) -> int:
        """
        Returns the value associated with the key if present. 
        Marks the key as recently used (MRU). Returns -1 if not found.
        Time complexity: O(1)
        """
        if key not in self._cache:
            return -1
        
        # Accessing the item makes it MRU by moving it to the end of the OrderedDict.
        self._cache[key] 
        self._cache.move_to_end(key)
        
        return self._cache[key]

    def put(self, key: int, value: int) -> None:
        """
        Inserts or updates a key-value pair. If the cache exceeds capacity, 
        the least recently used item is evicted.
        Time complexity: O(1)
        """
        if self.capacity == 0:
            return # Cannot store anything if capacity is zero

        # 1. Update existing entry or insert new one (always moves it to MRU)
        self._cache[key] = value
        self._cache.move_to_end(key)
        
        # 2. Check for overflow and evict LRU item if necessary
        if len(self._cache) > self.capacity:
            # popitem(last=False) removes the item from the beginning (the oldest/LRU item).
            # We discard the key returned, as we only care about eviction logic.
            self._cache.popitem(last=False)


if __name__ == "__main__":
    print("--- LRUCache Test Suite ---")

    # --- Test Case 1: Basic PUT and GET functionality (Capacity 2) ---
    print("\n[Test 1: Basic Flow]")
    cache = LRUCache(2)
    
    # Put a, b. Cache state: [a] -> [b]. Capacity used: 2/2.
    cache.put(1, 10);
    cache.put(2, 20);
    assert cache._cache == OrderedDict([(1, 10), (2, 20)]), "Initial put failed"

    # Get a. Moves 'a' to MRU. Cache state: [b] -> [a].
    val_a = cache.get(1)
    print(f"Get key 1: {val_a}")
    assert val_a == 10, "Get 1 failed"
    # Verify order change (2 should now be the LRU item at index 0)
    assert list(cache._cache.keys()) == [2, 1], "Order changed incorrectly after get"

    # Put c. Capacity exceeded. Evicts B (the current LRU). Cache state: [a] -> [c].
    print("Putting key 3...")
    cache.put(3, 30)
    assert cache._cache == OrderedDict([(1, 10), (3, 30)]), "Eviction failed or order incorrect"

    # Check if the evicted item is gone
    val_b = cache.get(2)
    print(f"Get key 2: {val_b}")
    assert val_b == -1, "Key 2 should have been evicted"

    # --- Test Case 2: Update and Hit/Miss Cycle (Capacity 3) ---
    print("\n[Test 2: Update & Eviction]")
    cache = LRUCache(3)
    
    # Put x, y, z. Cache state: [x] -> [y] -> [z].
    cache.put('x', 1);
    cache.put('y', 2);
    cache.put('z', 3);

    # Hit 'x'. Moves x to MRU. State: [y] -> [z] -> [x].
    val_x = cache.get('x')
    print(f"Get key 'x': {val_x}")
    assert val_x == 1, "Hit failed"
    assert list(cache._cache.keys()) == ['y', 'z', 'x'], "Order incorrect after hit"

    # Put w. Evicts LRU item: 'y'. State: [z] -> [x] -> [w].
    print("Putting key 'w'...")
    cache.put('w', 4)
    assert list(cache._cache.keys()) == ['z', 'x', 'w'], "Eviction/Order incorrect on put"

    # Miss check
    val_y = cache.get('y')
    print(f"Get key 'y': {val_y}")
    assert val_y == -1, "Key 'y' should be evicted"
    
    # Update 'z'. State: [x] -> [w] -> [z].
    cache.put('z', 30);
    assert list(cache._cache.keys()) == ['x', 'w', 'z'], "Order incorrect after update"

    print("\nAll LRUCache tests passed successfully!")