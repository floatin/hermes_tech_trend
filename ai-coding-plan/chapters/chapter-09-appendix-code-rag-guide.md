# Appendix E：代码 RAG 决策树与场景化方案

> **一句话看懂**：什么场景用什么工具组合，看这张图就够了。

---

## E.1 代码 RAG 决策树

```
代码仓库有多大？
│
├─ < 1万行，单一项目
│   └→ 不需要代码 RAG，直接丢给 AI
│
├─ 1-10万行，少量项目
│   └→ code-context search + grep fallback
│
├─ 10-50万行，多个服务
│   └→ code-context (claude-context + gitnexus)
│
└─ 50万+ 行，微服务架构
    └→ code-context + 增量索引 + 定期重建
```

```
你的问题是什么？
│
├─ "这段代码做什么？" → 语义搜索
│   └→ code-context search
│
├─ "这个函数在哪定义？" → 定义查找
│   └→ grep "def func_name"
│
├─ "谁调用了这个函数？" → 调用关系
│   └→ code-context who-calls
│
├─ "改这个会坏什么？" → 影响分析
│   └→ code-context impact
│
├─ "这个模块依赖什么？" → 依赖分析
│   └→ code-context graph
│
└─ "最近谁改了这个文件？" → 版本历史
    └→ git log --oneline -n 20
```

---

## E.2 场景化方案

### 场景 1：个人开发者，快速上手

```
推荐方案：code-context + grep

安装：
  npm install -g claude-context gitnexus
  pip install code-context  # 或直接用 bin 版本

效果：
  - 语义搜索：claude-context
  - 调用关系：gitnexus
  - 降级搜索：grep 永远能用

配置：无（自动发现项目根目录）
```

### 场景 2：5人团队，维护 2-3 个服务

```
推荐方案：code-context + 共享索引

code-context 配置：
  ~/.code-context/config.json
  {
    "codebase_path": "/path/to/repos",
    "shared_index": true  # 团队共享索引
  }

gitnexus 索引：
  # 在 CI 中运行
  gitnexus analyze --output ./index.json
  # 提交到仓库，团队共享

效果：
  - 新人能快速上手
  - 索引在仓库中版本化
  - 不依赖外部服务
```

### 场景 3：大型仓库，频繁重构

```
推荐方案：code-context + 增量索引 + 监控

增量索引：
  # 在 git post-commit hook 中运行
  # 只索引改动的文件
  gitnexus analyze --incremental

变更监控：
  # 监控高频改动文件
  # 这些文件的索引优先更新
  code-context monitor --top 10

效果：
  - 索引始终最新
  - 热点文件优先
  - 重构时影响分析准确
```

### 场景 4：遗留代码，需要快速理解

```
推荐方案：code-context + AI 辅助总结

步骤 1：结构探索
  code-context graph --focus src/
  code-context status

步骤 2：热点分析
  # 找出被引用最多的文件
  code-context impact --rank

步骤 3：AI 辅助理解
  # 将关键文件丢给 LLM 总结
  cat src/core/auth.py | clauden "这个文件做什么？"

效果：
  - 快速理解代码结构
  - AI 帮助提炼业务逻辑
  - 不需要完整索引
```

### 场景 5：需要代码搜索+知识图谱双能力

```
推荐方案：Graphify + claude-context 组合

Graphify 特点：
  - 一条命令生成知识图谱：graphify .
  - 多模态：代码 + PDF + 图片 + 表格 → 同一张图
  - token 节省 71.5 倍
  - PreToolUse Hook：Glob/Grep 前自动优先查图谱
  - 边置信度标记：EXTRACTED / INFERRED / AMBIGUOUS

安装：
  pip install graphifyy && graphify install

使用：
  graphify .                        # 建图
  graphify query "..."             # 查询架构关系
  graphify path A B                 # 追踪 A→B 的路径
  graphify install                  # 安装 PreToolUse Hook（Claude Code）

增量更新：
  graphify ./raw --update           # 只处理变更文件，合并到已有图谱

---

## E.3 避坑速查表

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| Graphify 建图失败 | Python < 3.10 | 升级 Python 或用 uv 安装 |
| graphify: command not found | pip 安装后 PATH 未刷新 | `uv tool install graphifyy` 或 `pipx install graphifyy` |
| Claude Code 查不到图谱 | PreToolUse Hook 未安装 | `graphify install` |
| code-context search 超时 | 大型仓库 grep 太慢 | 安装 claude-context |
| gitnexus analyze 失败 | 缺少依赖 | npm install -g gitnexus |
| 搜索结果不准确 | 没有索引 | code-context index |
| 影响分析漏掉引用 | grep 只搜同目录 | gitnexus impact |
| 索引占用空间太大 | 50万+ 文件 | 配置 .indexignore |
| AI 上下文爆炸 | 返回结果太多 | code-context 默认 20 行限制 |

---

## E.4 快速参考命令

```bash
# Graphify（知识图谱，多模态）
pip install graphifyy && graphify install
graphify .                        # 建图
graphify query "..."             # 查询
graphify path A B                 # 路径追踪
graphify ./raw --update          # 增量更新

# claude-context（语义搜索）
npm install -g claude-context
claude-context index

# GitNexus（调用链）
npm install -g gitnexus
gitnexus analyze

# code-context 统一入口
code-context search "..."      # 优先 claude-context
code-context who-calls "..."  # 优先 gitnexus
code-context impact "..."     # 优先 gitnexus
```

---

## E.5 ROI 计算

### 假设：20万行代码，5人团队

```
无工具：
  - 平均每次代码理解需要阅读 500 行
  - 每人每天 5 次 = 2,500 行
  - 5人 × 22天 × 12月 = 330,000 次/年

有 code-context：
  - 平均每次代码理解只需 50 行（精确检索）
  - 节省 90% 阅读量
  - AI 理解时间节省 80%

价值：
  - 工程师时间节省：~2小时/天/人
  - 错误定位时间节省：~1小时/天/人
  - 年化节省：5人 × 3小时 × 22天 × 12月 = 3,960 小时
  - 按 $50/小时 = $198,000/年
```

**结论**：code-context 类的工具价值不在工具本身，而在**工程师时间的节省**。

---

## E.6 工具对比速查

| 工具 | 擅长 | 不擅长 | 适合场景 |
|------|------|--------|----------|
| **grep** | 关键词搜索 | 语义理解 | 已知文件名/函数名 |
| **claude-context** | 语义搜索 | 调用链 | "这段代码做什么" |
| **gitnexus** | 调用链/影响 | 语义 | "改这个会坏什么" |
| **code-context** | 全能 | 无 | 日常开发 |
| **sourcegraph** | 跨仓库搜索 | 本地项目 | 大型企业代码库 |

---

**核心原则**：从最小方案（grep）开始，按需升级到 code-context。**不要过度工程化**。
