#!/usr/bin/env python3
"""
Expiring web cache and access tracker
"""

import redis
import requests
from functools import wraps
from typing import Callable

r = redis.Redis()


def cache_page_and_track(expire_time: int = 10) -> Callable:
    """
    Decorator to cache page content with expiration and track access count
    """
    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(url: str) -> str:
            cache_key = f"cached:{url}"
            count_key = f"count:{url}"
            cached = r.get(cache_key)

            if cached:
                return cached.decode("utf-8")

            # لو مفيش كاش، زود العداد وخزن النتيجة
            r.incr(count_key)
            result = method(url)
            if isinstance(result, bytes):
                result = result.decode("utf-8")
            r.setex(cache_key, expire_time, result)
            return result
        return wrapper
    return decorator


@cache_page_and_track(expire_time=10)
def get_page(url: str) -> str:
    """
    Get HTML content of a URL and cache it with expiration and access count
    """
    response = requests.get(url)
    return response.text
