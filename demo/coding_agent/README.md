# Coding Agent Demo: Thin Harness, Fat Skills

## 概述

本demo用Python实现了一个极简Coding Agent，演示Garry Tan和Mario Zechner的核心观点如何落地：

```
核心观点           → 代码实现
─────────────────────────────────────────
Thin Harness      → ~150行的主循环，无40+工具膨胀
Fat Skills        → markdown过程文件，可参数化调用
Resolver          → 上下文路由表，按任务类型加载正确文档
极简工具          → 4个核心工具：read/write/edit/bash
透明可观测        → 所有操作带日志，无后台注入
Latent/Deterministic → 明确区分智能判断和确定性执行
```

---

## 目录结构

```
demo/coding_agent/
├── harness/
│   ├── __init__.py
│   ├── main.py          # Thin Harness核心 (~150行)
│   ├── tools.py         # 4个极简工具
│   ├── resolver.py      # 上下文路由表
│   └── session.py       # Session管理（树结构）
├── skills/
│   ├── investigate.md   # 技能示例：调查分析
│   ├── enrich.md        # 技能示例：数据丰富
│   └── match.md         # 技能示例：匹配逻辑
├── run_demo.py          # 演示入口
└── README.md
```

---

## 快速开始

```bash
cd demo/coding_agent
pip install anthropic

# 运行演示
python run_demo.py
```

---

## 核心观点代码映射

### 1. Thin Harness (~150行)

```python
# harness/main.py - 核心循环仅负责：
# 1. 运行模型循环
# 2. 管理上下文
# 3. 执行工具
# 4. 安全防护

class ThinHarness:
    def __init__(self, skills_dir: str):
        self.skills = load_skills(skills_dir)  # 技能是胖的
        self.tools = get_minimal_tools()       # 工具是瘦的（4个）
        self.resolver = ContextResolver()
        self.session = Session()                # 树结构，非线性

    def run(self, task: str) -> str:
        context = self.resolver.route(task)    # 路由决定加载什么
        messages = [SystemMessage(self.skills), UserMessage(task)]
        # 主循环：模型思考 → 工具执行 → 结果返回
        while not is_complete(messages):
            response = self.llm.chat(messages)
            if response.tool_calls:
                for tool in response.tool_calls:
                    result = self.tools.execute(tool.name, tool.args)
                    messages.append(ToolResult(result))
            else:
                return response.content
        return final_answer
```

### 2. Fat Skills (Markdown过程)

```markdown
<!-- skills/investigate.md -->
# /investigate

七步调查法，用于深度分析一个主题。

## 参数
- TARGET: 调查目标
- QUESTION: 核心问题
- DATASET: 数据集路径

## 步骤
1. **Scope数据集**：确定数据边界和可用性
2. **构建时间线**：梳理事件先后顺序
3. **编年体摘要(diarize)**：读50文档→1页结构化判断
4. ** Synthesize**：综合分析
5. **Argue both sides**：正反两面论证
6. **引用来源**：所有结论有据可查

## 示例调用
```
/investigate TARGET="Dr. Sarah Chen" QUESTION="是否被噤声" DATASET="./emails/"
```
Same skill, different data → 医学研究员 vs 取证调查员
```

### 3. Resolver (上下文路由)

```python
# harness/resolver.py
class ContextResolver:
    """Mario Zechner的核心：透明加载，无后台注入"""

    def __init__(self):
        self.routing_table = {
            "bug": ["docs/debugging.md", "context/recent_commits.md"],
            "architecture": ["docs/architecture.md", "context/team_decisions.md"],
            "investigate": ["skills/investigate.md"],
            # 任务类型 → 需要加载的文档
        }

    def route(self, task: str) -> Context:
        task_type = classify(task)  # LLM判断任务类型
        docs = self.routing_table.get(task_type, [])
        return Context.load(docs)   # 明确加载，可追溯

    # 无后台偷偷注入 - Mario的透明性原则
```

### 4. 极简工具 (4个核心)

```python
# harness/tools.py
MINIMAL_TOOLS = ["read", "write", "edit", "bash"]

def execute(tool_name: str, args: dict) -> str:
    """Mario Zechner：4个工具打天下，不需要更多"""
    if tool_name == "read":
        return read_file(args["path"])
    elif tool_name == "write":
        return write_file(args["path"], args["content"])
    elif tool_name == "edit":
        return edit_file(args["path"], args["old"], args["new"])
    elif tool_name == "bash":
        return run_bash(args["command"])
    else:
        raise ValueError(f"Unknown tool: {tool_name}")
```

### 5. Latent vs Deterministic 分离

```python
def process_task(task: str):
    """Garry Tan核心：智能归LLM，信任归确定性代码"""

    # DETERMINISTIC: SQL查询 - 同输入同输出
    if is_lookup(task):
        return db.query(task)  # 不需要LLM介入

    # LATENT: 需要判断 - LLM来处理
    if needs_judgment(task):
        return llm.judge(task)  # 这里用LLM的智能

    # DETERMINISTIC: 格式化输出
    return format_result(result)  # 确定性函数
```

### 6. Diarization (编年体摘要)

```python
def diarize(documents: list[Document]) -> str:
    """
    Garry Tan核心洞察：
    读50份文档 → 1页结构化判断

    这是RAG做不到的事：必须模型真正读完、记住矛盾、注意到变化
    """
    all_text = "\n".join(doc.text for doc in documents)
    prompt = f"""读完后写一段结构化分析：

    SAYS vs ACTUALLY:
    - 文档中声称的目标:
    - 实际行为反映的目标:

    关键变化点:
    - 时间X: 变化描述

    结论: ..."""

    return llm.generate(prompt, context=all_text)
```

---

## 对比：胖Harness vs 瘦Harness

### ❌ 胖Harness (反模式)

```python
# 40+工具塞满上下文 - Mario批评的
胖Harness:
    tools = [
        "read", "write", "edit", "bash",
        "web_search", "web_fetch", "browser_open", "browser_click",
        "code_search", "git_log", "git_diff", "git_status",
        "db_query", "db_insert", "db_update",
        "file_tree", "file_glob", "file_watch",
        "subagent_spawn", "subagent_result",
        "eval_run", "eval_result",
        "context_expand", "context_shrink", "context_search",
        # ... 40+ 工具
    ]
    # 问题：上下文爆炸，注意力分散
```

### ✓ 瘦Harness (正模式)

```python
# 4个核心工具 + 可扩展Skills - Garry/Mario提倡的
瘦Harness:
    core_tools = ["read", "write", "edit", "bash"]

    # 通过Skill File扩展能力，不堆工具
    skills = {
        "investigate": load_skill("skills/investigate.md"),
        "enrich": load_skill("skills/enrich.md"),
        "match": load_skill("skills/match.md"),
    }
```

---

## 演示运行

```bash
$ python run_demo.py

=== Thin Harness, Fat Skills Demo ===

[1] 演示Skill File参数化调用
[2] 演示Resolver上下文路由
[3] 演示Latent vs Deterministic分离
[4] 演示Diarization

选择:
```

---

## 关键洞察的代码验证

| 观点 | 代码验证 |
|------|----------|
| "不需要40+工具" | 4个核心工具覆盖所有场景 |
| "技能文件像方法调用" | 同一investigate.md，不同参数=不同能力 |
| "上下文路由要透明" | Resolver明确加载哪些文档，无后台注入 |
| "Latent/Deterministic要分离" | is_lookup()决定是否需要LLM |
| "读50文档→1页判断" | diarize()函数实现 |

---

## 延伸思考

1. **为什么4个工具就够了？**
   - read/write/edit覆盖所有文件操作
   - bash覆盖所有系统操作
   - 其他能力通过Skill File封装

2. **为什么工具要瘦？**
   - 每多一个工具，上下文窗口就被吃掉一部分
   - 模型需要在众多工具中选择，注意力分散
   - 工具能力应该通过Skill参数化，而不是新增工具

3. **为什么透明度重要？**
   - 无后台注入 = 用户知道发生了什么
   - 可追溯 = 出问题时能定位
   - Mario: "掌控感的丧失是极其危险的"
