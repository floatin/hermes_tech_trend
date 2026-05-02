# AI Coding 系列：让 AI 成为真正的开发伙伴

> 程序员在 AI 时代的新角色 = **Harness 设计者**，不是写代码，而是设计 AI 写代码的约束系统。

---

## 系列概览

| 章节 | 主题 | 核心问题 | 状态 |
|------|------|----------|------|
| Ch7 | CLI + Skills 接入 MSP | 如何让 AI 连接外部工具？ | ✅ 草稿 + 深度 |
| Ch8 | Skills 膨胀管理 | 如何防止规范失控？ | ✅ 草稿 |
| Ch9 | 大型代码仓库高效访问 | 如何让 AI 理解 50万+ 行代码？ | ✅ 草稿 + 深度 |
| Ch10 | Git 行为约束 | 如何让 AI 遵守代码规范？ | ✅ 草稿 |
| Ch11 | Token 优化 | 如何节省 80% 的上下文成本？ | ✅ 草稿 + 深度 |
| Ch12 | 记忆系统 | 如何让 AI 记住人类习惯？ | ✅ 草稿 |

---

## 快速导航

### 按学习路径

```
入门路径（先读这些）：
  Ch7 + Ch7-deep  → MCP 协议 + Skills 集成
  Ch11 + Ch11-deep → RTK Token 优化

进阶路径：
  Ch9 + Ch9-deep  → 大型代码仓库访问
  Ch12            → 记忆系统

补充路径：
  Ch8             → Skills 膨胀管理
  Ch10            → Git 行为约束
```

### 按问题类型

| 你的问题是... | 读这些 |
|--------------|--------|
| "AI 不理解我的项目" | Ch9, Ch9-deep |
| "Token 消耗太快" | Ch11, Ch11-deep |
| "AI 总是不按规范来" | Ch8, Ch10 |
| "AI 记不住我的习惯" | Ch12 |
| "如何接入 GitHub/Slack" | Ch7, Ch7-deep |

---

## 目录结构

```
ai-coding-plan/
├── chapters/                    # 章节草稿
│   ├── chapter-07-draft.md     # CLI + Skills 接入 MSP（基础版）
│   ├── chapter-07-deep-dive.md # MCP 协议源码解析（深度版）
│   ├── chapter-07-appendix-*.md # MCP 决策树 + 场景化方案
│   ├── chapter-08-draft.md     # Skills 膨胀管理
│   ├── chapter-09-draft.md     # 大型代码仓库访问（基础版）
│   ├── chapter-09-deep-dive.md # code-context 架构解析（深度版）
│   ├── chapter-09-appendix-*.md # Code RAG 决策树
│   ├── chapter-10-draft.md     # Git 行为约束
│   ├── chapter-11-draft.md    # Token 优化（基础版）
│   ├── chapter-11-deep-dive.md # RTK 源码解析（深度版）
│   ├── chapter-11-appendix-*.md # Token 优化决策树
│   └── chapter-12-draft.md     # 记忆系统管理
│
├── research/                    # 调研报告
│   ├── three-topics-github-projects-2026.md   # 三大方向 GitHub 项目调研
│   └── openspec-agent-skills-harness-deep-dive-2026.md  # OpenSpec + Skills 深度研究
│
├── human-ai-collaborative-memory-design.md    # 人机协作记忆系统设计
├── human-ai-memory-experiment-report.md       # habit-tracker 实验报告
│
tools/                             # 配套工具
├── code-context/                  # 统一代码上下文 CLI
│   ├── bin/code-context          # 主程序
│   ├── skills/SKILL.md            # Agent 使用规范
│   └── README.md
│
└── habit-tracker/                # 习惯追踪系统原型
    ├── src/habit_tracker/        # 核心代码
    │   ├── models.py             # 数据模型
    │   ├── observer.py            # 模式识别
    │   ├── validator.py           # 动作验证
    │   └── storage.py             # 存储层
    └── setup.py

README.md（本文件）
```

---

## 核心洞察

### 1. Harness 设计者

```
AI 时代程序员的角色转变：

过去：实现功能 → 写代码
未来：设计约束 → 定义规范

Harness = OpenSpec 规范层 + Agent Skills 执行层 + PR/CI 约束层
```

### 2. Skills 三层架构

```
capabilities（原子）  → 单用途、近似确定性
composites（分子）     → 组合 2-10 个 capabilities
playbooks（复合）      → 编排多个 composites，给 AI 自主权
```

**杠杆效应**：驱动 Atoms → 5个原子任务；驱动 Compounds → 5复合+50分子+500原子（**100x 差异**）

### 3. Token 优化数据

```
RTK 压缩效果：
30分钟会话：118,000 → 23,900 tokens
节省：80%
年化节省：$170/人
```

### 4. 代码 RAG 决策树

```
< 1万行  → 不需要 RAG，直接丢给 AI
1-10万行 → code-context + grep
10-50万行 → code-context (claude-context + gitnexus)
50万+行  → code-context + 增量索引 + 定期重建
```

---

## 配套工具

### code-context

统一代码上下文 CLI，封装语义搜索和知识图谱查询。

```bash
# 安装
npm install -g claude-context gitnexus

# 语义搜索
code-context search "用户认证"

# 调用关系
code-context who-calls parse_user_token

# 影响分析
code-context impact src/auth/jwt.py

# 依赖图
code-context graph --focus src/
```

### habit-tracker

人机协作习惯追踪系统，记录 AI 和人类的工作习惯。

```bash
# 安装
pip install -e ~/hermes_tech_trend/habit-tracker

# 观察行为
habit-tracker observe human "直接说，不要绕弯" --action explaining

# 验证动作
habit-tracker validate "rm -rf src/legacy"

# 查看习惯
habit-tracker habits --list-all
```

---

## 延伸阅读

### 核心项目

| 项目 | Stars | 用途 |
|------|-------|------|
| [RTK](https://github.com/rtk-ai/rtk) | 39.6k | Token 优化 |
| [MCP SDK](https://github.com/modelcontextprotocol/python-sdk) | - | 协议实现 |
| [awesome-mcp-servers](https://github.com/wong2/awesome-mcp-servers) | 70k+ | MCP 生态 |
| [claude-context](https://github.com/zilliztech/claude-context) | 6.6k | 代码语义搜索 |
| [MemPalace](https://github.com/MemPalace) | 50.7k | 记忆系统 |
| [harness-init](https://github.com/Gizele1/harness-init) | - | 项目初始化 |

---

## 贡献指南

欢迎提交 Issue 和 PR！

- 发现错误？请提交 Issue
- 有补充内容？请提交 PR
- 有问题？请在 Discussion 区提问

---

**License**: MIT
**Author**: CTO @ Fashion B2B Platform
**Last Updated**: 2026-05-02
