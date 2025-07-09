#!/usr/bin/env python3
"""
Test file to verify the Cache implementation
"""

from exercise import Cache, replay

def test_basic_functionality():
    """Test basic cache functionality"""
    print("=== Testing Basic Functionality ===")
    
    cache = Cache()
    
    # Test storage
    data = b"hello"
    key = cache.store(data)
    print(f"Generated key: {key}")
    
    # Test retrieval
    retrieved = cache.get(key)
    print(f"Retrieved data: {retrieved}")
    print(f"Data matches: {data == retrieved}")

def test_type_conversions():
    """Test type conversion functionality"""
    print("\n=== Testing Type Conversions ===")
    
    cache = Cache()
    
    # Test cases from the requirements
    TEST_CASES = {
        b"foo": None,
        123: int,
        "bar": lambda d: d.decode("utf-8")
    }
    
    for value, fn in TEST_CASES.items():
        key = cache.store(value)
        result = cache.get(key, fn=fn)
        print(f"Value: {value}, Retrieved: {result}, Type: {type(result)}")
        assert result == value, f"Mismatch: {result} != {value}"
    
    print("All type conversion tests passed!")

def test_count_calls():
    """Test the count_calls decorator"""
    print("\n=== Testing Count Calls ===")
    
    cache = Cache()
    
    # Make some calls
    cache.store(b"first")
    count1 = cache.get(cache.store.__qualname__)
    print(f"Count after 1 call: {count1}")
    
    cache.store(b"second")
    cache.store(b"third")
    count3 = cache.get(cache.store.__qualname__)
    print(f"Count after 3 calls: {count3}")

def test_call_history():
    """Test the call_history decorator"""
    print("\n=== Testing Call History ===")
    
    cache = Cache()
    
    # Store some data
    s1 = cache.store("first")
    s2 = cache.store("second")
    s3 = cache.store("third")
    
    print(f"Keys generated: {s1}, {s2}, {s3}")
    
    # Check history
    inputs = cache._redis.lrange(f"{cache.store.__qualname__}:inputs", 0, -1)
    outputs = cache._redis.lrange(f"{cache.store.__qualname__}:outputs", 0, -1)
    
    print(f"Inputs: {inputs}")
    print(f"Outputs: {outputs}")

def test_replay():
    """Test the replay function"""
    print("\n=== Testing Replay Function ===")
    
    cache = Cache()
    
    # Store some data
    cache.store("foo")
    cache.store("bar")
    cache.store(42)
    
    # Replay the history
    replay(cache.store)

def test_convenience_methods():
    """Test get_str and get_int methods"""
    print("\n=== Testing Convenience Methods ===")
    
    cache = Cache()
    
    # Test string storage and retrieval
    str_key = cache.store("hello world")
    retrieved_str = cache.get_str(str_key)
    print(f"String: '{retrieved_str}', Type: {type(retrieved_str)}")
    
    # Test integer storage and retrieval
    int_key = cache.store(42)
    retrieved_int = cache.get_int(int_key)
    print(f"Integer: {retrieved_int}, Type: {type(retrieved_int)}")
    
    # Test non-existent key
    non_existent = cache.get_str("non-existent-key")
    print(f"Non-existent key result: {non_existent}")

if __name__ == "__main__":
    test_basic_functionality()
    test_type_conversions()
    test_count_calls()
    test_call_history()
    test_replay()
    test_convenience_methods()
    
    print("\n=== All Tests Completed ===")
