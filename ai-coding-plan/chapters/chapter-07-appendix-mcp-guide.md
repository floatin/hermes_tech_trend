# Appendix F：MCP + Skills 接入决策树与场景化方案

> **一句话看懂**：什么场景用什么 MCP Server，看这张图就够了。

---

## F.1 MCP Server 选型决策树

```
你需要什么能力？
│
├─ 代码管理（GitHub/GitLab）
│   ├─ GitHub → @modelcontextprotocol/server-github
│   └─ GitLab → community/mcp-server-gitlab
│
├─ 文件操作
│   ├─ 本地文件 → @modelcontextprotocol/server-filesystem
│   └─ S3 → aws/mcp-server-s3
│
├─ 数据库
│   ├─ PostgreSQL → modelcontextprotocol/server-postgres
│   ├─ MongoDB → cognitivity/mcp-mongodb
│   └─ Redis → redis/servers/redis-mcp
│
├─ 消息通知
│   ├─ Slack → modelcontextprotocol/server-slack
│   └─ Discord → garrett/mcp-discord
│
├─ 搜索
│   ├─ Brave → modelcontextprotocol/server-brave-search
│   └─ Google → mcp-server-google
│
└─ 生产监控
    ├─ Sentry → modelcontextprotocol/server-sentry
    └─ PagerDuty → mcp-pagerduty
```

---

## F.2 场景化方案

### 场景 1：个人开发者，快速接入 GitHub

```
推荐方案：GitHub MCP + 基础 SKILL

安装：
  npm install -g @modelcontextprotocol/server-github

配置：
  # ~/.config/claude-desktop.json
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

Token 权限：
  repo（推荐最小）
  read:user（获取用户信息）

效果：
  - 直接用自然语言管理 GitHub
  - "列出我最近的 PR"
  - "创建本周开发总结的 Issue"
```

### 场景 2：企业团队，需要权限控制

```
推荐方案：GitHub MCP (App 认证) + Slack MCP + 复合 SKILL

安装：
  npm install -g @modelcontextprotocol/server-github
  npm install -g @modelcontextprotocol/server-slack

配置：
  # GitHub App 认证（推荐）
  {
    "mcpServers": {
      "github": {
        "command": "node",
        "args": ["/path/to/github-mcp-server"],
        "env": {
          "GITHUB_APP_ID": "123456",
          "GITHUB_APP_PRIVATE_KEY": "-----BEGIN RSA..."
        }
      }
    }
  }

SKILL 规范：
  # 每个 MCP 工具都有对应的 SKILL.md
  # 定义触发词、权限、输出格式
  github-mcp-skill.md
  slack-mcp-skill.md
  pr-review-notify-composite-skill.md

效果：
  - 细粒度权限控制（按仓库）
  - PR 审查自动通知 Slack
  - AI 行为可审计
```

### 场景 3：需要接入内部系统

```
推荐方案：自建 MCP Server

步骤 1：定义工具规范
  # internal-tools.ts
  const tools = [
    {
      name: "order_query",
      description: "查询订单信息",
      inputSchema: {
        type: "object",
        properties: {
          orderId: { type: "string" }
        },
        required: ["orderId"]
      }
    },
    // ...
  ]

步骤 2：实现处理器
  async function orderQueryHandler(params) {
    const order = await internalAPI.getOrder(params.orderId)
    return {
      content: [{ type: "text", text: JSON.stringify(order) }]
    }
  }

步骤 3：部署
  # Docker 部署
  docker build -t internal-mcp .
  docker run -p 8080:8080 internal-mcp

步骤 4：接入 Skills
  # internal-api-skill.md
  # 封装为可复用规范

效果：
  - 内部 API 对 AI Agent 开放
  - 保持内部系统安全隔离
  - 工具可复用、可版本化
```

---

## F.3 SKILL 封装模式

### 模式 1：单一 MCP 工具封装

```markdown
# filesystem-read-skill.md

> 触发词："读取文件"、"查看代码"、"cat"

## MCP 工具
`filesystem/read`

## 参数
- path: 文件路径（必填）
- options.offset: 字节偏移（可选）
- options.limit: 读取行数（可选，默认 100）

## 约束
- 禁止读取：.env, *.key, *.pem, secrets/*
- 大文件（>1MB）需要确认

## 输出格式
```
// [文件路径]（第 N-M 行）
[代码内容]
```
```

### 模式 2：多 MCP 工具组合

```markdown
# github-pr-review-skill.md

> 触发词："审查 PR"、"检查代码"

## 执行流程

### Step 1: 获取 PR 信息
MCP: github/pulls_get

### Step 2: 获取代码变更
MCP: github/diff

### Step 3: 分析变更
（AI 内部推理）

### Step 4: 格式化审查意见
```

## 约束
- 只读，不自动评论
- 提供审查意见，让人类决定是否评论
```

### 模式 3：跨 MCP 服务编排

```markdown
# incident-alert-skill.md

> 触发词："生产问题"、"服务告警"、" incident"

## 执行流程

### Step 1: 从 Sentry 获取错误详情
MCP: sentry/events_list

### Step 2: 获取最近部署
MCP: github/deployments_list

### Step 3: 确定责任人
MCP: slack/users_find_by_email

### Step 4: 发送告警
MCP: slack/chat_postMessage

## 约束
- 自动发送到 #oncall 频道
- 包含：错误摘要 + 责任人 + 链接
- 保留 5 分钟内不重复告警
```

---

## F.4 避坑速查表

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| MCP Server 无法启动 | Node.js 版本不对 | Node.js ≥ 18 |
| Token 无效 | PAT 没有正确 scope | 检查 repo:read 或 repo |
| AI 不知道用 MCP | 缺少 SKILL 触发词 | 在 SKILL.md 定义触发词 |
| MCP 工具返回乱码 | 编码问题 | 使用 `--utf8` flag |
| Rate Limit | 频繁调用 API | 实现缓存 + 请求节流 |
| Docker 部署连接失败 | 端口映射问题 | `-p 8080:8080` |

---

## F.5 快速参考命令

```bash
# 安装 GitHub MCP Server
npm install -g @modelcontextprotocol/server-github

# 安装 Slack MCP Server
npm install -g @modelcontextprotocol/server-slack

# 安装 Filesystem MCP Server
npm install -g @modelcontextprotocol/server-filesystem

# 安装 Sentry MCP Server
npm install -g @modelcontextprotocol/server-sentry

# 查看已安装的 MCP Server
claude mcp list

# 测试 MCP Server
npx -y @modelcontextprotocol/server-github --help

# 调试 MCP 通信
DEBUG=mcp:* claude
```

---

## F.6 MCP Server 生态速查

| 分类 | Server | Stars | 官方 |
|------|--------|-------|------|
| **代码管理** | github-mcp-server | 2.1k | ✅ |
| | gitlab-mcp-server | 800+ | ❌ |
| | bitbucket-mcp | 200+ | ❌ |
| **文件系统** | filesystem | 4k+ | ✅ |
| **数据库** | postgres | 1.2k | ✅ |
| | mongodb | 500+ | ❌ |
| **消息** | slack | 2k+ | ✅ |
| | discord | 300+ | ❌ |
| **监控** | sentry | 1.5k | ✅ |
| | datadog | 200+ | ❌ |
| **搜索** | brave-search | 3k+ | ✅ |
| **云服务** | aws-mcp | 800+ | ❌ |
| | gcp-mcp | 300+ | ❌ |

---

**核心原则**：先用官方 Server 验证可行性，再按需扩展社区 Server，最后自建定制 Server。**不要过度工程化**。
