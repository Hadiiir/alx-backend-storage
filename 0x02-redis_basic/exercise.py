#!/usr/bin/env python3
""" Basic Redis cache """
import redis
import uuid
from typing import Union


class Cache:
    """Cache class to interact with Redis"""

    def __init__(self):
        """Initialize Redis client and flush database"""
        self._redis = redis.Redis()
        self._redis.flushdb()

    def store(self, data: Union[str, bytes, int, float]) -> str:
        """
        Store data in Redis under a randomly generated key

        Args:
            data (str | bytes | int | float): data to store

        Returns:
            str: the key under which the data is stored
        """
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key