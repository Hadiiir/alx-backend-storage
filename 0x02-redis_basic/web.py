#!/usr/bin/env python3
"""
Web cache and tracker implementation
"""
import requests
import redis
from functools import wraps
from typing import Callable

# Initialize Redis client
redis_client = redis.Redis()


def track_access(method: Callable) -> Callable:
    """
    Decorator to track URL access counts and cache results
    """
    @wraps(method)
    def wrapper(url: str) -> str:
        # Track URL access count
        count_key = f"count:{url}"
        redis_client.incr(count_key)

        # Check cache first
        cache_key = f"cache:{url}"
        cached_content = redis_client.get(cache_key)
        if cached_content:
            return cached_content.decode('utf-8')

        # Get fresh content if not in cache
        content = method(url)
        
        # Cache with 10 second expiration
        redis_client.setex(cache_key, 10, content)
        return content
    return wrapper


@track_access
def get_page(url: str) -> str:
    """
    Get the HTML content of a URL with caching and access tracking
    
    Args:
        url: The URL to fetch
        
    Returns:
        str: The HTML content of the page
    """
    response = requests.get(url)
    return response.text
    