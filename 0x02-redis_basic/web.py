#!/usr/bin/env python3
"""
Expiring web cache and tracker implementation
"""

import redis
import requests
from typing import Callable
from functools import wraps

# Initialize Redis client
redis_client = redis.Redis()


def cache_with_expiration(expiration: int = 10):
    """
    Decorator that caches the result of a function with expiration time
    and tracks access count
    
    Args:
        expiration: Cache expiration time in seconds (default: 10)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(url: str) -> str:
            # Keys for caching and counting
            cache_key = f"cache:{url}"
            count_key = f"count:{url}"
            
            # Increment access count
            redis_client.incr(count_key)
            
            # Try to get cached result
            cached_result = redis_client.get(cache_key)
            if cached_result:
                print(f"Cache hit for {url}")
                return cached_result.decode('utf-8')
            
            # Cache miss - fetch new data
            print(f"Cache miss for {url} - fetching new data")
            result = func(url)
            
            # Cache the result with expiration
            redis_client.setex(cache_key, expiration, result)
            
            return result
        return wrapper
    return decorator


@cache_with_expiration(expiration=10)
def get_page(url: str) -> str:
    """
    Fetch the HTML content of a URL with caching and access tracking
    
    Args:
        url: The URL to fetch
        
    Returns:
        str: The HTML content of the page
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for bad status codes
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return f"Error: Unable to fetch {url}"


def get_access_count(url: str) -> int:
    """
    Get the number of times a URL has been accessed
    
    Args:
        url: The URL to check
        
    Returns:
        int: The access count
    """
    count = redis_client.get(f"count:{url}")
    return int(count) if count else 0


def clear_cache(url: str = None) -> None:
    """
    Clear cache for a specific URL or all cached URLs
    
    Args:
        url: Specific URL to clear cache for, or None to clear all
    """
    if url:
        redis_client.delete(f"cache:{url}")
        print(f"Cache cleared for {url}")
    else:
        # Clear all cache entries
        cache_keys = redis_client.keys("cache:*")
        if cache_keys:
            redis_client.delete(*cache_keys)
            print("All cache cleared")
        else:
            print("No cache to clear")


def get_cache_info(url: str) -> dict:
    """
    Get cache information for a specific URL
    
    Args:
        url: The URL to check
        
    Returns:
        dict: Cache information including TTL and access count
    """
    cache_key = f"cache:{url}"
    count_key = f"count:{url}"
    
    is_cached = redis_client.exists(cache_key)
    ttl = redis_client.ttl(cache_key) if is_cached else -1
    access_count = get_access_count(url)
    
    return {
        'url': url,
        'is_cached': bool(is_cached),
        'ttl': ttl,
        'access_count': access_count
    }


# Alternative implementation without decorator for comparison
def get_page_simple(url: str) -> str:
    """
    Simple implementation without decorator for comparison
    """
    cache_key = f"cache:{url}"
    count_key = f"count:{url}"
    
    # Increment access count
    redis_client.incr(count_key)
    
    # Try to get cached result
    cached_result = redis_client.get(cache_key)
    if cached_result:
        print(f"Cache hit for {url}")
        return cached_result.decode('utf-8')
    
    # Cache miss - fetch new data
    print(f"Cache miss for {url} - fetching new data")
    try:
        response = requests.get(url)
        response.raise_for_status()
        result = response.text
        
        # Cache the result with 10 second expiration
        redis_client.setex(cache_key, 10, result)
        
        return result
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return f"Error: Unable to fetch {url}"


# Example usage and testing functions
def test_cache_functionality():
    """
    Test the caching functionality with slow response simulation
    """
    test_urls = [
        "http://slowwly.robertomurray.co.uk/delay/3000/url/http://www.example.com",
        "http://httpbin.org/delay/2",
        "http://httpbin.org/json"
    ]
    
    print("Testing cache functionality:")
    print("=" * 50)
    
    for url in test_urls:
        print(f"\nTesting URL: {url}")
        
        # First request (should be slow)
        import time
        start_time = time.time()
        result = get_page(url)
        first_request_time = time.time() - start_time
        
        print(f"First request time: {first_request_time:.2f} seconds")
        print(f"Access count: {get_access_count(url)}")
        
        # Second request (should be fast due to cache)
        start_time = time.time()
        result = get_page(url)
        second_request_time = time.time() - start_time
        
        print(f"Second request time: {second_request_time:.2f} seconds")
        print(f"Access count: {get_access_count(url)}")
        
        # Show cache info
        cache_info = get_cache_info(url)
        print(f"Cache info: {cache_info}")
        
        print("-" * 30)


if __name__ == "__main__":
    # Example usage
    print("Web Cache and Tracker System")
    print("=" * 40)
    
    # Test with a simple URL
    test_url = "http://httpbin.org/json"
    
    print(f"Fetching {test_url} for the first time...")
    result = get_page(test_url)
    print(f"Result length: {len(result)} characters")
    print(f"Access count: {get_access_count(test_url)}")
    
    print(f"\nFetching {test_url} again (should be cached)...")
    result = get_page(test_url)
    print(f"Result length: {len(result)} characters")
    print(f"Access count: {get_access_count(test_url)}")
    
    # Show cache info
    cache_info = get_cache_info(test_url)
    print(f"\nCache info: {cache_info}")
    
    # Uncomment to run full test
    # test_cache_functionality()