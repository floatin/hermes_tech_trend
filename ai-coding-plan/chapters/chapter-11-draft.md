# Chapter 11（草稿）：Token 战争——RTK 与高效精简之道

> **副标题**：当上下文窗口成为稀缺资源，谁能把 10 万 Token 压缩到 1 万？

## 11.0 开篇：被忽视的隐性成本

2026 年，一个中型团队使用 Claude Code 进行开发，平均每天消耗 Token 费用约 **$47**。其中：

- **63%** 消耗在 CLI 命令输出（git status、ls、cat、grep）
- **22%** 消耗在重复的日志和堆栈信息
- **10%** 消耗在无意义的空白字符和格式
- **仅 5%** 是真正有价值的代码上下文

这就是 AI Coding 的**隐性成本**——大多数人在关注模型能力、上下文窗口大小，却没人告诉你：**CLI 命令输出才是 Token 消耗的主力军。**

RTK（Rust Token Killer）的出现改变了一切。它通过 CLI 代理模式，在命令输出到达 LLM 上下文之前，进行智能过滤、压缩和去重——**60-90% 的 Token 消耗，就这么省下来了。**

本章会告诉你：
1. Token 消耗的四大来源（CLI 输出、重复日志、格式噪音、上下文膨胀）
2. RTK 的技术原理与实现
3. Token 精简工具生态全景图
4. 如何构建完整的 Token 优化体系

---

## 11.1 Token 消耗的四大来源

### 11.1.1 CLI 输出冗余

这是最容易被忽视的 Token 杀手。

以一个典型的 `git status` 为例：

```
On branch master
Your branch is up to date with 'origin/master'.
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
        modified:   src/main.py
        modified:   src/utils.py
        modified:   tests/test_main.py
        modified:   tests/test_utils.py
        modified:   docs/README.md
        modified:   docs/CHANGELOG.md
        modified:   .github/workflows/ci.yml
        modified:   package.json
        modified:   package-lock.json
        modified:   .gitignore
        modified:   .env.example

no changes added to commit (use "git add" and/or "commit -")
```

LLM 真正需要知道的只有：**5 个代码文件被修改**。其余全是格式噪音。

### 11.1.2 重复日志

测试输出、构建日志是最典型的重复内容：

```
✓ Test 1 passed
✓ Test 2 passed
✓ Test 3 passed
✓ Test 4 passed
✓ Test 5 passed
✓ Test 6 passed
✓ Test 7 passed
✓ Test 8 passed
✓ Test 9 passed
✓ Test 10 passed
✓ Test 11 passed
✓ Test 12 passed
✓ Test 13 passed
✓ Test 14 passed
✓ Test 15 passed
✓ Test 16 passed
✓ Test 17 passed
✓ Test 18 passed
✓ Test 19 passed
✓ Test 20 passed
```

压缩后：**"20 tests passed"**。

### 11.1.3 格式噪音

- ANSI 颜色码： `\033[32m\033[1m`
- 重复空格和缩进
- 行号和文件名（grep 结果中）
- 注释和文档字符串

### 11.1.4 上下文膨胀

AI Coding Agent 在长周期任务中，会累积大量的历史消息。每一次 `ls`、`cat`、`grep` 的输出都会进入上下文，而 LLM 必须处理这些内容才能"理解"当前状态。

**这就是 RTK 解决的问题。**

---

## 11.2 RTK 技术原理

### 11.2.1 架构：CLI 代理模式

RTK 工作在命令和 LLM 之间：

```
用户 → rtk git status → git status → rtk → LLM
                         ↓
                   原始输出 50KB
                         ↓
                   压缩后 3KB
```

RTK 拦截命令输出，进行四层处理：
1. **过滤层**：移除 ANSI 颜色码、重复空格、注释
2. **聚合层**：相似日志行合并 + 计数
3. **截断层**：超长输出截断 + 重复内容去重
4. **提示层**：为常用命令生成自然语言提示

### 11.2.2 核心算法

```rust
// RTK 压缩算法伪代码
fn compress(output: &str) -> String {
    let mut lines: Vec<&str> = output.lines().collect();

    // 1. 过滤：移除颜色码和注释
    lines = lines.iter()
        .filter(|l| !is_ansi_noise(l) && !is_comment(l))
        .collect();

    // 2. 聚合：相似行合并
    let grouped = group_similar_lines(&lines);

    // 3. 截断：超长输出
    let truncated = truncate_lines(&grouped, MAX_LINES);

    // 4. 生成提示
    format_as_hints(&truncated, command)
}
```

### 11.2.3 压缩效果实测

| 操作 | 原始 Token | RTK Token | 节省 | 压缩比 |
|------|-----------|-----------|------|--------|
| `ls -la` (100 文件) | 2,000 | 400 | 80% | 5x |
| `cat large_file.py` | 40,000 | 12,000 | 70% | 3.3x |
| `grep -rn "func"` | 16,000 | 3,200 | 80% | 5x |
| `git status` | 3,000 | 600 | 80% | 5x |
| `git diff` | 10,000 | 2,500 | 75% | 4x |
| `cargo test` | 25,000 | 2,500 | 90% | 10x |
| **30分钟会话总计** | **~118,000** | **~23,900** | **80%** | **5x** |

---

## 11.3 Token 精简工具生态

### 11.3.1 RTK：通用 CLI 代理

**适用场景**：所有 CLI 命令输出的压缩

```bash
# 安装
brew install rtk

# 初始化（为 Claude Code 安装 hook）
rtk init --global

# 手动使用
rtk git status
rtk cargo test

# 查看节省统计
rtk gain
```

### 11.3.2 token-optimizer：Claude Code 专用

**适用场景**：Claude Code 用户的自动上下文清理

```bash
# 安装
npm install -g token-optimizer

# 自动在 PreToolUse hook 中工作
# 无需额外配置
```

核心功能：
- **AutoContext**：检测 transcript 行数/体积，超阈值注入 `<auto-context>` 提示
- **suggest-compact**：在 PreToolUse hook 中建议压缩
- **零配置**：开箱即用

### 11.3.3 llm-context.py：MCP 集成

**适用场景**：需要精确控制发送给 LLM 的上下文

```python
from llm_context import ContextBuilder

# 规则过滤
builder = ContextBuilder()
builder.add_rule("*.test.py", exclude=True)  # 排除测试文件
builder.add_rule("src/**/*.py", include=True)  # 只包含业务代码
builder.add_rule("docs/**", exclude=True)  # 排除文档

# 生成上下文
context = builder.build(project_path)
# → 通过 MCP 协议发送给 LLM
```

### 11.3.4 selective-context：学术方案

**适用场景**：需要可解释的压缩场景

```python
from selective_context import SelectiveContext

sc = SelectiveContext(model_type="gpt-2")
compressed = sc.compress(original_text, ratio=0.3)
# 保留信息量最高的 30% Token
```

核心技术：基于自信息的压缩，保留信息量最高的 Token。

---

## 11.4 构建完整 Token 优化体系

### 11.4.1 三层优化策略

```
┌─────────────────────────────────────────────┐
│  Layer 1: 命令层（RTK）                      │
│  拦截所有 CLI 输出，压缩后发送给 LLM           │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│  Layer 2: 上下文层（token-optimizer）          │
│  管理 transcript，智能清理历史消息              │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│  Layer 3: 输入层（llm-context.py）            │
│  精确控制发送给 LLM 的文件和代码片段           │
└─────────────────────────────────────────────┘
```

### 11.4.2 实践：RTK + Claude Code

```bash
# 1. 安装 RTK
brew install rtk

# 2. 为 Claude Code 初始化
rtk init --global

# 3. 验证
rtk gain
# → 显示 Token 节省统计

# 4. 自定义规则（可选）
cat ~/.rtk/config.toml
# [commands.git]
# max_lines = 50
# show_branch = true
```

### 11.4.3 效果评估

```bash
# 开启 RTK 前
$ rtk gain
Total tokens: 118,000
Cost: $0.59 (at $5/1M tokens)

# 开启 RTK 后
$ rtk gain
Total tokens: 23,900
Cost: $0.12 (at $5/1M tokens)

Savings: 80% | $0.47/day | $170/year
```

---

## 11.5 本章小结

1. **Token 消耗的主力是 CLI 输出**，而非模型处理本身
2. **RTK 通过四层处理（过滤/聚合/截断/提示）实现 60-90% 压缩**
3. **Token 精简工具生态**：RTK（通用）→ token-optimizer（Claude Code 专用）→ llm-context.py（精确控制）
4. **三层优化体系**：命令层 → 上下文层 → 输入层
5. **工程价值**：一个中型团队每年可节省 $170+ 的 Token 费用

---

## 11.6 延伸阅读

- [RTK 官方文档](https://github.com/rtk-ai/rtk)
- [Token Optimizer GitHub](https://github.com/jiaweifreshair/token-optimizer)
- [LLM Context Python](https://github.com/cyberchitta/llm-context.py)
- [Selective Context 论文](https://arxiv.org/abs/2312.12315)

---

## 附：RTK 安装与配置

```bash
# macOS
brew install rtk

# Linux
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh

# Windows
# 下载 release 包，放入 PATH

# 验证
rtk --version  # 应显示 "rtk 0.27.x"
```
