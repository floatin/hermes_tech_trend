# /enrich

数据丰富技能，用于多来源数据整合。

## 描述

从多个来源拉取数据，整合到一个结构化画像中。
用于创始人、候选人、实体等的深度丰富。

## 参数

- ENTITY: 要丰富的实体（人/公司）
- SOURCES: 数据源列表
- DEPTH: 丰富深度（shallow/deep/full）

## 步骤

### 1. 拉取所有来源

对每个数据源执行确定性查询：
- 公开记录
- 社交信号
- 历史行为
- 第三方数据

### 2. Diarize每个来源

对每个来源进行编年体摘要：
```
SOURCE: [来源名称]
KEY_DATA: [关键数据点]
TEMPORAL: [时间信息]
```

### 3. 检测"说"vs"做"差异

**Garry Tan的核心洞察**：

```
SAYS: "[实体声称的目标/方向]"
ACTUALLY_BUILDING: "[从行为数据推断的实际方向]"
```

这是任何SQL查询或RAG pipeline做不到的事：
必须模型真正读完、记住矛盾、注意到变化。

### 4. 构建画像

整合所有来源到一个结构化输出：

```json
{
  "entity": "实体名称",
  "claimed_focus": "声称的方向",
  "actual_focus": "实际行为反映的方向",
  "signals": ["信号1", "信号2"],
  "contradictions": ["矛盾1", "矛盾2"],
  "confidence": "高/中/低"
}
```

### 5. 质量检查

- 覆盖度：关键来源是否都覆盖了？
- 一致性：各来源数据是否一致？
- 新增价值：丰富后增加了什么新洞察？

## 示例

```
/enrich ENTITY="Maria Santos" SOURCES="github,linkedin,application" DEPTH=full

输出：
{
  "entity": "Maria Santos",
  "claimed_focus": "Datadog for AI agents",
  "actually_building": "80% commits in billing module - FinOps tool disguised as observability",
  ...
}
```

## 关键洞察

**数据丰富不是数据聚合，是洞察生成**

- 聚合：把数据放在一起
- 丰富：理解数据背后的含义
- Diarization是丰富的核心操作
