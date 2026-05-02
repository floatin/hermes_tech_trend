# Chapter 9（草稿）：大型代码仓库高效访问——代码 RAG 之道

> **副标题**：当代码仓库超过 10 万行，"全量丢进上下文"就成了笑话。

## 9.0 开篇：代码 RAG 的挑战

一个 50 人团队维护的微服务代码仓库：
- **代码行数**：180 万行
- **文件数量**：3,200 个
- **服务依赖**：47 个内部服务 + 120 个外部 API
- **历史跨度**：8 年，12,000+ 次提交

传统的 Embedding + Vector Search 方案面临三个灵魂拷问：

1. **上下文窗口够用吗？** 180 万行代码，即使压缩也要 500 万 Token，而当前最大上下文窗口是 200k。
2. **噪声你能忍吗？** 测试代码、配置文件、生成代码——它们和业务逻辑一起被检索出来，LLM 被噪声淹没。
3. **跨文件依赖你能理解吗？** 用户问"这个 API 被哪些服务调用"——向量检索只管语义相似，不管调用链。

**答案：需要更聪明的代码 RAG 方案。**

本章告诉你：
1. 为什么传统 Embedding 方案在代码场景失效
2. 代码 RAG 的四大流派
3. 实战：claude-context + GitNexus 组合拳

---

## 9.1 传统 Embedding 方案为何失效

### 9.1.1 问题一：上下文窗口不够

```
180万行代码
├── src/ (80万行)
├── tests/ (60万行)
├── docs/ (20万行)
├── config/ (10万行)
└── generated/ (10万行)

即使 200k 上下文窗口，也只能装 0.01%
```

### 9.1.2 问题二：噪声过多

向量检索返回 Top-K 最相似的代码块——但"相似"不等于"相关"。

```python
# 用户查询："如何实现用户认证"
# 向量检索结果：

# 结果 1（相关）：auth/jwt.py - JWT 认证逻辑 ✓
# 结果 2（相似但无关）：tests/test_jwt.py - JWT 测试代码 ✗
# 结果 3（相似但无关）：docs/auth_design.md - 认证设计文档 ✗
# 结果 4（相似但噪声）：node_modules/jwt-decode/index.js - 第三方库 ✗
```

### 9.1.3 问题三：跨文件依赖丢失

```python
# 向量检索：语义相似度最高的代码块
# 但无法回答："这个函数被谁调用？调用链是什么？"

def parse_user_token(token):
    """解析用户 token"""
    ...

# LLM 看到的是孤立的函数
# 看不懂：parse_user_token → validate_permission → check_subscription → require_auth
```

---

## 9.2 代码 RAG 四大流派

### 9.2.1 流派一：向量检索（Vector Search）

**代表**：claude-context

**原理**：
```
代码 → Code-Aware Chunking → Embedding → Vector Database
查询 → Embedding → Vector Search → Top-K Chunks
```

**优点**：
- 语义理解能力强
- 实现简单
- 适合"这段代码做什么"的查询

**缺点**：
- 不捕获依赖关系
- 跨文件推理弱

### 9.2.2 流派二：知识图谱（Knowledge Graph）

**代表**：GitNexus

**原理**：
```
代码 → Tree-sitter 解析 → 实体识别 → 关系抽取 → 知识图谱
查询 → Cypher 查询 → 子图 → 注入上下文
```

**优点**：
- 捕获调用链、依赖关系
- 支持"Who calls this"、"What breaks if I change this"
- 跨文件推理能力强

**缺点**：
- 初始化需要完整索引
- 图谱维护成本高

### 9.2.3 流派三：混合检索（Hybrid Search）

**代表**：GraphRAG（微软）

**原理**：
```
代码 → 知识图谱 + 向量索引
查询 → 知识图谱检索 + 向量检索 → 结果融合
```

**优点**：
- 结合两者优点
- 支持局部查询 + 全局查询

**缺点**：
- 实现复杂
- 资源消耗大

### 9.2.4 流派四：代码感知检索（Code-Aware Retrieval）

**代表**：jina-clip-v2

**原理**：
```
代码 → Code-Specific Embedding Model（理解代码结构）
      → 保留函数边界、类结构、注释语义
查询 → 自然语言 → 语义匹配
```

**优点**：
- 代码结构感知
- 适合"如何实现 XXX 功能"

**缺点**：
- 模型依赖
- 对中文注释支持有限

---

## 9.3 实战：claude-context + GitNexus 组合

### 9.3.1 为什么需要组合

| 能力 | claude-context | GitNexus |
|------|----------------|----------|
| **语义搜索** | ✅ 强 | ❌ 弱 |
| **调用链分析** | ❌ 无 | ✅ 强 |
| **变更影响分析** | ❌ 无 | ✅ 强 |
| **代码结构理解** | ✅ 中 | ✅ 强 |

**组合效果**：
- 搜索引擎（claude-context）+ 地图导航（GitNexus）
- AI 既有语义理解能力，又有结构推理能力

### 9.3.2 安装配置

```bash
# 1. 安装 claude-context
npm install -g claude-context

# 2. 安装 GitNexus
npm install -g gitnexus

# 3. 配置到 Claude Code
claude mcp add claude-context -e OPENAI_API_KEY=***
gitnexus setup

# 4. 索引代码仓库
cd /path/to/repo
gitnexus analyze
```

### 9.3.3 使用示例

**场景一：语义搜索（claude-context）**

```
用户：用户认证逻辑在哪里？
AI → claude-context.search("用户认证")
→ 返回相关代码块和文件位置
```

**场景二：调用链分析（GitNexus）**

```
用户：这个函数被谁调用？
AI → gitnexus context parse_user_token
→ 返回调用者列表和调用位置
```

**场景三：变更影响分析（GitNexus）**

```
用户：修改这个文件会影响哪些地方？
AI → gitnexus impact src/auth/jwt.py
→ 返回变更影响范围和依赖路径
```

### 9.3.4 统一入口：code-context CLI

为了简化使用，我们封装了统一的 CLI：

```bash
# 语义搜索
code-context search "用户认证"

# 调用链分析
code-context who-calls parse_user_token

# 变更影响
code-context impact src/auth/jwt.py

# 依赖图
code-context graph --focus src/
```

---

## 9.4 代码 RAG 最佳实践

### 9.4.1 索引优化

```bash
# 1. 排除无关目录
.claude-context/
├── .indexignore
│   ├── node_modules/
│   ├── tests/
│   ├── docs/
│   └── generated/

# 2. 配置 chunk 大小
# .claude-config.yaml
chunk:
  max_lines: 100
  overlap: 10

# 3. 定期增量索引
gitnexus watch  # 监控文件变化，自动更新索引
```

### 9.4.2 检索优化

```python
# 检索结果重排序
def rerank_results(query: str, results: list) -> list:
    # 1. 位置权重：业务代码 > 测试代码
    # 2. 修改时间权重：最近修改 > 历史修改
    # 3. 依赖权重：被多处引用 > 少处引用
    return weighted_rerank(query, results)
```

### 9.4.3 上下文注入优化

```python
# 上下文组装策略
def build_context(query: str, results: list) -> str:
    # 1. 最多注入 3 个代码块
    # 2. 每个块最多 50 行
    # 3. 包含文件路径和相对位置
    context = []
    for r in results[:3]:
        context.append(f"// {r.file}:{r.line}")
        context.append(truncate(r.code, 50))
    return "\n".join(context)
```

---

## 9.5 本章小结

1. **传统 Embedding 在代码场景失效**：上下文窗口不够、噪声过多、跨文件依赖丢失
2. **代码 RAG 四大流派**：向量检索、知识图谱、混合检索、代码感知检索
3. **claude-context + GitNexus 组合**：语义搜索 + 调用链分析 = 完整代码理解
4. **统一入口 code-context CLI**：简化 AI Agent 的代码访问
5. **最佳实践**：索引优化 + 检索优化 + 上下文注入优化

---

## 9.6 延伸阅读

- [claude-context](https://github.com/zilliztech/claude-context)（6.6k stars）
- [GitNexus](https://github.com/AbhigyanK/taichi)（10.8k stars）
- [GraphRAG](https://github.com/microsoft/graphrag)（19k stars）
- [jina-clip-v2](https://github.com/jinaai/jina-clip-v2)
- [code-context CLI](https://github.com/your-username/code-context)（自建工具）
