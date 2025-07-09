#!/usr/bin/env python3
"""
Redis Cache implementation with decorators and history tracking
"""

import redis
import uuid
from typing import Union, Callable, Optional, Any
from functools import wraps


def count_calls(method: Callable) -> Callable:
    """
    Decorator that counts how many times a method is called
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        # Use the method's qualified name as the key
        key = method.__qualname__
        # Increment the counter in Redis
        self._redis.incr(key)
        # Call and return the original method
        return method(self, *args, **kwargs)
    return wrapper


def call_history(method: Callable) -> Callable:
    """
    Decorator that stores the history of inputs and outputs for a method
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        # Create keys for inputs and outputs
        input_key = f"{method.__qualname__}:inputs"
        output_key = f"{method.__qualname__}:outputs"
        
        # Store input arguments (convert to string for Redis)
        self._redis.rpush(input_key, str(args))
        
        # Execute the original method
        result = method(self, *args, **kwargs)
        
        # Store the output
        self._redis.rpush(output_key, result)
        
        return result
    return wrapper


class Cache:
    """
    Redis-based cache implementation
    """
    
    def __init__(self):
        """
        Initialize Redis client and flush the database
        """
        self._redis = redis.Redis()
        self._redis.flushdb()
    
    @call_history
    @count_calls
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """
        Store data in Redis with a random key
        
        Args:
            data: The data to store (str, bytes, int, or float)
            
        Returns:
            str: The generated key
        """
        # Generate a random key
        key = str(uuid.uuid4())
        
        # Store the data in Redis
        self._redis.set(key, data)
        
        return key
    
    def get(self, key: str, fn: Optional[Callable] = None) -> Any:
        """
        Retrieve data from Redis and optionally apply a conversion function
        
        Args:
            key: The Redis key
            fn: Optional conversion function
            
        Returns:
            The retrieved data, optionally converted
        """
        # Get the data from Redis
        data = self._redis.get(key)
        
        # Return None if key doesn't exist (preserving Redis.get behavior)
        if data is None:
            return None
        
        # Apply conversion function if provided
        if fn is not None:
            return fn(data)
        
        return data
    
    def get_str(self, key: str) -> Optional[str]:
        """
        Retrieve data from Redis and convert to string
        
        Args:
            key: The Redis key
            
        Returns:
            The data as a string, or None if key doesn't exist
        """
        return self.get(key, fn=lambda d: d.decode("utf-8"))
    
    def get_int(self, key: str) -> Optional[int]:
        """
        Retrieve data from Redis and convert to integer
        
        Args:
            key: The Redis key
            
        Returns:
            The data as an integer, or None if key doesn't exist
        """
        return self.get(key, fn=int)


def replay(method: Callable) -> None:
    """
    Display the history of calls for a particular function
    
    Args:
        method: The method to replay the history for
    """
    # Get the Redis instance from the method's class
    cache_instance = method.__self__
    redis_client = cache_instance._redis
    
    # Get the method's qualified name
    method_name = method.__qualname__
    
    # Get the call count
    call_count = redis_client.get(method_name)
    if call_count is None:
        call_count = 0
    else:
        call_count = int(call_count)
    
    print(f"{method_name} was called {call_count} times:")
    
    # Get inputs and outputs
    input_key = f"{method_name}:inputs"
    output_key = f"{method_name}:outputs"
    
    inputs = redis_client.lrange(input_key, 0, -1)
    outputs = redis_client.lrange(output_key, 0, -1)
    
    # Display the history
    for input_data, output_data in zip(inputs, outputs):
        input_str = input_data.decode("utf-8")
        output_str = output_data.decode("utf-8")
        print(f"{method_name}(*{input_str}) -> {output_str}")


if __name__ == "__main__":
    # Test the implementation
    cache = Cache()
    
    # Test basic storage and retrieval
    print("=== Basic Storage Test ===")
    data = b"hello"
    key = cache.store(data)
    print(f"Stored key: {key}")
    print(f"Retrieved data: {cache.get(key)}")
    
    # Test type conversion
    print("\n=== Type Conversion Test ===")
    TEST_CASES = {
        b"foo": None,
        123: int,
        "bar": lambda d: d.decode("utf-8")
    }
    
    for value, fn in TEST_CASES.items():
        key = cache.store(value)
        retrieved = cache.get(key, fn=fn)
        print(f"Original: {value}, Retrieved: {retrieved}, Match: {retrieved == value}")
    
    # Test count_calls
    print("\n=== Count Calls Test ===")
    cache.store(b"first")
    print(f"Call count after 1 call: {cache.get(cache.store.__qualname__)}")
    
    cache.store(b"second")
    cache.store(b"third")
    print(f"Call count after 3 calls: {cache.get(cache.store.__qualname__)}")
    
    # Test call_history
    print("\n=== Call History Test ===")
    inputs = cache._redis.lrange(f"{cache.store.__qualname__}:inputs", 0, -1)
    outputs = cache._redis.lrange(f"{cache.store.__qualname__}:outputs", 0, -1)
    print(f"Inputs: {inputs}")
    print(f"Outputs: {outputs}")
    
    # Test replay function
    print("\n=== Replay Test ===")
    replay(cache.store)
    
    # Test get_str and get_int
    print("\n=== Convenience Methods Test ===")
    str_key = cache.store("hello world")
    int_key = cache.store(42)
    
    print(f"String retrieval: {cache.get_str(str_key)}")
    print(f"Integer retrieval: {cache.get_int(int_key)}")