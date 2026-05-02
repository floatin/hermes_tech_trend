# Appendix D：Token 优化决策树与场景化方案

> **一句话看懂**：什么场景用什么工具，不用记，看这张图就够了。

---

## D.1 Token 优化决策树

```
你的问题是什么？
│
├─ "我的 Claude Code git diff 输出太长了"
│   └→ 用 RTK: rtk git diff
│
├─ "我的 transcript 越来越长，LLM 开始健忘"
│   └→ 用 token-optimizer: 开启 AutoContext
│
├─ "我要给 LLM 发送特定目录的文件列表"
│   └→ 用 llm-context.py: 配置 include/exclude 规则
│
├─ "我的测试输出有 1000 行，全是 passed"
│   └→ 用 RTK: cargo test (已有内置 filter)
│
├─ "我想让 AI 学会项目的代码规范"
│   └→ 写 AGENTS.md + CLAUDE.md，用 RTK 过滤你的命令示例
│
└─ "我不知道哪个工具适合我"
    └→ 先装 RTK，它有 discover 模块会自动推荐
```

---

## D.2 场景化方案

### 场景 1：个人开发者，单一项目

```
推荐方案：RTK 单一方案

安装：brew install rtk && rtk init --global
配置：~/.rtk/config.toml （可选，大多数情况不需要）
效果：CLI 输出压缩 60-90%，30分钟会话节省 80% tokens
成本：免费
```

### 场景 2：团队使用，多个项目

```
推荐方案：RTK + 项目级 CLAUDE.md

RTK：处理命令输出压缩
CLAUDE.md：项目规范（每个项目一个）
效果：CLI 压缩 + 项目上下文精确控制
成本：免费
注意：CLAUDE.md 需要团队统一维护
```

### 场景 3：大型代码仓库，频繁重构

```
推荐方案：RTK + token-optimizer + llm-context.py

RTK：CLI 输出
token-optimizer：transcript 管理
llm-context.py：精确的上下文过滤
效果：三层优化，Token 节省可达 90%+
成本：token-optimizer 和 llm-context.py 免费
注意：配置复杂，需要专人维护
```

### 场景 4：Claude Code 重度用户

```
推荐方案：RTK + token-optimizer

RTK：压缩所有 CLI 命令
token-optimizer：transcript 截断 + AutoContext
效果：开箱即用，零配置
配置：~/.claude/settings.json 配 token-optimizer hook
```

### 场景 5：生产环境，需要可观测性

```
推荐方案：RTK + analytics

RTK：压缩
rtk gain：查看 Token 节省统计
rtk analytics：详细报告
效果：Token 节省可量化
注意：analytics 数据本地存储，不上传
```

---

## D.3 避坑速查表

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| rtk git status 没压缩 | match_command 正则缺 `\b` | 检查 TOML filter 配置 |
| rtk hook 不生效 | Claude Code 没重启 | 重启 Claude Code |
| token-optimizer 截断太多 | max_tokens 太小 | 调大 `auto_context_max_tokens` |
| llm-context.py 过滤太狠 | exclude 规则太宽 | 检查规则顺序，include 优先 |
| AI 抱怨缺少上下文 | 过度压缩 | 对关键命令提高 max_lines |

---

## D.4 ROI 计算

### 30 分钟开发会话

```
无优化：
  git status × 20  = 2,000 tokens
  ls × 10          = 1,000 tokens
  cargo test × 5   = 2,500 tokens
  cat × 15         = 3,000 tokens
  grep × 20        = 1,600 tokens
  ─────────────────────────────
  总计             = 10,100 tokens
  费用 ($5/1M)     = $0.050

RTK 优化（80%）：
  10,100 × 20%    = 2,020 tokens
  费用             = $0.010

节省：$0.040/会话 × 20 会话/天 × 22 天/月 = $17.6/月
```

### 年化节省

```
个人：$17.6/月 × 12 = $211/年
5人团队：$1,055/年
20人团队：$4,220/年
```

**结论：RTK 的价值不是 $170/年，而是让 AI 在相同上下文窗口里处理更多有意义的内容。**

---

## D.5 快速参考命令

```bash
# 安装 RTK
brew install rtk

# 初始化（为 Claude Code 安装 hook）
rtk init --global

# 查看节省统计
rtk gain

# 手动使用
rtk git status
rtk cargo test
rtk npm run build

# 发现推荐
rtk discover --recommend

# 调试 filter
RTK_DEBUG=filter rtk <command>

# token-optimizer 安装
npm install -g token-optimizer

# llm-context.py 使用
python -m llm_context --project . --include "src/**" --exclude "*.test.py"
```

---

**核心原则**：从最小方案（RTK 单用）开始，按需叠加。**不要过度工程化**。
