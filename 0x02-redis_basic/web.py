#!/usr/bin/env python3
"""
Expiring web cache and access tracker
"""
import redis
import requests
from functools import wraps
from typing import Callable


r = redis.Redis()


def get_page(url: str) -> str:
    """
    Get HTML content of a URL and cache it
    
    Args:
        url: The URL to fetch
        
    Returns:
        str: HTML content of the page
    """
    # Count access
    count_key = f"count:{url}"
    r.incr(count_key)
    
    # Check cache
    cache_key = f"cached:{url}"
    cached = r.get(cache_key)
    
    if cached:
        return cached.decode("utf-8")
    
    # Get fresh content
    response = requests.get(url)
    result = response.text
    
    # Cache with expiration
    r.setex(cache_key, 10, result)
    
    return result