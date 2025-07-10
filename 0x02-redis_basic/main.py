#!/usr/bin/env python3
"""Main test file"""
from exercise import Cache, replay

cache = Cache()

# Test Task 0
data = b"hello"
key = cache.store(data)
print(key)
print(cache.get(key))

# Test Task 1
TEST_CASES = {
    b"foo": None,
    123: int,
    "bar": lambda d: d.decode("utf-8")
}
for value, fn in TEST_CASES.items():
    key = cache.store(value)
    assert cache.get(key, fn=fn) == value

# Test Task 2
cache.store(b"first")
print(cache.get(cache.store.__qualname__))
cache.store(b"second")
cache.store(b"third")
print(cache.get(cache.store.__qualname__))

# Test Task 3 & 4
cache.store("foo")
cache.store("bar")
cache.store(42)
replay(cache.store)