#!/usr/bin/env python3
"""
Redis Cache implementation with decorators and history tracking
"""

import redis
import uuid
from typing import Union, Callable, Optional, Any
from functools import wraps

#!/usr/bin/env python3
"""
Redis Cache implementation
"""

class Cache:
    """
    Cache class for Redis operations
    """
    
    def __init__(self):
        """
        Initialize the Cache instance with Redis client and flush the database
        """
        self._redis = redis.Redis()
        self._redis.flushdb()
    
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """
        Store data in Redis with a random key
        
        Args:
            data: The data to store (can be str, bytes, int, or float)
            
        Returns:
            str: The randomly generated key
        """
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key
    
    def get(self, key: str, fn: Optional[Callable] = None) -> Any:
        """
        Get data from Redis and optionally convert it using a callable
        
        Args:
            key: The key to retrieve
            fn: Optional callable to convert the data
            
        Returns:
            The data, optionally converted by fn
        """
        data = self._redis.get(key)
        if data is None:
            return None
        if fn is not None:
            return fn(data)
        return data
    
    def get_str(self, key: str) -> Optional[str]:
        """
        Get data from Redis and convert it to string
        
        Args:
            key: The key to retrieve
            
        Returns:
            str: The data as a string, or None if key doesn't exist
        """
        return self.get(key, fn=lambda d: d.decode("utf-8"))
    
    def get_int(self, key: str) -> Optional[int]:
        """
        Get data from Redis and convert it to int
        
        Args:
            key: The key to retrieve
            
        Returns:
            int: The data as an integer, or None if key doesn't exist
        """
        return self.get(key, fn=int)
    
def count_calls(method: Callable) -> Callable:
    """
    Decorator that counts how many times a method is called
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        # Use the method's qualified name as the key
        key = method.__qualname__
        # Increment the count in Redis
        self._redis.incr(key)
        # Call the original method and return its result
        return method(self, *args, **kwargs)
    return wrapper


def call_history(method: Callable) -> Callable:
    """
    Decorator that stores the history of inputs and outputs for a function
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        # Create keys for inputs and outputs
        input_key = f"{method.__qualname__}:inputs"
        output_key = f"{method.__qualname__}:outputs"
        
        # Store input arguments as a string in Redis
        self._redis.rpush(input_key, str(args))
        
        # Execute the wrapped function to get the output
        output = method(self, *args, **kwargs)
        
        # Store the output in Redis
        self._redis.rpush(output_key, output)
        
        return output
    return wrapper


class Cache:
    """
    Cache class for Redis operations
    """
    
    def __init__(self):
        """
        Initialize the Cache instance
        """
        self._redis = redis.Redis()
        self._redis.flushdb()
    
    @count_calls
    @call_history
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """
        Store data in Redis with a random key
        
        Args:
            data: The data to store (str, bytes, int, or float)
            
        Returns:
            str: The randomly generated key
        """
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key
    
    def get(self, key: str, fn: Optional[Callable] = None) -> Any:
        """
        Get data from Redis and optionally convert it using a callable
        
        Args:
            key: The key to retrieve
            fn: Optional callable to convert the data
            
        Returns:
            The data, optionally converted by fn
        """
        data = self._redis.get(key)
        if data is None:
            return None
        if fn is not None:
            return fn(data)
        return data
    
    def get_str(self, key: str) -> Optional[str]:
        """
        Get data from Redis and convert it to string
        
        Args:
            key: The key to retrieve
            
        Returns:
            The data as a string, or None if key doesn't exist
        """
        return self.get(key, fn=lambda d: d.decode("utf-8"))
    
    def get_int(self, key: str) -> Optional[int]:
        """
        Get data from Redis and convert it to int
        
        Args:
            key: The key to retrieve
            
        Returns:
            The data as an integer, or None if key doesn't exist
        """
        return self.get(key, fn=int)


def replay(method: Callable) -> None:
    """
    Display the history of calls of a particular function
    
    Args:
        method: The method to replay the history for
    """
    # Get the Redis instance from the method's class
    cache_instance = method.__self__
    redis_instance = cache_instance._redis
    
    # Get the method's qualified name
    method_name = method.__qualname__
    
    # Get the call count
    call_count = redis_instance.get(method_name)
    if call_count is None:
        call_count = 0
    else:
        call_count = int(call_count)
    
    print(f"{method_name} was called {call_count} times:")
    
    # Get inputs and outputs
    input_key = f"{method_name}:inputs"
    output_key = f"{method_name}:outputs"
    
    inputs = redis_instance.lrange(input_key, 0, -1)
    outputs = redis_instance.lrange(output_key, 0, -1)
    
    # Display the history
    for input_args, output in zip(inputs, outputs):
        input_str = input_args.decode("utf-8")
        output_str = output.decode("utf-8")
        print(f"{method_name}(*{input_str}) -> {output_str}")


# Test functions to verify each check
def test_check_0():
    """Test Check 0: Basic Cache class and store method"""
    print("=== CHECK 0: Writing strings to Redis ===")
    cache = Cache()
    data = b"hello"
    key = cache.store(data)
    print(f"Generated key: {key}")
    
    local_redis = redis.Redis()
    retrieved = local_redis.get(key)
    print(f"Retrieved data: {retrieved}")
    assert retrieved == data, f"Expected {data}, got {retrieved}"
    print("✓ Check 0 passed")


def test_check_1():
    """Test Check 1: Reading from Redis and type conversion"""
    print("\n=== CHECK 1: Reading from Redis and recovering original type ===")
    cache = Cache()
    
    TEST_CASES = {
        b"foo": None,
        123: int,
        "bar": lambda d: d.decode("utf-8")
    }
    
    for value, fn in TEST_CASES.items():
        key = cache.store(value)
        result = cache.get(key, fn=fn)
        print(f"Stored: {value}, Retrieved: {result}")
        assert result == value, f"Expected {value}, got {result}"
    
    # Test get_str and get_int
    str_key = cache.store("test")
    int_key = cache.store(42)
    
    assert cache.get_str(str_key) == "test"
    assert cache.get_int(int_key) == 42
    print("✓ Check 1 passed")


def test_check_2():
    """Test Check 2: Incrementing values with count_calls decorator"""
    print("\n=== CHECK 2: Incrementing values ===")
    cache = Cache()
    
    cache.store(b"first")
    count_1 = cache.get(cache.store.__qualname__)
    print(f"After 1 call: {count_1}")
    
    cache.store(b"second")
    cache.store(b"third")
    count_3 = cache.get(cache.store.__qualname__)
    print(f"After 3 calls: {count_3}")
    
    assert count_1 == b'1', f"Expected b'1', got {count_1}"
    assert count_3 == b'3', f"Expected b'3', got {count_3}"
    print("✓ Check 2 passed")


def test_check_3():
    """Test Check 3: Storing lists with call_history decorator"""
    print("\n=== CHECK 3: Storing lists ===")
    cache = Cache()
    
    s1 = cache.store("first")
    s2 = cache.store("second")
    s3 = cache.store("third")
    
    inputs = cache._redis.lrange(f"{cache.store.__qualname__}:inputs", 0, -1)
    outputs = cache._redis.lrange(f"{cache.store.__qualname__}:outputs", 0, -1)
    
    print(f"inputs: {inputs}")
    print(f"outputs: {outputs}")
    
    expected_inputs = [b"('first',)", b"('second',)", b"('third',)"]
    assert inputs == expected_inputs, f"Expected {expected_inputs}, got {inputs}"
    
    # Check that outputs are UUIDs
    assert len(outputs) == 3
    for output in outputs:
        assert len(output.decode()) == 36  # UUID length
    print("✓ Check 3 passed")


def test_check_4():
    """Test Check 4: Retrieving lists with replay function"""
    print("\n=== CHECK 4: Retrieving lists ===")
    cache = Cache()
    
    cache.store("foo")
    cache.store("bar")
    cache.store(42)
    
    print("Replay output:")
    replay(cache.store)
    print("✓ Check 4 passed")


def run_all_checks():
    """Run all checks"""
    test_check_0()
    test_check_1()
    test_check_2()
    test_check_3()
    test_check_4()
    print("\n🎉 All checks passed!")


if __name__ == "__main__":
    run_all_checks()