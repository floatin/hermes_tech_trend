# 三大方向 GitHub 高星开源项目调研报告

> 调研时间：2026年5月
> 数据来源：GitHub + 技术博客（因 GitHub 搜索限制，部分 Star 数为近似值，综合多篇博客文章交叉验证）

---

## Topic A：CLI + Skills 接入 MSP

> 注：这里的"MSP"主要指 Model Service Provider（模型服务商），如 OpenAI、Anthropic、Cohere 等，以及广义的 AI Agent 开发框架。

### 代表性开源项目

#### 1. `modelcontextprotocol/servers` ⭐ 官方维护
- **链接**：https://github.com/modelcontextprotocol/servers
- **Star**：官方参考实现，未公开宣传 Star 数（4085 commits）
- **语言**：TypeScript
- **定位**：MCP 协议官方参考服务器集合，由 MCP Steering Group 维护
- **包含内容**：Filesystem、Github、Slack、Brave Search、Sentry 等十余个官方实现
- **特点**：MCP 协议的"官方标准答案"，适合学习协议规范和 SDK 用法
- **近期更新**：2026年4月仍有活跃提交（4085 commits）

#### 2. `wong2/awesome-mcp-servers` ⭐ 70k+
- **链接**：https://github.com/wong2/awesome-mcp-servers
- **Star**：70k+（2025年10月数据），持续增长中
- **收录规模**：3000+ MCP Servers，分为40+分类
- **分类覆盖**：Aggregator、Art & Culture、Browser Automation、Cloud Platforms、Code Execution、Coding Agents、Command Line、Communication、Customer Data Platform、Database、DevOps、Education、Email、Environment Management、Finance、Framework、Legal、Media、Memory、Monitoring、Music、NLP/Text、ORM、Prompt Engineering、Research、Science、Security、SEO、Social Media、Travel、Version Control 等
- **近期更新**：2026年4月6日仍有提交
- **中文用户注意**：配合 `yzfly/Awesome-MCP-ZH` 使用更佳

#### 3. `github/github-mcp-server` ⭐ 2.1k+
- **链接**：https://github.com/github/github-mcp-server
- **Star**：2.1k+（持续增长中）
- **出品方**：GitHub 官方
- **功能**：Issues、Pull Requests、Repositories、Git 操作等完整 GitHub API 集成
- **特点**：支持 Docker 快速部署，有丰富的 API 接口覆盖

#### 4. `manusa/kubernetes-mcp-server` ⭐ 活跃
- **链接**：https://github.com/containers/kubernetes-mcp-server
- **Star**：未公开，但 commits 非常活跃（2026年4月持续更新）
- **功能**：Kubernetes + OpenShift 集群管理
- **特点**：支持 ServiceAccount token 自动挂载配置、Istio/Kiali 集成

#### 5. `yzfly/Awesome-MCP-ZH` ⭐ 中文用户必备
- **链接**：https://github.com/yzfly/Awesome-MCP-ZH
- **定位**：中文用户专属 MCP 资源合集
- **推荐组合**：Cherry Studio（客户端）+ 阿里 Qwen（大模型），免费易上手

#### 6. `modelcontextprotocol/typescript-sdk` ⭐ 官方SDK
- **链接**：https://github.com/modelcontextprotocol/typescript-sdk
- **Star**：未公开，1485 commits
- **定位**：官方 TypeScript SDK，可用于构建 MCP 服务器和客户端
- **近期更新**：2026年3月有重大更新

#### 7. `Gizele1/harness-init` ⭐ 31+（2026年新星）
- **链接**：https://github.com/Gizele1/harness-init
- **Star**：31+（2026年5月），Fork 6
- ** commits**：38 commits，活跃维护中
- **定位**：将仓库初始化为 agent-ready 环境的脚手架工具，深度践行 OpenAI Harness Engineering 方法论
- **核心价值**：不是又一个 MCP Server，而是一套**系统化解决 Skills 膨胀 + 上下文混乱 + 熵增**的工程框架
- **8 阶段闭环**：

| Phase | 内容 | 解决的问题 |
|-------|------|------------|
| 0. Discovery | 探测技术栈、映射架构、识别分层 | AI 不知道项目用了什么 |
| 1. AGENTS.md | ~100行定位地图（索引而非百科） | 上下文入口混乱 |
| 2. docs/ | `architecture/LAYERS.md` + `golden-principles/` + `SECURITY.md` + `guides/` | 知识散落各角落 |
| 3. Testing | 架构边界测试（ratchet 机制） | 架构随时间腐化 |
| 4. Linting | 导入限制规则（错误信息中包含修复方案） | 规范无法强制执行 |
| 5. CI | lint + typecheck + test + build 并行流水线 | 质量门禁缺失 |
| 6. GC | 垃圾回收脚本 + 每周定时扫描 | 熵增无法对抗 |
| 7. Hooks | Pre-commit 强制执行 | 人为跳过规范 |

- **核心理念**（来自 OpenAI Harness Engineering）：
  1. 工程师成为**环境设计者**——定义约束，而非实现
  2. 给 AI 一张**地图**，而不是百科全书——AGENTS.md ~100行
  3. **知识必须机器可读**——所有知识要在 repo 内，否则 AI 看不到
  4. 架构用**机械方式强制执行**——linter + 测试，而非文档
  5. **熵增管理 = 垃圾回收**——定期扫描防止腐化
  6. **最小阻塞门控**——吞吐优先，合并哲学改变
- **多 Agent 支持**：Claude Code、OpenAI Codex、Cursor、Cursor Rules
- **安装方式**（CLI 一键）：
  ```bash
  claude plugin marketplace add https://github.com/Gizele1/harness-init.git
  claude plugin install harness-init@harness-init
  ```
- **对 Topic B 的意义**：Skills 膨胀的终极解法不是限制 Skills 数量，而是通过 **AGENTS.md + docs/ + 分层文档** 让 AI 自己学会在正确的上下文里找正确的知识——harness-init 把这个过程自动化了

#### 8. `humanlayer/12-factor-agents` ⭐ 273 commits（LangChain 博客背书）
- **链接**：https://github.com/humanlayer/12-factor-agents
- **Star**：未公开高星，但作者在 LangChain 博客发布，引发广泛讨论
- ** commits**：273 commits，活跃
- **定位**：类比《12-Factor Apps》，提炼**构建可靠 LLM 应用的原则**
- **核心洞察**：作者深度使用过所有主流框架（LangChain、LangGraph、CrewAI、smolagents），并与大量 YC 创始人交流后发现——**真正决定 Agent 生产级可靠性的不是框架选择，而是工程实践**
- **12 因素**（类似 12-Factor Apps）：
  1. 单一职责的 Agent
  2. 明确的工具边界
  3. 可观测性（Agent 决策链路）
  4. 环境隔离
  5. 有状态的 Agent（持久化记忆）
  6. ...
- **对 Topic A 的意义**：在做 CLI + Skills 架构时，这 12 因素是检查清单——你的接入方案是否满足"生产级可靠性"？

#### 9. `coleam00/context-engineering-intro` ⭐ 低星（Context Engineering 模板）
- **链接**：https://github.com/coleam00/context-engineering-intro
- ** commits**：25 commits，但派生自 1140 commits 的 `davidkimai/Context-Engineering`
- **定位**：Context Engineering 的**实践入门模板**，不是理论文章
- **核心内容**：
  - `.claude/` — Claude Code 的项目级配置
  - `PRPs/` — Prompt-Refinement-Protocols（迭代优化 Prompt 的协议）
  - `validation/` — 让 AI **自己验证自己输出**的机制（Validation loops）
  - `examples/` — 实际可运行的示例
- **关键洞察**：这本书生成了一个让 AI **遵循 TDD 流程**的框架——不是告诉 AI"你要 TDD"，而是构建一个让 AI 自己跑 TDD 流程的环境
- **对 Topic B 的意义**："蒸馏 Skill" 的实战参考——如何把工程方法论封装成可执行的 Skill 模板

---

### FastMCP 框架（快速构建 MCP Server）

**FastMCP**（Python）是目前最流行的快速构建 MCP Server 框架，30行代码即可跑通：
```python
from fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def get_weather(city: str):
    return {"temp": 22, "city": city}
```

**关键坑点**：STDIO 模式下日志必须输出到 `sys.stderr`，不能写到 `stdout`，否则会污染 JSON-RPC 协议流。

---

### 趋势总结

| 方向 | 结论 |
|------|------|
| MCP 协议本身 | 头部玩家（Perplexity、OpenClaw）已转向 CLI/API，MCP 热度回落但基础设施价值仍在 |
| 生态导航 | `awesome-mcp-servers`（70k stars）证明开发者对"MCP 发现"需求强烈 |
| 企业级 MCP | Kubernetes、GitHub、Slack 等官方 MCP Server 活跃度最高 |
| 中文生态 | `Awesome-MCP-ZH` + Cherry Studio 组合降低入门门槛 |
| 快速接入 | FastMCP（Python）/ TypeScript SDK 让 MCP Server 开发门槛大幅降低 |

---

## Topic B：Skills 膨胀管理

### Agent Skills 生态全景

#### 顶层结构（三层加载机制）

```
L1 触发层（始终加载）：
  name + description（1-2句话，总计 < 4KB）
  → 决定 AI 是否激活该 Skill

L2 执行层（按需加载）：
  SKILL.md 核心指令（500-800 tokens）
  → 包含80%常见场景处理逻辑

L3 资源层（文件引用）：
  高级配置、模板、示例代码
  → 按需加载，避免主流程臃肿
```

### 代表性开源项目

#### 1. `affaan-m/everything-claude-code` ⭐ 63k+（Anthropic 黑客松冠军）
- **链接**：https://github.com/affaan-m/everything-claude-code
- **Star**：63.6k+（2026年4月数据），Fork 7.9k+
- ** commits**：1465 commits
- **核心定位**：生产级 Claude Code 配置体系，涵盖工作流、上下文管理、安全、MCP 配置
- **模块构成**：
  - `agents/`：13+ 按角色划分的子智能体（代码审查者、测试工程师、DevOps 等）
  - `skills/`：65+ 实战技能
  - `hooks/`：钩子实现（跨会话记忆、上下文压缩）
  - `rules/`：经过生产验证的规则集
  - `contexts/`：动态注入系统提示的上下文
  - `mcp-configs/`：MCP 服务器配置
- **解决的问题**：
  - 上下文窗口爆炸（MCP 工具描述消耗令牌）
  - 上下文腐烂（长对话信息丢失）
  - 工作流不确定性（聊天式写码 → 计划-实现-验证-复盘）
- **近期更新**：2026年4月仍有活跃提交

#### 2. `obra/superpowers` ⭐ 34k+（Claude 官方认证插件）
- **链接**：https://github.com/obra/superpowers
- **Star**：34k+（2026年1月数据），安装量 23万+
- **作者**：Jesse Vincent（obra）
- **核心定位**：一套完整的软件开发方法论，将 TDD、YAGNI、DRY 等工程最佳实践封装为可组合 Skills
- **与 ECC 的区别**：
  - ECC 更像"配置大礼包"，模块多且全
  - Superpowers 更聚焦"工程规范"，强制 AI 按特定方式执行
- **安装方式**：
  ```bash
  # Claude Code
  /plugin marketplace add obra/superpowers
  /plugin install superpowers@superpowers

  # Codex
  /plugin marketplace add obra/superpowers
  ```
- **特点**：不只让 AI"能做什么"，而是强制 AI"必须按特定方式做什么"
- **近期更新**：2026年3月仍有提交

#### 3. `anthropics/skills` ⭐ 官方基座
- **链接**：https://github.com/anthropics/skills
- **定位**：Claude Skills 官方基础技能集合
- **特点**：必装的第一个 Skills 来源，官方维护
- **安装量**：数百万级

#### 4. `libukai/awesome-agent-skills` ⭐ Agent Skills 导航
- **链接**：https://github.com/libukai/awesome-agent-skills
- **Star**：155 commits 活跃维护
- **定位**：Agent Skills 终极指南，包含快速入门、资源推荐、精选技能
- **中文文档完善**：提供 Claude-Skills 完全构建指南（中文）
- **docs 目录内容**：
  - Agent-Skill 五种设计模式
  - Claude-Code-Skills 实战经验
  - Claude-Skills 完全构建指南

#### 5. `ComposioHQ/awesome-claude-skills` ⭐ 19k+
- **链接**：https://github.com/ComposioHQ/awesome-claude-skills
- **Star**：19.2k+
- **定位**：Claude Skills 资源合集，Awesome 列表风格

#### 6. `JackyST0/awesome-agent-skills` ⭐ 中文一键安装版
- **链接**：https://github.com/JackyST0/awesome-agent-skills
- **特点**：一键安装脚本，支持 Claude Code、Codex、Copilot 等多平台

#### 7. 蒸馏 Skills 系列（人物技能包）
- **代表项目**：`同事.skill`、`老板.skill`、`女娲.skill`、`自己.skill`
- **原理**：将真实人物的知识、风格与决策模式提炼为可复用 AI 技能模块
- **现象**：2026年4月在 GitHub 集中爆发，最头部项目5天 6600+ Stars
- **适用场景**：需要特定思维框架的重复性工作

---

### Skills 膨胀管理的核心策略

> **harness-init 的启发**：Skills 膨胀的终极解法不是"少用 Skills"，而是**通过分层文档 + 机械执行让 AI 自己知道在什么场景下用什么知识**。Skills 是执行单元，上下文组织才是根因。

| 策略 | 做法 | 适用阶段 |
|------|------|----------|
| **元数据精简** | description ≤ 50字，避免重复触发词 | 10+ Skills |
| **分组管理** | 按领域/阶段/角色分组，AI 先选组再选 Skill | 20+ Skills |
| **版本锚定** | Skills 目录加版本号，明确变更日志 | 团队共享 |
| **生命周期管理** | 设立"活跃/存档/废弃"三态，定期清理 | 长期项目 |
| **Base Skill 继承** | 通用技能抽出为基础包，子 Skill 继承扩展 | 多个相似 Skill |
| **定期触发词审计** | 用 AI 检测 Skills 描述重叠，合并或区分 | 任何阶段 |
| **harness-init 8阶段** | Discovery → AGENTS.md → docs/ → Testing → Linting → CI → GC → Hooks | 全栈熵增管理 |

---

### 趋势总结

| 方向 | 结论 |
|------|------|
| Skills 生态规模 | 70万+ 技能包（Agent Skills 生态），持续爆发中 |
| 最强生产级方案 | `everything-claude-code`（63k stars，黑客松冠军）|
| 最强工程规范方案 | `superpowers`（34k stars，Claude 官方认证）|
| 膨胀管理 | 三层加载机制（L1触发/L2执行/L3资源）是行业共识 |
| 新趋势 | "蒸馏 Skill"（人物技能包）成为2026年新风口 |

---

## Topic C：大型代码仓库高效访问（代码 RAG）

### 问题的本质

代码仓库超过 10万行后，"全量 Embedding 丢进上下文"方案面临：
1. **上下文窗口不够**：即使 200k 窗口也不够装
2. **噪声过多**：测试代码、配置文件干扰检索质量
3. **语义碎片化**：跨文件依赖关系无法捕获

### 代表性开源项目

#### 1. `microsoft/GraphRAG` ⭐ 19k+（微软官方）
- **链接**：https://github.com/microsoft/GraphRAG
- **Star**：19k+（2024年7月开源，增长迅速）
- ** commits**：463 commits，v3.0.9（2026年4月14日）
- **定位**：基于知识图谱的模块化 RAG 系统
- **核心思路**：
  - LLM 生成知识图谱（实体 + 关系）
  - 构建社区层次结构（Leiden 算法）
  - 支持 Local Search（局部）和 Global Search（全局）两种模式
- **适用场景**：处理需要"连接分散信息点"的复杂查询
- **中文支持**：`jasonkylelol/graphrag-chinese` 提供中文模型支持
- **缺点**：官方实现较重，2000行左右代码，学习成本较高
- **近期更新**：2026年3-4月活跃更新

#### 2. `gusye1234/nano-graphrag` ⭐ 轻量实现
- **链接**：https://github.com/gusye1234/nano-graphrag
- **核心特点**：剔除测试和 prompt 后约 800 行代码
- **定位**：GraphRAG 的"小而美"版本，保留核心功能
- **优势**：易于阅读和修改，适合学习原理和二次开发
- **安装**：`pip install nano-graphrag` 或 `pip install lightrag-hku`
- **模型支持**：OpenAI API、Ollama、本地模型

#### 3. `big-data-ai/LightRAG` ⭐ 香港大学出品
- **链接**：https://github.com/big-data-ai/LightRAG
- **核心优势**：索引速度比 GraphRAG **快 10 倍**
- **架构**：
  - 索引阶段：文档切分 → 提取实体和边 → 分别向量化 → 存入向量知识库
  - 检索阶段：提取局部+全局关键词 → 同时检索向量知识库中的实体和边关系 → 结合 chunk 总结
- **特点**：
  - **双层检索**：局部 + 全局，兼顾细节和整体
  - **增量更新**：支持实时增量添加文档
  - **轻量高效**：比 GraphRAG 轻量很多
- **支持模型**：兼容 OpenAI 规范接口

#### 4. `codeaudit/fast-graphrag` ⭐ 可解释 + 低成本
- **链接**：https://github.com/codeaudit/fast-graphrag
- **核心特点**：
  - **成本降低 6 倍**：$0.08 vs GraphRAG $0.48（The Wizard of Oz 基准测试）
  - **可解释可调试**：图结构是人类可导航的知识视图
  - **基于 PageRank**：智能图探索，提高准确性和可靠性
  - **增量更新**：支持实时更新
  - **全异步 + 类型安全**：完整类型支持
- **适用**：需要复杂信息检索、对成本敏感的场景
- **作者**：`circlemind-ai/fast-graphrag`（主库）

#### 5. `graphrag/ms-graphrag` ⭐ 微软官方模块化分支
- **链接**：https://github.com/graphrag/ms-graphrag
- **定位**：微软 GraphRAG 的模块化版本，与主分支保持同步
- **包结构**：`packages/` 目录提供模块化拆分

#### 6. `trustgraph-ai/trustgraph` ⭐ 2026年新方案
- **链接**：https://github.com/trustgraph-ai/trustgraph
- **核心定位**：图原生存储 + 多模型支持 + 语义检索管道
- **特点**：
  - 支持 Anthropic、Cohere、 Gemini、 Mistral、OpenAI 等多模型
  - 支持 vLLM、Ollama、TGI、LM Studio 等本地推理
  - 向量存储在 Qdrant
  - S3 兼容对象存储（Garage）
  - Pulsar Pub/Sub
- **适用**：需要长期维护上下文的企业级场景

#### 7. `code-rag-bench/code-rag-bench` ⭐ 代码 RAG 基准测试
- **链接**：https://github.com/code-rag-bench/code-rag-bench
- **定位**：CodeRAG 基准测试，评估检索增强代码生成效果
- **覆盖数据集**：
  - Basic Programming：HumanEval、MBPP、Live Code Bench
  - Open-Domain：DS-1000、Odex
  - Repository-Level：RepoEval、SWE-bench

#### 8. `D-Star-AI/dsRAG` ⭐ 非结构化数据高性能检索
- **链接**：https://github.com/SuperpoweredAI/spRAG
- **特点**：擅长处理复杂查询，在财务报表、法律文档、学术论文等场景精度显著高于 Vanilla RAG
- **团队背景**：YC 校友创办的专业 AI 咨询公司

---

### 方案选型决策树

```
代码仓库规模？
│
├─ < 5万行
│   └─ Flat Embedding + tree-sitter 语义分块（chunk size=512 tokens）
│
├─ 5-20万行
│   ├─ Parent-Retrieval（子块召回 → 膨胀到函数/类级别）
│   ├─ 补充 BM25 关键词召回兜底
│   └─ 核心业务文件优先索引，测试/配置降权
│
└─ 20万行+
    ├─ GraphRAG 路径
    │   ├─ 轻量优先：nano-graphrag（800行，易修改）
    │   ├─ 速度优先：LightRAG（索引快10倍）
    │   ├─ 成本优先：fast-graphrag（6倍成本节省）
    │   └─ 企业级：TrustGraph（托管方案，多模型支持）
    │
    └─ 混合检索（可选进阶）
        └─ BM25 + 向量 + 重排序
```

### 深度洞察：三个被表面化处理的根本问题

> 以下内容超越"有哪些好项目"，直指三个方向**真正难解决的问题**。星数低不代表不重要，反而往往是因为太底层、还没有被产品化。

---

#### 洞察一：Prompt Engineering → Context Engineering → Harness Engineering 是同一问题的三层递进

| 时代 | 核心问题 | 答案 |
|------|---------|------|
| **2023 Prompt Engineering** | 怎么写好一条指令？ | Few-shot、CoT、ReAct |
| **2025 Context Engineering** | 上下文窗口里放什么？ | RAG、分块、层次检索 |
| **2026 Harness Engineering** | 如何让 Agent 在真实环境中可靠运行？ | 约束+反馈+控制系统 |

**关键洞察**：这三个词描述的是**同一个问题的不同深度**，不是替代关系。Harness Engineering 的本质是：

- Prompt Engineering = 告诉模型"做什么"
- Context Engineering = 给模型提供"它需要知道什么"
- Harness Engineering = 确保模型"在约束内可靠地做到"

OpenAI 的百万行实验验证了这个逻辑：3人团队、5个月、零手写代码。核心不是模型能力，而是围绕 Codex 构建的一整套 Harness——CI 流水线、执行计划持久化、决策日志、架构边界测试。

**对 Topic A 的意义**：CLI + Skills 的价值不在于"接入 MSP"，而在于构建 Agent 的**运行环境**。harness-init 的 8 阶段闭环本质上是把 Harness Engineering 自动化。

---

#### 洞察二：Skills 膨胀的根因不是"太多"，而是"上下文层级缺失"

所有 Skills 管理指南都在教你怎么**精简 Skills**——减少触发词、定期审计、版本锚定。但这治标不治本。

真正的问题是：Skills 作为**执行单元**是好的，但它缺少一个**上下文组织层**。

`davidkimai/Context-Engineering`（1140 commits，这个维护量说明它触及了深层问题）给出了一个分析框架，将上下文工程类比为生物组织层次：

| 层次 | 类比 | 上下文中的作用 |
|------|------|---------------|
| **Atoms** | 原子 | 单一 Prompt / 单一工具调用 |
| **Molecules** | 分子 | Few-shot Prompt（带示例） |
| **Cells** | 细胞 | 记忆系统 + 多 Agent 协作 |
| **Organs** | 器官 | 复杂 Agent 系统（规划+执行+反思） |
| **Neural Systems** | 神经网络 | 跨会话持久记忆 + 认知工具 |

**关键洞察**：Skills 膨胀之所以失控，是因为我们用"扁平列表"管理 Skills，但没有建立**层级索引**。harness-init 的 AGENTS.md（~100行定位地图）本质上是给 Skills 建索引：AI 执行任务前，先查 AGENTS.md 找到正确的 docs/ 路径，而不是遍历所有 Skills 描述。

**Skills 膨胀的解法不是少用 Skills，而是让 Skills 活在正确的上下文层次里。**

---

#### 洞察三：代码仓库检索的核心矛盾不是"向量不够准"，而是"语义和结构是两种不同的知识"

目前大多数 Code RAG 方案的核心假设是：**代码可以被语义向量化**。这个假设在简单场景下成立，但一旦涉及跨文件依赖、架构层级的理解，向量检索就暴露了根本缺陷：

- 问："哪些服务依赖用户数据库？" → 这是**结构查询**，不是语义查询
- 问："用户认证是怎么实现的？" → 这是**语义查询**

`Google Code Wiki`（Google 发布）揭示了一个被大多数中文技术社区忽略的核心架构：

```
第一层：结构解析（Tree-sitter AST）
  → 精准捕获函数签名、import 关系、调用图
  → 解决向量检索无法回答的"哪些文件调用了这个函数"

第二层：知识图谱（图数据库）
  → 节点：函数、模块、服务；边：调用/继承/依赖关系
  → 解决"哪些服务依赖 X"类型的结构查询

第三层：代理式混合检索
  → 语义问题 → 向量检索
  → 依赖问题 → 图遍历
  → 动态选择，不是把所有东西都塞给向量模型
```

**关键洞察**：`microsoft/GraphRAG`（19k stars）被热捧，但很多人没有理解它真正的价值：**不是"知识图谱"这个噱头，而是它实现了语义检索 + 结构检索的混合**。对于 20 万行以上的代码仓库，混合检索是必须的，而不是可选项。Tree-sitter 负责把代码解析成机器可理解的结构，知识图谱负责在这个结构上做推理。

---

### 趋势总结

| 方向 | 结论 |
|------|------|
| 头部项目 | GraphRAG 19k stars 仍是主流，但微软正在模块化拆分（v3.0.9）|
| 轻量替代 | nano-graphrag（800行）、LightRAG（10倍速）是两个最重要分支 |
| 成本优化 | fast-graphrag 给出明确数字：6倍成本节省 |
| 企业级 | TrustGraph（图原生 + 多模型 + S3兼容存储）面向长期运维 |
| 基准测试 | code-rag-bench 提供代码 RAG 效果量化评估标准 |
| 新兴方向 | Code Wiki / 可视化（CodeFlow 一键生成架构图）辅助人类理解 |

---

## 横向对比汇总

### MCP/CLI 方向

| 项目 | Star | 核心定位 | 近期活跃度 |
|------|------|----------|------------|
| awesome-mcp-servers | 70k+ | MCP 服务器导航 | 2026-04-06 更新 |
| github-mcp-server | 2.1k+ | GitHub 官方 MCP | 持续维护 |
| kubernetes-mcp-server | — | K8s 集群管理 | 2026-04 活跃 |
| awesome-mcp-zh | — | 中文 MCP 导航 | 维护中 |

### Skills 方向

| 项目 | Star | 核心定位 | 近期活跃度 |
|------|------|----------|------------|
| everything-claude-code | 63k+ | 黑客松冠军，生产级配置 | 2026-04 活跃 |
| superpowers | 34k+ | 工程规范，Claude 官方认证 | 2026-03 活跃 |
| anthropics/skills | 官方 | 官方基础技能 | 持续更新 |
| awesome-claude-skills | 19k+ | Skills 导航合集 | 维护中 |
| awesome-agent-skills（libukai） | — | Agent Skills 导航 | 2026-03 活跃 |

### 代码 RAG 方向

| 项目 | Star | 核心定位 | 近期活跃度 |
|------|------|----------|------------|
| microsoft/GraphRAG | 19k+ | 知识图谱 RAG 旗舰 | 2026-04-14 v3.0.9 |
| nano-graphrag | — | 轻量 GraphRAG，800行 | 2026-04 活跃 |
| LightRAG | — | 索引快10倍 | 2024-10 活跃 |
| fast-graphrag | — | 低成本+可解释 | 2026-04 活跃 |
| TrustGraph | — | 企业级图原生 | 2026-05 活跃 |

---

## 推荐阅读顺序

如果你是**系列文章作者**，建议按以下优先级深入：

1. **快速概览**：`wong2/awesome-mcp-servers` README + `libukai/awesome-agent-skills` docs
2. **MCP 深度**：`modelcontextprotocol/servers` 源码 + FastMCP 框架文档
3. **Skills 进阶**：`affaan-m/everything-claude-code` 架构解析 + `obra/superpowers` SKILL.md 模板
4. **代码 RAG 实战**：nano-graphrag（易读）→ GraphRAG 官方文档（全面）→ fast-graphrag benchmark（量化）
