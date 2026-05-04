# claude-context vs graphify 深度对比

> 调研时间：2026-05-04 | 对比版本：claude-context 0.1.11 / graphify 0.6.9

## 一、定位差异：一句话说清

| | claude-context | graphify |
|---|---|---|
| **一句话定位** | 语义搜索引擎——让 Agent 按意图找到代码片段 | 知识图谱引擎——让 Agent 理解代码的结构和关系 |
| **核心隐喻** | 代码界的 Google Search | 代码界的 Wolfram Alpha |
| **解决的问题** | "我要改支付逻辑，相关代码在哪？" | "这个项目的架构是什么样的？谁调谁？" |
| **输出形态** | 代码片段（chunk）列表 | 图谱（nodes + edges + communities） |

## 二、架构对比

### claude-context：向量检索架构

```
代码库 → 文件扫描 → AST/字符分块 → Embedding向量化 → Milvus向量库
                                                          ↓
Agent查询 → Embedding向量化 → BM25稀疏检索 + Dense向量检索 → RRF融合排序 → Top-K代码片段
```

**关键技术选型：**
- **向量库**：Milvus（自建）/ Zilliz Cloud（托管）
- **Embedding**：4家可选——OpenAI / VoyageAI / Gemini / Ollama
- **分块策略**：AST感知分块（默认）→ 字符分块（fallback）
- **增量机制**：Merkle Tree 检测文件变更，仅重索引差量
- **检索模式**：混合检索（BM25 + Dense，RRF融合）

### graphify：知识图谱架构

```
代码库 → 文件检测 → 三阶段提取 → NetworkX图构建 → Leiden社区发现 → 分析报告
                         ↓
              Pass1: tree-sitter AST（免费）
              Pass2: 音视频转写（本地whisper）
              Pass3: 文档/图片LLM语义提取（费token）
```

**关键技术选型：**
- **图引擎**：NetworkX（内存）→ JSON持久化
- **AST引擎**：tree-sitter（25语言）+ SQL特殊处理
- **语义增强**：Claude/Kimi K2.6 LLM子代理
- **社区发现**：Leiden（首选）→ Louvain（降级）
- **增量机制**：SHA256内容缓存，仅重提取变更文件

## 三、核心能力对比

| 能力维度 | claude-context | graphify | 评判 |
|---------|---------------|----------|------|
| **语义搜索** | ⭐⭐⭐⭐⭐ 核心 | ⭐⭐ BFS/DFS遍历 | CC完胜：向量检索天然适合"找相关代码" |
| **架构理解** | ⭐⭐ 返回片段 | ⭐⭐⭐⭐⭐ god nodes + community + GRAPH_REPORT | GF完胜：图谱结构天然适合"理解全局" |
| **调用链分析** | ⭐ 无法 | ⭐⭐ AST级同文件调用 | 都弱：CC无此能力，GF仅限同文件 |
| **影响分析** | ❌ | ❌ | 都不行：这是GitNexus的领域 |
| **增量更新** | ⭐⭐⭐⭐ Merkle Tree | ⭐⭐⭐ SHA256缓存 | CC更优雅：Merkle Tree更精确 |
| **多模态** | ❌ 纯代码 | ⭐⭐⭐⭐⭐ 代码+文档+PDF+图片+视频 | GF完胜：知识图谱天然接纳异构数据 |
| **跨仓库** | ❌ 单仓库索引 | ⭐⭐⭐ merge-graphs | GF支持 |
| **Token效率** | 40-80%节省 | 71.5x减少（官方数据） | GF声称更优，但场景不同不可直接比较 |
| **首次构建成本** | Embedding API费用（或Ollama免费） | LLM API费用（Pass3）/ AST免费 | CC更可控：Ollama可零成本 |
| **可视化** | ❌ | ⭐⭐⭐⭐⭐ HTML交互图 + Obsidian + SVG | GF完胜 |

## 四、MCP工具对比

### claude-context（4个工具）

| 工具 | 功能 |
|-----|------|
| `index_codebase` | 索引代码库 |
| `search_code` | 语义搜索（query + limit + extensionFilter） |
| `clear_index` | 清除索引 |
| `get_indexing_status` | 索引进度查询 |

**评价**：工具少但聚焦，search_code 是核心，简单直接。

### graphify（7个工具）

| 工具 | 功能 |
|-----|------|
| `query_graph` | BFS/DFS图谱搜索（含token budget控制） |
| `get_node` | 节点详情 |
| `get_neighbors` | 邻居节点 + 边关系 |
| `get_community` | 社区全貌 |
| `god_nodes` | 核心抽象发现 |
| `graph_stats` | 图谱统计 |
| `shortest_path` | 两概念间最短路径 |

**评价**：工具多且层次丰富，但语义搜索能力弱——query_graph 本质是图遍历，不是向量检索。

## 五、技术深度对比

### 5.1 检索原理

| | claude-context | graphify |
|---|---|---|
| **检索方式** | 向量相似度 + BM25关键词 → RRF融合 | 图遍历（BFS/DFS）+ 社区过滤 |
| **查询输入** | 自然语言 / 代码片段 | 自然语言 → context_filter推断 → 图遍历 |
| **排序机制** | RRF融合排序（向量+关键词） | 按图距离 / token预算截断 |
| **精度特征** | 高召回率（语义近似） | 高精度（结构关联） |
| **典型失败模式** | 语义相近但无结构关联的代码被召回 | 无法找到没有图边连接但语义相关的内容 |

**举例说明**：
- 搜索"用户认证" → **CC**：找到所有与认证语义相近的代码片段（含注释中提到auth的）
- 搜索"用户认证" → **GF**：找到AuthService节点 + 邻居 + 所在社区（只看结构关联的）

### 5.2 索引/构建

| | claude-context | graphify |
|---|---|---|
| **构建时间** | 中等（Embedding API调用） | AST快（秒级）/ 含LLM则慢（分钟级） |
| **存储格式** | Milvus向量库（需服务） | graph.json（单文件，可移植） |
| **存储大小** | 向量维度 × chunk数（通常远大于原始代码） | 图JSON（通常远小于原始代码） |
| **增量策略** | Merkle Tree（文件粒度，精确） | SHA256缓存（文件粒度，等效） |
| **依赖服务** | Milvus/Zilliz Cloud（必选） | 无外部依赖（NetworkX内存图） |

### 5.3 数据模型

**claude-context**：扁平的chunk列表
```
chunk = {id, content, metadata(file, line_range), embedding[]}
```

**graphify**：节点+边+社区+超边的图结构
```
node = {id, label, file_type, source_file, community, ...}
edge = {source, target, relation, confidence, context, ...}
community = {id, nodes[], cohesion}
hyperedge = {nodes[], relation}
```

**核心区别**：CC是"袋子里的文档"，GF是"网状的关系图"。

## 六、适用场景矩阵

| 场景 | 推荐工具 | 原因 |
|------|---------|------|
| "这个功能的代码在哪？" | **CC** | 语义搜索直接命中 |
| "项目架构是什么样的？" | **GF** | god nodes + GRAPH_REPORT |
| "找到所有处理支付的代码" | **CC** | 向量检索擅长语义匹配 |
| "X模块和Y模块有什么关系？" | **GF** | shortest_path + community |
| "代码里有没有类似的实现？" | **CC** | 语义近似是向量检索的强项 |
| "哪些模块是核心抽象？" | **GF** | god_nodes（度中心性） |
| "新项目快速onboarding" | **GF** | 一个命令出架构报告 |
| "AI Agent日常编码辅助" | **CC** | search_code简洁高效 |
| "理解跨模块的数据流" | **GF** | 图遍历可追踪调用链 |
| "搜索含特定注释的代码" | **CC** | BM25关键词匹配 |

## 七、互补性分析：1+1>2

两者不是竞品，而是**正交互补**：

```
claude-context（语义层）     graphify（结构层）
    "找到相关代码"              "理解代码关系"
         │                          │
         └──────── 互补 ────────────┘
                    │
                    ▼
          AI Coding Agent 的完整上下文
```

### 典型组合工作流

**场景1：修Bug**
1. `search_code("payment timeout handling")` → **CC** 找到相关代码片段
2. `get_neighbors("PaymentService")` → **GF** 理解上下游依赖
3. `shortest_path("PaymentService", "TimeoutHandler")` → **GF** 确认调用路径

**场景2：代码Review**
1. `query_graph("authentication", mode="bfs", depth=2)` → **GF** 看认证模块全貌
2. `search_code("SQL injection vulnerability pattern")` → **CC** 语义搜索安全隐患
3. `get_community(community_id=3)` → **GF** 定位核心业务模块

**场景3：架构重构**
1. `god_nodes()` → **GF** 识别核心抽象
2. `search_code("deprecated API usage")` → **CC** 找废弃API的调用点
3. `graph_stats()` → **GF** 评估重构影响范围

## 八、选型建议

### 只选一个？

| 如果你的核心需求是... | 选 |
|---------------------|-----|
| AI Agent 需要频繁搜索代码片段 | **claude-context** |
| 需要理解项目架构和模块关系 | **graphify** |
| 团队新项目多，需要快速onboarding | **graphify** |
| 日常编码为主，"找代码"比"看架构"频繁 | **claude-context** |
| 代码库包含大量文档/设计稿 | **graphify**（多模态） |
| 环境受限（无Milvus/无GPU） | **graphify**（零外部依赖） |

### 两个都要？

强烈推荐。部署成本：
- **CC**：需部署Milvus（Docker一键）+ Embedding API Key（或Ollama本地）
- **GF**：pip install 即可，AST模式零成本

两者MCP工具名无冲突，可同时注册到同一Agent。

## 九、与GitNexus的三方定位

```
检索精度低 ─────────────────────────── 检索精度高
  │                                      │
  │  claude-context    graphify    GitNexus
  │  (语义搜索)        (知识图谱)   (静态分析)
  │                                      │
  │  按意图找代码       按结构理解     按类型精确分析
  │  召回优先           关系优先       精度优先
  │                                      │
  浅 ─────────────────────────────── 深
```

| 维度 | claude-context | graphify | GitNexus |
|-----|---------------|----------|----------|
| 分析深度 | Embedding相似度 | AST+LLM语义 | 编译器级静态分析 |
| 影响分析 | ❌ | ❌ | ✅（6阶段调用DAG） |
| 跨文件类型推导 | ❌ | ❌ | ✅（4策略） |
| 首次构建速度 | 中（Embedding API） | 快（AST秒级） | 慢（分钟级） |
| 增量更新 | ✅ Merkle Tree | ✅ SHA256 | ❌ 全量重建 |
| 商用许可 | **MIT** ✅ | **MIT** ✅ | **PolyForm NC** ⚠️ |
| 外部依赖 | Milvus必选 | 无 | LadybugDB（内嵌） |

## 十、总结

1. **claude-context = 搜索引擎**：擅长"找到"，不擅长"理解"。对AI Agent日常编码场景最高频的"找代码"需求，效率最高。

2. **graphify = 知识图谱**：擅长"理解"，不擅长"精确定位"。对架构理解、onboarding、模块关系梳理，无可替代。

3. **两者互补而非竞争**：CC的弱项（结构理解）正是GF的强项，GF的弱项（语义搜索）正是CC的强项。组合使用效果远超单选。

4. **加GitNexus补齐第三层**：当需要"改这个方法会影响谁"这种编译器级别的影响分析时，两个都不够，需要GitNexus的深度静态分析。但要注意其**非商用许可**。

5. **实际建议**：先上graphify（零门槛），再加claude-context（需Milvus），按需引入GitNexus（非商用注意合规）。三层各司其职，是目前AI Coding Agent上下文工程的最优解。
