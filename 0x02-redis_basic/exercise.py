#!/usr/bin/env python3
"""
Redis basic exercise module
"""
import redis
import uuid
from functools import wraps
from typing import Union, Callable, Optional


def count_calls(method: Callable) -> Callable:
    """Counts how many times methods of Cache class are called"""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        key = method.__qualname__
        self._redis.incr(key)
        return method(self, *args, **kwargs)
    return wrapper


def call_history(method: Callable) -> Callable:
    """Stores input/output history for a function"""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        input_key = f"{method.__qualname__}:inputs"
        output_key = f"{method.__qualname__}:outputs"
        
        # Store input arguments
        self._redis.rpush(input_key, str(args))
        
        # Execute the original method
        output = method(self, *args, **kwargs)
        
        # Store output
        self._redis.rpush(output_key, output)
        
        return output
    return wrapper


def replay(method: Callable) -> None:
    """Displays the history of calls of a particular function"""
    cache = method.__self__
    qualname = method.__qualname__
    
    # Get count from Redis
    count = cache._redis.get(qualname)
    count_str = count.decode('utf-8') if count else "0"
    
    # Get inputs and outputs
    inputs = cache._redis.lrange(f"{qualname}:inputs", 0, -1)
    outputs = cache._redis.lrange(f"{qualname}:outputs", 0, -1)
    
    print(f"{qualname} was called {count_str} times:")
    
    for args, output in zip(inputs, outputs):
        args_str = args.decode('utf-8')
        output_str = output.decode('utf-8')
        print(f"{qualname}(*{args_str}) -> {output_str}")


class Cache:
    """Cache class for Redis operations"""
    
    def __init__(self):
        """Initialize Redis client and flush the database"""
        self._redis = redis.Redis()
        self._redis.flushdb()
    
    @count_calls
    @call_history
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """
        Store data in Redis with a random key
        
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
        Get data from Redis and optionally apply conversion function
        
        Args:
            key: Key to retrieve
            fn: Optional conversion function
            
        Returns:
            Data in original or converted format, or None if key doesn't exist
        """
        data = self._redis.get(key)
        if data is not None and fn is not None:
            return fn(data)
        return data
    
    def get_str(self, key: str) -> str:
        """Get data as string"""
        return self.get(key, fn=lambda d: d.decode("utf-8"))
    
    def get_int(self, key: str) -> int:
        """Get data as integer"""
        return self.get(key, fn=int)