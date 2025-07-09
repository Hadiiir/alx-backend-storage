#!/usr/bin/env python3
""" Test get_page """
from web import get_page
import redis

url = "http://slowwly.robertomurray.co.uk/delay/3000/url/https://example.com"

print("Fetching page content...")
html = get_page(url)
print(html[:200])

r = redis.Redis()
print("Access count:", r.get(f"count:{url}").decode("utf-8"))
