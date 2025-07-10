#!/usr/bin/env python3
"""
Expiring web cache and access tracker
"""
import redis
import requests
from functools import wraps
from typing import Callable


r = redis.Redis()


def url_access_count(func: Callable) -> Callable:
    """
    Decorator to count how many times a URL was accessed
    """
    @wraps(func)
    def wrapper(url: str) -> str:
        count_key = f"count:{url}"
        r.incr(count_key)
        return func(url)
    return wrapper


def cache_page(func: Callable) -> Callable:
    """
    Decorator to cache page content with expiration
    """
    @wraps(func)
    def wrapper(url: str) -> str:
        cache_key = f"cache:{url}"
        cached = r.get(cache_key)
        
        if cached:
            return cached.decode("utf-8")
        
        result = func(url)
        r.setex(cache_key, 10, result)
        return result
    return wrapper


@url_access_count
@cache_page
def get_page(url: str) -> str:
    """
    Get HTML content of a URL and cache it
    
    Args:
        url: The URL to fetch
        
    Returns:
        str: HTML content of the page
    """
    response = requests.get(url)
    return response.text