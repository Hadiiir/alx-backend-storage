#!/usr/bin/env python3
"""
Expiring web cache and access tracker
"""

import redis
import requests
from functools import wraps
from typing import Callable

r = redis.Redis()


def cache_and_count(expire_time: int = 10) -> Callable:
    """
    Decorator that caches the result of get_page and increments access count
    only when the page is not in cache.
    """
    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(url: str) -> str:
            cache_key = f"cached:{url}"
            count_key = f"count:{url}"

            # لو فيه كاش، رجّع المحتوى بدون ما تزود العداد
            cached = r.get(cache_key)
            if cached:
                return cached.decode('utf-8')

            # مفيش كاش → زود العداد وخزن النتيجة
            r.incr(count_key)
            content = method(url)
            r.setex(cache_key, expire_time, content)
            return content
        return wrapper
    return decorator


@cache_and_count(expire_time=10)
def get_page(url: str) -> str:
    """
    Retrieves the HTML content of a URL using requests
    """
    response = requests.get(url)
    return response.text
