# code-context Skill

> 统一代码上下文查询工具，封装语义搜索和知识图谱查询。

## 用途

当需要理解代码库结构、查找相关代码、分析依赖关系时使用此工具。

## 命令速查

| 命令 | 用途 | 回答的问题 |
|------|------|-----------|
| `code-context search <query>` | 语义搜索 | 这段代码做什么？ |
| `code-context who-calls <func>` | 调用关系 | 谁调用了这个函数？ |
| `code-context impact <symbol>` | 影响分析 | 修改这个会影响哪些？ |
| `code-context graph --focus <path>` | 依赖图 | 模块之间的依赖？ |

## 详细用法

### 1. 语义搜索

```bash
code-context search "用户认证逻辑"
code-context search "如何实现支付"
code-context search "error handling"
```

**适用场景**：
- 不确定代码在哪里
- 想了解某个功能的实现位置
- 需要找相似代码参考

**输出示例**：
```
Found 5 matches:
  src/auth/login.py:42 - 用户名密码验证逻辑
  src/auth/oauth.py:15 - 第三方 OAuth 认证
  src/middleware/auth.go:28 - JWT token 验证中间件
```

### 2. 调用关系查询

```bash
code-context who-calls PaymentService.validate
code-context who-calls UserService
code-context calls get_user_by_id
```

**适用场景**：
- 修改一个函数前，想知道谁在用
- 不确定能不能删除某段代码
- 想追踪调用链

**输出示例**：
```json
{
  "symbol": "PaymentService.validate",
  "callers": [
    {"file": "src/orders/create.py", "line": 42, "confidence": 0.95},
    {"file": "src/orders/refund.py", "line": 18, "confidence": 0.88}
  ],
  "clusters": ["orders", "payments"],
  "total_calls": 8
}
```

### 3. 影响范围分析

```bash
code-context impact UserService
code-context impact auth/permissions.py
```

**适用场景**：
- 评估修改风险
- 重构前了解影响面
- 代码审查时评估变更

**输出示例**：
```json
{
  "symbol": "UserService",
  "impact": {
    "callers": 12,
    "clusters": 3,
    "confidence": 0.92
  },
  "affected_modules": [
    "orders", "notifications", "payments", "analytics"
  ]
}
```

### 4. 依赖图生成

```bash
code-context graph
code-context graph --focus auth/
code-context graph --focus src/api/
```

**适用场景**：
- 了解模块结构
- 新人了解项目
- 可视化依赖关系

## 决策流程

```
需要了解代码？
    │
    ├── 不知道在哪里？→ search
    │
    ├── 想知道谁调用谁？→ who-calls
    │
    ├── 评估修改影响？→ impact
    │
    └── 需要整体结构？→ graph
```

## 注意事项

1. **首次使用需要索引**：
   ```bash
   code-context index  # 建立索引
   ```

2. **查看状态**：
   ```bash
   code-context status  # 查看索引状态和依赖
   ```

3. **降级策略**：
   - 如果 claude-context 未安装，使用 grep 语义搜索
   - 如果 gitnexus 未安装，使用 grep + 正则查找调用关系
   - 仍可正常工作，只是功能受限

4. **增量更新**：
   - 索引会保存在 `~/.code-context/`
   - 代码大幅变更后建议重新索引

## 安装依赖

```bash
# 安装核心依赖
npm install -g claude-context gitnexus

# 初始化
code-context index

# 验证
code-context status
```

## 输出格式

- **人类可读**：直接输出到终端，带颜色高亮
- **JSON 格式**：`who-calls` 和 `impact` 返回结构化 JSON
- **管道友好**：可与其他工具配合使用

## 示例对话

**用户**: "我想重构 `UserService` 类，但不确定有哪些地方依赖它"

**AI 行动**:
```bash
code-context impact UserService
code-context who-calls UserService
```

**AI 结论**: "这个类被 12 个模块引用，主要集中在 orders、notifications、payments 三个集群。修改前建议先看调用方的具体逻辑。"

---

**使用建议**：当不确定代码位置、依赖关系或修改影响时，优先使用此工具，而不是盲目搜索文件。
