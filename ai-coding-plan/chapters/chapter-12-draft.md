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

### 12.3.4 MemPalace：宫殿记忆术 + 本地优先

**代表项目**：`MemPalace/mempalace` ⭐ 50.7k（2026年4月发布，2天2.6万 Star）

**背景**：由演员 Milla Jovovich 与技术合伙人 Ben Sigman 联合发布，灵感来自古希腊"记忆宫殿"（Method of Loci）。它解决了一个根本问题——大多数记忆系统只是"大容量仓库"，而 MemPalace 实现了**按空间结构索引 + 语义检索**的双通道记忆。

**核心洞察：记忆宫殿的空间哲学**

古代演说家在想象中行走于建筑各处记忆演讲内容——每个房间存放一个念头。MemPalace 将此工程化：

```
MEMORY PALACE
├── WING（侧楼）     → 一个人物或一个项目
│   └── Room A      → 特定话题（如 auth-migration）
│       ├── Hall    → 概念分类（decisions/diary/explore）
│       │   ├── Closet → AAAK 压缩摘要（指向抽屉的指针）
│       │   └── Drawer → 逐字原文（向量检索层）
│       └── Hall    → 另一个分类
├── WING（另一个项目）
└── Tunnel          → Wing 之间的跨项目连接
```

**三层核心创新**：

#### 创新1：逐字存储（Verbatim Storage）

MemPalace **不摘要、不提取、不改写**。原始对话直接存入 Drawer：

```
传统 RAG：对话 → LLM 摘要 → 丢失细节 → 检索质量下降
MemPalace：对话 → 逐字存入 Drawer → 语义向量检索 → 96.6% R@5（零 API）
```

#### 创新2：AAAK 方言压缩

AAAK（实验性有损缩写系统）专为 AI 可读压缩设计：

```python
# 输入：Kai 今天说 auth-migration 项目已完成了，Maya 曾负责此项目

# AAAK 输出示例
HEADER: F003|KAI|2026-05-02|auth-migration complete
ZETTEL: Z003:[KAI,MAYA,AUTH-MIGRATION]|project_complete|"complete"|9|vul,joy|DECISION,TECHNICAL
```

- **实体编码**：KAI=Kai，MAYA=Maya（三字母大写）
- **情绪编码**：vul=vulnerability，joy=joy
- **标记位**：DECISION/TECHNICAL/PIVOT 等
- 无需解码器，任何 LLM 直接阅读

当前 AAAK 模式得分 84.2% R@5（vs 原始 96.6%），仍在迭代。

#### 创新3：时序知识图谱

内置 SQLite 图谱引擎，存储"实体-关系-时间窗"三元组：

```python
from mempalace.knowledge_graph import KnowledgeGraph
kg = KnowledgeGraph()

# 添加带时间窗的事实
kg.add_triple("Kai", "works_on", "Orion", valid_from="2025-06-01")
kg.add_triple("Maya", "assigned_to", "auth-migration", valid_from="2026-01-15")
kg.add_triple("Maya", "completed", "auth-migration", valid_from="2026-02-01")

# 当前查询（自动排除过期事实）
kg.query_entity("Maya")
# → completed 有效，assigned 已排除

# 时间旅行查询
kg.query_entity("Maya", as_of="2026-01-20")
# → 当时 Maya 还在做 auth-migration
```

**关键价值**：技术决策变更时，旧决策不删除而标记 `invalidated`。AI 能理解"为什么当时选 PostgreSQL 而非 MySQL"——以及"后来为什么换了"。

#### 创新4：4层记忆栈（Memory Stack）

分层渐进加载，而非一股脑注入全部记忆：

| 层级 | 内容 | Token | 触发 |
|------|------|-------|------|
| L0 Identity | 身份文件 | ~50-100 | **始终** |
| L1 Essential Story | 最重要时刻摘要 | ~500-800 | **始终** |
| L2 On-Demand Recall | Wing/Room 过滤检索 | 200-500/次 | 话题出现 |
| L3 Deep Search | 全量语义搜索 | 可变 | 显式提问 |

```python
from mempalace.layers import MemoryStack
stack = MemoryStack()

# 典型唤醒：L0 + L1 = ~600-900 tokens
wake = stack.wake_up()

# 按 Wing 检索（L2）
auth = stack.recall(wing="myapp", room="auth-migration")

# 深度搜索（L3）
results = stack.search("为什么从 JWT 换到 Session")
```

#### MCP 工具生态

29个 MCP 工具覆盖宫殿读写、知识图谱、跨 Wing 导航：

```javascript
// 跨 Wing 发现共享话题
mcp工具: mempalace_traverse
  → 发现 auth-migration 同时出现在 wing_kai, wing_driftwood

// 知识图谱操作
mempalace_kg_query      // 时序实体查询
mempalace_kg_add        // 添加事实
mempalace_kg_invalidate // 标记过期
mempalace_kg_timeline   // 时间线故事
```

#### 性能基准（可100%复现）

| 基准 | 指标 | 分数 | 说明 |
|------|------|------|------|
| LongMemEval（500题） | R@5 | **96.6%** | 零 API，纯原始检索 |
| LongMemEval（450题 held-out） | R@5 | **98.4%** | 混合模式泛化分数 |
| LoCoMo | R@10 | 88.9% | 混合模式 |
| ConvoMem | Avg Recall | 92.9% | 250条目 |

#### 安装与使用

```bash
pip install mempalace
mempalace init ~/projects/myapp

# CLI
mempalace mine ~/projects/myapp                    # 挖掘项目文件
mempalace mine ~/.claude/projects/ --mode convos   # 挖掘会话
mempalace search "为什么切换到 GraphQL"
mempalace wake-up                                  # 生成唤醒上下文
```

### 12.3.5 四系统对比

| 维度 | claude-mem | engram | agentmemory | **MemPalace** |
|------|------------|--------|-------------|---------------|
| 存储哲学 | LLM 摘要 | 原始文本 | 混合 | **逐字 + AAAK 可选** |
| 组织结构 | 平坦 | 平坦 | 平坦 | **宫殿结构** |
| 知识图谱 | ❌ | ❌ | 基础 | **时序图谱（SQLite）** |
| 压缩方案 | LLM 摘要 | 无 | 无 | **AAAK 方言** |
| 检索性能 | 未公布 | 未公布 | 未公布 | **96.6% R@5** |
| API 调用 | 需要 | 需要 | 需要 | **零 API（原始）** |
| 安装 | ⭐ 一键 | ⭐ 简单 | ⭐⭐ | **⭐ 简单** |
| 星星数 | 59k | 较小 | 较小 | **50.7k** |

**MemPalace 最适合**：追求本地优先、需要跨项目上下文关联、对检索质量要求高的团队。

### 12.3.5 Hindsight：仿生记忆 + 事实/经验/心智模型三层分离

**代表项目**：`vectorize-io/hindsight` ⭐ 活跃（2025年12月发布，LongMemEval SOTA）

**核心洞察**：大多数记忆系统只解决"回忆"（RAG），Hindsight 解决的是"学习"——让 Agent 不仅能记住，还能从经验中形成自己的认知模型。

**三层仿生记忆架构**：

```
┌──────────────────────────────────────────────────────────────┐
│                    HINDSIGHT 记忆架构                         │
├──────────────────────────────────────────────────────────────┤
│  WORLD FACTS（世界事实层）                                    │
│    客观知识，"百科全书"，静态可验证                           │
│    例："Python 装饰器在运行时执行"                            │
├──────────────────────────────────────────────────────────────┤
│  EXPERIENCES（经验层）                                        │
│    Agent 自身的交互经历，含完整上下文和结果                   │
│    例："用户问装饰器，我用 @functools.wraps 解决了"         │
├──────────────────────────────────────────────────────────────┤
│  MENTAL MODELS（心智模型层）                                  │
│    从经验中抽象出的规律，支持推理和预测                       │
│    例："用户偏好简洁代码示例，先给结论再解释"                  │
└──────────────────────────────────────────────────────────────┘
```

**三种核心操作**：

```python
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:8888")

# Retain：存储记忆
client.retain(bank_id="my-bank", content="用户Alice偏好简洁代码示例")

# Recall：检索记忆
client.recall(bank_id="my-bank", query="Alice有什么偏好？")

# Reflect：反思——从已有记忆生成新洞察
client.reflect(bank_id="my-bank", query="Alice的学习风格是什么？")
```

**关键创新**：`reflect` 操作让 Agent 能从记忆生成新洞察，而不只是回溯。这是与传统 RAG 的本质区别——Hindsight 是**学习系统**，而不只是**检索系统**。

**Benchmark 表现**：LongMemEval SOTA（2026年1月），由 Virginia Tech 独立复现验证。

**安装使用**：

```bash
# Docker 一键启动（推荐）
export OPENAI_API_KEY=***
docker run --rm -it -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_API_KEY=$OPENAI_API_KEY \
  ghcr.io/vectorize-io/hindsight:latest

# Python SDK
pip install hindsight-client -U

# 2行代码接入
from hindsight_client import Hindsight
client = Hindsight(base_url="http://localhost:8888")  # 自动记忆存储和检索
```

### 12.3.6 Honcho：实体为中心 + 时间感知

**代表项目**：`plastic-labs/honcho` ⭐ 活跃（500 Commits，多语言 SDK）

**核心洞察**：Honcho 将记忆围绕**实体**（用户、Agent、想法）组织，并内置时间感知——它理解实体随时间变化的事实。这解决了"用户去年说喜欢X，但现在喜欢Y"这类时序一致性问题。

**核心概念**：

```python
from honcho import Honcho

# 1. 初始化 Workspace
honcho = Honcho(workspace_id="my-app")

# 2. 创建实体（Peer）
alice = honcho.peer("alice")      # 用户实体
tutor = honcho.peer("tutor")      # Agent 实体

# 3. 创建会话（Session）
session = honcho.session("session-1")
session.add_messages([
    alice.message("你能帮我辅导数学作业吗？"),
    tutor.message("当然可以，发来第一道题！")
])

# 4. 利用记忆推理
response = alice.chat("用户最佳的学习风格是什么？")
context = session.context(summary=True, tokens=10_000)
results = alice.search("数学作业")
```

**关键创新**：

1. **Peer（实体）概念**：每个实体（用户/Agent）有独立的记忆空间
2. **时序感知**：Honcho 理解实体状态随时间的变化
3. **多语言 SDK**：Python + TypeScript 官方支持
4. **Managed Service**：有托管服务，也支持自部署

**架构特点**：

```
Honcho 核心架构
├── Storage（PostgreSQL + pgvector）
├── Reasoning（LLM 驱动的推理层）
│   ├── Deriver：生成表示、摘要、Peer 卡片
│   └── Dreamer：异步记忆整合
└── Retrieval（自然语言查询 + 语义搜索）
```

**Benchmark**：Honcho 声称定义了"Agent Memory 的 Pareto 前沿"，有独立的 [evals.honcho.dev](https://evals.honcho.dev/) 评测页面。

**安装使用**：

```bash
# Python
pip install honcho-ai

# TypeScript
npm install @honcho-ai/sdk

# Docker 快速体验
cp docker-compose.yml.example docker-compose.yml
docker compose up -d database
uv run alembic upgrade head
uv run fastapi dev src/main.py
```

### 12.3.7 六系统综合对比

| 维度 | claude-mem | engram | agentmemory | MemPalace | Hindsight | Honcho |
|------|------------|--------|-------------|-----------|-----------|--------|
| 存储哲学 | LLM 摘要 | 原始文本 | 混合 | 逐字+AAAK | 事实/经验/心智 | 实体+时序 |
| 组织结构 | 平坦 | 平坦 | 平坦 | 宫殿结构 | 三层仿生 | Peer/Session |
| 知识图谱 | ❌ | ❌ | 基础 | 时序图谱 | 关系图谱 | 实体图谱 |
| 检索性能 | 未公布 | 未公布 | 未公布 | **96.6% R@5** | **LongMemEval SOTA** | Pareto 前沿 |
| API 调用 | 需要 | 需要 | 需要 | 零API(原始) | 需要 | 需要 |
| 学习能力 | 检索 | 检索 | 检索 | 检索 | **Reflect 反思** | 推理增强 |
| 多语言 SDK | Claude 专用 | MCP | Python | Python | Py/TS/多 | **Py/TS** |
| 星星数 | 59k | 较小 | 较小 | 50.7k | 活跃 | 活跃 |
| 适合场景 | Claude 用户 | 多 Agent | 企业级 | 本地优先+高质量 | **学习型 Agent** | 多用户+时序 |

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
