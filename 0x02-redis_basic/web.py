#!/usr/bin/env python3
""" Web cache and tracker """
import redis
import requests
from typing import Callable
from functools import wraps


r = redis.Redis()


def count_url_access(method: Callable) -> Callable:
    """Decorator to count how many times a URL is accessed"""
    @wraps(method)
    def wrapper(url: str) -> str:
        key = f"count:{url}"
        r.incr(key)
        return method(url)
    return wrapper


@count_url_access
def get_page(url: str) -> str:
    """Fetches page content with Redis cache and tracking"""
    cached_key = f"cached:{url}"
    cached_content = r.get(cached_key)

    if cached_content:
        return cached_content.decode("utf-8")

    # Not in cache, fetch and store
    response = requests.get(url)
    content = response.text

    r.setex(cached_key, 10, content)  # Store with expiration of 10 sec
    return content