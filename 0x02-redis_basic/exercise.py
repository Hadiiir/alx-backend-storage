#!/usr/bin/env python3
"""
Redis Cache implementation - Basic version
"""

import redis
import uuid
from typing import Union


class Cache:
    """
    Redis-based cache implementation
    """
    
    def __init__(self):
        """
        Initialize Redis client and flush the database
        """
        self._redis = redis.Redis()
        self._redis.flushdb()
    
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """
        Store data in Redis with a random key
        
        Args:
            data: The data to store (str, bytes, int, or float)
            
        Returns:
            str: The generated key
        """
        # Generate a random key using uuid
        key = str(uuid.uuid4())
        
        # Store the data in Redis using the random key
        self._redis.set(key, data)
        
        # Return the key
        return key
