#!/usr/bin/env python3
import urllib.request
import re

try:
    # 访问百度
    response = urllib.request.urlopen('https://www.baidu.com')
    content = response.read().decode('utf-8')
    
    print("=" * 60)
    print("成功访问百度首页!")
    print("=" * 60)
    
    # 提取标题
    title_match = re.search(r'<title>(.*?)</title>', content)
    if title_match:
        print(f"页面标题: {title_match.group(1)}")
    
    # 提取一些关键信息
    print(f"\n页面大小: {len(content)} 字符")
    
    # 查找百度logo
    if '百度一下' in content:
        print("检测到百度搜索框")
    
    # 显示页面开头部分
    print("\n页面开头部分:")
    print("-" * 40)
    lines = content.split('\n')
    for i, line in enumerate(lines[:10]):
        if line.strip():
            print(f"{i+1}: {line[:100]}...")
    
    print("\n访问成功！百度网站可以正常访问。")
    
except Exception as e:
    print(f"访问百度时出错: {e}")