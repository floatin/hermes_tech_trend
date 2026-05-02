# Chapter 7（草稿）：CLI + Skills 接入 MSP

> **副标题**：当 MCP 协议成为 AI Agent 的"USB-C"，谁能最先插上？

## 7.0 开篇：接口战争的本质

2026 年，AI Agent 战场从"模型能力比拼"转向"生态建设竞赛"。

这场竞赛的核心问题之一：**如何让 AI Agent 连接到外部世界？**

答案就是 **MCP（Model Context Protocol）**——一个被 HashiCorp 创始人 Mitchell Hashimoto 称为"AI Agent 的 USB-C"的协议。

但问题是：
- 3000+ MCP Servers 散落在 GitHub 各处
- 每个 MSP（Model Service Provider）有各自的接入方式
- AI Agent 的 Skills 系统如何与 MCP 无缝结合？

本章告诉你：
1. MCP 协议的核心原理
2. 如何用 CLI + Skills 快速接入 MSP
3. 精选 MSP 高价值接入方案

---

## 7.1 MCP 协议核心原理

### 7.1.1 什么是 MCP？

MCP 是一个开放协议，定义了 AI 应用与外部工具之间的通信标准：

```
┌─────────────────────────────────────────────┐
│              AI Agent / LLM                │
└─────────────────────────────────────────────┘
                      ↕ MCP
┌─────────────────────────────────────────────┐
│           MCP Host (Claude Desktop)         │
│                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │Filesystem│  │  GitHub  │  │ Slack   │   │
│  │ Server   │  │  Server  │  │ Server  │   │
│  └─────────┘  └─────────┘  └─────────┘   │
└─────────────────────────────────────────────┘
```

**类比**：MCP 就像 USB-C 接口——不管你用的是哪个品牌的电脑，只要设备支持，就能用同一条线连接所有外设。

### 7.1.2 MCP 的三层架构

```
MCP Message Format (JSON-RPC)
         ↓
┌─────────────────────────────────┐
│    Transport Layer              │
│    (stdio / HTTP / SSE)        │
└─────────────────────────────────┘
         ↓
┌─────────────────────────────────┐
│    MCP Protocol                │
│    - initialize                │
│    - tools/list                │
│    - tools/call               │
│    - resources/*              │
└─────────────────────────────────┘
         ↓
┌─────────────────────────────────┐
│    MCP Server Implementation   │
│    (Python / TypeScript / Go)  │
└─────────────────────────────────┘
```

### 7.1.3 MCP 与 Skills 的关系

| 维度 | MCP | Skills |
|------|-----|--------|
| **定位** | 通信协议 | 执行规范 |
| **作用** | 连接外部工具 | 定义如何使用工具 |
| **加载时机** | 运行时 | 启动时 |
| **示例** | GitHub MCP Server | `github-skills` |

**最佳实践**：MCP 作为底层传输，Skills 作为上层抽象。

---

## 7.2 CLI + Skills 快速接入模式

### 7.2.1 三种接入方式

```
┌────────────────────────────────────────────────────┐
│           CLI + Skills 接入 MSP                    │
├────────────────────────────────────────────────────┤
│                                                    │
│  方式 1：官方 MCP Server（推荐）                    │
│  npm install -g @modelcontextprotocol/server-github │
│  → 直接使用，品质有保证                            │
│                                                    │
│  方式 2：社区汇总方案                              │
│  awesome-mcp-servers (70k+ stars)                 │
│  → 3000+ MCP Servers 一网打尽                    │
│                                                    │
│  方式 3：自建 MCP Server                          │
│  TypeScript SDK / Python SDK                       │
│  → 定制化需求时使用                               │
│                                                    │
└────────────────────────────────────────────────────┘
```

### 7.2.2 官方 MCP Server 接入

```bash
# 1. 安装官方 server
npm install -g @modelcontextprotocol/server-github

# 2. 配置到 Claude Desktop
cat ~/.config/claude-desktop.json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your-token"
      }
    }
  }
}

# 3. 重启 Claude Desktop，验证
# → 可以直接问："列出最近 5 个 PR"
```

### 7.2.3 企业级 MCP 配置

```bash
# 通过 SKILL.md 封装 MCP 使用规范

# ───────────────────────────────────────
# github-skill.md
# ───────────────────────────────────────

# GitHub MCP Server 使用规范

## 触发条件
当用户提到以下关键词时激活：
- "GitHub"、"PR"、"Issue"、"Repo"
- "创建 PR"、"合并分支"、"查看提交"

## 使用限制
- 只读操作：无需审批
- 写操作（创建 PR、合并）：需要确认
- 删除操作：禁止

## 输出格式
- PR 信息：标题 + 状态 + 审查者
- Issue 信息：标题 + 标签 + 负责人
- 提交信息：简短描述 + 文件变更统计

## 敏感信息
- 不显示 token
- 不显示内部 API 地址
```

---

## 7.3 精选 MSP 高价值接入方案

### 7.3.1 GitHub（MCP）

**用途**：代码审查、PR 管理、Issue 处理

```bash
# 安装
npm install -g @modelcontextprotocol/server-github

# 功能覆盖
- repos/*：仓库管理
- issues/*：Issue CRUD
- pulls/*：PR 管理
- git/*：Git 操作
```

**适用场景**：代码审查流程自动化

### 7.3.2 Filesystem（MCP）

**用途**：文件读写、代码搜索

```bash
# 安装
npm install -g @modelcontextprotocol/server-filesystem

# 功能覆盖
- directory/*：目录操作
- file/*：文件 CRUD
- search/*：内容搜索
```

**适用场景**：大仓代码检索

### 7.3.3 Slack（MCP）

**用途**：团队通知、审批流程

```bash
# 安装
npm install -g @modelcontextprotocol/server-slack

# 功能覆盖
- chat.postMessage：发送消息
- conversations.list：列出频道
- users.list：列出用户
```

**适用场景**：AI 审查结果通知

### 7.3.4 Sentry（MCP）

**用途**：错误监控、告警处理

```bash
# 安装
npm install -g @modelcontextprotocol/server-sentry

# 功能覆盖
- events/*：错误事件
- issues/*：问题跟踪
- projects/*：项目管理
```

**适用场景**：生产问题自动告警

---

## 7.4 接入最佳实践

### 7.4.1 权限最小化原则

```json
// MCP Server 配置 - 权限控制
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

**Token 权限建议**：
- 只读场景：`repo:read` scope
- 读写场景：`repo` scope
- 企业场景：使用 GitHub App token

### 7.4.2 SKILL 封装规范

```markdown
# 安全审计 Skill

## 触发词
"安全"、"审计"、"漏洞"、"权限"

## 执行流程
1. 调用 Sentry MCP 检查最近错误
2. 调用 GitHub MCP 检查权限变更
3. 生成审计报告

## 禁止操作
- 不允许删除任何资源
- 不允许修改权限
- 不允许访问敏感配置
```

### 7.4.3 错误处理

```python
# MCP 调用错误处理
try:
    result = mcp.call_tool("github", "pulls_list", {
        "owner": "org",
        "repo": "repo",
        "state": "open"
    })
except MCPError as e:
    if e.code == "GITHUB_RATE_LIMITED":
        # 退化为缓存查询
        return get_cached_prs()
    raise
```

---

## 7.5 本章小结

1. **MCP 是 AI Agent 的 USB-C**，统一了外部工具的连接标准
2. **CLI + Skills 接入 MSP** 的三种方式：官方 Server → 社区汇总 → 自建
3. **企业级 MCP 配置** 需要：权限最小化 + SKILL 封装 + 错误处理
4. **最佳实践**：MCP 作为传输层，Skills 作为抽象层

---

## 7.6 延伸阅读

- [MCP 官方文档](https://modelcontextprotocol.io)
- [awesome-mcp-servers](https://github.com/wong2/awesome-mcp-servers)（70k+ stars）
- [GitHub MCP Server](https://github.com/github/github-mcp-server)
- [中文用户参考](https://github.com/yzfly/Awesome-MCP-ZH)
