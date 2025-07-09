#!/usr/bin/env python3
""" Expiring web cache and tracker with decorators """

import redis
import requests
from functools import wraps
from typing import Callable

# Redis client
r = redis.Redis()


def count_calls(method: Callable) -> Callable:
    """Decorator to count how many times a URL is accessed"""
    @wraps(method)
    def wrapper(url: str) -> str:
        r.incr(f"count:{url}")
        return method(url)
    return wrapper


def cache_page(expire: int = 10) -> Callable:
    """Decorator to cache HTML page for `expire` seconds"""
    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(url: str) -> str:
            cache_key = f"cached:{url}"
            cached = r.get(cache_key)
            if cached:
                return cached.decode("utf-8")

            html = method(url)
            r.setex(cache_key, expire, html)
            return html
        return wrapper
    return decorator


@count_calls
@cache_page(expire=10)
def get_page(url: str) -> str:
    """Fetch HTML content from URL"""
    response = requests.get(url)
    return response.text