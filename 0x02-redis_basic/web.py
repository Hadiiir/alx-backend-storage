#!/usr/bin/env python3
"""
Expiring web cache and access tracker
"""

import redis
import requests
import hashlib
from functools import wraps
from typing import Callable

r = redis.Redis()


def safe_key(prefix: str, url: str) -> str:
    """Generate a safe Redis key using SHA-256"""
    return f"{prefix}:{hashlib.sha256(url.encode()).hexdigest()}"


def count_and_cache(expire: int = 10) -> Callable:
    """Decorator to count access and cache HTML"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(url: str) -> str:
            cache_key = safe_key("cached", url)
            count_key = safe_key("count", url)

            cached = r.get(cache_key)
            if cached:
                return cached.decode("utf-8")

            # Count access
            r.incr(count_key)

            html = func(url)

            # تأكدي إن اللي بيتخزن هو string متكوّد
            if isinstance(html, str):
                html = html.encode('utf-8')

            r.setex(cache_key, expire, html)

            return html.decode('utf-8')
        return wrapper
    return decorator


@count_and_cache(10)
def get_page(url: str) -> str:
    """Fetch page content"""
    response = requests.get(url)
    return response.text
