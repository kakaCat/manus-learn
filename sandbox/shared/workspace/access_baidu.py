#!/usr/bin/env python3
import urllib.request
try:
    response = urllib.request.urlopen('https://www.baidu.com')
    content = response.read()
    print("Successfully accessed Baidu!")
    print(f"Response length: {len(content)} bytes")
    print(f"First 200 characters: {content[:200]}")
except Exception as e:
    print(f"Error accessing Baidu: {e}")