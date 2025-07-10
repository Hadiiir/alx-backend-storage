#!/usr/bin/env python3
"""
Expiring web cache and access tracker
"""

import redis
import requests
from typing import Callable
from functools import wraps

r = redis.Redis()


def count_access(method: Callable) -> Callable:
    """
    Decorator to count how many times a URL was accessed
    """
    @wraps(method)
    def wrapper(url: str) -> str:
        key = f"count:{url}"
        r.incr(key)
        return method(url)
    return wrapper


def cache_page(expire_time: int = 10) -> Callable:
    """
    Decorator to cache page content with expiration
    """
    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(url: str) -> str:
            cache_key = f"cached:{url}"
            cached = r.get(cache_key)
            if cached:
                return cached.decode("utf-8")
            result = method(url)
            # تأكد إنك بتخزن string صريح
            if isinstance(result, bytes):
                result = result.decode("utf-8")
            r.setex(cache_key, expire_time, result)
            return result
        return wrapper
    return decorator


@count_access
@cache_page(expire_time=10)
def get_page(url: str) -> str:
    """
    Get HTML content of a URL and cache it
    """
    response = requests.get(url)
    return response.text
