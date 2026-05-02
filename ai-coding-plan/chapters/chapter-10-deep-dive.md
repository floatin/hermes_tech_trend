# Chapter 10（深度版）：Git 才是 AI Coding 的最后一块拼图

> **副标题**：用状态机视角重新理解 Git——branch 是状态转移，PR 是约束门禁，Commit 是审计日志

**前置阅读**：[Chapter 10 草稿](./chapter-10-draft.md) — 建议先读草稿掌握全貌

---

## 10.0 开篇：Git 的新语义

2026 年，GitHub 官方在 Commit 规范中新增了两个字段：

```bash
# 2026 年新增的标准 AI Commit 格式
feat(auth): add captcha to login endpoint

Co-authored-by: claude-code <agent@claude.ai>
Task-ID: #1234
Out-of-scope: user registration, password reset, session management
Agent-Version: claude-sonnet-4-20250501
```

这不是一个"最佳实践"——这是 **Git 被迫为 AI Coding 时代扩展语义**。

**传统 Git 语义**：

```
commit = 代码快照 + 作者 + 时间 + 消息
branch = 指向 commit 的指针
PR = 代码审查 + 合并请求
```

**AI 时代 Git 新增语义**：

```
commit += Co-authored-by（区分人/AI贡献）
commit += Task-ID（追溯任务来源）
commit += Out-of-scope（声明行为边界）

PR += Scope Declaration（机器可读的任务边界）
PR += AI Review Gate（自动化行为检查）

branch = 任务边界（每个 branch 是一个孤立的任务宇宙）
```

理解这一点，才能理解为什么 **Git 是 AI Coding 时代最被低估的基础设施**——它的设计本来就适合"分布式、异步、多方贡献"的场景，而人机协同正是这样的场景。

---

## 10.1 用状态机视角理解 Git

### 10.1.1 Git 本质是一个有限状态机

把 Git 仓库看作一个状态机，很多事情就清楚了：

```
状态定义：
  S = 仓库中所有文件的完整内容

转移操作：
  commit  =  S → S'（产生新状态快照）
  branch  =  重命名一个状态指针
  merge   =  两个状态合并成新状态
  rebase  =  重排状态历史
  reset   =  回退到某个历史状态

状态转移规则：
  - 每个文件有且只有一个状态（最新 commit）
  - branch 是状态的标签，不是副本
  - 工作目录是"状态编辑器"，暂存区是"状态确认区"
```

### 10.1.2 AI Coding 时代的状态机扩展

```
新增状态：
  E = AI 编辑过的文件集合
  C = AI 声明的约束集合（Out-of-scope）
  R = Human Review 通过的状态集合

新增转移规则：
  AI commit  →  需标注 Co-authored-by
  AI push    →  触发 CI 行为检查
  PR merge   →  必须经过 Human Review Gate
```

### 10.1.3 Branch 是"任务的物理隔离"

```bash
# 传统理解：branch 是一个副本
git branch feature/login  # 复制了整个仓库

# 正确理解：branch 是一个状态指针
git branch feature/login  # 只是创建了一个指向当前 commit 的指针

# worktree 才是真正的物理隔离
git worktree add ../feature-login feature/login  # 创建独立工作目录
# 两个目录可以同时编辑同一个文件，不互相干扰
```

**AI Coding 的关键洞察**：

```
Agent A 在 src/auth/login.py 写：userId → user_id
Agent B 在 src/auth/login.py 写：UserId → user_id

如果在同一目录 → 冲突，必须串行
如果在不同 worktree → 无冲突，可以并行
```

---

## 10.2 PR 约束层的架构解析

### 10.2.1 草稿中的六层设计，对应三层实现

草稿中的"六大设计"实际上是三层实现：

```
┌─────────────────────────────────────────────────────┐
│ 表现层：PR 模板 + Branch 命名                        │
│  → 人类可读，声明任务边界                            │
├─────────────────────────────────────────────────────┤
│ 逻辑层：.ai_constraints + CI 检查                   │
│  → 机器可执行，自动拦截违规                          │
├─────────────────────────────────────────────────────┤
│ 验证层：GitHub Actions + Human Review               │
│  → 最终门禁，保证质量                               │
└─────────────────────────────────────────────────────┘
```

### 10.2.2 .ai_constraints 文件格式

```yaml
# .ai-constraints（项目根目录）
# 机器可读的 AI 行为约束配置

version: "1.0"  # 格式版本，便于后续升级

# 文件范围白名单
allowed_paths:
  - "src/auth/"
  - "src/handlers/"
  - "tests/unit/auth/"

# 文件范围黑名单（保护核心文件）
blocked_paths:
  - "src/core/"        # 核心业务逻辑，AI 不得单独修改
  - "src/legacy/"      # 遗留代码，需要特殊权限
  - ".env*"             # 环境变量，绝对禁止
  - "config/prod*"     # 生产配置，禁止 AI 改动

# 单次任务的文件数量上限
max_files_per_pr: 5

# 是否强制关联 issue
require_issue_link: true

# 允许的文件类型
allowed_extensions:
  - ".py"
  - ".ts"
  - ".js"
  - ".yaml"

# 禁止的命令（AI 不得执行）
blocked_commands:
  - "rm -rf"
  - "DROP DATABASE"
  - "chmod 777"

# Commit 规范
commit_format:
  required_fields:
    - "type"           # feat/fix/docs/refactor
    - "scope"          # 影响范围
    - "description"   # 简短描述
  ai_specific_fields:
    - "Co-authored-by"
    - "Task-ID"
    - "Out-of-scope"

# Diff 大小限制（防止一次改太多）
max_diff_lines: 300
```

### 10.2.3 CI 检查实现（GitHub Actions）

```yaml
# .github/workflows/ai-constraint-check.yml

name: AI Constraint Check

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  ai-constraint-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Parse Task-ID from branch
        id: parse
        run: |
          BRANCH="${{ github.head_ref }}"
          # 从 feat/ai/1234-add-captcha 提取 1234
          TASK_ID=$(echo "$BRANCH" | grep -oE '[0-9]+' | head -1)
          echo "task_id=$TASK_ID" >> $GITHUB_OUTPUT

      - name: Check files changed
        id: file-check
        run: |
          CHANGED_FILES=$(git diff --name-only ${{ github.base_ref }}...HEAD)
          echo "files=$CHANGED_FILES" >> $GITHUB_OUTPUT

      - name: Validate .ai-constraints
        run: |
          # 读取约束配置
          CONSTRAINT_FILE=".ai-constraints"
          if [ ! -f "$CONSTRAINT_FILE" ]; then
            echo "No .ai-constraints found, skipping"
            exit 0
          fi

          # 解析约束（使用 yq）
          ALLOWED=$(yq '.allowed_paths[]' $CONSTRAINT_FILE)
          BLOCKED=$(yq '.blocked_paths[]' $CONSTRAINT_FILE)
          MAX_FILES=$(yq '.max_files_per_pr' $CONSTRAINT_FILE)

          # 检查文件数量
          FILE_COUNT=$(echo "$CHANGED_FILES" | wc -l)
          if [ $FILE_COUNT -gt $MAX_FILES ]; then
            echo "ERROR: Changed $FILE_COUNT files, max allowed is $MAX_FILES"
            exit 1
          fi

          # 检查黑名单
          for file in $CHANGED_FILES; do
            for blocked in $BLOCKED; do
              if [[ "$file" == $blocked ]]; then
                echo "ERROR: File $file is in blocked paths"
                exit 1
              fi
            done
          done

          echo "All constraint checks passed"

      - name: Check commit format
        run: |
          COMMITS=$(git log ${{ github.base_ref }}..HEAD --format="%s")
          for commit in $COMMITS; do
            # 检查是否有 Co-authored-by（AI commit 标识）
            if git log -1 --format="%b" "$commit" | grep -q "Co-authored-by"; then
              echo "AI commit detected: $commit"
              # 检查 Out-of-scope 声明
              if ! git log -1 --format="%b" "$commit" | grep -q "Out-of-scope"; then
                echo "WARNING: AI commit without Out-of-scope declaration: $commit"
              fi
            fi
          done
```

---

## 10.3 七类失控的代码级诊断信号

### 3.1 Gold Plating（过度工程化）

**代码级信号**：

```python
# 信号1：导入了与任务无关的库
import logging        # 任务只需要 requests.get()
import dataclasses    # 任务只需要返回 dict
from abc import ABC   # 任务只需要简单函数

# 信号2：类继承层级超过必要
class BaseHandler(ABC):
    class Impl(BaseHandler):
        class FinalHandler(Impl):  # 三层继承，只为处理简单请求

# 信号3：定义了从未使用的配置类
@dataclass
class Config:
    retry_count: int = 3
    cache_enabled: bool = True
    cache_ttl: int = 300
    # Config 实例化后只用了 base_url

# 诊断命令：
# 检查 skill 的 L2 步骤是否包含非必需的抽象
```

### 3.2 Scope Creep（范围蔓延）

**代码级信号**：

```python
# 信号：改动涉及多个不相关的模块
# 文件 A：user/views.py（任务范围内）
# 文件 B：payments/views.py（任务范围外）
# 文件 C：notifications/handlers.py（任务范围外）

# AI "学到"了 login 需要发通知，于是改了通知模块
# 但用户的原始任务只是"login 加验证码"

# 诊断命令：
git diff --name-only | xargs -I {} dirname {}
# 如果输出包含超过 2 个独立模块的目录 → Scope Creep
```

### 3.3 Reuse Failure（复用失灵）

**代码级信号**：

```python
# 信号：项目已有 utils/http.py，AI 无视它自己写了一套
# 诊断：搜索项目中已有的工具函数，看 AI 是否重复实现

# 在任务开始前让 AI 读取项目工具清单：
# cat .claude/project-tools.md
# 会显示项目中已有的工具：
# - utils/http.py：HTTP 请求工具
# - cache_utils.py：缓存工具
# - db_helpers.py：数据库工具

# AI 应该被要求在开始前声明：
# "我将使用 utils/http.py 进行 HTTP 请求，而不是重新实现"
```

### 3.4 Hallucination Confidence（幻觉自信）

**代码级信号**：

```python
# 信号1：AI 说"测试通过"，但实际没运行测试
# AI 输出："✅ 所有测试通过"
# 实际情况：测试框架报错 "ModuleNotFoundError"

# 信号2：AI 声明完成，但有未捕获的导入错误
from django.db import models

class UserProfile(models.Model):
    class Meta:
        unique_together = ('name', 'email')  # ❌ 语法错误

# 诊断：强制要求 AI 在声明完成前执行：
# pytest --tb=short
# python -m py_compile src/**/*.py
# ruff check src/
```

### 3.5 Context Exhaustion（上下文耗尽）

**代码级信号**：

```python
# 信号：任务后期开始出现与早期约束不一致的代码
# 任务开始时：使用项目已有的 cache_utils
# 任务进行到第 20 个文件后：自己写了一套 cache

# 诊断：定期（每 N 个文件）强制 AI 复述原始约束
# 在 SKILL.md 中加入：
# ===
# 【每处理 5 个文件后，简要复述你的任务范围：
#  原始任务：
#  已完成：
#  剩余：
#  是否有偏离？
# 】
```

### 3.6 Aesthetic Overreach（审美越界）

**代码级信号**：

```python
# 信号1：函数参数超过 5 个
def func(a, b, c, d, e, f, g, h, i):  # 9 个参数

# 信号2：函数体超过 50 行
# 信号3：嵌套层级超过 3 层
# 信号4：圈复杂度 > 10

# 诊断命令：
# 函数参数数检查
grep -rn "def .*(" src/ | while read line; do
    func_def=$(echo "$line" | sed 's/.*def //')
    params=$(echo "$func_def" | grep -o "," | wc -l)
    if [ $params -gt 5 ]; then
        echo "TOO MANY PARAMS: $line"
    fi
done

# 函数行数检查
find src/ -name "*.py" -exec wc -l {} \; | awk '$1 > 50 {print $2, $1" lines"}'
```

### 3.7 Convention Mismatch（规范失配）

**代码级信号**：

```python
# 信号1：命名与项目规范不符
userData     # 项目用 snake_case：user_data
createOrder  # 项目用 camelCase：create_order

# 信号2：架构模式与项目不符
# Django CBV 项目里用了 Flask 函数视图
# DRF 项目里没用 Serializer

# 诊断：在 CLAUDE.md 中明确声明：
# 项目规范：
# - Python: snake_case, Django CBV, DRF Serializer
# - TypeScript: camelCase, React Hooks
# - 行数上限：单个函数 < 50 行
```

---

## 10.4 Git Worktree 多 Agent 并行架构

### 10.4.1 为什么是 Worktree 而不是调度器

```
方案对比：

1. 外部调度器（如 Ray/ Airflow）
   - 优点：功能强大，支持复杂 DAG
   - 缺点：引入新依赖，学习成本高
   - 适用：真正需要任务编排的场景

2. 多个 Git 副本（每个 Agent 一个 repo）
   - 优点：完全隔离
   - 缺点：合并困难，代码同步噩梦
   - 适用：几乎不适用

3. Git Worktree
   - 优点：共享 .git，最终可合并，独立工作目录无冲突
   - 缺点：同一文件不能在不同 worktree 同时修改
   - 适用：AI Coding 的多任务并行
```

### 10.4.2 Worktree 的技术原理

```bash
# Git 仓库的数据结构
.git/
├── objects/      # 所有 commit、tree、blob 对象（共享）
├── refs/         # 分支和 tag 指针（共享）
└── worktrees/    # worktree 元数据（每个 worktree 一条记录）

# 创建一个 worktree 时：
# 1. 在 .git/worktrees/ 创建元数据
# 2. 在 refs/ 创建 worktree 专属分支
# 3. 从 objects/ 检出文件到新目录（硬链接，不复制）
# 4. 新目录有独立的工作目录和暂存区

# 最终合并时：
git merge worktree-auth-refactor/feature/auth-refactor
# Git 自动处理所有变更
```

### 10.4.3 Claude Code + Worktree 集成

```bash
# Claude Code 官方 CLI 支持（2026年2月+）

# 启动 Claude Code 时指定 worktree
claude --worktree auth-refactor

# Claude Code 会自动：
# 1. 在对应分支创建/检出代码
# 2. 所有 commit、push 操作在正确分支
# 3. 不影响其他 worktree 的工作

# 推荐工作流：tmux + worktree
# 在 tmux 中为每个 Agent 创建独立会话
session-0: main repo (主开发)
session-1: feat/auth (认证重构)
session-2: feat/chat (聊天功能)
session-3: hotfix/urgent (紧急修复)

# 每个会话运行独立的 Claude Code 实例
```

### 10.4.4 Worktree 生命周期管理

```bash
#!/bin/bash
# worktree-manager.sh — 多 Agent Worktree 管理脚本

WORKTREE_BASE="/tmp/ai-worktrees"
REPO_DIR="$PWD"

# 创建新的 Agent Worktree
create_worktree() {
    local feature_name=$1
    local branch_name="feat/ai/$feature_name"
    local worktree_path="$WORKTREE_BASE/$feature_name"

    # 创建 worktree
    git worktree add "$worktree_path" -b "$branch_name"
    
    # 初始化 Claude Code 配置
    cat > "$worktree_path/.claude/project.md" << EOF
# AI Worktree: $feature_name
任务：$feature_name
分支：$branch_name
工作目录：$worktree_path
EOF

    echo "Worktree created: $worktree_path"
    echo "Start Claude: cd $worktree_path && claude"
}

# 列出所有 Worktree
list_worktrees() {
    git worktree list
}

# 清理已合并的 Worktree
cleanup_merged() {
    git worktree list --porcelain | grep "^worktree" | while read -r line; do
        path=$(echo "$line" | cut -d' ' -f2-)
        branch=$(git worktree list --porcelain "$path" | grep "^branch" | cut -d' ' -f2-)
        
        # 检查分支是否已合并到 main
        if git branch --merged main | grep -q "$branch"; then
            echo "Removing merged worktree: $path"
            git worktree remove "$path"
        fi
    done
}

# 主逻辑
case "$1" in
    create) create_worktree "$2" ;;
    list) list_worktrees ;;
    cleanup) cleanup_merged ;;
    *) echo "Usage: $0 {create|list|cleanup}" ;;
esac
```

---

## 10.5 Git Hooks 作为 AI 约束层

### 10.5.1 Git Hooks 在 AI 时代的价值

传统上 Git Hooks 用于：

- `pre-commit`：格式化代码、检查语法
- `commit-msg`：检查 commit 格式
- `pre-push`：运行测试

AI 时代可以新增：

- `pre-commit`：检查 AI 的改动范围
- `commit-msg`：强制 AI 声明 Out-of-scope
- `pre-merge`：AI 行为最终检查

### 10.5.2 AI 专用 Hooks 实现

```bash
#!/bin/bash
# .git/hooks/pre-commit-ai — AI 提交前检查

echo "Running AI constraint checks..."

# 读取本次改动的文件
CHANGED_FILES=$(git diff --cached --name-only)

# 读取 .ai-constraints
if [ -f ".ai-constraints" ]; then
    MAX_FILES=$(yq '.max_files_per_pr' .ai-constraints)
    
    FILE_COUNT=$(echo "$CHANGED_FILES" | wc -l)
    if [ $FILE_COUNT -gt $MAX_FILES ]; then
        echo "ERROR: Changing $FILE_COUNT files, max allowed is $MAX_FILES"
        exit 1
    fi
fi

# 检查是否有 Co-authored-by（AI commit 标识）
if grep -q "Co-authored-by: claude-code" .git/COMMIT_EDITMSG; then
    echo "AI commit detected, checking Out-of-scope..."
    if ! grep -q "Out-of-scope:" .git/COMMIT_EDITMSG; then
        echo "ERROR: AI commit must declare Out-of-scope"
        echo "Add: Out-of-scope: [what-you-did-not-change]"
        exit 1
    fi
fi

echo "All AI constraint checks passed"
```

```bash
#!/bin/bash
# .git/hooks/pre-merge-ai — AI PR merge 前最终检查

echo "Running AI merge gate checks..."

# 获取 AI 改动的文件列表
AI_FILES=$(git log --format="%H" --author="claude-code" $MERGE_BASE..HEAD --name-only | sort -u)

# 检查文件是否在允许范围内
for file in $AI_FILES; do
    if [ -f ".ai-constraints" ]; then
        BLOCKED=$(yq '.blocked_paths[]' .ai-constraints)
        for blocked in $BLOCKED; do
            if [[ "$file" == $blocked ]]; then
                echo "ERROR: File $file is in blocked paths"
                exit 1
            fi
        done
    fi
done

# 强制运行测试
echo "Running tests..."
if ! pytest --tb=short; then
    echo "ERROR: Tests failed, AI PR cannot be merged"
    exit 1
fi

echo "AI merge gate passed"
```

### 10.5.3 启用 AI Hooks

```bash
# 在项目初始化时安装 AI Hooks
cat > scripts/install-ai-hooks.sh << 'EOF'
#!/bin/bash

HOOKS_DIR=".git/hooks"
AI_HOOKS_DIR="scripts/ai-hooks"

for hook in pre-commit pre-merge; do
    if [ -f "$AI_HOOKS_DIR/${hook}-ai" ]; then
        # 如果已有 hook，追加内容
        if [ -f "$HOOKS_DIR/$hook" ]; then
            echo -e "\n# AI Hook\nexec '$AI_HOOKS_DIR/${hook}-ai'" >> "$HOOKS_DIR/$hook"
        else
            # 创建新 hook
            cp "$AI_HOOKS_DIR/${hook}-ai" "$HOOKS_DIR/$hook"
            chmod +x "$HOOKS_DIR/$hook"
        fi
    fi
done

echo "AI hooks installed"
EOF

chmod +x scripts/install-ai-hooks.sh
./scripts/install-ai-hooks.sh
```

---

## 10.6 Harness Engineering 四要素与 Git 映射

### 10.6.1 Spec / Hook / Review / Gate 在 Git 中的对应

| Harness 要素 | Git 对应 | 作用 |
|-------------|---------|------|
| **Spec** | Branch 名称 + PR 描述模板 | 声明任务边界（人类意图） |
| **Hook** | pre-commit/pre-merge hooks | 自动触发行为检查 |
| **Review** | PR Review + Human-in-the-loop | 人类最终决策 |
| **Gate** | CI/CD pipeline + 质量门禁 | 自动化验收标准 |

### 10.6.2 四要素的完整流程

```
用户发起任务
    ↓
创建 feature branch（Spec：定义任务边界）
    ↓
AI 开始开发
    ↓
pre-commit hook（Hook：检查文件范围、commit 格式）
    ↓
Commit（带 Co-authored-by + Task-ID + Out-of-scope）
    ↓
Push 到远程分支
    ↓
CI Pipeline（Gate：测试、lint、diff 大小）
    ↓
PR 创建（Review：Human Review 清单）
    ↓
Human Review 通过
    ↓
Merge（最终 Gate：最后一次测试）
```

---

## 10.7 七类失控的约束矩阵

| 失控类型 | 主要约束层 | 次要约束层 | 量化指标 |
|----------|-----------|-----------|---------|
| Gold Plating | CI diff 行数限制 | PR review 清单 | 单 PR < 300 行 diff |
| Scope Creep | Branch 策略 + PR scope 声明 | pre-commit 检查 | 改动的目录数 < 3 |
| Reuse Failure | CLAUDE.md 工具清单 | AI 强制声明复用 | 复用率 > 80% |
| Hallucination Confidence | 强制 CI 测试通过 | pre-merge hook | 测试覆盖率 > 70% |
| Context Exhaustion | 定期约束复述 | 任务拆解 | 单任务文件数 < 10 |
| Aesthetic Overreach | 行数/嵌套检查 CI | PR review | 单函数 < 50 行 |
| Convention Mismatch | Lint + CI | CLAUDE.md 规范 | Lint 错误 = 0 |

---

## 10.8 本章小结

**Git 在 AI Coding 时代的新语义**：

- Commit 增加 Co-authored-by + Task-ID + Out-of-scope
- PR 增加 Scope Declaration（机器可读的任务边界）
- Branch 成为任务的物理隔离单元

**三层约束架构**：

1. 表现层：PR 模板 + Branch 命名（人类可读）
2. 逻辑层：.ai-constraints + CI 检查（机器可执行）
3. 验证层：GitHub Actions + Human Review（最终门禁）

**Worktree 的核心价值**：

- 共享 .git（最终可合并）
- 独立工作目录（并行无冲突）
- Claude Code 原生支持（开箱即用）

**Git Hooks 的扩展**：

- pre-commit：检查文件范围、commit 格式
- pre-merge：最终行为检查
- AI Hooks 与传统 Hooks 可以共存

---

## 10.9 延伸阅读

| 资源 | 链接 | 推荐理由 |
|------|------|----------|
| Martin Fowler - Harness Engineering | https://martinfowler.com/articles/harness-engineering-for-llm-agents/ | Harness 理论奠基 |
| Phodal - Routa | https://github.com/phodal/routa | Harness 实战项目 |
| Git Worktree 文档 | https://git-scm.com/docs/git-worktree | 官方文档 |
| Claude Code Worktree 支持 | Anthropic 官方博客（2026-02） | CLI 原生支持 |

---

*Chapter 10 Deep Dive v1.0 | 预估阅读时间：30 分钟 | 适合人群：AI Coding 团队负责人、DevOps 工程师、Harness 设计者*
