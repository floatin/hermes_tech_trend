# Chapter 8（草稿）：Skills 膨胀管理

> **副标题**：当 65 个 Skills 塞满你的 AI，如何保持清醒？

## 8.0 开篇：Skills 也会膨胀

一个讽刺的现象：

我们嫌弃 macOS 系统盘太满，学会了定期清理。
我们嫌弃冰箱里食物过期，学会了及时处理。
我们嫌弃代码复杂度膨胀，学会了重构和模块化。

**但我们却往 AI Agent 里塞了 65 个 Skills，然后问：为什么它变慢了？**

这就是 Skills 膨胀问题——AI Coding 领域的"技术债"。

本章告诉你：
1. Skills 膨胀的三大症状
2. 膨胀的根源：L1/L2/L3 三层加载机制
3. 一线团队的管理方案
4. 工具链：如何让 Skills"减重"

---

## 8.1 Skills 膨胀的三大症状

### 8.1.1 症状一：选择困难症

**表现**：用户不知道该用哪个 Skill，AI 不知道该激活哪个 Skill。

```
用户：帮我优化这段 SQL
AI：[激活 skills/sqlite] [激活 skills/postgres] [激活 skills/database-optimization]
AI：我应该用哪个？
```

### 8.1.2 症状二：上下文干扰

**表现**：不相关的 Skills 描述污染了 AI 的上下文窗口。

```
[Skills 加载]
- skill-1: "用于处理用户认证..."
- skill-2: "用于发送邮件..."
- skill-3: "用于处理支付..."
- skill-4: "用于日志记录..."
...
(total: 65 skills, 280KB context)
```

AI 要在 280KB 的 Skills 描述中找到"当前需要的那个"——这本身就是浪费。

### 8.1.3 症状三：维护噩梦

**表现**：Skills 之间有依赖、更新冲突、版本不兼容。

```
skill-A 要求 node>=18
skill-B 要求 node<17
skill-C 要求 exactly node=16
→ 依赖地狱
```

---

## 8.2 膨胀的根源：三层加载机制

### 8.2.1 三层结构

```
┌─────────────────────────────────────────────┐
│ L1 触发层（始终加载）                       │
│  name + description                         │
│  1-2 句话，总计 < 4KB                      │
│  → 决定是否激活该 Skill                    │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│ L2 执行层（按需加载）                       │
│  SKILL.md 核心指令                          │
│  500-800 tokens                            │
│  → 包含 80% 常见场景处理逻辑              │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│ L3 资源层（文件引用）                       │
│  高级配置、模板、示例代码                    │
│  → 按需加载，避免主流程臃肿                │
└─────────────────────────────────────────────┘
```

### 8.2.2 膨胀的根本原因

| 层次 | 设计目的 | 膨胀后 |
|------|---------|--------|
| L1 | 快速判断是否激活 | 描述越来越长、越来越模糊 |
| L2 | 核心执行逻辑 | 包含过多边缘场景 |
| L3 | 扩展资源 | 堆积过时模板和示例 |

### 8.2.3 "好心"导致的膨胀

AI 添加 Skill 时的心理：
- "这个场景可能用得上" → 堆积
- "用户可能会问这个" → 覆盖
- "反正 context 够大" → 放任

**结果**：Skills 从 10 个变成 65 个，AI 反而变慢了。

---

## 8.3 Skills 膨胀管理方案

### 8.3.1 方案一：角色分组（Role-Based）

**原理**：按工作角色组织 Skills，AI 只加载当前任务相关的组。

```
skills/
├── coder/
│   ├── debug.md        # 调试技能
│   ├── test.md        # 测试技能
│   └── refactor.md    # 重构技能
├── reviewer/
│   ├── code-review.md
│   └── security-scan.md
└── devops/
    ├── deploy.md
    └── monitor.md
```

**激活方式**：
```
用户：帮我审查这段代码
AI：加载 reviewer/ 组
→ 只激活 code-review.md, security-scan.md
→ 忽略其他组
```

### 8.3.2 方案二：技能标签（Tag-Based）

**原理**：给每个 Skill 打标签，按需筛选。

```yaml
# skill metadata
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
```

**按需加载**：
```python
def load_skills_for_task(task: str) -> list[Skill]:
    tags = extract_tags(task)  # 从用户输入提取标签
    return [s for s in all_skills if matches_tags(s, tags)]
```

### 8.3.3 方案三：技能编排（Skill Composition）

**原理**：将复杂任务拆分为 Skills 流水线。

```
用户：部署到 K8s 并配置监控

Skill Pipeline:
1. docker-build (构建镜像)
   ↓
2. k8s-deploy (部署)
   ↓
3. monitoring-setup (配置监控)
```

**代表项目**：
- `everything-claude-code`：提供 65+ 可组合 Skills
- `obra/superpowers`：TDD、YAGNI、DRY 等工程实践的 Skill 封装

---

## 8.4 一线团队的管理实践

### 8.4.1 Anthropic 官方建议

```
1. Skill 数量控制：建议 < 20 个
2. L1 描述简洁：< 4KB 总计
3. L2 指令精简：500-800 tokens
4. L3 资源按需：按需加载，不一次性加载
```

### 8.4.2 百度 CodeOps 经验

```
Skills 管理三原则：
1. 最小激活：只加载当前任务必需的 Skills
2. 版本锁定：固定 Skills 版本，避免自动更新
3. 定期清理：每月 review 一次，删除过时 Skills
```

### 8.4.3 ECC（everything-claude-code）方案

```bash
# 目录结构
skills/
├── agents/          # 13+ 子智能体
│   ├── code-reviewer.md
│   ├── test-engineer.md
│   └── devops.md
├── skills/         # 65+ 实战技能
│   ├── debugging/
│   ├── testing/
│   └── deployment/
├── hooks/           # 钩子实现
│   └── memory-hint.md
└── rules/          # 规则集
    └── naming-convention.md
```

**特点**：
- 按角色分组，减少上下文干扰
- 规则集统一管理，避免 Skill 之间的冲突
- Hooks 实现跨会话记忆，减少重复加载

---

## 8.5 Skills 减重工具链

### 8.5.1 Skills 分析工具

```bash
# 分析 Skills 膨胀情况
npx skills-analyzer

# 输出示例
Skills Count: 65
Total L1 Size: 4.2KB
Total L2 Size: 48KB
Total L3 Size: 2.1MB

Recommendations:
- [HIGH] skill-X has 3 unused triggers
- [MEDIUM] skill-Y L2 exceeds 800 tokens
- [LOW] skill-Z L3 has duplicate templates
```

### 8.5.2 Skills 优化工具

```bash
# 自动优化 Skills
npx skills-optimizer --fix

# 执行操作：
# - 合并重复的触发词
# - 精简过长的 L2 描述
# - 移除未使用的 L3 资源
```

### 8.5.3 Skills 版本管理

```bash
# 锁定 Skills 版本
skills lock

# 升级 Skills
skills upgrade

# 回滚 Skills
skills rollback --to=2026-04-01
```

---

## 8.6 本章小结

1. **Skills 膨胀的三大症状**：选择困难、上下文干扰、维护噩梦
2. **膨胀根源**：L1/L2/L3 三层加载机制被滥用
3. **管理方案**：角色分组、标签筛选、技能编排
4. **最佳实践**：Anthropic 建议 < 20 Skills，定期清理
5. **工具链**：skills-analyzer → skills-optimizer → skills lock

---

## 8.7 延伸阅读

- [everything-claude-code](https://github.com/affaan-m/everything-claude-code)（63k+ stars）
- [obra/superpowers](https://github.com/obra/superpowers)（34k+ stars）
- [Anthropic Skills 文档](https://docs.anthropic.com/en/docs/claude-code/skills)
- [Skills 膨胀问题讨论](https://github.com/anthropics/claude-code/discussions)
