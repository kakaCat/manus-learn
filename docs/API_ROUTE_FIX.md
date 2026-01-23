# API 路由问题修复报告

## 🐛 问题描述

前端 ChatPanel 调用 `POST http://localhost:8000/api/chat` 返回 **404 Not Found**

## 🔍 根本原因

后端路由配置错误,导致路径嵌套错误:

```python
# backend/app/main.py:85
app.include_router(chat.router, prefix="/api")  # 添加 /api 前缀

# backend/app/api/chat.py:15
router = APIRouter(prefix="/chat", tags=["chat"])  # 添加 /chat 前缀

# backend/app/api/chat.py:105 (修复前)
@router.post("/api/chat", response_model=ChatResponse)  # ❌ 又添加了 /api/chat
```

**实际生成的路径**: `/api` + `/chat` + `/api/chat` = `/api/chat/api/chat` ❌

**期望的路径**: `/api/chat` ✓

## ✅ 修复方案

修改 [backend/app/api/chat.py:105](backend/app/api/chat.py#L105):

```python
# 修复前
@router.post("/api/chat", response_model=ChatResponse)

# 修复后
@router.post("", response_model=ChatResponse)  # 空字符串表示使用 router 的 prefix
```

## 📋 完整的 API 路由映射

### Chat API (`/api/chat`)

| 方法 | 路径 | 功能 | 状态 |
|------|------|------|------|
| WebSocket | `/api/chat/ws` | 实时聊天 (WebSocket) | ✅ 正确 |
| POST | `/api/chat` | 发送聊天消息 (REST) | ✅ 已修复 |
| POST | `/api/chat/clear` | 清除聊天历史 | ✅ 正确 |
| GET | `/api/chat/sessions` | 获取会话列表 | ✅ 正确 |

### Sandbox API (`/api/sandbox`)

| 方法 | 路径 | 功能 | 状态 |
|------|------|------|------|
| GET | `/api/sandbox/status` | 获取沙盒状态 | ✅ 正确 |
| GET | `/api/sandbox/processes` | 获取进程列表 | ✅ 正确 |
| ... | ... | ... | ... |

### 系统 API

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/` | 服务信息 |
| GET | `/health` | 健康检查 |
| GET | `/docs` | Swagger 文档 |

## 🧪 验证方法

### 1. 启动后端

```bash
cd backend
python -m app.main
```

### 2. 测试 REST API

```bash
# 测试聊天端点
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello",
    "chat_history": []
  }'

# 预期响应
{
  "status": "success",
  "response": "...",
  "error": null
}
```

### 3. 查看 Swagger 文档

访问 http://localhost:8000/docs 查看所有可用的 API 端点

### 4. 测试前端

```bash
cd frontend
npm run dev
# 打开 http://localhost:5173
# 在聊天框发送消息,应该不再出现 404 错误
```

## 📝 代码变更

**文件**: `backend/app/api/chat.py`

**变更行**: 第 105 行

```diff
- @router.post("/api/chat", response_model=ChatResponse)
+ @router.post("", response_model=ChatResponse)
  async def api_chat(request: ChatRequest):
      """
      REST API endpoint for chat (alternative to WebSocket).
+
+     Accessible at: POST /api/chat

      Request body:
          {
```

## 🚀 后续建议

### 1. 添加 API 测试

创建 `backend/tests/test_api_routes.py`:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_chat_endpoint_exists():
    """Test that POST /api/chat endpoint exists and returns 200/422"""
    response = client.post("/api/chat", json={
        "message": "test",
        "chat_history": []
    })
    # Should not be 404
    assert response.status_code != 404
```

### 2. 统一路由命名规范

在项目文档中明确规定:

- 主应用 prefix: `/api`
- 子路由 prefix: `/资源名` (如 `/chat`, `/sandbox`)
- 端点路径: 使用相对路径,避免重复前缀

**示例**:
```python
# ✅ 正确
router = APIRouter(prefix="/chat")
@router.post("")           # → /api/chat
@router.get("/sessions")   # → /api/chat/sessions

# ❌ 错误
@router.post("/api/chat")  # → /api/chat/api/chat (重复)
```

### 3. 添加路由自动检查脚本

创建 `backend/scripts/check_routes.py`:

```python
from app.main import app

print("=== Registered Routes ===")
for route in app.routes:
    if hasattr(route, "methods"):
        print(f"{list(route.methods)[0]:7} {route.path}")
```

运行:
```bash
python backend/scripts/check_routes.py
# 输出所有注册的路由,便于检查
```

## ✅ 问题已解决

- [x] 修复 `/api/chat` 路由 404 问题
- [x] 验证路由配置正确性
- [x] 更新文档说明实际路径
- [x] 提供测试验证方法

---

**修复时间**: 2026-01-22
**影响范围**: 前端聊天功能
**向后兼容**: 是 (只修复了错误的路由)
