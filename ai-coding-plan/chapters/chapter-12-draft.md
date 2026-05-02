# Chapter 12（草稿）：记忆系统——让 AI 记住一切

> **副标题**：Claude Code 没有记忆，但你的代码库有。

## 12.0 开篇：AI 编程的"金鱼问题"

Claude Code 有个外号：**"金鱼"**。

为什么？

因为金鱼的记忆只有 7 秒。
Claude Code 的记忆更短——**每次新会话，都是一张白纸**。

上个月你花了 3 天解决的认证 Bug，Claude Code 不知道。
上周你做的"为什么用 JWT 不用 Session"的架构决策，Claude Code 不记得。
昨天你重构的支付模块，Claude Code 不理解为什么那样改。

**这就是 AI Coding 的"金鱼问题"——上下文窗口用完，AI 就忘了。**

记忆系统要解决的，就是这个问题。

本章告诉你：
1. 为什么 AI 需要记忆
2. 记忆系统的四层架构
3. 主流记忆系统对比
4. 如何构建适合自己团队的记忈系统

---

## 12.1 为什么 AI 需要记忆

### 12.1.1 AI 编程的记忆困境

```
传统软件开发：
  开发者 → 代码 → 注释 → 文档 → 团队知识库
                ↑____________________________|
                    人类的持久记忆

AI 编程：
  AI Agent → 代码 → 上下文窗口
                    ↑____|
                      AI 没有持久记忆
```

### 12.1.2 记忆缺失的后果

| 问题 | 表现 | 代价 |
|------|------|------|
| 重复工作 | 上个月解决的 Bug，这个月又出现 | 浪费 3 天 |
| 决策丢失 | 为什么用 JWT 而非 Session？没人知道 | 技术债堆积 |
| 上下文断裂 | 新会话要重新介绍项目背景 | 每次多花 30 分钟 |
| 知识孤岛 | 团队成员各自为战 | 重复造轮子 |

### 12.1.3 记忆系统的价值

```
有记忆系统后：
  新会话开始
  ↓
  AI 自动注入历史上下文
  "你上次解决了认证 Bug，使用了 JWT 方案..."
  ↓
  AI 理解项目背景，继续工作
  ↓
  节省 30 分钟上下文重建时间
```

---

## 12.2 记忆系统的四层架构

### 12.2.1 四层模型

```
┌─────────────────────────────────────────────────────────┐
│                 记忆系统分层架构                          │
├─────────────────────────────────────────────────────────┤
│  L4 语义记忆 (Semantic Memory)                          │
│       项目级知识：架构决策、技术栈、约定俗成               │
│       "为什么选 PostgreSQL 而非 MySQL"                  │
├─────────────────────────────────────────────────────────┤
│  L3 情景记忆 (Episodic Memory)                          │
│       事件级记录：完成的功能、修复的 Bug、尝试过的方案    │
│       "2026-04 完成支付模块重构"                        │
├─────────────────────────────────────────────────────────┤
│  L2 工作记忆 (Working Memory)                           │
│       会话级状态：当前任务目标、进行中的上下文            │
│       "当前正在处理订单历史页面"                        │
├─────────────────────────────────────────────────────────┤
│  L1 感知记忆 (Sensory Memory)                           │
│       原始输入：工具调用、文件改动、命令输出              │
│       "文件 X 被修改，函数 Y 被删除"                    │
└─────────────────────────────────────────────────────────┘
```

### 12.2.2 各层特点

| 层次 | 内容 | 持久性 | 检索方式 |
|------|------|--------|---------|
| L1 感知记忆 | 原始工具输出 | 临时 | 日志 |
| L2 工作记忆 | 当前会话状态 | 会话级 | 内存 |
| L3 情景记忆 | 完成的事件 | 持久 | 时间线 |
| L4 语义记忆 | 项目知识 | 持久 | 语义 |

### 12.2.3 渐进式披露策略

最好的记忆系统不是一股脑把所有记忆塞给 AI，而是**按需渐进披露**：

```
Level 1: 最近 3 条观察记录（最近 10 分钟）
         → "今天我重构了 auth 模块的 token 验证逻辑"

Level 2: 项目概览（最近 5 次会话）
         → "本周完成了：支付集成、订单历史、用户画像功能"

Level 3: 详细历史（按需检索）
         → 检索 "auth 相关决策" → 找到 "2024-03 使用 JWT 而非 Session"
```

---

## 12.3 主流记忆系统对比

### 12.3.1 claude-mem：Claude Code 专用

**代表项目**：`thedotmack/claude-mem` ⭐ 59k

**架构**：
```
7 个生命周期钩子
├── context-hook    → 会话启动：注入历史上下文
├── new-hook       → 用户提问：保存会话
├── save-hook      → 工具执行后：捕获文件改动
├── summary-hook   → 会话结束：AI 摘要持久化
└── cleanup-hook   → 停止指令：清理临时数据

存储层
├── SQLite FTS5    → 全文检索
└── Chroma        → 向量语义搜索
```

**核心能力**：
- **AI 压缩**：将 1000~10000 Token 的工具输出压缩为约 500 Token 的语义摘要
- **渐进式披露**：Level 1 → Level 2 → Level 3
- **开箱即用**：Claude Code Plugin 市场一键安装

**安装**：
```bash
# Claude Code 中
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem
# 重启后自动生效
```

### 12.3.2 engram：Agent 无偏好

**代表项目**：`Gentleman-Programming/engram`

**特点**：
- Go 语言，单二进制，无外部依赖
- MCP 协议兼容，可接入任何 Agent
- SQLite FTS5 全文检索
- Web UI 内置

**安装**：
```bash
curl -fsSL https://engram.sh/install.sh | sh
engram server --port 8080
```

### 12.3.3 agentmemory：多 Agent 支持

**代表项目**：`rohitg00/agentmemory`

**特点**：
- ChromaDB 向量存储 + PostgreSQL 可选
- Claude Code Plugin 市场官方收录
- 支持 `doctor` 命令自检
- 内置文件压缩工具

### 12.3.4 对比表

| 系统 | 存储 | Agent 支持 | 安装难度 | 适合场景 |
|------|------|-----------|---------|---------|
| claude-mem | SQLite + Chroma | Claude Code 专用 | ⭐ 一键 | Claude Code 用户 |
| engram | SQLite FTS5 | MCP 兼容 | ⭐ 简单 | 多 Agent 团队 |
| agentmemory | Chroma + PG | 多 Agent | ⭐⭐ 中等 | 企业级 |

---

## 12.4 构建适合自己团队的记忈系统

### 12.4.1 最小化方案：使用 claude-mem

```bash
# 1. 安装
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem

# 2. 配置存储位置（可选）
export CLAUDE_MEM_PATH=~/claude-mem-data

# 3. 验证
> /mem status
# → 显示记忆状态和统计
```

### 12.4.2 企业级方案：自建 engram

```bash
# 1. 部署 engram 服务
docker run -d \
  --name engram \
  -p 8080:8080 \
  -v engram-data:/data \
  ghcr.io/gentleman-programming/engram

# 2. 配置 MCP 接入
# 在 Claude Code 的 MCP 配置中添加：
{
  "mcpServers": {
    "engram": {
      "command": "npx",
      "args": ["-y", "@engram/mcp"],
      "env": {
        "ENGRAM_URL": "http://localhost:8080"
      }
    }
  }
}

# 3. 验证
> /mem query "架构决策"
# → 返回历史记录
```

### 12.4.3 记忆组织最佳实践

```markdown
# 项目记忆结构示例

## 项目级知识 (L4)
- architecture.md        # 架构决策记录
- tech-stack.md         # 技术栈说明
- conventions.md         # 代码规范

## 情景记忆 (L3)
- 2026-04-payment.md   # 本月完成的功能
- 2026-03-auth.md      # 上月完成的功能

## 决策记录 (L3)
- decisions/
  - 2026-04-15-jwt-vs-session.md
  - 2026-03-10-postgres-vs-mysql.md
```

---

## 12.5 记忆系统的局限与应对

### 12.5.1 记忆的时效性

**问题**：记忆可能过时

**应对**：
```bash
# 定期清理
/mem cleanup --older-than=30d

# 手动标记过期
/mem update <id> --expire
```

### 12.5.2 记忆的隐私

**问题**：敏感信息可能被记住

**应对**：
```bash
# 设置隐私规则
# .claude-memory-ignore
passwords/**
secrets/**
.env
```

### 12.5.3 记忆的检索质量

**问题**：检索结果不相关

**应对**：
- 定期优化检索词
- 使用语义相似度重排序
- 手动标记重要记忆

---

## 12.6 本章小结

1. **AI 编程的"金鱼问题"**：新会话没有上下文，每次都要重建
2. **四层记忆架构**：感知记忆 → 工作记忆 → 情景记忆 → 语义记忆
3. **渐进式披露**：Level 1（最近）→ Level 2（概览）→ Level 3（详情）
4. **主流系统对比**：claude-mem（Claude Code 专用）vs engram（多 Agent）vs agentmemory（企业级）
5. **最佳实践**：最小化方案用 claude-mem，企业级方案用 engram

---

## 12.7 延伸阅读

- [claude-mem](https://github.com/thedotmack/claude-mem)（59k stars）
- [engram](https://github.com/Gentleman-Programming/engram)
- [agentmemory](https://github.com/rohitg00/agentmemory)
- [AI Agents Memory: State of the Art](https://arxiv.org/abs/xxxx.xxxxx)（学术论文）
