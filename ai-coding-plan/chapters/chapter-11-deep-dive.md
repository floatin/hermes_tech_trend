# Chapter 11-B（深度补充）：RTK 源码解析与生产环境避坑指南

> **副标题**：从 39.6k stars 项目看 Token 优化的工程精髓

---

## 11-B.0 开篇：为什么深入 RTK？

RTK 是 AI Coding 生态里唯一一个**从第一性原理出发**解决 Token 消耗问题的开源项目。它的价值不只是节省 $170/年，而是一套**可复用的 CLI 输出压缩方法论**。

深入它的源码，你可以学到：
1. **如何设计一个生产级的 Rust CLI 工具**
2. **如何用 TOML 配置驱动复杂逻辑**
3. **如何构建可扩展的 Filter 插件系统**
4. **如何实现零配置的智能默认值**

---

## 11-B.1 源码架构解析

### 11-B.1.1 整体架构

```
RTK CLI (main.rs, 101KB)
├── cmds/          # 命令行子命令 (git, cargo, docker, ...)
├── core/          # 核心抽象 (config, filter, runner, stream, ...)
├── discover/      # 自动发现命令并推荐 filter
├── filters/       # 56 个 TOML filter 定义
├── hooks/         # Claude Code / Cline 集成
├── learn/         # 从历史使用中学习
├── analytics/     # Token 节省统计
└── parser/        # 命令解析器
```

**关键洞察**：RTK 的架构是**插件化的**，核心是一个 FilterRunner，56 个 filter 通过 TOML 配置注册进去。这意味着：

- 添加新命令的 filter **不需要改 Rust 代码**，只需加一个 TOML 文件
- 所有 filter 在编译时通过 `build.rs` 拼接成一个大 TOML，打包进二进制

### 11-B.1.2 Filter 系统核心逻辑

Filter 系统是 RTK 的心脏。源码在 `src/core/filter.rs`：

```rust
pub enum FilterLevel {
    None,       // 不过滤
    Minimal,     // 只去 ANSI 颜色码
    Aggressive, // 注释 + 空白 + 样板代码全去掉
}
```

Filter 策略接口：

```rust
pub trait FilterStrategy {
    fn filter(&self, content: &str, lang: &Language) -> String;
}
```

每种语言有自己的注释模式：

```rust
impl Language {
    pub fn comment_patterns(&self) -> CommentPatterns {
        match self {
            Language::Rust    => CommentPatterns { line: Some("//"), block: Some(("/*", "*/")) },
            Language::Python  => CommentPatterns { line: Some("#"), block: Some(("'''", "'''"), ("\"\"\"", "\"\"\"")) },
            Language::JavaScript => CommentPatterns { line: Some("//"), block: Some(("/*", "*/")) },
            // ...
        }
    }
}
```

### 11-B.1.3 TOML Filter 机制

这是 RTK 最精妙的设计。`src/filters/README.md` 解释了为什么用 TOML：

> TOML filters strip noise lines — they don't reformat output.
> TOML works well for commands with **predictable, line-by-line text output** where regex filtering achieves 60%+ savings.

每个 filter 是一个 TOML 文件，比如 `git-status.toml`（推测结构）：

```toml
[filters.git-status]
description = "Simplify git status output"
match_command = "^git status\\b"

# 去掉无意义的提示行
strip_lines_matching = [
    "^\\s*$",                           # 空行
    "^Changes not staged",              # 提示行
    "^No changes added",
    "^use \"git add",
    "^use \"git checkout",
]

# 最多保留 20 行
max_lines = 20

# 空输出时的提示
on_empty = "git status: clean"

[[tests.git-status]]
name = "basic status"
input = """
On branch master
Changes not staged for commit:
        modified:   src/main.py
        modified:   src/utils.py
"""
expected = "modified: src/main.py\nmodified: src/utils.py"
```

关键点：**测试内联在 TOML 里**。运行 `cargo test` 时，构建步骤会验证每个 filter 的测试用例。

### 11-B.1.4 discover 模块：自动感知

`src/discover/` 是 RTK 的"自适应大脑"：

```rust
// 发现用户常用的命令，自动推荐 filter
pub fn discover_commands(shell_history: &str) -> Vec<CommandHint> {
    // 解析 shell 历史
    // 统计命令频率
    // 对高频命令推荐 rtk filter
}
```

这就是为什么 RTK 能**零配置工作**——它会从你的 shell 历史里学习你常用的命令。

---

## 11-B.2 生产环境避坑指南

### 坑 #1：filter 匹配不上

**症状**：`rtk git status` 没有压缩，原始输出直接出来

**原因**：TOML filter 的 `match_command` 是**正则表达式**，且必须**全匹配**。

```toml
# ❌ 错误：少了 \b 词边界
match_command = "^git status"

# ✅ 正确：确保词边界
match_command = "^git status\\b"
```

**排查步骤**：

```bash
# 1. 列出所有可用 filter
rtk discover --list

# 2. 测试特定命令的 filter
rtk discover --test "git status"

# 3. 查看详细匹配日志
RTK_LOG=debug rtk git status
```

### 坑 #2：过度压缩丢失关键信息

**症状**：压缩后的输出缺少错误信息，AI 无法定位问题

**原因**：`max_lines` 设置太小，或 `strip_lines_matching` 把错误行也去掉了

**解决**：在 `~/.rtk/config.toml` 中为特定命令覆盖默认值

```toml
[commands.git-diff]
max_lines = 200  # diff 需要更多上下文

[commands.cargo-test]
# 不要去掉 "error[E0308]" 这种关键错误信息
strip_lines_matching = [
    "^\\s*$",
    "^test result: ok",
]
```

### 坑 #3：hook 安装后不生效

**症状**：Claude Code 里 `git status` 还是原始输出

**排查**：

```bash
# 1. 确认 hook 安装成功
rtk hook --status

# 2. 手动测试 hook
rtk hook --test

# 3. 确认 Claude Code 重启过
# RTK hook 需要在 Claude Code 启动时注入
```

### 坑 #4：Windows 路径问题

RTK 在 Windows 上的 hook 机制不同：

```bash
# Windows: 使用 'rtk hook claude' 不 fallback
# 不像 Unix 用 shell alias
```

Windows 用户需要：

```powershell
# 在 $HOME/.claude/settings.json 中添加
{
  "hooks": {
    "preToolUse": ["rtk", "hook", "claude"]
  }
}
```

### 坑 #5：自定义 filter 语法错误

TOML filter 语法严格，容易出错：

```toml
# ❌ 错误：正则中有未转义的 \
strip_lines_matching = ["^\s*$"]

# ✅ 正确：TOML 字符串中 \ 需要双重转义
strip_lines_matching = ["^\\s*$"]

# ❌ 错误：数组元素类型不一致
strip_lines_matching = ["^foo", 123]

# ✅ 正确：全字符串
strip_lines_matching = ["^foo", "^bar"]
```

验证方法：

```bash
cargo test --test filter_tests
# 或者
rtk validate-config
```

---

## 11-B.3 扩展 RTK：添加自定义 Filter

### 场景：为一个内部 CLI 工具添加 filter

假设你公司有一个 `deploy-tool` CLI，输出如下：

```
[INFO] Starting deployment to production
[INFO] Building image...
[INFO] Pushing to registry...
[INFO] Deploying to 3 replicas...
[SUCCESS] Deployment complete
[INFO] Cleanup started
[INFO] Cleanup complete
```

你想压缩成：

```
Building image... → Pushing to registry... → Deploying (3 replicas) → SUCCESS
```

### 步骤 1：创建 TOML filter

创建 `~/.rtk/filters/deploy-tool.toml`：

```toml
[filters.deploy-tool]
description = "Compact deploy-tool output"
match_command = "^deploy-tool\\b"

# 去掉 info 日志
strip_lines_matching = [
    "^\\[INFO\\] Starting",
    "^\\[INFO\\] Cleanup",
    "^\\[INFO\\] Push",
]

# 保留关键信息行并简化
transform_lines = [
    { match = "^\\[INFO\\] Building", replace = "Building" },
    { match = "^\\[INFO\\] Deploying to (\\d+) replicas", replace = "Deploying ($1 replicas)" },
    { match = "^\\[SUCCESS\\] Deployment complete", replace = "SUCCESS" },
]

max_lines = 5
on_empty = "deploy-tool: no output"
```

### 步骤 2：测试 filter

```bash
# 手动测试
echo "[INFO] Starting deployment
[INFO] Building image...
[INFO] Deploying to 3 replicas...
[SUCCESS] Deployment complete" | rtk filter deploy-tool

# 或使用 rtk 的调试模式
RTK_DEBUG=filter rtk deploy-tool
```

### 步骤 3：验证并提交 PR

如果这是一个通用工具，值得提交到上游：

```bash
# 1. fork rtk
# 2. 添加 filter 到 src/filters/deploy-tool.toml
# 3. 添加测试用例到同一个文件
# 4. 运行 cargo test
# 5. 提交 PR
```

---

## 11-B.4 RTK 的工程设计精髓

### 精髓 #1：数据驱动的配置

RTK 几乎所有行为都由 TOML 配置决定，Rust 代码只做**解释执行**。这意味着：

- **非 Rust 开发者也能贡献 filter**
- **生产环境可以热更新配置**而不需要重新编译
- **测试只需验证 TOML + 预期输出**，不需要写 Rust 测试

### 精髓 #2：零成本抽象

Rust 的 trait system 让 FilterStrategy 可以动态切换：

```rust
pub trait FilterStrategy {
    fn filter(&self, content: &str, lang: &Language) -> String;
}

// 编译时确定使用哪个实现，运行时零成本分发
```

### 精髓 #3：可测试的设计

每个 TOML filter 都内联测试用例：

```toml
[[tests.git-status]]
name = "removes untracked files hint"
input = "..."
expected = "..."
```

构建步骤（`build.rs`）会在编译时运行这些测试，**确保 filter 不会因维护而退化**。

### 精髓 #4：自描述的错误信息

RTK 的错误信息包含**修复建议**：

```bash
$ rtk unknown-cmd
Error: No filter found for 'unknown-cmd'
Hint: Run 'rtk discover --recommend' to find available filters
```

---

## 11-B.5 与其他工具的对比

| 维度 | RTK | token-optimizer | llm-context.py |
|------|-----|-----------------|----------------|
| 架构 | CLI 代理 | Claude Code hook | MCP 协议 |
| 压缩方式 | TOML 正则过滤 | 启发式截断 | 规则匹配 |
| 扩展方式 | TOML 文件 | JavaScript | Python 配置 |
| 学习能力 | discover 模块 | 无 | 无 |
| 生产成熟度 | 39.6k stars | 低 | 中 |
| 适用场景 | 所有 CLI | Claude Code | 精确上下文 |

---

## 11-B.6 本章小结

1. **RTK 的核心是 FilterRunner + TOML 配置**，插件化架构让添加新命令 filter 不需要改 Rust 代码
2. **Filter 三层：FilterLevel (None/Minimal/Aggressive) + 语言注释模式 + TOML 正则规则**
3. **生产环境避坑**：正则词边界、max_lines 过小、hook 安装、Windows 路径、 TOML 语法
4. **扩展 RTK**：创建 `~/.rtk/filters/custom.toml`，内联测试，调试用 `RTK_DEBUG=filter`
5. **工程设计精髓**：数据驱动零成本抽象、内联可测试、自描述错误

---

## 延伸阅读

- [RTK 源码 - src/core/filter.rs](https://github.com/rtk-ai/rtk/blob/master/src/core/filter.rs)
- [RTK 源码 - src/filters/README.md](https://github.com/rtk-ai/rtk/blob/master/src/filters/README.md)
- [RTK CONTRIBUTING.md - 设计哲学](https://github.com/rtk-ai/rtk/blob/master/CONTRIBUTING.md)
- [RTK 安装指南](https://github.com/rtk-ai/rtk/blob/master/INSTALL.md)
