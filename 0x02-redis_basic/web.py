#!/usr/bin/env python3
"""
Enhanced Expiring Web Cache and Access Tracker
This module combines request caching, access tracking, and safe key generation.
Features:
- URL content caching with expiration
- Access counting for each URL
- SHA-256 hashed keys for security
- Redis storage for persistence
"""

import redis
import requests
import hashlib
from functools import wraps
from typing import Callable

# Create Redis connection
redis_store = redis.Redis()

def safe_key(prefix: str, url: str) -> str:
    """
    Generate a safe Redis key using SHA-256 hashing to avoid:
    - Invalid characters in keys
    - Very long keys
    - Security issues with raw URLs
    
    Args:
        prefix: The key prefix (e.g., 'cached' or 'count')
        url: The URL to be hashed
        
    Returns:
        A safe Redis key string in format "prefix:sha256hash"
    """
    return f"{prefix}:{hashlib.sha256(url.encode()).hexdigest()}"

def count_and_cache(expire: int = 10) -> Callable:
    """
    Decorator factory that counts accesses and caches results with expiration.
    
    Args:
        expire: Cache expiration time in seconds (default: 10)
        
    Returns:
        A decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(url: str) -> str:
            """
            Wrapper function that handles:
            - Access counting
            - Cache lookup
            - Cache storage
            - Result return
            
            Args:
                url: The URL to fetch
                
            Returns:
                The HTML content as string
            """
            # Generate safe keys
            cache_key = safe_key("cached", url)
            count_key = safe_key("count", url)
            
            # Increment access count
            redis_store.incr(count_key)
            
            # Check cache first
            cached_content = redis_store.get(cache_key)
            if cached_content:
                return cached_content.decode("utf-8")
                
            # Get fresh content if not cached
            fresh_content = func(url)
            
            # Ensure we store bytes in Redis
            if isinstance(fresh_content, str):
                fresh_content = fresh_content.encode("utf-8")
            
            # Store with expiration
            redis_store.setex(cache_key, expire, fresh_content)
            
            return fresh_content.decode("utf-8")
        return wrapper
    return decorator

@count_and_cache(10)
def get_page(url: str) -> str:
    """
    Fetches the content of a URL with caching and tracking.
    
    Args:
        url: The URL to fetch
        
    Returns:
        The HTML content as string
    """
    response = requests.get(url)
    return response.text