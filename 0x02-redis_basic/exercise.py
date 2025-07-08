#!/usr/bin/env python3
"""Redis cache implementation"""
import uuid
import redis
from typing import Union, Callable, Optional, Any
from functools import wraps


class Cache:
    """Cache class for storing data in Redis"""
    def __init__(self):
        """Initialize Redis client and flush the database"""
        self._redis = redis.Redis()
        self._redis.flushdb()

    @count_calls
    @call_history
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """
        Store data in Redis with a randomly generated key
        
        Args:
            data: Data to store (str, bytes, int, or float)
            
        Returns:
            str: The generated key
        """
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key

    def get(
            self,
            key: str,
            fn: Optional[Callable] = None
        ) -> Union[str, bytes, int, float, None]:
        """
        Retrieve data from Redis and optionally apply conversion function
        
        Args:
            key: Key to retrieve
            fn: Optional callable to convert the data
            
        Returns:
            Original data or converted data
        """
        data = self._redis.get(key)
        if data is None:
            return None
        if fn is not None:
            return fn(data)
        return data

    def get_str(self, key: str) -> str:
        """
        Get data as UTF-8 string
        
        Args:
            key: Key to retrieve
            
        Returns:
            str: Decoded UTF-8 string
        """
        return self.get(key, fn=lambda d: d.decode('utf-8'))

    def get_int(self, key: str) -> int:
        """
        Get data as integer
        
        Args:
            key: Key to retrieve
            
        Returns:
            int: Converted integer
        """
        return self.get(key, fn=int)


def count_calls(method: Callable) -> Callable:
    """Decorator to count how many times a method is called"""
    @wraps(method)
    def wrapper(self, *args, **kwargs) -> Any:
        """Wrapper function for counting calls"""
        key = method.__qualname__
        self._redis.incr(key)
        return method(self, *args, **kwargs)
    return wrapper


def call_history(method: Callable) -> Callable:
    """Decorator to store the history of inputs and outputs"""
    @wraps(method)
    def wrapper(self, *args, **kwargs) -> Any:
        """Wrapper function for storing history"""
        input_key = f"{method.__qualname__}:inputs"
        output_key = f"{method.__qualname__}:outputs"
        
        # Store input arguments
        self._redis.rpush(input_key, str(args))
        
        # Execute the method and store output
        output = method(self, *args, **kwargs)
        self._redis.rpush(output_key, str(output))
        
        return output
    return wrapper


def replay(method: Callable) -> None:
    """Display the history of calls of a particular function"""
    if not hasattr(method, '__self__'):
        raise TypeError("Method must be bound to an instance")
    
    cache = method.__self__
    qualname = method.__qualname__
    
    # Get call count
    call_count = cache.get(f"{qualname}")
    if call_count is None:
        call_count = 0
    elif isinstance(call_count, bytes):
        call_count = int(call_count.decode())
    
    print(f"{qualname} was called {call_count} times:")
    
    # Get inputs and outputs
    inputs = cache._redis.lrange(f"{qualname}:inputs", 0, -1)
    outputs = cache._redis.lrange(f"{qualname}:outputs", 0, -1)
    
    for args, output in zip(inputs, outputs):
        args_str = args.decode('utf-8')
        output_str = output.decode('utf-8')
        print(f"{qualname}(*{args_str}) -> {output_str}")