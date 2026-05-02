# Chapter 12 附录：记忆系统实战指南

> **副标题**：从零到生产级记忆系统的完整路径 + 选型决策树

---

## A.1 选型决策树

### 决策树 1：选择记忆系统类型

```
【问题】你的团队需要什么类型的记忆系统？

├── 主要在 Claude Code 里用 AI 编程？
│   │
│   ├─ 即装即用，不想折腾？
│   │   └─ → claude-mem（Plugin 市场一键安装）
│   │
│   └─ 需要跨会话记住更多上下文？
│       └─ → 继续判断
│
├── 需要支持多个 Agent（Claude Code / Codex / Cursor 同时用）？
│   │
│   ├─ 是 → engram（MCP 协议兼容，接入任何 Agent）
│   └─ 否 → 继续判断
│
├── 需要高检索质量（R@5 > 90%）？
│   │
│   ├─ 是
│   │   ├─ 本地优先，不想依赖外部 API？
│   │   │   └─ → MemPalace（零 API，96.6% R@5）
│   │   │
│   │   └─ 需要从记忆生成新洞察？
│   │       └─ → Hindsight（Reflect 反思能力）
│   │
│   └─ 否 → 继续判断
│
├── 多用户场景，需要实体状态追踪？
│   │
│   ├─ 是 → Honcho（Peer/实体概念）
│   └─ 否 → 继续判断
│
└── 企业级，需要 PostgreSQL 生态？
    │
    └─ 是 → agentmemory（PostgreSQL + pgvector）
```

### 决策树 2：评估团队需求

```
【问题】你的团队规模和使用场景？

├── 个人开发者（< 3 个项目）
│   └─ → claude-mem（最简单）
│
├── 小团队（3-10 人，共享项目）
│   │
│   ├─ 主要是 AI Coding
│   │   └─ → claude-mem + MEMORY.md 规范
│   │
│   └─ 需要跨 Agent
│       └─ → engram
│
├── 中型团队（10-50 人，多项目）
│   │
│   ├─ 高检索质量需求
│   │   └─ → MemPalace
│   │
│   └─ 需要洞察生成
│       └─ → Hindsight
│
└── 大型团队（> 50 人，企业级）
    └─ → agentmemory + 自建知识库
```

### 决策树 3：评估技术能力

```
【问题】你的团队能投入多少工程资源？

├── 不想运维任何服务
│   └─ → claude-mem（即装即用）
│
├── 能运维 Docker 容器
│   │
│   ├─ 单一服务即可
│   │   └─ → engram（单二进制）
│   │
│   └─ 需要更多能力
│       ├─ → MemPalace（Docker 部署）
│       └─ → Hindsight（Docker 部署）
│
└─ 能运维数据库
    └─ → agentmemory（PostgreSQL + pgvector）
```

---

## A.2 六系统安装与配置

### A.2.1 claude-mem（最简方案）

```bash
# 1. Claude Code 中安装
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem

# 2. 配置存储位置
export CLAUDE_MEM_PATH=~/.claude-mem-data

# 3. 基本使用
> /mem status              # 查看记忆状态
> /mem query "JWT 决策"    # 检索记忆
> /mem save                 # 手动保存当前会话
> /mem cleanup --older-than=30d  # 清理旧记忆

# 4. 配置 .claude-mem.yaml
# ~/.claude-mem/config.yaml
capture:
  tools:
    enabled: true
  files:
    enabled: true
  decisions:
    enabled: true
    keywords: ["决定", "选择", "采用", "因为"]
retention:
  max_age_days: 90
  max_entries: 10000
```

### A.2.2 engram（多 Agent 方案）

```bash
# 1. Docker 部署
docker run -d \
  --name engram \
  -p 8080:8080 \
  -v engram-data:/data \
  ghcr.io/gentleman-programming/engram

# 2. MCP 配置（Claude Code）
# ~/.claude/mcp.json 或项目 .mcp.json
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

# 3. 基本使用
/engram save "架构决策：选择 JWT 而非 Session"
/engram query "JWT Session"
/engram list

# 4. API 调用
curl -X POST http://localhost:8080/api/memories \
  -H "Content-Type: application/json" \
  -d '{"content": "架构决策", "tags": ["architecture"]}'
```

### A.2.3 MemPalace（高质量检索方案）

```bash
# 1. 安装
pip install mempalace

# 2. 初始化项目记忆库
mempalace init ~/projects/myapp

# 3. 基本使用
mempalace mine ~/projects/myapp                    # 挖掘项目文件
mempalace mine ~/.claude/projects/ --mode convos   # 挖掘会话
mempalace search "为什么切换到 GraphQL"            # 语义搜索
mempalace wake-up                                  # 生成唤醒上下文

# 4. MCP 工具（29 个工具）
# 在 Claude Code 的 MCP 配置中：
{
  "mcpServers": {
    "mempalace": {
      "command": "mempalace",
      "args": ["mcp", "start"]
    }
  }
}

# 5. 知识图谱操作
from mempalace.knowledge_graph import KnowledgeGraph
kg = KnowledgeGraph()

# 添加带时间窗的事实
kg.add_triple("Kai", "works_on", "Orion",
              valid_from="2025-06-01")
kg.add_triple("Maya", "assigned_to", "auth-migration",
              valid_from="2026-01-15",
              valid_until="2026-02-01")

# 查询（自动排除过期）
current = kg.query_entity("Maya")

# 时间旅行
past = kg.query_entity("Maya", as_of="2026-01-20")

# 6. 记忆栈唤醒（典型上下文）
from mempalace.layers import MemoryStack
stack = MemoryStack()
wake = stack.wake_up()  # L0 + L1 = ~600-900 tokens
```

### A.2.4 Hindsight（学习型 Agent 方案）

```bash
# 1. Docker 启动（推荐）
export OPENAI_API_KEY=sk-***
docker run --rm -it -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_API_KEY=$OPENAI_API_KEY \
  ghcr.io/vectorize-io/hindsight:latest

# 2. Python SDK
pip install hindsight-client -U

# 3. 基本使用
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:8888")

# Retain：存储记忆
client.retain(bank_id="my-bank",
              content="用户 Alice 偏好简洁代码示例")

# Recall：检索记忆
client.recall(bank_id="my-bank",
              query="Alice 有什么偏好？")

# Reflect：反思生成洞察
client.reflect(bank_id="my-bank",
               query="Alice 的学习风格是什么？")

# 4. 三层操作
# 存储到指定层
client.retain(bank_id="my-bank",
              content="Python 装饰器在运行时执行",
              layer="facts")

client.retain(bank_id="my-bank",
              content="用户问装饰器，我用 @functools.wraps 解决",
              layer="experiences")

# 从 Mental Models 层检索
client.recall(bank_id="my-bank",
              query="用户偏好",
              layer="mental_models")
```

### A.2.5 Honcho（多用户/实体方案）

```bash
# 1. 安装
pip install honcho-ai

# 或 TypeScript
npm install @honcho-ai/sdk

# 2. Docker 快速启动
cp docker-compose.yml.example docker-compose.yml
docker compose up -d database
uv run alembic upgrade head
uv run fastapi dev src/main.py

# 3. 基本使用（Python）
from honcho import Honcho

honcho = Honcho(workspace_id="my-app")

# 创建实体（Peer）
alice = honcho.peer("alice")  # 用户实体
tutor = honcho.peer("tutor")  # Agent 实体

# 创建会话
session = honcho.session("session-1")
session.add_messages([
    alice.message("你能帮我辅导数学作业吗？"),
    tutor.message("当然可以，发来第一道题！")
])

# 利用记忆推理
response = alice.chat("用户最佳的学习风格是什么？")
context = session.context(summary=True, tokens=10_000)
results = alice.search("数学作业")
```

### A.2.6 agentmemory（企业级方案）

```bash
# 1. 安装
pip install agentmemory

# 2. 基本使用
/agentmemory enable          # 启用
/agentmemory status          # 查看状态
/agentmemory search "JWT"   # 搜索
/agentmemory doctor          # 自检

# 3. Claude Code Plugin
/plugin marketplace add rohitg00/agentmemory
/plugin install agentmemory

# 4. 配置向量存储
# 支持 ChromaDB 或 PostgreSQL
export AGENTMEMORY_STORAGE="chroma"  # 或 "postgres"
```

---

## A.3 团队记忆规范模板

### A.3.1 .claude/MEMORY.md（必选）

```markdown
# 项目记忆（最小集）

> 每次新会话开始前，AI 应先阅读此文件

## 架构决策
- [DATE]: [决策标题]
  - 选择：[方案 A / 方案 B]
  - 原因：[简要原因]
  - 替代方案：[被否决的方案及原因]

## 技术栈
- 后端：[框架 + 版本]
- 前端：[框架 + 版本]
- 数据库：[数据库 + 版本]
- 重要库：[关键依赖及用途]

## 代码规范
- 命名：[语言 + 约定]
- 架构：[项目特定规范]
- 测试：[覆盖率目标]

## 当前进行中
- [x] [已完成任务]（完成日期）
- [ ] [进行中任务]（预计完成日期）

## 已知问题
- [问题描述] - [状态：已知/修复中/已修复]
```

### A.3.2 decisions/YYYY-MM-DD-template.md（推荐）

```markdown
## 决策标题

**日期**：{{date}}
**发起人**：{{author}}
**状态**：ACCEPTED | REJECTED | SUPERSEDED | DEPRECATED

## 背景
[描述问题和动机。为什么需要做这个决策？]

## 选项

### 选项 A：[名称]
**描述**：[方案描述]
**优点**：
- [优点1]
- [优点2]

**缺点**：
- [缺点1]
- [缺点2]

### 选项 B：[名称]
**描述**：[方案描述]
...

## 决定
**选择**：{{selected_option}}
**理由**：[决策原因]

## 后果
**预期正面影响**：
- [影响1]
- [影响2]

**预期负面影响/风险**：
- [风险1]
- [风险2]

## 追溯
**相关决策**：
- [决策A]（[链接]）
- [决策B]（[链接]）

**后续行动**：
- [行动1]
- [行动2]

**评审日期**：{{review_date}}
```

### A.3.3 .claude-memory-ignore（隐私保护）

```gitignore
# 敏感信息，不记忆
passwords/**
secrets/**
.env*
**/credentials.json
**/id_rsa*
**/*.key
**/secrets.yaml

# 构建产物，不记忆
dist/**
build/**
node_modules/**

# 临时文件，不记忆
*.tmp
*.log
.DS_Store
```

---

## A.4 渐进式实施路径

```
Week 1：建立最小记忆基础设施
  ├─ 创建 .claude/MEMORY.md
  ├─ 安装 claude-mem
  └─ 配置 .claude-memory-ignore

Week 2：规范化记忆流程
  ├─ 建立 decisions/ 目录结构
  ├─ 制定决策记录规范
  └─ 开始记录每次架构决策

Week 3：自动化记忆捕获
  ├─ 配置 claude-mem 自动捕获
  ├─ 设置 /mem save 习惯
  └─ 验证检索质量

Week 4-8：评估与升级
  ├─ 评估检索质量（用 A.5 的测试用例）
  ├─ 如果 R@5 < 70%：考虑升级到 MemPalace
  ├─ 如果需要洞察生成：考虑 Hindsight
  └─ 如果多 Agent：考虑 engram

Month 3+：持续优化
  ├─ 每月 /mem cleanup
  ├─ 每季度记忆 review
  └─ 按需扩展系统能力
```

---

## A.5 记忆系统评估测试用例

```python
# memory-eval-test.py
# 用于评估记忆系统质量的测试用例

TEST_CASES = [
    # 架构决策追溯
    {
        "id": "arch-decision-1",
        "query": "我们什么时候讨论过 JWT vs Session？",
        "expected_keywords": ["JWT", "Session", "2024-03"],
        "expected_facts": [
            "最终选择方案",
            "选择原因"
        ]
    },

    # 人员追踪
    {
        "id": "person-tracking-1",
        "query": "Maya 上次做的项目是什么？",
        "expected_keywords": ["Maya", "auth-migration", "完成"],
    },

    # 决策演变
    {
        "id": "decision-evolution-1",
        "query": "为什么当时选择 PostgreSQL？",
        "expected_keywords": ["PostgreSQL", "MySQL", "JSON 支持"],
    },

    # 技术债务
    {
        "id": "tech-debt-1",
        "query": "我们有什么已知的技术债？",
        "expected_facts": [
            "至少一条技术债",
            "相关背景"
        ]
    },

    # 偏好学习
    {
        "id": "preference-1",
        "query": "用户偏好什么样的代码示例？",
        "expected_keywords": ["简洁", "示例", "先结论"],
    },
]

def evaluate(memory_system, test_cases):
    """评估记忆系统"""
    results = []

    for tc in test_cases:
        retrieved = memory_system.search(tc["query"])

        # 计算关键词命中率
        keyword_hits = sum(
            1 for kw in tc.get("expected_keywords", [])
            if kw.lower() in retrieved.lower()
        )
        keyword_recall = keyword_hits / max(len(tc.get("expected_keywords", [])), 1)

        # 计算事实完整性
        fact_hits = sum(
            1 for fact in tc.get("expected_facts", [])
            if fact.lower() in retrieved.lower()
        )
        fact_recall = fact_hits / max(len(tc.get("expected_facts", [1])), 1)

        results.append({
            "id": tc["id"],
            "query": tc["query"],
            "keyword_recall": keyword_recall,
            "fact_recall": fact_recall,
            "overall": (keyword_recall + fact_recall) / 2
        })

    # 输出报告
    print("\n=== Memory System Evaluation ===")
    for r in results:
        print(f"\n{r['id']}: {r['query']}")
        print(f"  Keyword Recall: {r['keyword_recall']:.1%}")
        print(f"  Fact Recall: {r['fact_recall']:.1%}")
        print(f"  Overall: {r['overall']:.1%}")

    avg = sum(r["overall"] for r in results) / len(results)
    print(f"\n=== Average R@5: {avg:.1%} ===")

    return results
```

---

## A.6 快速参考命令

```bash
# ============================================
# claude-mem
# ============================================
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem
/mem status
/mem query "关键词"
/mem save
/mem cleanup --older-than=30d

# ============================================
# engram
# ============================================
docker run -d --name engram -p 8080:8080 ghcr.io/gentleman-programming/engram
/engram save "记忆内容"
/engram query "关键词"

/plugin marketplace add @engram/mcp

# ============================================
# MemPalace
# ============================================
pip install mempalace
mempalace init ~/projects/myapp
mempalace mine ~/projects/myapp
mempalace search "关键词"
mempalace wake-up

# ============================================
# Hindsight
# ============================================
docker run --rm -it -p 8888:8888 ghcr.io/vectorize-io/hindsight:latest
pip install hindsight-client

from hindsight_client import Hindsight
client = Hindsight(base_url="http://localhost:8888")
client.retain(bank_id="my-bank", content="记忆内容")
client.recall(bank_id="my-bank", query="关键词")
client.reflect(bank_id="my-bank", query="洞察问题")

# ============================================
# Honcho
# ============================================
pip install honcho-ai
from honcho import Honcho
honcho = Honcho(workspace_id="my-app")
honcho.peer("user").chat("问题")
```

---

*附录版本 v1.0 | 对应 Chapter 12 Deep Dive*
