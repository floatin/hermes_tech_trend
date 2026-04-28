# /match

匹配技能，用于在大量候选中找出最优匹配。
Garry Tan YC实战案例的核心技能。

## 描述

在大量候选中根据多个维度进行匹配和推荐。
适用于：创业者匹配、团队组建、资源分配等场景。

## 参数

- CANDIDATES: 候选列表（文件路径或ID列表）
- CRITERIA: 匹配标准
- STRATEGY: 匹配策略（affinity/serendipity/nearest）
- LIMIT: 返回数量

## 策略类型

### 1. Affinity（领域亲和）

按领域分组，同类相聚：
```
每组30人
按 sector 聚类
确保同组内有足够多样性
```

### 2. Serendipity（意外发现）

跨领域偶遇，创造意外连接：
```
每组8人
跨 sector 配对
主题由LLM发明
```

### 3. Nearest（最近邻）

实时推荐，基于当前状态：
```
200ms响应
1:1配对
排除已认识的人
```

## 步骤

### 1. 解析候选

加载候选数据：
- 读取候选文件
- 解析结构化信息
- 识别关键属性

### 2. Embedding（可选）

对候选进行向量嵌入：
- 用于相似度计算
- 但不是唯一依据

### 3. Apply策略

根据策略类型应用不同逻辑：

**Affinity**:
- 按领域分组
- 嵌入 + 确定性assign

**Serendipity**:
- 跨领域配对
- LLM发明主题
- 人工干预

**Nearest**:
- 实时最近邻
- 200ms内响应
- 实时更新

### 4. 人类判断

**Garry Tan核心洞察**：

> "No embedding captures the Kim reclassification. No algorithm can do it. The model has to read the entire profile."

```
某些判断必须由LLM做出：
- "这两个人看似竞争，实际互补"
- "Kim申请的是DevTools，实际做的是Compliance"
```

这是纯算法做不到的事。

### 5. 输出结果

结构化匹配结果：
```
Group 1:
  - Candidate A (理由)
  - Candidate B (理由)
  主题: [LLM发明的主题]

Group 2:
  ...
```

## 示例

```
/match CANDIDATES="./founders_2026.csv" STRATEGY=serendipity LIMIT=20

Same skill, different strategy:
- /match-breakout → affinity
- /match-lunch → serendipity
- /match-live → nearest
```

## 关键洞察

**匹配不是查找，是判断**

- 查找：找到完全匹配的
- 匹配：找到最优组合的

最优组合需要理解每个候选的：
- 表面需求
- 深层动机
- 潜在价值

这需要LLM的判断力，不是纯算法。
