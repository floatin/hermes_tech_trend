# Chapter 8 附录：Skills 管理实战指南

> **副标题**：从 0 到 65 个 Skills 的避坑速查 + 决策树

---

## A.1 自检清单：你的 Skills 系统健康吗？

### 基础指标（每月检查）

| 检查项 | 健康值 | 警告信号 | 修复方法 |
|--------|--------|----------|----------|
| Skills 总数 | < 20 | > 30 | 审计 + 合并 |
| L1 总大小 | < 4KB | > 8KB | 精简 description |
| L2 平均长度 | 500-800 tokens | > 1000 tokens | 拆分到 L3 |
| capability 占比 | > 50% | < 30% | 原子化拆分 |
| 五层是否分离 | 是 | 否 | 重构目录结构 |
| 有无版本控制 | 是 | 否 | git 管理 |

### 五层职责检查

```
[ ] agents/ 里的每个 agent 都有清晰的职责边界？
[ ] skills/ 不再包含 rules/ 应该做的事？
[ ] commands/ 的触发条件不与 skills/ 重复？
[ ] rules/ 的约束没有硬编码到 skills/ 里？
[ ] hooks/ 的触发时机和执行逻辑正确？
```

---

## A.2 决策树完整版

### 决策树 1：新建一个 Skill 之前

```
你想新建一个 Skill？
│
├─ 它是"每次任务都要做的"吗？
│   ├─ 是 → 做成 hook，不是 skill
│   └─ 否 → 继续
│
├─ 它需要"始终生效"吗？
│   ├─ 是 → 做成 rule，不是 skill
│   └─ 否 → 继续
│
├─ 用户会"手动触发"吗？（会说 /xxx）
│   ├─ 是 → 做成 command，不是 skill
│   └─ 否 → 继续
│
├─ 它是"单一操作"吗？（git status、格式化代码）
│   ├─ 是 → capability
│   └─ 否 → 继续
│
├─ 它是"多步骤流程"吗？（TDD、代码审查）
│   ├─ 是 → composite
│   └─ 否 → 继续
│
└─ 它是"完整剧本"吗？（>800 tokens）
    ├─ 是 → 拆成 pipeline 或引用外部文件
    └─ 否 → 写成 composite
```

### 决策树 2：Skills 数量已经膨胀

```
Skills 太多，AI 不知道激活哪个？
│
├─ 数量 < 20
│   └─ Tag 驱动筛选，暂可接受
│
├─ 数量 20-50
│   │
│   ├─ description 相互重叠？
│   │   ├─ 是 → 合并相似的 skills
│   │   └─ 否 → 继续
│   │
│   └─ 激活时经常冲突？
│       ├─ 是 → 五层分离（见重构步骤）
│       └─ 否 → 继续
│
└─ 数量 > 50
    │
    ├─ 第一步：审计
    │   └─ 找出长时间未用的、重复的、模糊的
    │
    ├─ 第二步：分类
    │   └─ 按 capability/composite/command/rule/hook 分类
    │
    └─ 第三步：重组
        └─ 五层目录结构
```

### 决策树 3：L2 超过 800 tokens

```
单个 SKILL.md 超过 800 tokens？
│
├─ 包含边缘场景处理？
│   └─ → 移到 references/edge-cases.md
│
├─ 包含大量参考代码？
│   └─ → 移到 examples/ 目录
│
├─ 包含长文档链接？
│   └─ → 只保留摘要，链接放到 L3
│
└─ 核心流程本身过长？
    └─ → 拆成 composite pipeline
```

### 决策树 4：激活冲突

```
多个 Skills 同时被激活？
│
├─ description 写得太通用？
│   └─ → 精准化触发条件，缩小范围
│
├─ capability 和 composite 混在一个文件？
│   └─ → 拆成两个独立文件
│
├─ 同一个触发条件写了两个 skill？
│   └─ → 合并或明确区分触发场景
│
└─ rules/ 应该做的事写在 skill 里？
    └─ → 迁移到 rules/
```

---

## A.3 重构操作手册

### 重构步骤 1：创建五层目录

```bash
cd ~/.claude

# 创建目录结构
mkdir -p agents/
mkdir -p skills/capabilities/
mkdir -p skills/composites/
mkdir -p skills/playbooks/
mkdir -p commands/
mkdir -p rules/
mkdir -p hooks/
mkdir -p references/    # L3 资源目录
mkdir -p examples/     # L3 示例目录

# 创建 .gitkeep 便于 git 追踪
touch agents/.gitkeep
touch skills/capabilities/.gitkeep
touch skills/composites/.gitkeep
touch skills/playbooks/.gitkeep
touch commands/.gitkeep
touch rules/.gitkeep
touch hooks/.gitkeep
touch references/.gitkeep
touch examples/.gitkeep
```

### 重构步骤 2：迁移文件

```python
#!/usr/bin/env python3
""" migrate_skills.py — 将扁平 skills/ 迁移到五层结构 """

import os
import re
import shutil
from pathlib import Path

SKILLS_DIR = Path("~/.claude/skills").expanduser()
TARGETS = {
    "capability": SKILLS_DIR / "capabilities",
    "composite": SKILLS_DIR / "composites",
    "playbook": SKILLS_DIR / "playbooks",
}

def detect_skill_type(content: str) -> str:
    """根据内容判断 skill 类型"""
    lines = content.split("\n")
    
    # capability：单一操作，主要用工具调用
    if any(kw in content for kw in ["git ", "npm ", "pip ", "执行命令"]):
        # 检查是否有多步骤
        step_count = len([l for l in lines if l.strip().startswith(("1.", "2.", "3."))])
        if step_count <= 1:
            return "capability"
    
    # playbook：超过 800 tokens
    if len(content) > 4000:  # 约 800 tokens
        return "playbook"
    
    # 默认 composite
    return "composite"

def migrate():
    # 扫描原始 skills
    for skill_file in SKILLS_DIR.glob("*.md"):
        if skill_file.stem in ["README", "SKILL"]:  # 跳过索引
            continue
        
        content = skill_file.read_text()
        skill_type = detect_skill_type(content)
        
        target_dir = TARGETS[skill_type]
        target_file = target_dir / skill_file.name
        
        shutil.move(str(skill_file), str(target_file))
        print(f"moved: {skill_file.name} -> {skill_type}/")

if __name__ == "__main__":
    migrate()
```

### 重构步骤 3：建立 agents/ 和 skills/ 的映射

```markdown
# agents/backend-developer.md

---
name: backend-developer
description: 后端开发专家。处理 API 设计、数据库、认证授权等任务。
激活条件：用户提到"后端"、"API"、"数据库"、"认证"、"JWT"。
---

# 加载的 Skills

## 必需
- skills/capabilities/git-workflow.md
- skills/composites/api-design.md

## 按需（根据任务判断）
- skills/capabilities/postgres-query.md  （数据库相关）
- skills/composites/auth-implementation.md （认证相关）
- skills/rules/security.md                （安全约束，始终生效）
```

### 重构步骤 4：版本锁定

```bash
cd ~/.claude
git init
git add agents/ skills/ commands/ rules/ hooks/
git commit -m "feat: lock skills architecture $(date +%Y-%m-%d)"

# 每月 review 前创建 tag
git tag -a 2026-05-review -m "May monthly review"
```

---

## A.4 避坑速查表

| 坑 | 特征 | 后果 | 修复 |
|----|------|------|------|
| **capability 和 composite 混用** | 一个文件里既有"执行命令"又有"步骤1/2/3" | AI 不知道该走工具调用还是 LLM 推理 | 拆成两个文件 |
| **rules/ 硬编码到 skills/** | 每个 skill 都有"【注意】不要..." | 约束不统一，难以修改 | 迁移到 rules/ |
| **description 过于通用** | "什么场景都能用" | 激活判断失效，多个 skill 同时激活 | 精准化触发条件 |
| **L2 超过 800 tokens** | 一个 skill 写了所有边缘场景 | 推理成本高，执行慢 | 拆分到 L3 |
| **L1 总计超过 4KB** | 所有 skill 的 description 加起来太长 | AI 激活判断变慢 | 精简 + 合并 |
| **commands/ 和 skills/ 混淆** | 该手动的写成了自动，该自动的写成了手动 | 用户体验不一致 | 按触发类型分开 |
| **追求通用 skill** | 一个 skill 覆盖 N 个相关场景 | description 越来越长，激活越来越模糊 | 拆成多个精准的 skill |
| **没有版本控制** | skills/ 没有 git 管理 | 更新后出问题无法回滚 | git 锁定版本 |
| **忽视定期 review** | 从来不检查 skills 列表 | 过时的 skill 堆积，干扰激活 | 每月一次 review |
| **hooks/ 过度使用** | 到处写 before/after 钩子 | 自动化泛滥，难以调试 | 只保留关键钩子 |

---

## A.5 快速参考命令

### 统计命令

```bash
# Skills 总数
find ~/.claude/skills/ -name "*.md" | wc -l

# 各层数量
find ~/.claude/skills/capabilities/ -name "*.md" | wc -l
find ~/.claude/skills/composites/ -name "*.md" | wc -l
find ~/.claude/commands/ -name "*.md" | wc -l
find ~/.claude/rules/ -name "*.md" | wc -l
find ~/.claude/hooks/ -name "*.md" | wc -l

# L1 总大小
find ~/.claude/skills/ -name "SKILL.md" \
  -exec sed -n '1,10p' {} \; \
  | grep "^description:" -A 3 \
  | wc -c

# 超过 800 tokens 的 L2
for f in $(find ~/.claude/skills/ -name "SKILL.md"); do
  size=$(wc -c < "$f")
  if [ $size -gt 4000 ]; then
    echo "$f: $size bytes"
  fi
done
```

### 管理命令

```bash
# 锁定版本
cd ~/.claude && git add -A && git commit -m "lock: $(date +%Y-%m-%d)"

# 每月 review 检查清单
# 1. 统计未使用的 skills
# 2. 检查重复功能
# 3. 验证激活逻辑
# 4. 更新文档

# 导出 skills 索引（用于团队共享）
find ~/.claude/skills/ -name "*.md" \
  -exec basename {} .md \; \
  | sort > skills-index.txt
```

---

## A.6 Anthropic 官方建议速记

```
┌────────────────────────────────────────────────────┐
│                 Skills 健康速记                     │
├────────────────────────────────────────────────────┤
│  数量：< 20 个（建议），> 30 个（警告）             │
│  L1：所有 description 总计 < 4KB                   │
│  L2：每个 skill 500-800 tokens                     │
│  L3：按需加载，不一次性加载                         │
│  capability 占比 > 50%                             │
│  每月 review 一次                                   │
│  用 git 管理版本                                    │
└────────────────────────────────────────────────────┘
```

---

*附录版本 v1.0 | 对应 Chapter 8 Deep Dive*
