#!/usr/bin/env python3
""" Redis basic - Cache system """
import redis
import uuid
from typing import Union, Callable, Optional
from functools import wraps


def count_calls(method: Callable) -> Callable:
    """Decorator to count how many times a method is called"""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        key = method.__qualname__
        self._redis.incr(key)
        return method(self, *args, **kwargs)
    return wrapper


def call_history(method: Callable) -> Callable:
    """Decorator to store history of inputs and outputs"""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        input_key = f"{method.__qualname__}:inputs"
        output_key = f"{method.__qualname__}:outputs"

        self._redis.rpush(input_key, str(args))
        output = method(self, *args, **kwargs)
        self._redis.rpush(output_key, output)

        return output
    return wrapper


class Cache:
    """Cache class wrapping Redis client"""
    def __init__(self):
        self._redis = redis.Redis()
        self._redis.flushdb()

    @call_history
    @count_calls
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """Store the data in Redis with a random key"""
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key

    def get(self, key: str, fn: Optional[Callable] = None) -> Union[bytes, str, int, None]:
        """Retrieve a value from Redis and apply a conversion function if provided"""
        value = self._redis.get(key)
        if value is None:
            return None
        return fn(value) if fn else value

    def get_str(self, key: str) -> Optional[str]:
        """Retrieve string value from Redis"""
        value = self.get(key, fn=lambda d: d.decode("utf-8"))
        return value

    def get_int(self, key: str) -> Optional[int]:
        """Retrieve int value from Redis"""
        value = self.get(key, fn=int)
        return value


def replay(method: Callable):
    """Display the history of calls of a function"""
    redis_client = redis.Redis()
    method_name = method.__qualname__
    inputs = redis_client.lrange(f"{method_name}:inputs", 0, -1)
    outputs = redis_client.lrange(f"{method_name}:outputs", 0, -1)

    print(f"{method_name} was called {len(inputs)} times:")
    for input_val, output_val in zip(inputs, outputs):
        print(f"{method_name}(*{input_val.decode('utf-8')}) -> {output_val.decode('utf-8')}")