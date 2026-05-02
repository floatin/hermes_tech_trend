# Chapter 10 附录：AI Harness 实战指南

> **副标题**：从 .ai-constraints 到 CI Pipeline 的完整约束体系落地

---

## A.1 决策树完整版

### 决策树 1：识别 AI 失控类型

```
【问题】AI 提交了 PR，以下哪个最符合观察到的问题？

├── 代码过于复杂，导入了不需要的库
│   └── → Gold Plating（过度工程化）
│
├── 改动涉及多个不相关的模块
│   └── → Scope Creep（范围蔓延）
│
├── 有现成的工具函数，AI 重新实现了一套
│   └── → Reuse Failure（复用失灵）
│
├── AI 说完成了，但实际有错误/测试失败
│   └── → Hallucination Confidence（幻觉自信）
│
├── 任务后期开始出现与早期约束不一致的代码
│   └── → Context Exhaustion（上下文耗尽）
│
├── 代码审美失控：超长函数、深度嵌套
│   └── → Aesthetic Overreach（审美越界）
│
└── 命名/架构与项目规范不符
    └── → Convention Mismatch（规范失配）
```

### 决策树 2：选择约束层

```
【问题】识别到失控类型后，选择哪个约束层？

├── 想在 AI 提交前自动拦截
│   ├── 拦截文件范围 → pre-commit hook
│   ├── 拦截 commit 格式 → commit-msg hook
│   └── 拦截命令执行 → pre-push hook
│
├── 想在 AI PR 创建后自动检查
│   ├── 检查文件范围 → CI workflow（.ai-constraints 解析）
│   ├── 检查 diff 大小 → CI workflow
│   ├── 检查测试通过 → CI workflow
│   └── 检查代码规范 → CI workflow（lint）
│
└── 想保留人类最终决策权
    ├── PR review 清单 → Human Review
    └── Merge gate → 必须 Human Review 通过
```

### 决策树 3：设计 Branch 命名策略

```
【问题】团队如何组织 AI 任务的分支命名？

├── 小团队（< 5 人同时用 AI）
│   └── → 简单前缀：feat/ai/{issue-id}-description
│
├── 中团队（5-20 人）
│   ├── 按角色分：feat/ai/auth-{issue-id}、feat/ai/backend-{issue-id}
│   └── 按紧急程度分：feat/ai/{issue-id}、hotfix/ai/{issue-id}
│
└── 大团队（> 20 人）
    ├── 必须 worktree 隔离（每个 AI 任务一个 worktree）
    ├── 分支命名包含 worktree 标识
    └── 定期合并到集成分支
```

### 决策树 4：Worktree vs 串行

```
【问题】团队同时有多个 AI 任务，该如何选择？

├── 任务是否涉及同一个文件/模块？
│   ├── 是 → 必须串行（Worktree 也无法解决同一文件冲突）
│   └── 否 → 继续判断
│
├── 任务是否需要实时协作？
│   ├── 是 → 单 repo + 外部调度器（Ray/Airflow）
│   └── 否 → 继续判断
│
├── 团队规模？
│   ├── 小团队（< 5 个并发任务）→ Worktree 推荐
│   └── 大团队 → 需要 worktree 管理脚本
│
└── 选择
    ├── 推荐：Worktree（独立目录 + 最终合并）
    └── 备选：多个 repo 副本（仅极端隔离场景）
```

---

## A.2 .ai-constraints 完整配置模板

```yaml
# .ai-constraints
# AI Coding 行为约束配置
# 放置于项目根目录

version: "1.0"

# ============================================
# 文件范围控制
# ============================================

allowed_paths:
  # 模块白名单：AI 只能改动这些目录
  - "src/features/{feature_name}/"  # 替换为具体功能名
  - "tests/unit/{feature_name}/"

blocked_paths:
  # 核心文件保护：绝对禁止 AI 单独修改
  - "src/core/"                     # 核心业务逻辑
  - "src/shared/entities/"          # 共享实体
  - ".env*"                         # 环境变量
  - "config/prod*"                  # 生产配置
  - "config/secrets*"               # 密钥配置
  - "migrations/"                    # 数据库迁移（需 DBA）

max_files_per_pr: 5                  # 单次任务最多改 5 个文件

# ============================================
# Commit 规范
# ============================================

commit_format:
  required:
    - type          # feat/fix/docs/refactor
    - scope         # 影响范围
    - description   # 简短描述

  ai_specific:
    - "Co-authored-by: claude-code <agent@claude.ai>"  # AI 提交标识
    - "Task-ID: #{issue_id}"                            # 追溯任务来源
    - "Out-of-scope: [未改动的相邻模块]"                # 声明边界

  format: "<type>(<scope>): <description>"

# ============================================
# Diff 控制
# ============================================

max_diff_lines: 300                  # 单 PR 最多 300 行 diff
max_file_lines: 100                  # 单文件最多 100 行改动

# ============================================
# 命令限制
# ============================================

blocked_commands:
  - "rm -rf /"                      # 危险操作
  - "DROP DATABASE"                  # 数据库危险操作
  - "chmod 777"                     # 权限问题
  - "curl.*--insecure"              # SSL 绕过
  - "git push --force"              # 强制推送

allowed_commands:
  - "git add"
  - "git commit"
  - "git push"
  - "pytest"
  - "ruff check"
  - "ruff format"
  - "mypy"

# ============================================
# 测试要求
# ============================================

test_requirements:
  require_test: true                # 改动必须包含测试
  min_coverage: 70                  # 最低覆盖率
  required_checks:
    - "pytest --tb=short"
    - "ruff check src/"
    - "ruff format --check src/"

# ============================================
# AI 行为信号
# ============================================

hallucination_signals:
  # AI "幻觉自信"时的典型输出模式
  patterns:
    - "所有测试通过"
    - "已完成"
    - "✅ 完成"
    - "任务完成"
  # 检测到这些词时强制要求验证
  require_verification: true

# ============================================
# 通知配置
# ============================================

notifications:
  # Scope Creep 检测到时通知
  scope_creep_alert:
    enabled: true
    channels:
      - slack: "#ai-coding-alerts"
      - feishu: "ai-coding-team"

  # 上下文耗尽检测到时通知
  context_exhaustion_alert:
    enabled: true
    channels:
      - slack: "#ai-coding-alerts"

# ============================================
# 版本控制
# ============================================

constraints_version:
  locked_at: "2026-05-01"           # 锁定日期
  locked_by: "tech-lead"            # 锁定人
  review_cycle: "monthly"           # 每月 review 一次
```

---

## A.3 CI Pipeline 完整实现

### GitHub Actions Workflow

```yaml
# .github/workflows/ai-harness.yml

name: AI Harness Gate

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  # ============================================
  # Gate 1: 文件范围检查
  # ============================================
  file-scope-check:
    name: File Scope Constraint Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Get changed files
        id: changed
        uses: tj-actions/changed-files@v44

      - name: Parse .ai-constraints
        uses: mikefarah/yq@v4

      - name: Validate file scope
        run: |
          CHANGED="${{ steps.changed.outputs.all_changed_files }}"
          MAX_FILES=$(yq '.max_files_per_pr' .ai-constraints 2>/dev/null || echo "5")
          
          FILE_COUNT=$(echo "$CHANGED" | wc -l)
          MAX=${MAX_FILES:-5}
          
          if [ $FILE_COUNT -gt $MAX ]; then
            echo "ERROR: Changed $FILE_COUNT files, max allowed is $MAX"
            exit 1
          fi
          
          echo "File count check passed: $FILE_COUNT files"

      - name: Check blocked paths
        run: |
          CHANGED="${{ steps.changed.outputs.all_changed_files }}"
          
          # 读取黑名单
          BLOCKED=$(yq '.blocked_paths[]' .ai-constraints 2>/dev/null)
          
          for file in $CHANGED; do
            for block in $BLOCKED; do
              if [[ "$file" == $block ]]; then
                echo "ERROR: File $file matches blocked pattern: $block"
                exit 1
              fi
            done
          done
          
          echo "Blocked path check passed"

  # ============================================
  # Gate 2: Diff 大小检查
  # ============================================
  diff-size-check:
    name: Diff Size Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Calculate diff stats
        run: |
          DIFF_LINES=$(git diff --numstat ${{ github.base_ref }}...HEAD | awk '{sum += $1} END {print sum}')
          MAX_LINES=$(yq '.max_diff_lines' .ai-constraints 2>/dev/null || echo "300")
          
          echo "Diff: $DIFF_LINES lines (max: $MAX_LINES)"
          
          if [ "$DIFF_LINES" -gt "$MAX_LINES" ]; then
            echo "ERROR: Diff too large ($DIFF_LINES > $MAX_LINES)"
            exit 1
          fi

  # ============================================
  # Gate 3: 代码质量检查
  # ============================================
  code-quality:
    name: Code Quality Gate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install ruff pytest pytest-cov

      - name: Run ruff check
        run: |
          ruff check src/ || {
            echo "Ruff check failed"
            exit 1
          }

      - name: Check code format
        run: |
          ruff format --check src/ || {
            echo "Code format check failed"
            exit 1
          }

  # ============================================
  # Gate 4: 测试通过检查
  # ============================================
  test-gate:
    name: Test Gate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e . pytest pytest-cov

      - name: Run tests
        run: |
          pytest --tb=short -v || {
            echo "Tests failed"
            exit 1
          }

      - name: Check coverage
        run: |
          MIN_COVERAGE=$(yq '.test_requirements.min_coverage' .ai-constraints 2>/dev/null || echo "70")
          COVERAGE=$(pytest --cov=. --cov-report=term-missing 2>/dev/null | grep "TOTAL" | awk '{print $NF}' | tr -d '%')
          
          echo "Coverage: ${COVERAGE}% (min: ${MIN_COVERAGE}%)"
          
          if [ "${COVERAGE:-0}" -lt "${MIN_COVERAGE:-70}" ]; then
            echo "Coverage too low"
            exit 1
          fi

  # ============================================
  # Gate 5: Commit 格式检查
  # ============================================
  commit-format-check:
    name: Commit Format Check
    runs-on: ubuntu-latest
    if: "github.actor == 'claude-code'"
    steps:
      - uses: actions/checkout@v4

      - name: Check AI commits
        run: |
          COMMITS=$(git log ${{ github.base_ref }}..HEAD --format="%H %s")
          
          for commit in $COMMITS; do
            COMMIT_HASH=$(echo "$commit" | cut -d' ' -f1)
            
            # 检查是否有 Co-authored-by
            if ! git log -1 --format="%b" "$COMMIT_HASH" | grep -q "Co-authored-by"; then
              echo "WARNING: Commit $COMMIT_HASH missing Co-authored-by"
            fi
            
            # 检查是否有 Out-of-scope
            if ! git log -1 --format="%b" "$COMMIT_HASH" | grep -q "Out-of-scope"; then
              echo "WARNING: Commit $COMMIT_HASH missing Out-of-scope declaration"
            fi
          done

  # ============================================
  # Gate 6: 人类 Review 必须
  # ============================================
  human-review-required:
    name: Human Review Required
    runs-on: ubuntu-latest
    needs: [file-scope-check, diff-size-check, code-quality, test-gate]
    steps:
      - name: All automated gates passed
        run: |
          echo "All AI Harness gates passed"
          echo "PR requires human review before merge"
          
          # 设置 PR 标签
          echo "AIHarness=Passed" >> $GITHUB_OUTPUT

---

## A.4 Worktree 管理脚本

```bash
#!/bin/bash
# scripts/worktree-manager.sh — 多 Agent Worktree 完整管理

set -e

WORKTREE_BASE="${WORKTREE_BASE:-/tmp/ai-worktrees}"
PROJECT_NAME=$(basename $(git rev-parse --show-toplevel))

usage() {
    cat << EOF
Usage: $0 <command> [options]

Commands:
    create <feature-name> [issue-id]
        创建新的 AI Agent Worktree
        
    list
        列出所有 Worktree
        
    activate <feature-name>
        激活指定 Worktree 的 Claude Code
        
    cleanup
        清理已合并的 Worktree
        
    sync <feature-name>
        同步主仓库的最新变更到指定 Worktree

Examples:
    $0 create auth-captcha 1234
    $0 list
    $0 activate auth-captcha
    $0 cleanup
EOF
}

# 创建新的 Worktree
cmd_create() {
    local feature_name=$1
    local issue_id=${2:-""}
    
    if [ -z "$feature_name" ]; then
        echo "Error: feature-name required"
        exit 1
    fi
    
    local branch_name="feat/ai/${feature_name}"
    local worktree_path="$WORKTREE_BASE/${PROJECT_NAME}-${feature_name}"
    
    # 检查是否已存在
    if [ -d "$worktree_path" ]; then
        echo "Error: Worktree already exists at $worktree_path"
        exit 1
    fi
    
    # 创建 worktree 和分支
    git worktree add "$worktree_path" -b "$branch_name"
    
    # 创建 CLAUDE.md
    cat > "$worktree_path/CLAUDE.md" << EOF
# AI Agent: $feature_name

## 任务信息
- Issue ID: ${issue_id:-"未关联"}
- 分支: $branch_name
- 创建时间: $(date +%Y-%m-%d)

## 约束
- 遵循 .ai-constraints 配置
- 单 PR 最多 5 个文件
- 必须包含测试
- Commit 必须带 Co-authored-by

## 激活命令
cd $worktree_path && claude
EOF

    # 创建 .claude 目录（如果不存在）
    mkdir -p "$worktree_path/.claude"
    
    echo "✅ Worktree created: $worktree_path"
    echo "   Branch: $branch_name"
    echo "   Issue: ${issue_id:-"未关联"}"
    echo ""
    echo "   To start Claude Code:"
    echo "   cd $worktree_path && claude"
}

# 列出所有 Worktree
cmd_list() {
    echo "Worktrees for $PROJECT_NAME:"
    echo ""
    git worktree list --porcelain | while read -r line; do
        if [[ "$line" == worktree/* ]]; then
            path=$(echo "$line" | cut -d' ' -f2-)
            branch=$(git worktree list --porcelain "$path" 2>/dev/null | grep "^branch" | cut -d' ' -f2- || echo "(main)")
            echo "  📁 $path"
            echo "     Branch: $branch"
            echo ""
        fi
    done
}

# 激活指定 Worktree
cmd_activate() {
    local feature_name=$1
    
    if [ -z "$feature_name" ]; then
        echo "Error: feature-name required"
        exit 1
    fi
    
    local worktree_path="$WORKTREE_BASE/${PROJECT_NAME}-${feature_name}"
    
    if [ ! -d "$worktree_path" ]; then
        echo "Error: Worktree not found: $worktree_path"
        echo "Run '$0 list' to see available worktrees"
        exit 1
    fi
    
    echo "Activating Claude Code in $worktree_path..."
    cd "$worktree_path" && claude
}

# 清理已合并的 Worktree
cmd_cleanup() {
    echo "Checking for merged worktrees..."
    
    git worktree list --porcelain | grep "^worktree" | while read -r line; do
        path=$(echo "$line" | cut -d' ' -f2-)
        branch=$(git worktree list --porcelain "$path" 2>/dev/null | grep "^branch" | cut -d' ' -f2-)
        
        if [ -z "$branch" ]; then
            continue
        fi
        
        # 检查分支是否已合并到 main
        if git branch --merged main 2>/dev/null | grep -q "$branch"; then
            echo "Removing merged worktree: $path (branch: $branch)"
            git worktree remove "$path"
        fi
    done
    
    echo "Cleanup complete"
}

# 同步主仓库变更
cmd_sync() {
    local feature_name=$1
    
    if [ -z "$feature_name" ]; then
        echo "Error: feature-name required"
        exit 1
    fi
    
    local worktree_path="$WORKTREE_BASE/${PROJECT_NAME}-${feature_name}"
    
    if [ ! -d "$worktree_path" ]; then
        echo "Error: Worktree not found: $worktree_path"
        exit 1
    fi
    
    echo "Syncing main to $worktree_path..."
    git -C "$worktree_path" fetch origin main
    git -C "$worktree_path" merge origin/main --no-edit
    
    echo "✅ Synced successfully"
}

# 主逻辑
case "${1:-}" in
    create) cmd_create "$2" "$3" ;;
    list) cmd_list ;;
    activate) cmd_activate "$2" ;;
    cleanup) cmd_cleanup ;;
    sync) cmd_sync "$2" ;;
    *) usage ;;
esac
```

---

## A.5 Human Review 清单模板

```markdown
## AI PR Review 清单

### 基本信息
- [ ] Issue 关联：PR 标题包含 Issue ID
- [ ] 分支命名：符合 feat/ai/{issue-id} 格式
- [ ] Commit 数量：合理（建议 < 5 个 commit）

### 范围检查
- [ ] 改动文件在允许范围内
- [ ] 没有改动 blocked_paths 中的文件
- [ ] 文件数量 < 5 个
- [ ] 没有 Scope Creep（改动涉及多个不相关模块）

### 质量检查
- [ ] 所有测试通过
- [ ] Lint 检查通过
- [ ] Diff 行数 < 300 行
- [ ] 单文件改动 < 100 行

### AI 行为检查
- [ ] Commit 带 Co-authored-by
- [ ] Commit 带 Task-ID
- [ ] Commit 带 Out-of-scope 声明
- [ ] 没有 Gold Plating（没有不必要的抽象/库）
- [ ] 没有 Reuse Failure（复用了现有工具）
- [ ] 没有 Aesthetic Overreach（没有超长函数/深嵌套）

### 规范检查
- [ ] 命名符合项目规范（snake_case/camelCase）
- [ ] 架构符合项目模式（Django CBV/DRF/React Hooks）
- [ ] 错误处理方式一致

### 沟通（如有问题）
- [ ] 在 PR 下评论具体问题
- [ ] 要求 AI 修复后重新提交
```

---

## A.6 快速参考命令

```bash
# ============================================
# Worktree 管理
# ============================================

# 创建 worktree
./scripts/worktree-manager.sh create auth-captcha 1234

# 列出所有 worktree
./scripts/worktree-manager.sh list

# 激活 Claude Code
./scripts/worktree-manager.sh activate auth-captcha

# 清理已合并的 worktree
./scripts/worktree-manager.sh cleanup

# ============================================
# AI Hooks
# ============================================

# 安装 AI hooks
./scripts/install-ai-hooks.sh

# 测试 pre-commit hook
git commit --dry-run

# ============================================
# CI 调试
# ============================================

# 本地模拟 CI 检查
yq '.blocked_paths[]' .ai-constraints
git diff --name-only | wc -l

# ============================================
# Claude Code + Worktree
# ============================================

# 在 worktree 中启动 Claude
cd /tmp/ai-worktrees/my-project-auth-captcha && claude

# 指定 worktree 启动
claude --worktree auth-captcha
```

---

*附录版本 v1.0 | 对应 Chapter 10 Deep Dive*
