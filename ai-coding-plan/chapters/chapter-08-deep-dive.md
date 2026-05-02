# Chapter 8（深度版）：Skills 膨胀管理

> **副标题**：当 65 个 Skills 塞满你的 AI，五层架构是解药还是安慰剂？

**前置阅读**：[Chapter 8 草稿](./chapter-08-draft.md) — 建议先读草稿掌握全貌

---

## 8.0 一个反直觉的现象

ECC（Everything Claude Code）在 2026 年 4 月底突破 **105,000 stars**，一个月暴涨 53,000 star。

它的 skills/ 目录里有 **65+ 个工作流技能**，被全网当作"Skills 管理标杆"来引用。

但如果你仔细看它的源码，会发现一个有趣的事实：

**ECC 的 Skills 管理秘密，不在 `skills/` 目录里。**

```
ecc 目录结构（核心部分）：

.claude-plugin/
├── plugin.json          # 插件清单
├── marketplace.json     # 市场目录
│
├── agents/              # ← 第1层：角色
│   ├── code-reviewer.md
│   ├── test-engineer.md
│   └── devops.md
│
├── skills/              # ← 第2层：技能（65+）
│   ├── debugging/
│   ├── testing/
│   └── deployment/
│
├── commands/            # ← 第3层：斜杠命令
│   ├── plan.md
│   ├── tdd.md
│   └── code-review.md
│
├── rules/               # ← 第4层：规则约束
│   └── naming-convention.md
│
└── hooks/               # ← 第5层：事件钩子
    └── memory-hint.md
```

65 个 skills 是**结果**，不是**解法**。

ECC 真正解决的是：**把不同性质的东西放在不同的目录里**。

这引出了我们今天要深入探讨的核心命题：

> **Skills 膨胀有两个维度——数量维（越积越多）和结构维（越写越乱）。ECC 的五层架构解决的是结构维，但数量维需要另一套治理机制。两者都要处理，否则按下葫芦浮起瓢。**

---

## 8.1 Skills 膨胀的两个维度

### 8.1.1 维度一：数量膨胀

**表现**：

```
第1个月：5 个 skills（都很精炼）
第3个月：15 个 skills（开始有点多）
第6个月：32 个 skills（需要分组了）
第12个月：65 个 skills（AI 激活判断开始出错）
```

**典型症状**：

```
用户：帮我优化这段 SQL
AI：[激活 skills/postgres] [激活 skills/sqlite] [激活 skills/mysql]
AI：我应该用哪个？
用户：就普通的后端数据库查询
AI：[激活 skills/backend] [激活 skills/database] [激活 skills/query-optimization]
AI：……还是不确定
```

**根本原因**：每个 skill 单独看都合理，加在一起就开始相互干扰。**"每个 Skill 都有道理，加在一起就不合理"**——这是数量膨胀的本质。

### 8.1.2 维度二：结构混乱

**表现**：

同一个 SKILL.md 文件里混了三种东西：

```markdown
---
name: database-debug
description: 用于调试数据库连接和 SQL 查询问题
---

# 这个 Skill 做的事：

## 1. 能力定义（capability）
（用于判断是否激活）

## 2. 复合流程（composite）
（用于指导具体执行步骤）

## 3. 约束规则（rule）
（用于限制执行边界）

## 4. 触发命令（command）
（用于手动激活）
```

**一个文件干了四件事，这就是结构混乱。**

### 8.1.3 两个维度的对比

| 维度 | 表现 | 解决思路 |
|------|------|----------|
| **数量膨胀** | 65 个 skills，AI 不知道激活哪个 | 审计 + 合并 + 定期清理 |
| **结构混乱** | capability/composite/command/rule 混在一个文件里 | 五层分离 + 边界划清 |

**ECC 的五层架构解决的是结构混乱，不是数量膨胀。**

ECC 有 65 个 skills——**数量依然在膨胀**，但因为结构清晰，所以 AI 激活判断仍然准确。

---

## 8.2 ECC 五层架构源码解析

### 8.2.1 第一层：agents/ — 角色边界

**文件格式**：

```markdown
---
name: code-reviewer
description: |
  专业代码审查智能体。专注于发现 bug、
  安全漏洞、性能问题和代码风格问题。
  当用户说"审查代码"、"看看有没有问题"、
  "PR review"时激活。
---

# 执行流程

1. 接收代码片段或文件路径
2. 按维度逐一分析
3. 输出结构化审查报告
```

**关键设计**：

- `name` 是机器友好的标识符
- `description` 是**激活触发器**（L1），描述了何时调用这个 agent
- **不包含执行细节**——那是 skills/ 的职责

**和 skills/ 的关系**：

```
agents/code-reviewer.md
  └→ 激活后会加载 skills/code-review.md（具体执行）
  └→ 加载 rules/security.md（约束）
  └→ 加载 hooks/pre-review.md（前置钩子）
```

**也就是说，agents/ 定义的是"谁来干"，skills/ 定义的是"怎么干"。**

### 8.2.2 第二层：skills/ — 能力封装（三层架构）

这是最核心的一层。先回顾草稿里的三层定义，再深入源码。

**SKILL.md 标准格式**：

```markdown
---
name: tdd-workflow
description: 测试驱动开发流程。激活条件：
  用户提到 TDD、测试优先、红绿重构。
---

# L1 触发描述（<4KB，总计）

这个 Skill 用于 TDD 流程。
激活场景：用户要求 TDD、要求先写测试、
要求红绿重构循环。

# L2 核心执行逻辑（500-800 tokens）

## TDD 三步循环

1. **红**（Red）：先写一个失败的测试
   - 描述期望的行为
   - 不管实现，只管测试

2. **绿**（Green）：写最小实现让测试通过
   - 不追求完美，只求通过
   - 可以硬编码

3. **重构**（Refactor）：改善代码质量
   - 消除重复
   - 保持测试通过

## 常用命令

\`\`\`bash
npm test
npm run test:watch
\`\`\`

# L3 资源引用（按需加载）

模板文件：`templates/tdd-test-template.py`
示例：`examples/tdd-auth-flow.py`
参考：`https://example.com/tdd-guide`
```

**capabilities / composites / playbooks 三层的实际区分**：

```python
# 这是草稿里的三层定义
SKILL_TYPES = {
    # capabilities — 原子能力，<100 tokens
    # 激活后作为工具调用，不进入 LLM 推理
    "capability": "atomic skill, tool-like invocation",

    # composites — 复合流程，500-800 tokens
    # 激活后进入 LLM 推理，引导执行步骤
    "composite": "workflow skill, step-by-step guidance",

    # playbooks — 完整剧本，>800 tokens
    # 应该拆分或引用外部文件
    "playbook": "full scenario, should be split or externalized"
}
```

**区分标准**：

| 类型 | 特征 | LLM 参与度 | 示例 |
|------|------|-----------|------|
| **capability** | 单一操作，可工具化调用 | 几乎零 | `git-commit`：执行 git commit |
| **composite** | 多步骤流程，需要推理引导 | 中等 | `tdd-workflow`：红→绿→重构 |
| **playbook** | 完整场景，包含分支和异常处理 | 高 | `full-code-review`：从 fetch 到 report |

**膨胀的标志**：当你的 capability 开始包含 if/else 分支，它就已经不是 capability 了。

### 8.2.3 第三层：commands/ — 斜杠命令触发

**文件格式**：

```markdown
---
name: /tdd
description: 启动 TDD 开发流程
---

# 执行步骤

1. 加载 skills/tdd-workflow.md
2. 确认当前文件语言和测试框架
3. 开始红：写第一个测试
4. 开始绿：写最小实现
5. 开始重构：清理代码
6. 循环直到完成

# 触发方式

用户输入 `/tdd` 时激活。
```

**commands/ vs skills/ 的边界**：

```
什么时候用 command？
  └→ 用户需要手动触发的入口
  └→ 明确的"一键执行"场景

什么时候用 skill？
  └→ AI 根据 description 自动判断激活
  └→ 需要 LLM 推理引导的场景
```

**膨胀的坑**：把 skills/ 里的 composite 当成 command 来用——"反正用户知道要用这个 skill"。结果是 skills/ 越来越依赖人工记忆，失去了自动激活的价值。

### 8.2.4 第四层：rules/ — 持续约束

**文件格式**：

```markdown
---
name: naming-convention
description: 命名规范约束，始终生效
---

# 命名规则

## 通用规则

- 变量名和函数名使用 camelCase 或 snake_case
  （项目约定为准）
- 类名使用 PascalCase
- 常量全部大写 + 下划线

## TypeScript 特定

- 接口名加 `I` 前缀：`IUserData`
- 类型名不加前缀：`type UserData = {...}`

## 禁止

- 不要用单字母变量名（循环计数器除外）
- 不要用中文拼音命名
- 不要用缩写，除非是公认的（API、URL、ID）
```

**关键特性**：rules/ 是**始终加载**的，不像 skills/ 那样需要匹配 description。

**rules/ vs skills/ L2 的约束部分**：

```python
# 混淆示例：约束写在 skill 里
skill = {
    "description": "用于数据库调试",
    "l2_steps": [
        "步骤1：检查连接池",
        "步骤2：验证SQL语法",      # ← 这是流程
        "【注意】不要在生产环境直接执行 DELETE"  # ← 这是约束
    ]
}

# 正确做法：约束写到 rules/
rules/naming-convention.md  # 始终生效的约束
skills/database-debug.md     # 只包含执行流程
```

### 8.2.5 第五层：hooks/ — 事件驱动自动化

**文件格式**：

```markdown
---
name: memory-hint
description: 任务结束时自动记录上下文提示
trigger: after_task_complete
---

# 自动执行

1. 提取本次任务的关键决策
2. 生成上下文提示（用于下次类似任务）
3. 追加到 .claude/memory/hints.md
```

**钩子类型**：

```python
HOOK_TYPES = {
    "before_task": "任务开始前执行",
    "after_task": "任务结束后执行",
    "on_error": "错误发生时执行",
    "before_tool": "工具调用前执行",
    "after_tool": "工具调用后执行",
}
```

**hooks/ 的价值**：把**每次都要做的事**自动化，而不是每次都让 skill 重复描述。

---

## 8.3 Skills 膨胀的五大根源

> 基于对 ECC 源码和 Anthropic 内部实践的分析

### 根源一：capability 和 composite 混用

**表现**：一个 skill 既当原子工具又当复合流程，激活后 AI 不知道该走工具调用还是 LLM 推理。

```markdown
# ❌ 混在一起的写法
---
name: git-helper
description: Git 辅助工具
---

# 步骤1：检查状态
git status

# 步骤2：添加文件
git add .

# 步骤3：提交
git commit -m "$1"

---
description: Git 常用命令封装
---
```

```markdown
# ✅ 正确分离

# --- capabilities/git-status.md ---
name: git-status
type: capability
description: 检查 Git 工作区状态
trigger: "git status"、"查看改动"
tools: ["Bash(git status)"]

# --- capabilities/git-commit.md ---
name: git-commit
type: capability
description: 提交更改
trigger: "提交"、"commit"
tools: ["Bash(git commit *)"]

# --- composites/git-workflow.md ---
name: git-workflow
type: composite
description: Git 标准工作流程
trigger: "标准 git 流程"、"commit 规范"
steps:
  1. 执行 git status 确认状态
  2. 执行 git add 添加文件
  3. 生成符合 conventional commits 的 message
  4. 执行 git commit
```

### 根源二：skills/ 和 commands/ 边界模糊

**表现**：该用 command 触发的写成了 skill，该自动激活的写成了 command。

```python
# 边界判断标准

def should_use_command(skill_description):
    """满足以下任一条件 → 用 command"""
    return any([
        "用户会主动说" in skill_description,        # 手动触发场景
        "一键" in skill_description,               # 明确入口
        "当用户说 /" in skill_description,         # 斜杠命令
    ])

def should_use_skill(skill_description):
    """满足以下任一条件 → 用 skill"""
    return any([
        "当用户提到" in skill_description,          # 自动判断
        "分析" in skill_description,               # 需要推理
        "审查" in skill_description,               # 需要 LLM 介入
    ])
```

### 根源三：rules/ 缺失，约束硬编码在 skill 里

**表现**：每个 skill 都重复写着"不要在生产环境..."、"必须验证输入..."。

```markdown
# ❌ 约束写在 skill 里（重复 + 难以全局修改）
---
name: db-migration
---
步骤：
1. 备份数据库
2. 执行迁移脚本
3. 验证结果
【注意】所有操作必须先在测试环境验证
【注意】不要在业务高峰期执行
【注意】执行前必须备份

---
name: cache-clear
---
步骤：
1. 检查缓存大小
2. 确认清理范围
3. 执行清理
【注意】所有操作必须先在测试环境验证
【注意】不要在业务高峰期执行
【注意】执行前必须备份
# ← 这三条约束重复了三遍
```

```markdown
# ✅ 约束写到 rules/（一次定义，全部生效）

# --- rules/production-safety.md ---
---
name: production-safety
description: 生产环境安全约束，始终生效
---
- 所有操作必须先在测试环境验证
- 不要在业务高峰期执行
- 执行前必须备份

# --- skills/db-migration.md ---
---
name: db-migration
description: 数据库迁移
---
步骤：
1. 备份数据库
2. 执行迁移脚本
3. 验证结果

# --- skills/cache-clear.md ---
---
name: cache-clear
description: 缓存清理
---
步骤：
1. 检查缓存大小
2. 确认清理范围
3. 执行清理
```

### 根源四：追求"通用 skill"，激活判断失效

**表现**：description 写得越通用越好，"什么场景都能用"成了目标。

```markdown
# ❌ 过度通用的 skill
---
name: coding-helper
description: |
  这是一个编程辅助 skill，当用户需要写代码、
  改代码、分析代码、审查代码、测试代码、
  部署代码、优化代码、调试代码时激活。
  几乎涵盖了所有编程相关场景。
---
```

```markdown
# ✅ 精准激活的 skill
---
name: python-unittest
description: |
  Python unittest 框架使用指南。
  激活条件：用户提到 unittest、TestCase、
  setUp、tearDown、assertEqual、单元测试。
  不包含：pytest（见 skills/pytest-guide）、
  集成测试（见 skills/integration-test）。
---
```

**根本原则**：description 的目标是**精准激活**，不是**全面覆盖**。

### 根源五：L1 描述膨胀，总计超过 4KB

**表现**：所有 skills 的 L1 description 加起来超过了 Anthropic 建议的 4KB 上限。

```python
# Anthropic 官方建议
SKILL_LIMITS = {
    "l1_total": "< 4KB（所有 skills 的 description 总计）",
    "l2_per_skill": "500-800 tokens",
    "l3_per_skill": "按需加载，不一次性加载"
}
```

**自检方法**：

```bash
# 计算当前 L1 总大小
find ~/.claude/skills/ -name "SKILL.md" -exec head -10 {} \; \
  | grep "^description:" -A 5 \
  | wc -c
```

---

## 8.4 扁平 vs 分层：三种实战方案

### 方案一：ECC 五层分离（生产验证，推荐）

**适用场景**：团队协作、Skills 数量 20+

**架构**：

```
.claude/
├── agents/          # 角色定义（谁来做）
├── skills/          # 能力封装（怎么做）
│   ├── capabilities/   # 原子能力
│   ├── composites/     # 复合流程
│   └── playbooks/      # 完整剧本
├── commands/        # 斜杠命令（什么时候做）
├── rules/           # 约束规则（必须遵守什么）
└── hooks/           # 事件钩子（自动化）
```

**优点**：

- 职责清晰，AI 激活判断准确
- 支持多人协作，按角色分工
- 可单独审计每一层

**缺点**：

- 初期建设成本高
- 需要团队约定和文档

### 方案二：Tag 驱动筛选（轻量级，适合 <20 skills）

**适用场景**：个人使用、Skills 数量 <20

**实现**：

```yaml
# SKILL.md 加上 tags
---
name: sql-optimization
tags:
  - database
  - performance
  - backend
  - postgresql
triggers:
  - "sql"
  - "数据库"
  - "查询慢"
---

# 按标签加载
def load_skills(task: str) -> list[Skill]:
    task_tags = extract_tags_from_task(task)
    return [
        s for s in all_skills
        if s.tags & task_tags  # 标签交集 > 0
    ]
```

**优点**：

- 简单，不需要复杂的目录结构
- 灵活，一个 skill 可以有多个标签

**缺点**：

- 标签的一致性难以维护
- 超过 20 个 skills 后判断成本变高

### 方案三：Skills Composition 流水线（适合复杂工作流）

**适用场景**：有明确流程的重复性任务

**原理**：把一个复杂任务拆成 Skills 流水线，每个 Skill 做一步。

```
用户：部署到 K8s 并配置监控

Pipeline:
skill-1: docker-build      → 构建镜像
    ↓
skill-2: k8s-deploy        → 部署到集群
    ↓
skill-3: monitoring-setup  → 配置监控
    ↓
skill-4: smoke-test         → 冒烟验证
```

**ECC 里的实践**：

```markdown
# agents/fullstack-developer.md
---
name: fullstack-developer
description: 全栈开发智能体，可处理前端、后端、数据库任务
---

# 会按需加载以下 skills：

## 必需
- skills/backend-api-design.md
- skills/frontend-component.md

## 按需
- skills/database-schema.md  （如涉及数据库）
- skills/testing-e2e.md       （如涉及 E2E 测试）
```

---

## 8.5 膨胀治理三部曲（Anthropic 内部经验）

> 来自 Anthropic 官方文档和社区实践

### 第一步：审计——量化膨胀程度

```bash
# 统计 Skills 数量
find ~/.claude/skills/ -name "SKILL.md" | wc -l

# 计算 L1 总大小
find ~/.claude/skills/ -name "SKILL.md" \
  -exec sed -n '1,10p' {} \; \
  | grep -v "^---" \
  | grep -v "^name:" \
  | wc -c

# 找出超过 800 tokens 的 L2
for f in $(find ~/.claude/skills/ -name "SKILL.md"); do
  tokens=$(wc -w < "$f")
  if [ $tokens -gt 800 ]; then
    echo "$f: $tokens tokens"
  fi
done

# 统计各类型比例
find ~/.claude/skills/ -name "SKILL.md" \
  -exec grep -l "type: capability" {} \; | wc -l
find ~/.claude/skills/ -name "SKILL.md" \
  -exec grep -l "type: composite" {} \; | wc -l
```

**健康指标**：

| 指标 | 建议值 | 警告值 |
|------|--------|--------|
| Skills 总数 | < 20 | > 30 |
| L1 总大小 | < 4KB | > 8KB |
| L2 平均 tokens | 500-800 | > 1000 |
| capability 占比 | > 50% | < 30% |

### 第二步：分离——按五层架构重组

**操作步骤**：

```
1. 创建目录结构
mkdir -p agents/ skills/capabilities/ skills/composites/ commands/ rules/ hooks/

2. 识别每个 skill 的类型
  ├→ 原子操作 → capabilities/
  ├→ 复合流程 → composites/
  ├→ 手动触发 → commands/
  ├→ 持续约束 → rules/
  └→ 事件驱动 → hooks/

3. 迁移和拆分
  └→ 原始 skill 有多种类型 → 拆成多个文件

4. 验证激活逻辑
  └→ 同一触发条件不应激活多个 skill
```

### 第三步：锁定——版本控制 + 定期 review

```bash
# 锁定 Skills 版本（git 管理）
cd ~/.claude
git init
git add skills/ agents/ rules/ commands/ hooks/
git commit -m "feat: lock skills version $(date +%Y-%m-%d)"

# 定期 review（每月一次）
# review 检查清单：
#   - 有没有长时间未用的 skill？
#   - 有没有功能重复的 skill？
#   - 有没有 description 过于模糊的 skill？
#   - 有没有可以合并的 capability？
```

---

## 8.6 五大避坑指南

### 坑1：把所有逻辑都塞进 SKILL.md 的 description

**错误示例**：

```markdown
# L2 写了 2000 tokens，包含了所有边缘场景
# 结果：LLM 推理成本高，AI 执行速度慢
```

**正确做法**：

```markdown
# L2 只写核心流程，边缘场景引用 L3
---
name: http-client
---

# 核心流程（<800 tokens）

1. 构造请求
2. 发送请求
3. 处理响应
4. 错误处理

# 边缘场景（引用 L3）
参见：references/edge-cases.md
```

### 坑2：skills/ 和 commands/ 选一个但混用

**错误示例**：

```markdown
# skills/submodule-update.md
---
description: 当用户说"更新子模块"时激活
---
# 用户明明可以说 /submodule-update
# 但你写成了 skill，AI 会先判断激活
# 然后再执行，绕过了 command 的直接性
```

**正确做法**：

```markdown
# 如果是手动触发 → 用 command
# --- commands/submodule-update.md ---
name: /submodule-update
description: 手动更新 Git 子模块
---

# 如果是 AI 自动判断 → 用 skill
# --- skills/git-submodule.md ---
description: Git 子模块相关操作...
---
```

### 坑3：没有 rules/，靠 skill 硬编码约束条件

**错误示例**：

```markdown
# skills/deploy.md
---
description: 部署相关
---
步骤1：登录服务器
步骤2：停止服务
步骤3：备份数据
【注意】不要在业务高峰期部署
【注意】部署前必须通知相关人员
【注意】部署后要验证服务正常
```

**正确做法**：

```markdown
# --- rules/production-deployment.md ---
---
name: production-deployment
description: 生产部署安全规范，始终生效
---
- 部署前必须通知相关人员
- 部署后要验证服务正常
- 禁止在业务高峰期部署

# --- skills/deploy.md ---
---
description: 部署执行流程
---
步骤1：登录服务器
步骤2：停止服务
步骤3：备份数据
步骤4：执行部署
```

### 坑4：追求"通用 skill"导致激活判断失效

**错误示例**：

```markdown
description: |
  用于各种编程任务，包括但不限于：
  写代码、改代码、审查代码、测试代码、
  部署代码、调试代码、优化代码、分析代码、
  重构代码、文档编写、API 设计、数据库设计...
```

**正确做法**：

```markdown
description: |
  Python 单元测试编写。
  激活条件：用户提到 unittest、TestCase、
  setUp、tearDown、assertEqual。
  不包含：pytest（见 skills/pytest）、集成测试。
```

### 坑5：忽视 L1 描述膨胀

**自检命令**：

```bash
# 检查 L1 总大小
total=0
for f in $(find ~/.claude/skills/ -name "SKILL.md"); do
  desc=$(sed -n '/^---$/,/^---$/p' "$f" | grep "^description:" | wc -c)
  total=$((total + desc))
done
echo "L1 total: $total bytes (建议 < 4096)"
```

---

## 8.7 决策树

```
【问题1】这个组件是什么性质？

├── 单一操作，可工具化调用
│   └── → capability（skills/capabilities/）
│
├── 多步骤流程，需要 LLM 推理引导
│   └── → composite（skills/composites/）
│
├── 完整场景剧本，>800 tokens
│   └── → playbook（拆分或外部引用）
│
├── 用户手动触发，一键执行
│   └── → command（commands/）
│
├── 始终生效的约束，不需要判断激活
│   └── → rule（rules/）
│
└── 事件驱动，每次任务自动执行
    └── → hook（hooks/）


【问题2】Skills 数量膨胀怎么办？

├── 总数 < 20
│   └── → Tag 驱动筛选，暂不需要复杂架构
│
├── 总数 20-50
│   └── → 按五层分离，建立 agents/ 和 rules/
│
└── 总数 > 50
    └── → 审计 + 合并 + 五层重组 + 定期 review


【问题3】激活时多个 Skills 冲突怎么办？

├── description 过于通用
│   └── → 精准化 description，限制触发条件
│
├── capability 和 composite 混用
│   └── → 拆分成独立文件
│
└── 同一角色有多个 Skill
    └── → 合并或按触发场景进一步细分


【问题4】L2 超过 800 tokens 怎么办？

├── 包含边缘场景处理
│   └── → 移到 L3 引用文件
│
├── 包含参考文档
│   └── → 移到 L3 外部链接
│
└── 核心流程本身就过长
    └── → 拆成多个 composite 流水线
```

---

## 8.8 本章小结

**Skills 膨胀的两个维度**：

1. **数量维度**：Skills 越积越多，激活判断成本高
   → 解法：审计 + 合并 + 定期清理

2. **结构维度**：capability/composite/command/rule/hook 混在一起
   → 解法：ECC 五层分离架构

**ECC 的真正价值**：

- 不是"65 个 skills 就该这样管"
- 而是"把不同性质的东西放在不同的目录里，AI 才知道什么时候激活哪个"

**治理三步曲**：

1. 审计：量化膨胀程度，找到问题所在
2. 分离：按五层架构重组，划清边界
3. 锁定：版本控制 + 每月 review，防止回潮

**Anthropic 官方建议**：

- Skills 总数 < 20
- L1 总计 < 4KB
- L2 每个 500-800 tokens
- capability 占比 > 50%

---

## 8.9 延伸阅读

| 资源 | 链接 | 推荐理由 |
|------|------|----------|
| ECC GitHub | https://github.com/affaan-m/everything-claude-code | 105k stars，生产验证 |
| Anthropic Skills 文档 | https://docs.anthropic.com/en/docs/claude-code/skills | 官方定义，最权威 |
| Skills 三层架构（Shiv Sakhuja） | 原文见 Chapter 7 deep-dive | capabilities/composites/playbooks 原始论文 |
| Claude Code Skills 完全指南 | CSDN（2026-04） | 中文详解，16 个预置技能 |
| Anthropic 内部团队技巧 | https://www.cnblogs.com/leadingcode/p/19615864 | 官方工程师实战 |

---

## 附录：ECC 五层架构速查卡

```
┌─────────────────────────────────────────────────────┐
│  agents/     │ 角色边界        │ 谁来做             │
├──────────────┼─────────────────┼───────────────────┤
│  skills/     │ 能力封装        │ 怎么做             │
│   ├capability│  原子操作       │  工具调用          │
│   ├composite │  复合流程       │  LLM 推理          │
│   └playbook  │  完整剧本       │  拆分或引用        │
├──────────────┼─────────────────┼───────────────────┤
│  commands/   │ 斜杠命令        │ 什么时候做         │
├──────────────┼─────────────────┼───────────────────┤
│  rules/      │ 约束规范        │ 必须遵守什么       │
├──────────────┼─────────────────┼───────────────────┤
│  hooks/      │ 事件钩子        │ 自动化             │
└─────────────────────────────────────────────────────┘
```

---

*Chapter 8 Deep Dive v1.0 | 预估阅读时间：25 分钟 | 适合人群：Claude Code 深度用户、团队 AI Harness 设计者*
