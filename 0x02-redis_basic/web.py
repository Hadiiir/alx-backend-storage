#!/usr/bin/env python3
"""
Expiring web cache and access tracker
"""
import redis
import requests
from typing import Callable
from functools import wraps

# Initialize Redis connection
redis_client = redis.Redis()


def track_and_cache(method: Callable) -> Callable:
    """
    Combined decorator to track access counts and cache responses
    
    Args:
        method: The function to decorate
        
    Returns:
        The decorated function
    """
    @wraps(method)
    def wrapper(url: str) -> str:
        # Track URL access
        count_key = f"count:{url}"
        redis_client.incr(count_key)
        
        # Check cache
        cache_key = f"cache:{url}"
        cached_content = redis_client.get(cache_key)
        if cached_content:
            return cached_content.decode('utf-8')
        
        # Get fresh content if not cached
        content = method(url)
        
        # Ensure we store as string
        if isinstance(content, bytes):
            content = content.decode('utf-8')
            
        # Cache with expiration
        redis_client.setex(cache_key, 10, content)
        return content
    return wrapper


@track_and_cache
def get_page(url: str) -> str:
    """
    Get HTML content of a URL with caching and access tracking
    
    Args:
        url: The URL to fetch
        
    Returns:
        The HTML content as string
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        return f"Error fetching URL: {str(e)}"