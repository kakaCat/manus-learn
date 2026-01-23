import urllib.request
try:
    response = urllib.request.urlopen('https://www.baidu.com')
    content = response.read()
    print(f"Success! Got {len(content)} bytes from Baidu")
    print("First 200 characters:")
    print(content[:200])
except Exception as e:
    print(f"Error: {e}")