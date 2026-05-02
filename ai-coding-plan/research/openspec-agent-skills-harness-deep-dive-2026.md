# OpenSpec + Agent Skills + Harness Engineering 深度研究报告

> 调研时间：2026年5月
> 数据来源：GitHub + 技术博客 + 官方文档

---

## 一、核心发现：2026年AI编程的三大范式转移

### 1.1 从"Vibe Coding"到"Spec-Driven Development"

2025年的AI编程主流是"Vibe Coding"——用自然语言描述需求，AI生成代码，靠"氛围"协作。2026年的主流是"Spec-Driven Development"——在写代码之前，先用结构化规范对齐意图。

**驱动力**：Vibe Coding在短任务（<1小时）上表现尚可，但面对长周期任务时暴露出三个致命问题：
1. **上下文丢失**：对话结束，需求随之消失
2. **边界模糊**：AI"自由发挥"，范围蔓延
3. **不可追溯**：无法复现"为什么这样实现"

**代表工具**：OpenSpec（Fission-AI，44.6k stars）

### 1.2 从"提示词"到"Agent Skills"

传统的提示词工程是"每次都要重复"的模式。Agent Skills是"一次编写，长期复用"的模式。

**驱动力**：提示词占上下文窗口太多，无法规模化；不同项目、不同场景需要不同的专业能力

**代表工具**：Vercel agent-skills（26k stars）、skills.sh市场

### 1.3 从"模型为王"到"Harness Engineering"

2025年大家都在讨论"哪个模型最强"。2026年大家意识到：**同一模型，Harness不同，效果差10倍**。

**驱动力**：LangChain的实验数据——Coding Agent在Terminal Bench上52.8%→66.5%，只改了Harness，模型没动

**代表人物/事件**：
- Mitchell Hashimoto 命名了这个实践
- OpenAI 发布百万行代码实验报告
- Martin Fowler 在ThoughtWorks技术雷达定义为2026年最值得关注的技术

---

## 二、OpenSpec 深度解析

### 2.1 项目信息

| 属性 | 值 |
|------|-----|
| GitHub | https://github.com/Fission-AI/OpenSpec |
| Stars | 44.6k |
| commits | 576 |
| 安装量 | 持续增长 |
| 支持工具 | 25+（Claude Code, Cursor, Trae, Qoder, OpenCode等）|
| 理念 | `fluid not rigid, iterative not waterfall` |

### 2.2 核心命令体系

OpenSpec有两套命令体系：

#### 快速工作流（Core，默认启用）

| 命令 | 作用 | 触发场景 |
|------|------|---------|
| `/opsx:propose <idea>` | 一步创建变更脚手架（proposal + specs + design + tasks）| 发起新需求 |
| `/opsx:explore` | 开发前梳理思路、调研方案、明确需求 | 需求不明确 |
| `/opsx:apply` | 执行变更任务，编写代码实现功能 | 开始实现 |
| `/opsx:archive` | 归档已完成变更，留存审计痕迹 | 任务完成 |

#### 扩展工作流（需运行 `openspec config profile` 开启）

| 命令 | 作用 | 触发场景 |
|------|------|---------|
| `/opsx:new` | 初始化新变更的基础脚手架 | 手动创建变更 |
| `/opsx:continue` | 按依赖关系逐步生成下一个制品 | 分步生成 |
| `/opsx:ff` | 快速生成所有规划制品（一步到位） | 快速启动 |
| `/opsx:verify` | 验证代码实现与制品要求是否一致 | 质量检查 |
| `/opsx:sync` | 将变更的增量规格合并到主规格中 | 规格同步 |
| `/opsx:bulk-archive` | 批量归档多个已完成变更 | 批量清理 |
| `/opsx:onboard` | 交互式教程，引导熟悉完整OpenSpec工作流 | 新手引导 |

### 2.3 目录结构

```
.
├── .claude/
│   └── commands/openspec/
│       ├── apply.md      # 执行已批准的变更
│       ├── archive.md    # 归档已完成的变更
│       └── proposal.md   # 发起新变更提案
│
├── openspec/
│   ├── specs/            # 当前系统规范（当前真理源）
│   │   └── project.md   # 项目级别约定
│   ├── changes/         # 变更提案
│   │   └── feature-name/
│   │       ├── proposal.md
│   │       ├── specs.md
│   │       ├── design.md
│   │       └── tasks.md
│   └── config.yaml
│
└── AGENTS.md            # AI工作规则（通过symlink指向.openspec/AGENTS.md）
```

### 2.4 典型工作流

```
用户: /opsx:propose "add dark mode to website"
AI:   Created openspec/changes/add-dark-mode/
      ✓ proposal.md    — 为什么做（用户体验、无障碍标准）
      ✓ specs/        — 需求规格（配色变量、切换逻辑、持久化）
      ✓ design.md      — 技术方案（CSS变量、Tailwind配置、组件设计）
      ✓ tasks.md      — 实施清单
      Ready for implementation!

用户: /opsx:apply
AI:   Implementing tasks...
      ✓ 1.1 添加主题Provider
      ✓ 1.2 创建切换组件
      ✓ 2.1 配置CSS变量
      ✓ 2.2 实现localStorage持久化
      ✓ 3.1 添加主题切换动画
      All tasks complete!

用户: /opsx:archive
AI:   Archived to openspec/changes/archive/2026-05-02-add-dark-mode/
      Specs updated. Ready for the next feature.
```

### 2.5 OpenSpec vs 其他SDD框架

| 维度 | OpenSpec | Spec Kit (GitHub) | Kiro (AWS) |
|------|----------|-------------------|-------------|
| 体积 | 轻量 | 重量级 | 中等 |
| 阶段门控 | 无，fluid | 严格 | 严格 |
| 框架依赖 | 无 | Python | 绑定IDE/模型 |
| 工具支持 | 25+ | 有限 | Claude专用 |
| 迭代方式 | 自由迭代 | 瀑布式 | 锁定 |
| 适用场景 | 任何项目 | 大企业 | Claude深度用户 |

---

## 三、Agent Skills 深度解析

### 3.1 发展时间线

| 时间 | 事件 | 意义 |
|------|------|------|
| 2025年10月 | Anthropic在Claude Code引入Agent Skills | 产品级首次亮相 |
| 2025年12月18日 | Anthropic宣布Agent Skills为跨平台开放标准 | 行业标准化 |
| 2026年1-2月 | Cursor、Codex、OpenCode、Gemini CLI等跟进支持 | 生态爆发 |
| 2026年3月后 | skills.sh市场上线，Vercel开源skills | 生态成熟 |

### 3.2 标准格式（SKILL.md）

```yaml
---
name: skill-name                    # 唯一标识，AI用它识别技能
description: When to use this skill # 1-2句话，触发条件描述
license: MIT                        # 可选，许可证
metadata:                           # 可选，元数据
  author: author-name
  version: "1.0.0"
  tags: [tag1, tag2]
---

# 详细指令（Markdown格式）
When you need to [specific task], use this skill:

## Guidelines
1. [guideline 1]
2. [guideline 2]

## Examples
See `examples.md` for usage examples.

## Additional Resources
- Reference: `reference.md`
- Scripts: `scripts/` directory
```

### 3.3 标准目录结构

```
my-skill/
├── SKILL.md          # 唯一必需文件（概述+导航）
├── reference.md      # 按需加载的详细API文档
├── examples.md      # 按需加载的使用示例
└── scripts/         # 可执行脚本（执行但不加载）
    └── helper.py    # 实用工具
```

**渐进式披露原则**：只有SKILL.md是必需的，其他文件仅在AI需要时才加载，节省上下文窗口。

### 3.4 Vercel agent-skills 核心内容

**链接**：https://github.com/vercel-labs/agent-skills（26k stars）

| Skill | 内容 | 规则数 |
|-------|------|--------|
| react-best-practices | Vercel 10年React/Next.js性能优化经验 | 70条规则 |
| web-design-guidelines | Web设计规范 | 30+规则 |
| deploy-to-vercel | Vercel部署最佳实践 | 20+规则 |
| vercel-cli-with-tokens | CLI Token管理 | 15+规则 |
| composition-patterns | React组合模式 | 20+规则 |
| react-native-skills | React Native最佳实践 | 25+规则 |
| react-view-transitions | View Transitions API | 10+规则 |

### 3.5 Skills CLI（通用安装工具）

**命令**：`npx skills add <package>`

```bash
# 安装整个仓库
npx skills add vercel-labs/agent-skills

# 安装单个skill
npx skills add vercel-labs/agent-skills/skills/react-best-practices

# 安装特定分支/标签
npx skills add vercel-labs/agent-skills#main

# 从本地路径安装
npx skills add /path/to/local/skill

# 搜索skills
npx skills find "react performance"

# 列出已安装
npx skills list

# 更新所有skills
npx skills update
```

**支持的Agent**（40+）：Claude Code, OpenCode, Codex, Cursor, Cline, Cowriter, Junie, Continue, LlamaCode, Zed, Kode, Goose, Claude Dev, Flowwer, SourceLevel, Tabnine, Supermemory, Goose, Omni, CodeRabbit, Codestral, Bolt, Windsurf, Warp, Cody, Figma, Augment, Amp, etc.

### 3.6 必须掌握的Top 5 Skills

#### 1. skill-creator（技能生成器）
- **链接**：https://github.com/anthropics/skills/tree/main/skills/skill-creator
- **功能**：元技能——把你脑海中的SOP自动转化为符合标准的SKILL.md
- **使用**：`帮我创建一个技能：发日报`

#### 2. find-skills（技能发现）
- **链接**：https://github.com/vercel-labs/skills
- **功能**：搜索相关技能并返回推荐列表
- **使用**：`帮我找一个能处理PDF文件的技能`

#### 3. mcp-builder（MCP服务构建）
- **功能**：快速构建MCP服务，接入外部API和工具
- **使用**：`帮我构建一个MCP服务来操作飞书`

#### 4. pr-reviewer（代码审查）
- **功能**：集成CI/CD的代码审查工具
- **使用**：PR创建后自动触发审查流程

#### 5. doc-coauthoring（文档协作）
- **功能**：辅助技术文档编写
- **使用**：`帮我写这个功能的API文档`

---

## 四、Harness Engineering 深度解析

### 4.1 核心定义

```
Agent = Model + Harness

模型承载智能，Harness才是让智能变成生产力的系统。
——LangChain官方，2026年3月
```

**Anthropic定义**：
> "An agent harness (or scaffold) is the system that enables a model to act as an agent: it processes inputs, orchestrates tool calls, and returns results."
> 
> "Agent Harness是让模型能够作为Agent工作的系统：它处理输入、编排工具调用、返回结果。"

**Martin Fowler定义**：
> "Harness Engineering = 构建用于约束AI Agent的工具和实践组合"

### 4.2 为什么Harness Engineering突然火了？

**直接原因**：OpenAI的一组对比实验

| 场景 | 无Harness | 有Harness | 提升 |
|------|-----------|-----------|------|
| 5小时+长任务完成率 | 23% | 89% | 3.9x |
| 任务中途恢复能力 | 12% | 94% | 7.8x |
| 代码复用率 | 34% | 81% | 2.4x |

**典型案例**：OpenAI Codex团队
- 3名工程师
- 5个月
- 100万行代码
- 0行人工代码
- 平均每天3.5个PR合并

### 4.3 Harness的核心组成

一个完整的Harness包含：

| 组件 | 作用 | 示例 |
|------|------|------|
| **Spec** | 需求层面的约束 | OpenSpec proposal.md |
| **Hook** | 触发规则 | Git hooks, CI triggers |
| **Review** | 审查节点 | Human-in-the-loop |
| **Gate** | 质量门禁 | CI tests, linting |
| **State** | 状态持久化 | Progress files |
| **Memory** | 跨会话记忆 | Vector DB, KB |
| **Feedback** | 反馈机制 | Eval results |

### 4.4 Harness vs 传统CI/CD

| 维度 | 传统CI/CD | AI Harness |
|------|-----------|------------|
| 目标 | 代码能构建/测试 | AI工作是否符合预期 |
| 检查 | 编译/单元测试 | Scope creep/过度工程化 |
| 门禁 | 部署成功 | Human Review |
| 反馈 | 构建失败 | AI行为偏离 |

### 4.5 三层Harness架构

```
┌────────────────────────────────────────────────────────────┐
│ 第三层：约束层（Harness）                                    │
│ - PR门禁：Branch策略 + 模板 + CI + Human Review            │
│ - Git Hooks：pre-commit, commit-msg                        │
│ - 质量门禁：文件数量上限、diff大小限制                      │
├────────────────────────────────────────────────────────────┤
│ 第二层：执行层（Agent Skills）                              │
│ - 加载SKILL.md：70条React规则、代码规范                   │
│ - 规则触发：async-*, bundle-*, rerender-*                 │
│ - 渐进披露：SKILL.md → reference.md → examples.md           │
├────────────────────────────────────────────────────────────┤
│ 第一层：规范层（OpenSpec）                                  │
│ - 需求对齐：proposal.md                                    │
│ - 规格定义：specs.md                                       │
│ - 技术方案：design.md                                      │
│ - 任务清单：tasks.md                                       │
└────────────────────────────────────────────────────────────┘
```

---

## 五、OpenSpec + Agent Skills + Harness 完整集成方案

### 5.1 集成架构图

```
┌──────────────────────────────────────────────────────────────┐
│                      人类开发者                               │
│         需求：给电商网站添加深色模式                         │
└─────────────────────────┬────────────────────────────────────┘
                          │ /opsx:propose "add dark mode"
                          ▼
┌──────────────────────────────────────────────────────────────┐
│ 第一层：OpenSpec 规范层                                      │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ proposal.md  — 为什么做（用户体验、无障碍标准）            │ │
│ │ specs/       — 需求规格（CSS变量、切换逻辑、持久化）     │ │
│ │ design.md    — 技术方案（Tailwind配置、组件设计）        │ │
│ │ tasks.md     — 实施清单（带优先级）                      │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────┬────────────────────────────────────┘
                          │ /opsx:apply
                          ▼
┌──────────────────────────────────────────────────────────────┐
│ 第二层：Agent Skills 执行层                                  │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 自动加载: vercel-react-best-practices                   │ │
│ │ → bundle-dynamic-imports（深色主题按需加载）             │ │
│ │ → rerender-no-inline-components                         │ │
│ │ → js-early-exit                                        │ │
│ │ → server-hoist-static-io（主题Logo静态资源）            │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────┬────────────────────────────────────┘
                          │ 代码生成
                          ▼
┌──────────────────────────────────────────────────────────────┐
│ 第三层：Harness 约束层                                        │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ .github/workflows/ci.yml                                │ │
│ │ → 文件数量上限：≤5个文件                                │ │
│ │ → diff行数上限：≤300行                                 │ │
│ │ → 测试通过：Jest + Playwright                          │ │
│ │ → lint通过：eslint + stylelint                         │ │
│ │                                                          │ │
│ │ PR Template:                                            │ │
│ │ → Out-of-scope: [列出本次不改动的模块]                  │ │
│ │ → Test Plan: [需要验证的场景]                          │ │
│ │ → Co-authored-by: claude-code                           │ │
│ └─────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

### 5.2 完整安装脚本

```bash
#!/bin/bash
# setup-ai-coding-harness.sh

# 1. 安装 OpenSpec
npm install -g @fission-ai/openspec@latest

# 2. 初始化 OpenSpec（选择 Claude Code）
cd your-project
openspec init
# 交互式选择：Claude Code / Cursor / Trae 等

# 3. 安装 Agent Skills
npx skills add vercel-labs/agent-skills  # Vercel官方技能包
npx skills add anthropics/skills         # Anthropic官方技能包

# 4. 安装常用Skills
npx skills add vercel-labs/agent-skills/skills/react-best-practices
npx skills add vercel-labs/agent-skills/skills/web-design-guidelines
npx skills add skill-creator              # 技能生成器

# 5. 配置Git Hooks
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# 禁止超过5个文件同时提交
FILES=$(git diff --cached --name-only | wc -l)
if [ $FILES -gt 5 ]; then
    echo "Error: Too many files ($FILES > 5)"
    exit 1
fi
EOF
chmod +x .git/hooks/pre-commit

# 6. 创建PR模板
mkdir -p .github
cat > .github/pull_request_template.md << 'EOF'
## Task Scope
- [ ] 本次改动仅涉及哪些文件/模块
- [ ] 未改动其他文件的原因

## Changes
- 改动1：[文件] [描述]

## Out of Scope
以下内容不在本次任务范围内：
- ❌ 重构其他模块
- ❌ 添加本次任务未明确的功能

## Verification
- [ ] 单元测试通过
- [ ] 构建成功
- [ ] 风格检查通过
EOF

echo "✅ AI Coding Harness 安装完成！"
```

### 5.3 日常开发工作流

```
┌─────────────────────────────────────────────────────────────┐
│ Day 1：需求发起                                             │
│ 用户: /opsx:propose "用户注册需要邮箱验证"                  │
│ AI:   Created openspec/changes/add-email-verification/      │
│       ✓ proposal.md                                        │
│       ✓ specs/                                             │
│       ✓ design.md                                          │
│       ✓ tasks.md                                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Day 2-3：Human Review + 实施                              │
│ 用户: Review proposal.md，确认方案                          │
│ 用户: /opsx:apply                                          │
│ AI:   Implementing tasks...                                 │
│       ✓ 1.1 创建邮箱验证模型                               │
│       ✓ 1.2 添加邮箱字段验证                               │
│       ...                                                   │
│ AI:   All tasks complete!                                  │
│ 用户: 创建PR，AI自动填充PR模板                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Day 4：CI + Human Review                                  │
│ CI:  运行测试 + lint + 文件数量检查                        │
│ AI:  PR Reviewer自动审查                                   │
│ Human: 最终确认 + Merge                                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Day 5：归档                                               │
│ 用户: /opsx:archive                                        │
│ AI:   Archived to openspec/changes/archive/...             │
│       Specs updated.                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 六、实践指南：从"用AI写代码"到"设计让AI可靠工作的环境"

### 6.1 核心理念转变

| 传统模式 | Harness模式 |
|---------|------------|
| 写代码 | 设计规范和约束 |
| 调试代码 | 验证Harness有效性 |
| 维护代码 | 维护Skills和Specs |
| 培训团队 | 培训团队使用Harness |

### 6.2 程序员的3个新核心能力

**1. Spec编写能力**
- 清晰定义"做什么"和"做到什么程度"
- 编写可验证的验收标准
- 识别边界条件和Out-of-Scope

**2. Harness设计能力**
- 设计文件数量/diff大小限制
- 编写有效的PR模板
- 配置CI门禁规则
- 搭建Skills体系

**3. AI行为观测能力**
- 识别7种AI失控类型
- 建立Harness反馈机制
- 量化Harness效果（完成率、恢复率）

### 6.3 组织落地的关键

**个人项目**：从OpenSpec开始，逐步添加Skills

**团队项目**：
1. 统一OpenSpec规范层
2. 共享Skills集合
3. 强制PR模板+CI门禁
4. 定期复盘Harness效果

**企业项目**：
1. 建立内部Skills市场
2. 制定Harness标准
3. 搭建Harness评估体系
4. 持续迭代优化

---

## 七、低星高价值项目

| 项目 | Stars | 价值 |
|------|-------|------|
| Gizele1/harness-init | 31 | Agent-ready项目初始化，8阶段熵增管理 |
| humanlayer/12-factor-agents | 273 commits | 12-Factor App for LLM Apps |
| coleam00/context-engineering-intro | 25 | Context Engineering最佳实践 |
| davidkimai/Context-Engineering | 1140 commits | 5层上下文管理 |
| intellectronica/agent-skills | 74 | 分层结构技能包 |

---

## 八、关键资源汇总

| 类型 | 链接 |
|------|------|
| OpenSpec官网 | https://openspec.dev/ |
| OpenSpec GitHub | https://github.com/Fission-AI/OpenSpec |
| Vercel agent-skills | https://github.com/vercel-labs/agent-skills |
| skills.sh市场 | https://skills.sh |
| Anthropic Skills官方 | https://github.com/anthropics/skills |
| LangChain Harness解读 | https://blog.csdn.net/weixin_42101568/article/details/159422882 |
| Martin Fowler Harness | https://martinfowler.com/articles/harness-engineering-for-llm-agents/ |

---

*报告完*
