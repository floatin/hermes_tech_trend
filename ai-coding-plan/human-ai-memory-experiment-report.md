# Human-AI Collaborative Memory System: Experiment Report

> **结论先行**：这套系统**可行**，但需要人类主动配合记录初始习惯。核心价值不在于自动发现，而在于提供**结构化的习惯存储和验证机制**。

---

## 1. 实验目标

验证"让 AI 和人类都能在协作中学习和适应对方工作习惯"这一设计是否落地可行。

## 2. 原型实现

### 2.1 代码结构

```
habit-tracker/
├── src/habit_tracker/
│   ├── __init__.py          # 模块入口
│   ├── models.py            # 数据模型（Habit, Interaction, Identity）
│   ├── observer.py          # 模式识别引擎
│   ├── storage.py           # JSON 文件存储层
│   ├── validator.py         # 动作验证器（适配习惯）
│   └── cli.py               # 命令行工具
└── setup.py
```

### 2.2 核心功能验证

| 功能 | 状态 | 说明 |
|------|------|------|
| 身份管理 | ✅ | `identity --set-ai claude-code` 正常工作 |
| 习惯添加 | ✅ | `habits --add "内容" --priority 0` 正常工作 |
| 动作验证 | ✅ | `validate "rm -rf"` 成功调用验证器 |
| 模式识别 | ✅ | `observe human "不要删" --action caution` 识别出 `red_line:no_delete_without_confirm` |
| 模式识别 | ✅ | `observe human "直接说" --action explaining` 识别出 `communication_style:direct_communication` |
| P0 过滤 | ✅ | `habits --p0` 正确过滤关键习惯 |
| 导出功能 | ✅ | `export --format json` 正常 |

### 2.3 观察者模式识别能力验证

```
输入: "不要删未确认的文件，必须先确认"
动作: caution
输出: red_line:no_delete_without_confirm ✅

输入: "直接说，不要绕弯"
动作: explaining
输出: communication_style:direct_communication ✅

输入: "这是我的标准做法"
动作: pattern_statement
输出: decision_pattern:standard_practice ✅
```

## 3. 设计验证结果

### 3.1 可行的部分

1. **结构化习惯存储** — Habit 模型设计合理，支持优先级/置信度/证据链
2. **模式识别引擎** — observer.py 的关键词+动作组合识别机制轻量有效
3. **动作验证器** — validator.py 的规则匹配机制可扩展
4. **CLI 设计** — 命令行交互符合习惯追踪的使用场景

### 3.2 需改进的部分

1. **中文支持不完整** — `no_delete_without_confirm` 习惯验证器未注册，需要显式注册英文 pattern
2. **自动发现能力弱** — 目前的 observer 依赖手动 `--action` 标注，真正的自动发现需要 NLP
3. **存储后端单一** — 目前是 JSON 文件，可扩展到 MemPalace/engram
4. **AI 习惯记录缺失** — 还没有实现 hook 机制自动记录 AI 工具调用

### 3.3 关键发现

```
发现 #1: 习惯必须显式命名
------------------------------
用户说"不要删未确认的文件" → 系统识别为 "no_delete_without_confirm"
这个映射需要人类来确认，AI 无法无中生有

发现 #2: 动作 + 内容 = 习惯
------------------------------
单独的内容（如"直接说"）无意义
必须配合动作（explaining/caution/pattern_statement）
才能推断出具体习惯类型

发现 #3: 验证是双向的
------------------------------
validator 不仅验证 AI 行为
也可以验证人类行为（如人类说"随便"时触发警告）
```

## 4. 与设计文档的对应关系

| 设计文档章节 | 对应代码 | 验证结果 |
|-------------|----------|----------|
| §2 人类习惯分类 | models.py HabitType | ✅ 实现 |
| §3 AI 习惯分类 | models.py HabitType (AI_*) | ✅ 实现 |
| §4 记录机制 | observer.py | ✅ 基础验证完成 |
| §5 验证机制 | validator.py | ✅ 基础验证完成 |
| §6 优先级管理 | models.py HabitPriority | ✅ P0/P1/P2 实现 |
| §7 存储层 | storage.py | ✅ JSON 实现 |
| §8 工具钩子 | (未实现) | ❌ 待实现 |
| §9 冲突解决 | validator.py check_conflicts | ✅ 基础实现 |

## 5. 实际集成场景

### 5.1 Hermite Agent 集成

```python
# 在 Hermes Agent 的 tools/ 目录添加 hook
from habit_tracker import HabitTracker

tracker = HabitTracker()

def after_tool_call(tool_name, args, result):
    """工具调用后自动记录"""
    tracker.observe(
        subject="ai",
        observation=f"used {tool_name}",
        action="tool_call",
        context={"tool": tool_name, "args": str(args)}
    )

# 在验证危险操作前
def before_delete(path):
    validation = tracker.validate(f"rm {path}")
    if not validation.ok:
        return f"⚠️ {validation.message}"
    return None
```

### 5.2 GitHub PR 流程集成

```bash
# PR 描述中自动检查
habit-tracker validate "force push to main"

# 输出:
# 🔴 Force push detected on protected branch
#    Habit: no_force_push_to_main (P0, 3x confirmed)
#    Suggestion: Use merge commit instead
```

## 6. 下一步行动

### 立即可做（本周）

1. **完善中文习惯名映射** — 在 validator.py 中添加中文 pattern 注册表
2. **实现 Git hook** — 提供 `pre-commit` / `pre-push` 钩子示例
3. **添加置信度衰减** — 90 天未确认的习惯置信度自动下降

### 短期计划（本月）

4. **集成 MemPalace** — 将存储层替换为 MemPalace 的宫殿结构
5. **实现 AI 习惯自动记录** — 在 LLM 调用前后添加 hook
6. **CLI 完善** — 添加 `habit-tracker learn` 交互式学习模式

### 中期计划（下季度）

7. **多 Agent 支持** — 添加 agent-to-agent 习惯传递
8. **可视化仪表盘** — Web 界面查看习惯图谱
9. **导入/导出** — 支持与 Claude Code/Cline 共享习惯数据

## 7. 结论

### 可行性评估

| 维度 | 评分 | 说明 |
|------|------|------|
| 技术可行性 | 8/10 | 核心机制已验证，主要障碍是 NLP 自动发现 |
| 实用价值 | 7/10 | 对高频协作场景价值大，对低频场景投入产出比低 |
| 集成难度 | 5/10 | 需要在 Agent 工具层加 hook，有一定侵入性 |
| 用户接受度 | 6/10 | 人类习惯记录需要主动配合，依赖组织文化 |

### 最终建议

> **最小可行版本**：用一个 JSON 文件存储习惯 + validator.py 做验证 + observer.py 做基础识别。这 200 行核心代码可以独立于任何外部系统工作，是这套设计的"第一推动力"。

等习惯积累到一定量级（如 20+ 条）后，再考虑迁移到 MemPalace 或 engram 等专业系统。

---

**实验日期**: 2026-05-02
**代码位置**: `~/workspace/habit-tracker/`
**设计文档**: `human-ai-collaborative-memory-design.md`
