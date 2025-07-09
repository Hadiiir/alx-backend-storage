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