#!/usr/bin/env python3
"""Web cache and tracker implementation"""
import requests
import redis
from typing import Callable
from functools import wraps

# Initialize Redis client
redis_client = redis.Redis()


def track_access(method: Callable) -> Callable:
    """Decorator to track URL access counts"""
    @wraps(method)
    def wrapper(url: str) -> str:
        """Wrapper function for tracking"""
        count_key = f"count:{url}"
        redis_client.incr(count_key)
        return method(url)
    return wrapper


def cache_page(method: Callable) -> Callable:
    """Decorator to cache page content with expiration"""
    @wraps(method)
    def wrapper(url: str) -> str:
        """Wrapper function for caching"""
        cache_key = f"cache:{url}"
        
        # Try to get cached content
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
@cache_page
def get_page(url: str) -> str:
    """
    Get the HTML content of a URL with caching and access tracking
    
    Args:
        url: URL to fetch
        
    Returns:
        str: HTML content of the page
    """
    response = requests.get(url)
    return response.text


if __name__ == "__main__":
    # Example usage
    slow_url = "http://slowwly.robertomurray.co.uk/delay/5000/url/http://example.com"
    print(get_page(slow_url))  # First call - will be slow
    print(get_page(slow_url))  # Second call within 10s - will be fast from cache
    print(f"Access count: {redis_client.get(f'count:{slow_url}').decode('utf-8')}")