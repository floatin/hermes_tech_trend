# Chapter 7-B（深度补充）：MCP 协议原理与 Skills 集成实战

> **副标题**：从协议栈到源码，理解 MCP 如何成为 AI Agent 的"USB-C"

---

## 7-B.0 开篇：为什么深入 MCP？

**问题**：市面上有 3000+ MCP Servers，但大多数开发者只停留在"安装和使用"层面，不理解：

1. MCP 的协议栈是如何设计的？
2. 为什么 MCP 能统一"AI Agent 连接外部世界"的体验？
3. 如何基于 SDK 实现自己的 MCP Server？

不理解原理，就只能做使用者；理解原理，才能做创造者。

---

## 7-B.1 MCP 协议栈解析

### 7-B.1.1 三层架构

MCP 协议分为三层，每层有明确的职责：

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Application Layer（应用层）                          │
│   MCP Protocol Messages                                     │
│   - tools/call, resources/read, prompts/get                │
└─────────────────────────────────────────────────────────────┘
                           ↓ JSON-RPC 2.0
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Transport Layer（传输层）                           │
│   - stdio（本地进程通信）                                   │
│   - SSE（Server-Sent Events，HTTP 长连接）                   │
│   - Streamable HTTP（双向流）                               │
│   - WebSocket                                               │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Message Format（消息格式）                         │
│   - JSON-RPC 2.0                                           │
│   - Content Blocks（文本、图片、资源）                        │
│   - Error Objects                                          │
└─────────────────────────────────────────────────────────────┘
```

**设计亮点**：传输层和消息格式分离。同一个 MCP Server，可以通过 stdio 连接本地 Claude Desktop，也可以通过 HTTP 连接远程 AI Agent。

### 7-B.1.2 消息格式（JSON-RPC 2.0）

MCP 所有消息都是 JSON-RPC 2.0 格式：

```json
// 请求
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "github_pulls_list",
    "arguments": {
      "owner": "facebook",
      "repo": "react",
      "state": "open"
    }
  }
}

// 响应
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Found 42 open pull requests..."
      }
    ]
  }
}

// 错误
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": "Missing required parameter: owner"
  }
}
```

### 7-B.1.3 Content Blocks：MCP 的内容抽象

MCP 定义了统一的内容块格式：

```python
# Python SDK 中的 Content 类型
class TextContent(BaseModel):
    type: Literal["text"]
    text: str

class ImageContent(BaseModel):
    type: Literal["image"]
    data: str  # base64
    mimeType: str

class ResourceContents(BaseModel):
    type: Literal["resource"]
    resource: Resource
    mimeType: str
    text: str | None

# 工具返回结果可以是多种 Content 的混合
CallToolResult(content=[
    TextContent(text="PR #123: Fix bug"),
    ImageContent(data="...", mimeType="image/png"),
])
```

**设计亮点**：统一了文本、图片、资源的格式。AI Agent 看到的永远是一致的结构，不需要为每种内容类型写不同的处理逻辑。

---

## 7-B.2 Python SDK 源码解析

### 7-B.2.1 核心类型

MCP Python SDK 的类型定义在 `src/mcp/types.py`：

```python
# 工具定义
class Tool(BaseModel):
    name: str
    description: str | None = None
    inputSchema: dict[str, Any]  # JSON Schema

# 资源定义
class Resource(BaseModel):
    uri: str
    name: str | None = None
    description: str | None = None
    mimeType: str | None = None

# Prompt 定义
class Prompt(BaseModel):
    name: str
    description: str | None = None
    arguments: list[PromptArgument] | None = None
```

### 7-B.2.2 Server 类的核心结构

从 `src/mcp/server/lowlevel/server.py` 的源码（行 30-50）：

```python
class Server(Generic[LifespanResultT]):
    def __init__(
        self,
        name: str,
        *,
        version: str | None = None,
        title: str | None = None,
        description: str | None = None,
        instructions: str | None = None,
        # 生命周期钩子
        lifespan: Callable[
            [Server[LifespanResultT]],
            AbstractAsyncContextManager[LifespanResultT],
        ] = lifespan,
        # 请求处理器
        on_list_tools: Callable[
            [ServerRequestContext, types.PaginatedRequestParams | None],
            Awaitable[types.ListToolsResult],
        ] | None = None,
        on_call_tool: Callable[
            [ServerRequestContext, types.CallToolParams],
            Awaitable[types.CallToolResult],
        ] | None = None,
        on_list_resources: Callable[...],
        on_read_resource: Callable[...],
        on_list_prompts: Callable[...],
        # ... 更多钩子
    ):
```

**设计亮点**：基于**钩子（Hook）的注册模式**。不是继承一个基类，而是传入回调函数。这让 MCP Server 的实现非常灵活。

### 7-B.2.3 创建 MCP Server 的标准范式

```python
# 1. 定义工具处理器
async def list_pulls(ctx, params):
    """列出 Pull Requests"""
    return types.ListToolsResult(tools=[
        types.Tool(
            name="github_pulls_list",
            description="List pull requests in a GitHub repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "state": {"type": "string", "enum": ["open", "closed", "all"]},
                },
                "required": ["owner", "repo"],
            },
        )
    ])

async def call_pulls_list(ctx, params):
    """调用 GitHub API"""
    # 调用真实的 GitHub API
    result = await github_api.pulls.list(...)
    return types.CallToolResult(content=[
        types.TextContent(text=f"Found {len(result)} PRs")
    ])

# 2. 创建 Server 实例
server = mcp.server.Server(
    "github",
    on_list_tools=list_pulls,
    on_call_tool=call_pulls_list,
)

# 3. 运行 Server
async def main():
    async with mcp.server.stdio.stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

asyncio.run(main())
```

**核心洞察**：MCP Server 的开发模式非常简单——**定义工具 → 注册处理器 → 运行**。业务逻辑和协议处理完全分离。

### 7-B.2.4 传输层实现

#### stdio 传输（`src/mcp/server/stdio.py`）

```python
@asynccontextmanager
async def stdio_server():
    """标准输入输出传输"""
    read_stream = ReadStream.from_stdout()  # 从 stdin 读取
    write_stream = WriteStream.to_stdin()     # 写入 stdout
    
    # 注意：MCP 协议通过 stdin/stdout 通信
    # Claude Desktop 启动 MCP Server 时，stdin 接收 JSON-RPC 消息
    # stdout 发送 JSON-RPC 响应
    yield read_stream, write_stream
```

**典型应用场景**：

```
Claude Desktop 启动 github-mcp-server:
  stdin ← JSON-RPC 请求（"调用 tools/call"）
  stdout → JSON-RPC 响应（"PR 列表"）
```

#### Streamable HTTP（`src/mcp/server/streamable_http.py`）

```python
class StreamableHTTPASGIApp:
    """HTTP 长连接传输"""
    # 支持：
    # - POST /mcp/message/：发送请求
    # - GET /mcp/stream/：SSE 流式接收
    # - DELETE /mcp/sessions/{id}：关闭会话
```

**典型应用场景**：

```
远程 AI Agent 连接 MCP Server:
  POST https://api.example.com/mcp/message/
  Body: { "jsonrpc": "2.0", "method": "tools/call", ... }
  Response: { "jsonrpc": "2.0", "result": { "content": [...] } }
```

---

## 7-B.3 GitHub MCP Server 架构解析

### 7-B.3.1 项目结构

```
github-mcp-server/
├── src/
│   ├── github/
│   │   ├── client.ts         # GitHub API 客户端
│   │   ├── tools/
│   │   │   ├── repos.ts      # 仓库操作
│   │   │   ├── issues.ts     # Issue 操作
│   │   │   ├── pulls.ts      # PR 操作
│   │   │   └── ...
│   │   └── index.ts          # 入口
│   └── main.ts               # CLI 入口
├── package.json
└── README.md
```

### 7-B.3.2 工具定义模式

以 `pulls.ts` 为例：

```typescript
// 定义工具
export const pullsListTool: Tool = {
  name: "pulls_list",
  description: "List pull requests in a GitHub repository",
  inputSchema: {
    type: "object",
    properties: {
      owner: { type: "string", description: "Repository owner" },
      repo: { type: "string", description: "Repository name" },
      state: {
        type: "string",
        enum: ["open", "closed", "all"],
        description: "Filter by state"
      },
      per_page: { type: "number", default: 30 },
    },
    required: ["owner", "repo"],
  },
}

// 实现处理器
export async function pullsListHandler(params: any) {
  const { owner, repo, state = "open", per_page = 30 } = params
  
  const pulls = await githubClient.pulls.list({
    owner, repo, state, per_page
  })
  
  return {
    content: pulls.map(pr => ({
      type: "text" as const,
      text: `PR #${pr.number}: ${pr.title} (${pr.state})`
    }))
  }
}
```

### 7-B.3.3 认证机制

GitHub MCP Server 支持两种认证：

```typescript
// 方式 1：Personal Access Token（适合个人使用）
// 配置：GITHUB_PERSONAL_ACCESS_TOKEN

// 方式 2：GitHub App Token（适合企业）
// 配置：GITHUB_APP_ID + GITHUB_APP_PRIVATE_KEY

// 内部自动处理 token 刷新
class GitHubClient {
  private async getAccessToken(): Promise<string> {
    if (this.authType === "app") {
      // 使用 jwt 签名获取 App token
      return this.getAppToken()
    }
    return this.personalToken
  }
}
```

---

## 7-B.4 Skills 与 MCP 集成实战

### 7-B.4.1 集成的三种模式

```
┌─────────────────────────────────────────────────────────────┐
│ Skills 层（MCP 使用规范）                                    │
│                                                             │
│   Skill: github-check-pr-skill.md                           │
│   ├── 触发词：PR、审查、合并                                 │
│   ├── 调用：github_mcp pulls_list                           │
│   └── 输出格式：标题 + 状态 + 审查者                         │
└─────────────────────────────────────────────────────────────┘
                            ↓ 调用
┌─────────────────────────────────────────────────────────────┐
│ MCP 层（协议传输）                                           │
│                                                             │
│   MCP Server → stdio → Claude Desktop                       │
│   或                                                         │
│   MCP Server → HTTP → 远程 AI Agent                         │
└─────────────────────────────────────────────────────────────┘
                            ↓ 请求
┌─────────────────────────────────────────────────────────────┐
│ 外部服务层（真实 API）                                       │
│                                                             │
│   GitHub API / Slack API / Filesystem                       │
└─────────────────────────────────────────────────────────────┘
```

### 7-B.4.2 SKILL.md 封装示例

创建 `skills/github-mcp-skill.md`：

```markdown
# GitHub MCP Skill

> 当用户提到以下关键词时激活此 Skill：
> "GitHub"、"PR"、"Issue"、"Repo"、"创建 PR"、"合并分支"

## 工具映射

| 操作 | MCP 工具 | 参数 |
|------|----------|------|
| 列出 PR | `pulls_list` | owner, repo, state |
| 创建 PR | `pulls_create` | owner, repo, title, body, head, base |
| 查看提交 | `commits_list` | owner, repo, sha |
| 创建 Issue | `issues_create` | owner, repo, title, body |

## 使用约束

### 只读操作（无需确认）
- 查看 PR 列表
- 查看 Issue 列表
- 查看提交历史
- 查看代码

### 写操作（需要人类确认）
- 创建 PR
- 合并 PR
- 创建 Issue
- 评论

### 禁止操作（永不执行）
- 删除仓库
- 删除 PR
- 修改保护分支规则

## 输出格式

### PR 信息
```
#[PR编号] [标题]
状态: [open/closed/merged]
作者: @用户名
审查者: @用户名1, @用户名2
链接: https://github.com/...
```

### Issue 信息
```
#[Issue编号] [标题]
标签: [bug/enhancement/documentation]
负责人: @用户名
创建时间: YYYY-MM-DD
链接: https://github.com/...
```

## 错误处理

### Rate Limit
```
GitHub API 速率限制已触发。请：
1. 等待 1 小时后重试
2. 或使用 --token 指定更高权限的 token
```

### 认证失败
```
GitHub 认证失败。请检查：
1. GITHUB_PERSONAL_ACCESS_TOKEN 是否设置
2. Token 是否有 repo 权限
```

### 资源不存在
```
未找到指定的仓库或资源。请确认：
1. owner/repo 名称正确
2. 你有访问该仓库的权限
```
```

### 7-B.4.3 复合 Skill 示例

组合 GitHub + Slack MCP 实现"PR 审查通知"：

```markdown
# PR Review Notify Composite Skill

> 触发词："通知审查者"、"PR 审查"、"审查完了"

## 执行流程

### Step 1: 获取 PR 信息
```
MCP 调用: github_mcp pulls_get
参数: { owner, repo, pull_number }
→ 获取 PR 标题、审查者、状态
```

### Step 2: 格式化通知消息
```
标题: [PR] {title} 需要审查
正文:
- PR #{number} 于 {created_at} 创建
- 审查者: {reviewers}
- 链接: {html_url}
```

### Step 3: 发送到 Slack
```
MCP 调用: slack_mcp chat_postMessage
参数: {
  channel: "#engineering",
  text: 格式化后的消息
}
```

### Step 4: 确认发送
```
返回: 已通知 {reviewer_count} 位审查者
```
```

---

## 7-B.5 生产环境避坑指南

### 坑 #1：Token 权限过大

**症状**：MCP Server 可以访问所有仓库，包括私有仓库

**原因**：使用的 PAT（Personal Access Token）有 `repo` 全部权限

**解决**：使用最小权限的 Token

```bash
# 只读场景
token scopes: repo:read

# 读写场景
token scopes: repo

# 建议：使用 GitHub App 替代 PAT
# GitHub App 可以精确控制每个仓库的权限
```

### 坑 #2：stdio 模式下 Server 不退出

**症状**：Claude Desktop 关闭后，MCP Server 进程仍在运行

**原因**：没有正确处理 `SIGTERM` 信号

**解决**：在 Server 代码中处理生命周期

```python
async def main():
    # 设置优雅退出
    shutdown = anyio.Event()
    
    def signal_handler():
        shutdown.set()
    
    # 注册信号处理器
    signal.signal(signal.SIGTERM, lambda s, f: shutdown.set())
    
    async with mcp.server.stdio.stdio_server() as (read, write):
        await server.run(read, write, ...)  # 使用 shutdown 事件
```

### 坑 #3：HTTP 模式下的 CORS 问题

**症状**：浏览器端无法调用 MCP Server

**原因**：缺少 CORS 头

**解决**：在 HTTP 传输层配置 CORS

```python
app = StreamableHTTPASGIApp(
    ...
    cors_allow_origins=["https://claude.ai"],
    cors_allow_methods=["POST", "GET"],
    cors_allow_headers=["Content-Type", "Authorization"],
)
```

### 坑 #4：Rate Limit 导致服务不可用

**症状**：间歇性返回空结果或错误

**原因**：GitHub API 速率限制（5000 请求/小时）

**解决**：实现请求节流和缓存

```python
class RateLimitedClient:
    def __init__(self):
        self.cache = {}
        self.last_request = 0
        self.min_interval = 0.1  # 最小请求间隔
    
    async def request(self, method, **kwargs):
        # 节流
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            await asyncio.sleep(self.min_interval - elapsed)
        
        # 检查缓存
        cache_key = f"{method}:{kwargs}"
        if cache_key in self.cache:
            cached, timestamp = self.cache[cache_key]
            if time.time() - timestamp < 300:  # 5 分钟缓存
                return cached
        
        result = await self.github_api.request(method, **kwargs)
        self.cache[cache_key] = (result, time.time())
        return result
```

---

## 7-B.6 本章小结

1. **MCP 协议栈**：应用层（JSON-RPC）→ 传输层（stdio/HTTP/SSE）→ 消息格式（Content Blocks）
2. **Python SDK 核心**：基于钩子的 Server 类，业务逻辑和协议处理分离
3. **GitHub MCP Server**：工具定义 + API 客户端 + 认证管理
4. **Skills 集成**：SKILL.md 封装 MCP 工具为可复用规范
5. **生产避坑**：Token 最小权限、优雅退出、CORS、Rate Limit

---

## 延伸阅读

- [MCP Python SDK 源码](https://github.com/modelcontextprotocol/python-sdk)
- [MCP TypeScript SDK 源码](https://github.com/modelcontextprotocol/typescript-sdk)
- [GitHub MCP Server 源码](https://github.com/github/github-mcp-server)
- [awesome-mcp-servers](https://github.com/wong2/awesome-mcp-servers)（70k+ stars）
- [MCP 协议规范](https://spec.modelcontextprotocol.io)
