# Human-AI Collaborative Memory System Design

## Context Tracker: 习惯追踪系统设计文档

> 让 AI 和人类都能在协作中学习和适应对方的工作习惯

---

## 1. 问题定义

### 1.1 现状

```
当前人机协同的问题：

AI 不了解人类：
  - 不知道人的沟通风格（直接/间接）
  - 不知道人的技术偏好（保守/激进）
  - 不知道人的决策模式（快速/谨慎）
  - 不知道人的红线（不删文件/需要确认）

人类不了解 AI：
  - 不知道 AI 的决策路径
  - 不知道 AI 的失败模式
  - 不知道 AI 的能力边界
  - 不知道 AI 的工作习惯

结果：
  - 重复沟通成本高
  - 预期错位导致返工
  - 协作摩擦
```

### 1.2 目标

```
设计一个人类与AI协作的习惯追踪系统，实现：

1. AI 理解人类：
   - 沟通风格
   - 技术偏好
   - 决策模式
   - 工作习惯

2. 人类理解 AI：
   - AI 的工作模式
   - AI 的能力边界
   - AI 的常见失误

3. 双向适应：
   - AI 主动适应人类
   - 人类学会与 AI 高效协作
```

---

## 2. 核心设计

### 2.1 双主体记忆架构

```
┌─────────────────────────────────────────────────────────────┐
│              Human-AI Collaborative Memory                   │
├─────────────────────┬───────────────────────────────────────┤
│   Human Memory      │          AI Memory                     │
│  (About Human)      │       (About Human's AI)               │
├─────────────────────┼───────────────────────────────────────┤
│ • Identity          │ • AI Behavior Traces                   │
│ • Communication     │ • Decision Patterns                   │
│ • Preferences       │ • Failure Modes                        │
│ • Decision Style    │ • Capability Boundaries                │
│ • Technical Stack   │ • Working Habits                       │
│ • Red Lines         │ • Improvement Log                     │
└─────────────────────┴───────────────────────────────────────┘
```

### 2.2 人类侧记忆（Human Memory）

```markdown
## Wing: @human

### Room: identity
- name: [用户姓名]
- role: [职务]
- experience_level: [AI协作经验: 新手/中级/高级]
- timezone: [时区]
- working_hours: [工作时间]

### Room: communication
- style: [direct/indirect]
- feedback_delivery: [immediate/filtered]
- question_frequency: [high/medium/low]
- preferred_response_length: [brief/detailed]

### Room: preferences
- technical_conservatism: [conservative/moderate/aggressive]
- preferred_languages: [list]
- testing_requirements: [strict/moderate/minimal]
- documentation_level: [minimal/standard/comprehensive]

### Room: decision_patterns
- approval_needed_for: [deletions/refactors/new_deps]
- options_before_decision: [数字]
- speed_vs_quality: [balanced/speed/quality]
- risk_tolerance: [low/medium/high]

### Room: red_lines
- NO_DELETE_UNCONFIRMED: true
- NO_NEW_DEP_WITHOUT_APPROVAL: ["lodash", "moment"]
- NO_STAGING_PUSH_TO_MAIN: true
```

### 2.3 AI 侧记忆（AI Memory）

```markdown
## Wing: @ai-[ai_name]

### Room: behavior_traces
- decision_path: [决策路径记录]
- tool_usage_patterns: [工具使用模式]
- context_building: [上下文构建方式]
- error_recovery: [错误恢复策略]

### Room: failure_modes
- common_errors: [常见失误列表]
- correction_history: [被纠正的历史]
- context_blindness: [已知的上下文盲点]

### Room: capability_boundaries
- reliable_tasks: [可靠任务]
- unreliable_tasks: [不可靠任务]
- needs_human_help: [需要人类帮助的场景]

### Room: improvement_log
- [日期] 学会了: [新习惯]
- [日期] 被纠正: [错误行为]
- [日期] 改进了: [改进项]
```

---

## 3. 核心机制

### 3.1 习惯观察者（Habit Observer）

```python
class HabitObserver:
    """
    观察人类和 AI 的行为模式，提取习惯
    """
    
    def observe(self, interaction: Interaction) -> Observation:
        """
        观察一次交互，提取可记录的观察
        """
        observations = []
        
        # 观察人类行为
        human_observations = self._observe_human(interaction)
        observations.extend(human_observations)
        
        # 观察 AI 行为
        ai_observations = self._observe_ai(interaction)
        observations.extend(ai_observations)
        
        return observations
    
    def _observe_human(self, interaction) -> List[Observation]:
        # 检测沟通风格
        # 检测决策模式
        # 检测技术偏好
        # 记录反馈模式
        pass
    
    def _observe_ai(self, interaction) -> List[Observation]:
        # 检测工作模式
        # 记录失败模式
        # 跟踪改进进度
        pass
```

### 3.2 习惯验证器（Habit Validator）

```python
class HabitValidator:
    """
    当 AI 假设知道人类习惯时，主动验证
    """
    
    def validate_before_action(self, 
                              ai_action: AIAction,
                              human_context: HumanContext) -> ValidationResult:
        """
        在执行可能触犯人类习惯的动作前验证
        """
        relevant_habits = self._find_relevant_habits(ai_action, human_context)
        
        for habit in relevant_habits:
            if not self._check_compliance(ai_action, habit):
                return ValidationResult(
                    conflict=True,
                    habit=habit,
                    suggestion=self._suggest_alternative(ai_action, habit)
                )
        
        return ValidationResult(conflict=False)
    
    def _check_compliance(self, action, habit) -> bool:
        """
        检查动作是否违反习惯
        """
        pass
```

### 3.3 双向反馈环（Feedback Loop）

```
┌─────────────────────────────────────────────────────────────────┐
│                      双向反馈环                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐                                               │
│   │ 人类观察AI   │ ← 人类标记 AI 的好/差行为                       │
│   └──────┬───────┘                                               │
│          ↓                                                       │
│   ┌──────────────┐                                               │
│   │ 记录习惯     │ ← 存储到 AI Memory                             │
│   └──────┬───────┘                                               │
│          ↓                                                       │
│   ┌──────────────┐                                               │
│   │ AI学习改进   │ ← 下次行为参考已有习惯                         │
│   └──────┬───────┘                                               │
│          ↓                                                       │
│   ┌──────────────┐                                               │
│   │ AI主动确认   │ ← 遇到不确定的习惯时，主动向人类确认            │
│   └──────┬───────┘                                               │
│          ↓                                                       │
│   ┌──────────────┐                                               │
│   │ 人类验证反馈 │ → 人类纠正/确认 AI 的理解                       │
│   └──────────────┘                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. 关键设计决策

### 4.1 谁主导记录？

| 维度 | 主导方 | 原因 |
|------|-------|------|
| AI 的习惯 | 人类（外部） | AI 没有自我反思能力 |
| 人类的习惯 | AI（主动观察） | 人类不会主动记录 |
| 习惯冲突 | 人类裁决 | 人类是最终决策者 |
| 习惯更新 | 人类确认 | 防止 AI 自我合理化 |

### 4.2 习惯的优先级

```
P0 - 红线（必须遵守）
  - 删除文件前必须确认
  - 关键决策前必须汇报
  - 不确定的必须问

P1 - 重要偏好（尽量遵守）
  - 沟通风格（直接/间接）
  - 文档详细程度
  - 测试要求

P2 - 一般习惯（默认遵守）
  - 工作时间偏好
  - 工具选择偏好
  - 决策速度偏好
```

### 4.3 习惯的可信度

```python
@dataclass
class Habit:
    name: str
    description: str
    evidence_count: int      # 被观察到的次数
    confirmation_count: int  # 被人类确认的次数
    last_observed: datetime
    last_confirmed: datetime
    source: str              # 'observation' / 'human_direct' / 'ai_inference'
    
    @property
    def confidence(self) -> float:
        """计算习惯的可信度"""
        base = min(self.evidence_count * 0.2, 0.6)
        confirmation_bonus = min(self.confirmation_count * 0.2, 0.3)
        recency_bonus = 0.1 if self.last_confirmed > datetime.now() - timedelta(days=7) else 0
        return min(base + confirmation_bonus + recency_bonus, 0.95)
    
    @property
    def priority(self) -> int:
        """推断优先级"""
        if self.confirmation_count >= 3:
            return 0  # P0
        elif self.confirmation_count >= 1:
            return 1  # P1
        else:
            return 2  # P2
```

---

## 5. 实施计划

### Phase 1: MVP（2周）
```
目标：实现基础的习惯观察和记录

组件：
1. HabitObserver - 观察人类和AI的行为
2. MemoryStorage - 基于 MemPalace 存储
3. BasicCLI - 命令行接口

交付：
- 人类习惯的被动观察
- AI行为的简单记录
- 习惯查询命令
```

### Phase 2: 验证（2周）
```
目标：让AI能够主动验证和适应

组件：
1. HabitValidator - 验证AI行为是否触犯习惯
2. ConfirmationFlow - 习惯确认流程
3. ContextInjector - 上下文注入

交付：
- AI 在执行前检查习惯
- 不确定时主动向人类确认
- 确认后更新习惯可信度
```

### Phase 3: 学习（持续）
```
目标：AI 能够从反馈中学习

组件：
1. LearningEngine - 从反馈中提取规律
2. ConflictResolver - 习惯冲突解决
3. PreferencePredictor - 预测人类偏好

交付：
- AI 主动发现新习惯
- 习惯冲突时智能裁决
- 预测人类偏好并提前适应
```

---

## 6. 开放问题

1. **习惯谁来定义**：AI 归纳的习惯是否算"真正的习惯"？
2. **习惯冲突**：AI 习惯 vs 人类习惯，以谁为准？
3. **隐私问题**：习惯记录是否会被滥用？
4. **过度适应**：AI 过度迎合人类是否会导致能力退化？
5. **谁来审计**：如何确保习惯记录是准确的？

---

## 7. 参考实现

- MemPalace：宫殿结构的记忆存储
- Hindsight：三层记忆架构（World Facts / Experiences / Mental Models）
- Honcho：实体为中心的时序记忆

---

## 8. 附录：示例习惯记录

```markdown
# 示例：完整的人类习惯记录

## Wing: @human-alice

### Room: identity
- name: Alice
- role: Senior Backend Engineer
- ai_collab_age: 2_years
- experience_level: advanced

### Room: communication
- style: direct
- feedback: immediate_and_specific
- questions: only_when_blocked
- response_length: brief_with_essential_context

### Room: preferences
- tech_conservatism: moderate
  - will_adopt_new_deps_if_clear_benefit
  - prefers_proven_over_new
- testing: strict
  - requires_unit_tests
  - requires_integration_tests_for_apis
- docs: minimal
  - only_for_nonobvious_logic
  - inline_preferred

### Room: decision_patterns
- approval_for:
  - delete_operations
  - schema_changes
  - new_external_apis
- options_needed: 2
  - always_present_alternatives
- speed: quality_first
  - "take your time to do it right"

### Room: red_lines
- NO_UNREVIEWED_DELETE: true
- NO_STAGING_MAIN: true
- NO_BLIND_PUSH: true

### Room: ai_memory
- ai_name: claude-code
- trust_level: high
- good_patterns:
  - explains_before_changing
  - asks_clarifying_questions
  - provides_test_coverage
- improvement_areas:
  - sometimes_assumes_too_much
  - needs_reminder_about_test_requirements
```
