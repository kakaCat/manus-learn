import asyncio
import json
import base64
import os
from datetime import datetime
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run():
    # 1. 配置连接参数
    # 我们通过 docker exec -i 调用容器内的 MCP Server，并将其 stdin/stdout 映射出来
    server_params = StdioServerParameters(
        command="docker",
        args=[
            "exec", "-i", 
            "sandbox-chrome",  # 确保与 docker-compose.yml 中的 container_name 一致
            "node", "/usr/lib/node_modules/chrome-devtools-mcp/build/src/index.js",
            "--browserUrl", "http://127.0.0.1:9222"
        ],
        env=None
    )

    print("🤖 正在连接到 Chrome MCP 沙盒环境...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化会话
            await session.initialize()
            
            # 获取可用工具列表
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            print(f"✅ 连接成功！可用工具: {len(tool_names)} 个")
            print(f"   工具列表: {tool_names}")
            
            # ---------------------------------------------------------
            # 场景：在 Baidu 搜索 "MCP Protocol" 并截图
            # ---------------------------------------------------------
            
            # 1. 导航到 Baidu
            print("\n🌐 1. 正在打开 Baidu (https://www.baidu.com)...")
            # 工具名: navigate_page
            nav_result = await session.call_tool("navigate_page", arguments={"url": "https://www.baidu.com"})
            print(f"   导航结果: {nav_result}")
            
            print("   ⏳ 等待 5 秒让页面加载...")
            await asyncio.sleep(5)
            
            # 截图查看当前状态
            print("📸 1.5 页面加载后截图...")
            # 确保 workspace 目录存在
            os.makedirs("workspace", exist_ok=True)
            
            if "take_screenshot" in tool_names:
                # 必须传入一个对象，即使是空的
                screenshot_result = await session.call_tool("take_screenshot", arguments={})
                
                img_content = None
                for content in screenshot_result.content:
                    if content.type == "image":
                        img_content = content
                        break
                    elif content.type == "text":
                         print(f"   截图文本信息: {content.text[:100]!r}")
                         # 如果包含 data:image，可能是嵌入在 text 中的
                         if "data:image" in content.text:
                             img_content = content
                             break
                
                if img_content:
                    try:
                        data = img_content.data if hasattr(img_content, "data") else img_content.text
                        if "data:image" in data and "base64," in data:
                             data = data.split("base64,")[1]
                        
                        # 补全 padding
                        padding = len(data) % 4
                        if padding > 0:
                             data += "=" * (4 - padding)
                             
                        filepath = "workspace/screenshot_step1.png"
                        with open(filepath, "wb") as f:
                            f.write(base64.b64decode(data))
                        print(f"   ✅ 已保存: {filepath}")
                    except Exception as e:
                        print(f"   ❌ 保存截图失败: {e}")
                else:
                    print("   ⚠️ 未找到图像数据")

            # 2. 获取页面标题 (使用 evaluate_script)
            if "evaluate_script" in tool_names:
                print("📑 2. 获取页面标题...")
                # 参数修正: 传入完整的函数定义
                result = await session.call_tool("evaluate_script", arguments={
                    "function": "function() { return document.title; }"
                })
                print(f"   页面标题: {result.content}")

            # 3. 模拟搜索输入 (使用 fill 和 click 工具)
            print("⌨️  3. 输入搜索词 'MCP Protocol'...")
            
            if "fill" in tool_names:
                print("   正在输入关键词...")
                await session.call_tool("fill", arguments={
                    "selector": "#kw",
                    "value": "MCP Protocol"
                })
            
            if "click" in tool_names:
                print("   正在点击搜索按钮...")
                await session.call_tool("click", arguments={
                    "selector": "#su"
                })
            
            print("   ⏳ 等待 5 秒让搜索结果加载...")
            await asyncio.sleep(5)

            # 4. 最终截图
            print("📸 4. 正在最终截图...")
            if "take_screenshot" in tool_names:
                try:
                    screenshot_result = await session.call_tool("take_screenshot", arguments={})
                    
                    img_content = None
                    for content in screenshot_result.content:
                        if content.type == "image":
                            img_content = content
                            break
                        elif content.type == "text":
                            if "data:image" in content.text:
                                img_content = content
                                break
                    
                    if img_content:
                        data = img_content.data if hasattr(img_content, "data") else img_content.text
                        if "data:image" in data and "base64," in data:
                             data = data.split("base64,")[1]
                        
                        padding = len(data) % 4
                        if padding > 0:
                             data += "=" * (4 - padding)
                             
                        filepath = "workspace/screenshot_final.png"
                        with open(filepath, "wb") as f:
                            f.write(base64.b64decode(data))
                        print(f"   ✅ 已保存: {filepath}")
                    else:
                        print("   ⚠️ 未找到图像数据")
                except Exception as e:
                    print(f"   ❌ 截图失败: {e}")

if __name__ == "__main__":
    asyncio.run(run())
