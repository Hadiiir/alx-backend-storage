#!/usr/bin/env python3
"""
Expiring web cache and tracker
"""
import redis
import requests
from functools import wraps
from typing import Callable

# Create Redis connection
redis_store = redis.Redis()

def count_access(method: Callable) -> Callable:
    """
    Decorator to count URL accesses and cache results with expiration
    """
    @wraps(method)
    def wrapper(url: str) -> str:
        """
        Wrapper function that:
        - Tracks URL access count
        - Implements caching with expiration
        """
        # Key for counting accesses
        count_key = f"count:{url}"
        
        # Increment access count
        redis_store.incr(count_key)
        
        # Key for cached content
        cache_key = f"cached:{url}"
        
        # Check if content is cached
        cached_content = redis_store.get(cache_key)
        if cached_content:
            return cached_content.decode('utf-8')
        
        # Get fresh content if not cached
        html_content = method(url)
        
        # Cache the content with 10 second expiration
        redis_store.setex(cache_key, 10, html_content)
        
        return html_content
    return wrapper

@count_access
def get_page(url: str) -> str:
    """
    Get the HTML content of a URL with caching and access tracking
    
    Args:
        url: The URL to fetch
        
    Returns:
        The HTML content as string
    """
    response = requests.get(url)
    return response.text
    