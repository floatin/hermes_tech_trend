# Coding Agents 研究报告
> 生成日期：2026-04-28
> 研究主题：Coding Agents 架构设计与最佳实践

---

## 一、研究背景

本系列文章旨在从第一性原理出发，探索AI编程工具的本质能力边界和人机协同模式。在这一框架下，理解当前行业内顶尖专家对Coding Agents的思考和实践至关重要。

本次研究聚焦于两篇极具价值的参考文献：
1. **Garry Tan - "Thin Harness, Fat Skills"**（YC President & CEO）
2. **Mario Zechner - "写了17年开源代码，我为什么认为Coding Agents堆功能是在瞎折腾？"**（libGDX创始人）

---

## 二、核心洞察对比

### 2.1 Garry Tan - Thin Harness, Fat Skills

**核心论点**：100x生产力的差距不在于模型本身，而在于围绕模型构建的**系统架构**。

**五个核心概念**：

| 概念 | 定义 | 反面教材 |
|------|------|----------|
| **Skill File** | 可复用的markdown过程文件，像方法调用一样接受参数 | prompt engineering（一次性、无复用） |
| **Harness** | ~200行的LLM运行层，负责上下文管理和安全防护 | 40+工具定义塞满上下文窗口 |
| **Resolver** | 上下文路由表，在正确时刻加载正确文档 | 20000行CLAUDE.md（无差别堆放） |
| **Latent vs Deterministic** | 智能在潜在空间，信任在确定性代码 | 把SQL查询塞进LLM |
| **Diarization** | 读50份文档→1页结构化判断 | RAG pipeline无法做到 |

**三层架构**：
```
Fat Skills（顶层，90%价值）
    ↓
Thin Harness（中层，~200行）
    ↓
Deterministic Tools（底层确定性基础设施）
```

**YC实战案例**：用/enrich-founder、/match-*、/improve等技能处理6000名创业者数据，通过"读取→归整→判断→写回"循环实现接近人类分析师的能力，并自我优化（"还行"评分从12%降至4%）。

**关键洞察**：技能是永久升级，系统具备复利效应；模型能力提升时所有技能自动变强，而确定性部分保持稳定。

---

### 2.2 Mario Zechner - 堆功能是在瞎折腾

**核心论点**：让Coding Agent适应你的需求，而不是反过来。

**对现有工具的批评**：

| 工具 | 问题 |
|------|------|
| **Claude Code** | 功能多得像"宇宙飞船"，90%是无人知晓的"暗物质"；后台偷偷修改上下文，缺乏可观测性；UI用React导致终端闪烁 |
| **OpenCode** | 上下文管理糟糕（SessionCompaction.prune破坏prompt cache）；在agent工作时挂LSP会误导；架构设计问题（每条消息存独立JSON文件、默认RCE安全漏洞） |

**极简主义实验**：
> "不需要文件工具，不需要子agent，不需要联网搜索，啥都不需要。"
> ——结果：仅用tmux发送按键+读取VT序列，就拿下TerminalBench排行榜顶级表现

**作者的项目pi**：
- 只有4个工具：read、write、edit、bash
- 主流agent中最短的system prompt（模型已通过RL训练"知道"自己是coding agent）
- 通过extension实现可扩展性（skills、自定义工具、UI、hot reload）
- Session为树结构，非线性聊天记录
- 完全透明，无后台注入

**金句**：
> "当你发现AI在背地里偷偷修改你的上下文，而你却对此一无所知时，这种掌控感的丧失是极其危险的。"

---

## 三、两种路线的共鸣与分歧

### 3.1 核心共鸣

1. **反对堆功能**：Garry说"harness要瘦"，Mario说"堆功能是瞎折腾"
2. **强调极简**：Garry的harness~200行，Mario的pi只有4个工具
3. **透明性**：Garry的Resolver加载上下文可追溯，Mario反对"后台偷偷修改上下文"
4. **扩展性**：两者都强调通过某种机制（Skill File / Extension）实现可扩展性，而非内置所有功能

### 3.2 表面分歧，实则互补

| 维度 | Garry Tan | Mario Zechner |
|------|------------|---------------|
| **核心抽象** | Skill File（markdown过程） | Extension（代码扩展） |
| **上下文管理** | Resolver路由表 | 完全透明，无后台注入 |
| **扩展方式** | 技能文件+参数调用 | extension机制 |
| **学习方式** | 技能文件自我重写 | 不强调，强调确定性 |

**表面分歧的实质**：这是**不同层次的抽象**，不是互斥的路线。

- Garry说的是**What（做什么）**：把智能推入Skills，把执行推入确定性工具
- Mario说的是**How（怎么做）**：工具要极简，过程要透明

一个真正好的Coding Agent，完全可以同时是：
```
Fat Skills（智能在技能层）
    ↓
Thin Harness（~200行，极简工具集）
    ↓
Deterministic Tools（确定性执行，透明可观测）
```

Garry的Skill File完全可以基于Mario的极简工具（read/write/edit/bash）来实现。pi的extension机制就是Garry"Skill File"概念的工程落地。

---

## 四、代码示例：核心观点的工程落地

为验证上述观点，我们实现了一组Python演示代码，位于 `demo/coding_agent/` 目录。

### 4.1 架构概览

```
demo/coding_agent/
├── README.md                    # 概念说明文档
├── run_demo.py                  # 演示入口
├── harness/
│   ├── tools.py                 # Mario的4个极简工具 + 可观测性追踪
│   ├── resolver.py              # Garry的Context Resolver（透明路由）
│   ├── session.py               # Mario的非线性Session树
│   └── main.py                  # ThinHarness核心（~150行）
└── skills/
    ├── investigate.md           # Garry的Diarization技能示例
    ├── enrich.md                # 多来源数据丰富技能
    └── match.md                 # YC实战匹配技能
```

### 4.2 核心观点→代码映射

| 观点 | 代码实现 |
|------|----------|
| Mario: 只需要4个工具 | `tools.py` - `MINIMAL_TOOLS = {read, write, edit, bash}` |
| Mario: 无后台注入，透明可追溯 | `ToolTracer` 类 - 每次工具调用都记录 |
| Garry: Skill File是方法调用 | `skills/*.md` - 参数化markdown过程文件 |
| Garry: Resolver决定加载什么上下文 | `resolver.py` - `TransparentResolver.route()` |
| Mario: Session是树结构 | `session.py` - `Session.branch()` / `Session.backtrack()` |
| Garry: Latent vs Deterministic分离 | `ThinHarness.is_deterministic()` 自动判断 |

### 4.3 关键代码片段

**Mario的4个极简工具** (`harness/tools.py`)：

```python
MINIMAL_TOOLS = {
    "read": read,    # 读取文件
    "write": write,  # 写入文件
    "edit": edit,    # 编辑文件
    "bash": bash,   # 执行命令
}

def execute_tool(tool_name: str, args: dict) -> str:
    """这是唯一的工具执行入口，无后台注入"""
    return MINIMAL_TOOLS[tool_name](**args)
```

**透明可观测性追踪** (`harness/tools.py`)：

```python
class ToolTracer:
    """Mario的原则：所有操作可追溯，无暗箱操作"""
    def trace(self, tool_name: str, args: dict, result: str):
        execution = ToolExecution(tool_name, args, result)
        self.executions.append(execution)
        print(f"  → {execution}")
```

**Garry的Resolver路由** (`harness/resolver.py`)：

```python
class TransparentResolver:
    """上下文路由表 - 决定何时加载什么文档"""
    def route(self, task: str) -> Context:
        task_type = self.classify(task)      # 分类任务类型
        docs_to_load = self.routing_table.get(task_type, [])
        # 完全透明：日志记录路由决策
        self.routing_log.append({
            "task": task,
            "task_type": task_type,
            "loaded_files": [d["path"] for d in docs_to_load],
        })
        return Context(task_type=task_type, documents=docs_to_load)
```

**Mario的非线性Session树** (`harness/session.py`)：

```python
class Session:
    """树结构会话，支持分支和回溯"""
    def branch(self):
        """创建分支点，保留当前路径"""
        self.branches.append(self.current)

    def backtrack(self):
        """回溯到父节点，尝试另一种方法"""
        self.current = session_db[self.current.parent_id]
```

**Fat Skill示例** (`skills/investigate.md`)：

```markdown
# /investigate

## 步骤

### 1. Scope数据集
确定可用数据边界...

### 2. 编年体摘要(Diarization)
**这是Garry Tan的核心洞察：读50份文档，产出1页结构化判断**

格式：
```
SAYS: [文档中声称的目标]
ACTUALLY: [实际行为反映的目标]
关键矛盾:
- [矛盾1]
- [矛盾2]
```

## 示例

Same skill, different parameters:
```
/investigate TARGET="Dr. Sarah Chen" QUESTION="是否被噤声" DATASET="./emails/"
/investigate TARGET="FBI调查" QUESTION="是否存在共谋" DATASET="./fec/"
```
```

### 4.4 运行演示

```bash
cd demo/coding_agent
python3 run_demo.py           # 运行全部演示
python3 run_demo.py 1         # 只运行第1个演示
python3 run_demo.py 4         # 只运行Skill File演示
```

### 4.5 验证结果

核心模块已通过测试验证：

```
✓ MINIMAL_TOOLS: ['read', 'write', 'edit', 'bash']

=== Context Resolver Demo ===
Task: 'investigate a potential data breach'
  → Type: 'investigate', Files: ['skills/investigate.md', 'docs/investigation_guide.md']

Task: 'architect a new microservices system'
  → Type: 'architecture', Files: ['docs/architecture.md', 'context/team_decisions.md']

=== Session Tree Demo ===
 [user] Fix the login bug...
   [assistant] I'll investigate......
→    [tool] Reading auth.py......
```

---

## 五、真正冲突的是什么

**Garry和Mario共同反对的**：**FAT HARNESS, THIN SKILLS**的产品

| 特征 | 问题 |
|------|------|
| 40+工具定义 | 塞满上下文，模型注意力分散 |
| 后台偷偷修改状态 | 缺乏可观测性，用户失去掌控感 |
| 90%的功能没人知道 | "暗物质"，维护成本高 |
| 缺乏透明机制 | 难以调试和信任 |
| 无差别的上下文堆放 | 20000行CLAUDE.md的灾难 |

---

## 五、对本系列的启示

### 5.1 架构设计原则

1. **瘦Harness，胖Skills**：把领域知识和流程封装在Skills中，而不是塞进工具定义
2. **极简工具集**：4个核心工具（read/write/edit/bash）比40个工具更好用
3. **透明可观测**：无后台注入，所有上下文修改可追溯
4. **确定性优先**：能确定性解决的问题，不要扔给LLM

### 5.2 章节关联

- **第一章**（概率模型）：为"为什么需要Skill File"提供理论基础——LLM擅长概率补全，不擅长精确执行
- **第四章**（Prompt工程）：Skill File是Prompt工程的进阶——不只是指令，是可参数化的过程
- **第五章**（人机协作）：瘦Harness模式是协作的最佳载体

### 5.3 待进一步研究

1. pi项目的extension机制具体实现
2. Resolver路由表的实现方案
3. Self-improving Skills的实现难度和边界

---

## 六、参考文献

1. Garry Tan, "Thin Harness, Fat Skills", Y Combinator, 2026-04-09
   - 原始链接：https://github.com/garrytan/gbrain/blob/master/docs/ethos/THIN_HARNESS_FAT_SKILLS.md
2. Mario Zechner, "写了17年开源代码，我为什么认为Coding Agents堆功能是在瞎折腾？", 2026
   - 研究链接：https://www.sohu.com/a/1015171051_355140
