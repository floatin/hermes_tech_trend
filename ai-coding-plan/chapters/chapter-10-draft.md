# Chapter 10（草稿）：Git 才是 AI Coding 的最后一块拼图

> **副标题**：当 AI 接管开发速度，谁来接管 AI 的行为边界？

## 10.0 开篇：一个被忽视的真相

2026年，GitHub 周提交量突破 2.5 亿次。在这场 AI 编程浪潮中，所有人都在讨论模型能力、上下文窗口、Agent 架构——却没有人告诉你：**Git 才是 AI Coding 时代最被低估的基础设施。**

为什么？

因为 Git 最初就是为"分布式、异步、多方贡献"场景设计的——而这恰恰是人机协同的核心需求：分支隔离、PR 审核、Commit 历史、版本追溯。Git 的每一个设计都在回答一个问题：**当多方（人+AI）同时工作，谁来保证系统的一致性和可追溯性？**

本章会告诉你：
1. AI Coding 的七大失控类型（附代码示例）
2. 为什么 PR 是约束 AI 行为边界的核心机制
3. 如何用 Git Worktree 实现多 Agent 并行工作
4. 百度、Phodal 等一线团队的实战约束体系

---

## 10.1 AI 开发行为的七大失控类型

基于 2025-2026 年业界实战复盘，AI Coding Agent 在长周期任务中表现出七大典型失效模式。理解它们是设计约束机制的前提。

### 10.1.1 Gold Plating（过度工程化）

**症状**：用户只需要一个简单的 API 调用，AI 写出了一个完整的 SDK。

这是最常见的失控类型。AI 的训练数据中充斥着"最佳实践"，导致它默认认为：越完善越好。日志框架、配置抽象、缓存管理器——明明不需要，AI 也要"未雨绸缪"。

```python
# 用户真实需求：requests.get(url) 返回 JSON
# AI "好心"生成的代码：
# ===================== sdk/client.py =====================
import logging
import json
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from functools import wraps
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@dataclass
class APIConfig:
    """API 配置类"""
    base_url: str
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0
    cache_enabled: bool = True
    cache_ttl: int = 300
    _instance: Optional['APIConfig'] = None

    def __post_init__(self):
        APIConfig._instance = self

    @classmethod
    def get_instance(cls) -> 'APIConfig':
        if cls._instance is None:
            cls._instance = cls(base_url="")
        return cls._instance

def retry_on_failure(max_attempts: int = 3):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < max_attempts - 1:
                        time.sleep(1)
            raise last_exception
        return wrapper
    return decorator

class CacheManager:
    """缓存管理器"""
    _cache: Dict[str, tuple[Any, float]] = {}

    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        ...

class BaseClient(ABC):
    """抽象基类"""
    @abstractmethod
    def get(self, endpoint: str) -> Dict[str, Any]:
        pass

class APIClient:
    """API 客户端主类"""
    def __init__(self, config: Optional[APIConfig] = None):
        self.config = config or APIConfig.get_instance()
        self._session = None

    @retry_on_failure(max_attempts=3)
    def get(self, endpoint: str) -> Dict[str, Any]:
        with api_call_context(f"GET {endpoint}"):
            cache_key = f"{endpoint}"
            cached = CacheManager.get(cache_key)
            if cached is not None:
                logger.debug("Returning cached result")
                return cached
            # ...
```

用户只需要 3 行，你给了 200 行。

---

### 10.1.2 Scope Creep（范围蔓延）

**症状**：用户只要求加验证码，AI 重构了注册、登录、密码重置、Session 管理，还改了支付模块。

Scope Creep 的根源是任务边界定义不清。当用户说"给登录页加验证码"，AI 理解的是"改进登录功能"，然后自然延伸到"那注册也需要验证码"、"Session 管理需要优化"——最后整个用户系统都被重构了一遍。

```python
# ===================== user/views.py =====================
# AI 改动的文件：user/views.py
# 原始任务：login 加验证码
# AI 额外改动：register, password_reset, session, permissions...

class LoginView(View):
    def post(self, request):
        # ✅ 原始任务：加验证码
        captcha = request.POST.get('captcha')
        if not self.verify_captcha(captcha):
            return JsonResponse({'error': '验证码错误'}, status=400)

        # AI 额外添加：自动注册功能（❌ 这是 register 的职责）
        username = request.POST.get('username')
        password = request.POST.get('password')
        if not User.objects.filter(username=username).exists():
            # AI "好心"：登录用户不存在就自动创建
            User.objects.create_user(username=username, password=password)
            ...

# ===================== payments/views.py =====================
# 原始任务：完全不涉及支付模块！
# AI "顺手"添加了：支付限频、交易记录...

class PaymentView(View):
    def post(self, request):
        # AI 从 session 管理代码里"学到"了限频逻辑
        if self.check_rate_limit(session_key):
            return JsonResponse({'error': '请求过于频繁'}, status=429)
        self.log_transaction(request)  # AI 擅自添加
        ...
```

---

### 10.1.3 Reuse Failure（复用失灵）

**症状**：项目已有 `utils/http.py` 的 HTTP 工具函数，AI 在新模块里又写了一套。

软件工程几十年最核心的原则是"复用"。但 AI 不知道你仓库里有什么——除非你显式告诉它。当 AI 面临一个 HTTP 请求任务，它默认会"从零开始"，而不是搜索现有工具。

```python
# ===================== utils/http.py（项目已有）=====================
import requests

def get(url: str, **kwargs) -> dict:
    """HTTP GET 请求工具"""
    response = requests.get(url, **kwargs)
    return response.json()

def post(url: str, data: dict, **kwargs) -> dict:
    """HTTP POST 请求工具"""
    response = requests.post(url, json=data, **kwargs)
    return response.json()

# ===================== ai_integration/api.py（AI 新写的）=====================
# AI 完全无视 utils/http.py，自己写了一套
import urllib.request
import urllib.parse
import json
import ssl

def fetch_user_data(user_id: int) -> dict:
    """获取用户数据 - AI 自己写的 HTTP 工具"""
    base_url = "https://api.example.com"
    path = f"/users/{user_id}"

    # 手动处理 SSL（项目已有工具已经处理过）
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(path, context=context, timeout=30) as response:
            data = response.read().decode()
            return json.loads(data)
    except Exception as e:
        # 错误处理方式和项目其他地方不一致（用 print 而非 logging）
        print(f"Error: {e}")
        return {}
```

**后果**：重复代码 + 错误处理不一致 + 新旧工具行为差异。

---

### 10.1.4 Hallucination Confidence（幻觉自信）

**症状**：AI 声称完成了用户模块，实际上其他模块已经无法导入。

这是最危险的失控类型。AI 有一个"自信宣布完成"的毛病——它在单个文件或模块内测试通过后，就会认为"任务完成"。但它不知道其他模块依赖它的输出，当它提交代码后，整个系统才会 broken。

```python
# AI 的输出：
# "✅ 已完成用户模块！创建了 user/views.py 和 user/models.py，
#  实现了完整的 CRUD 功能，所有测试通过。"

# ===================== user/models.py =====================
from django.db import models

class UserProfile(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()

    # AI 自信地说：已添加 unique 约束
    class Meta:
        unique_together = ('name', 'email')  # ❌ 语法错误！
        # 正确语法：unique_together = ['name', 'email']

# ===================== 其他模块 =====================
# 实际上：
# 1. user/models.py 有语法错误，django check 失败
# 2. 所有导入 user 模块的地方都报错
# 3. user/views.py 的 JsonResponse 序列化会失败

# AI 完全不知道这些，因为它只在"自己的文件"里做局部检查
```

---

### 10.1.5 Context Exhaustion（上下文耗尽）

**症状**：30 个文件的重构任务，AI 在第 20 个文件时已经忘记最初的指令。

上下文窗口是有限的。当 AI 处理的第 20 个文件时，第 1 个文件的指令可能已经被挤出窗口。更糟糕的是，AI 会"悄悄适应"新上下文，忘记最初的约束。

```python
# 任务指令：
# """
# 1. 在 src/reports/generator.py 添加缓存支持
# 2. 使用项目已有的 cache_utils，不要自己写
# 3. 保持原有接口不变
# 4. 确保向后兼容
# """

# AI 处理到第 20 个文件时...
class ReportGenerator:
    def __init__(self):
        # AI 开始"自由发挥"
        self.cache = {}  # 没有用项目的 cache_utils
        self.cache_ttl = 3600  # 没有询问，自己定的
        self.async_mode = True  # 擅自添加异步模式

        # 擅自改变接口：
        # 原始：generate_report(report_type, params)
        # 新：async generate_report_async(report_type, params, callback)
        # 破坏了所有调用方
```

---

### 10.1.6 Aesthetic Overreach（审美越界）

**症状**：一个 280 行参数、5 层嵌套、3 层三元表达式的函数。

人类开发者有隐式的"审美防线"：300 行以上的文件要拆、嵌套超过 3 层要重构。但 AI 没有这种嗅觉——它会写出超长的参数列表、深度的嵌套回调、无穷的三元表达式，然后自信地说"代码功能完整"。

```python
# ===================== services/order_service.py =====================
def process_order(order_id, user_id, items, payment_method, shipping_address,
                 billing_address, coupon_code=None, gift_wrap=False,
                 gift_message=None, priority=False, backorder=False,
                 group_items=True, split_shipments=False, insurance=False,
                 insurance_amount=0.0, delivery_notes=None,
                 customer_notification=True, sms_notification=False,
                 email_notification=True, push_notification=False,
                 internal_remarks=None, promo_codes=None, loyalty_points=None,
                 gift_cards=None, store_credit=None, reference_number=None,
                 po_number=None, company_name=None, vat_number=None,
                 tax_exempt=False, special_instructions=None):
    # 280 行参数，一个屏幕都放不下

    def validate_order():
        def check_items():
            def verify_stock():
                def fetch_product():
                    def query_db():
                        pass
                    return query_db() if True else None
                return verify_stock()
            return check_items()
        return validate_order()

    result = validate_order() if (True if (False or True) else False) else None

    if (result is not None and
        (order_id is not None and
         (user_id is not None and
          (len(items) > 0 and
           (payment_method in ['card', 'paypal', 'bank'] and
            (shipping_address is not None and
             (len(shipping_address) > 0))))))):

        final_result = process_payment(
            amount=sum(item['price'] * item['quantity'] for item in items)
                if (True and True) else 0,
            method=payment_method if (payment_method is not None) else 'card',
            user_id=user_id
        ) if (customer_notification and email_notification) else None
    else:
        final_result = None

    return final_result if (priority or (delivery_notes is not None)) \
        else (result if True else None)
```

---

### 10.1.7 Convention Mismatch（规范失配）

**症状**：Python 项目用 snake_case，AI 写出了 camelCase；Django 项目用 CBV，AI 用了 Flask 风格的函数视图。

每个团队都有隐式的编码规范：命名约定、架构模式、错误处理方式。AI 不理解这些规范——尤其是在不熟悉的代码库里，它会按"自己的理解"写出与团队规范完全不符的代码。

```python
# ===================== orders/views.py =====================
# 项目规范：Django + snake_case + 类视图
# AI 按"自己的理解"写

def createOrder(request):  # ❌ 应该是 snake_case: create_order
    """创建订单 - AI 用了函数视图而非 CBV"""

    OrderData = request.POST  # ❌ 应该是 camelCase: order_data

    NewOrder = Order.objects.create(  # ❌ camelCase: new_order
        orderID = OrderData['orderId'],  # ❌ camelCase
        userID = OrderData['userId'],
        TotalAmount = OrderData['totalAmount'],  # ❌ camelCase
        orderDate = timezone.now(),
        ShippingAddress = OrderData.get('shippingAddress'),
        BillingAddress = OrderData.get('billingAddress'),
        orderStatus = 'pending'
    )

    # 没有使用项目的 ModelForm
    # 没有使用 DRF Serializer
    if NewOrder.id is not None:
        return {'success': True, 'orderId': NewOrder.id}
    else:
        return {'success': False, 'error': 'Failed'}


# ===================== orders/models.py =====================
class Order(models.Model):
    OrderId = models.AutoField(primary_key=True)  # ❌ 应该是 id
    UserId = models.IntegerField()  # ❌ 应该是 user_id + ForeignKey
    TotalAmount = models.DecimalField()  # ❌ 应该是 total_amount
    OrderDate = models.DateTimeField()  # ❌ 应该是 order_date
    OrderStatus = models.CharField()  # ❌ 应该是 order_status

    class Meta:
        db_table = 'orders'  # ❌ 应该用 app_model 格式：orders_order
```

---

## 10.2 为什么 PR 是约束 AI 的核心机制

### 10.2.1 传统 CI/CD vs AI 时代的 Harness

传统 CI/CD 关注的是"代码能否构建/测试通过"。

AI 时代的 Harness 关注的是"AI 的工作是否符合预期"：

| 传统 CI/CD | AI Harness |
|------------|------------|
| 代码能否编译？ | AI 是否改了任务范围之外的文件？ |
| 单元测试是否通过？ | AI 是否有过度工程化？ |
| 风格检查是否通过？ | AI 是否遵循团队的编码规范？ |
| 部署是否成功？ | AI 的决策是否可追溯？ |

GitHub PR 天然承载了这两种需求——它是代码审核的工具，也是行为约束的载体。

### 10.2.2 PR 作为强制约束层的六大设计

**1. Branch 策略：任务的边界定义**

```bash
# AI 任务专用分支前缀
feat/ai/{issue-id}-short-description

# 强制关联 issue-id，防止 AI 自行发散
feat/ai/1234-add-login-captcha
feat/ai/1235-fix-payment-timeout
```

**2. PR 描述模板：任务的边界声明**

```markdown
## Task Scope（必须填写）
- [ ] 本次改动仅涉及哪些文件/模块
- [ ] 未改动其他文件的原因

## Changes（必须列出）
- 改动1：[文件] [描述]
- 改动2：[文件] [描述]

## Out of Scope（必须声明）
以下内容不在本次任务范围内，如发现请 review 时指出：
- ❌ 重构其他模块
- ❌ 添加本次任务未明确的功能
- ❌ 修改配置文件（除非明确说明）

## Verification（CI 自动检查）
- [ ] 单元测试通过
- [ ] 构建成功
- [ ] 风格检查通过
```

**3. 文件范围约束：机器可读的边界定义**

```json
// .ai-constraints
{
  "allowed_paths": ["src/auth/", "src/handlers/"],
  "blocked_paths": ["src/core/", "src/legacy/", "tests/e2e/"],
  "max_files_per_pr": 5,
  "require_issue_link": true
}
```

**4. CI 自动检查：防止人工疏忽**

| 检查项 | 工具 | 约束效果 |
|--------|------|---------|
| 文件数量上限 | `claude-code --max-files 5` | 防止一次改太多 |
| 文件范围限制 | 自定义 glob pattern | 禁止改无关模块 |
| 禁止文件列表 | `.ai-blocked-files` | 核心文件保护 |
| 测试通过 | pytest / jest / go test | 改动必须有测试 |
| 风格检查 | ruff / golangci-lint | 强制代码规范 |
| 构建成功 | 编译/打包验证 | 确保可构建 |
| Diff 大小上限 | `git diff --stat` | 防止超大 PR |

**5. Commit Message 规范：追溯 AI 的决策链**

```bash
# AI commit 强制格式
<type>(<scope>): <short summary>

Co-authored-by: claude-code <agent@claude.ai>
Task-ID: #1234
Out-of-scope: [列出未改动的相邻模块]

# 示例
feat(auth): add captcha to login endpoint

Co-authored-by: claude-code <agent@claude.ai>
Task-ID: #1234
Out-of-scope: user registration, password reset, session management
```

**6. Review 强制节点：Human-in-the-loop**

```
PR 流程：
AI 完成 → 自测 → 提交 PR → AI Review（自动）→ Human Review（必须）→ Merge

Human Review 清单：
□ 改动是否在任务范围内？
□ 是否有未请求的"优化"？
□ 是否有重复造轮子（没复用现有工具）？
□ 测试覆盖是否充分？
□ 风格是否符合团队规范？
□ 是否有超长函数或深层嵌套？
```

---

## 10.3 Git Worktree：多 Agent 并行工作的基础设施

### 10.3.1 问题：同时运行多个 Agent 的困境

在同一个 Git 仓库里同时运行多个 AI Agent，会遇到文件修改冲突：
- Agent A 在写 `src/auth/login.py`
- Agent B 同时也在写 `src/auth/login.py`
- 谁的改动会被保留？

### 10.3.2 传统解法的局限

| 方案 | 问题 |
|------|------|
| 外部调度器协调 | 复杂度高，引入额外依赖 |
| 轮流使用同一工作区 | 低效，Agent 之间相互等待 |
| 手动创建多个 repo 副本 | 难以合并，代码同步问题 |

### 10.3.3 Git Worktree：近乎完美的解法

Git Worktree 允许从同一个仓库创建多个独立工作目录，每个目录对应一个分支，共享 `.git` 数据。

```bash
# 结构
/projects/
├── my-go-app/          # 主仓库（含 .git）
├── auth-refactor/      # 宇宙 A：重构认证模块
├── ai-chat-feature/    # 宇宙 B：新聊天功能
└── bug-fix-patch/      # 宇宙 C：紧急修复

# 创建 worktree
git worktree add ../auth-refactor feat/auth-refactor
git worktree add ../ai-chat-feature feat/chat-feature
git worktree add ../bug-fix-patch hotfix/urgent
```

**核心价值**：
- 共享 `.git` 数据 → 最终可以合并
- 独立工作目录 → 并行无冲突
- 原生 Git 支持 → 无需额外工具

### 10.3.4 Claude Code 的原生支持

2026年2月，Claude Code CLI 版本原生支持 `--worktree` 参数：

```bash
# 在新的 worktree 中启动 Claude
claude --worktree auth-refactor

# 在专属 tmux 会话中启动
claude --worktree ai-chat-feature --tmux
```

每个 Agent 获得专属的独立工作区，彻底解决多任务并发时的代码修改冲突问题。

---

## 10.4 实战约束体系：百度 vs Phodal

### 10.4.1 百度 CodeOps：约束-观测-干预三阶段

百度在 Code Agent 企业落地实践中，总结出完整的约束体系：

**阶段一：约束**
- 通过 `.ai_constraints` 定义文件白名单/黑名单
- Branch 策略强制关联 issue
- PR 模板强制声明 Out-of-Scope

**阶段二：观测**
- 通过 Routa 的 Trace 可视化观测 AI 的文件访问热力图
- 识别高频访问文件和冷门文件
- 发现异常模式（如 AI 反复访问不该改动的文件）

**阶段三：干预**
- AI 行为偏离时通过 Slack/飞书告警
- 人工介入时机：Scope Creep 迹象、上下文耗尽信号
- 干预后的经验反馈到约束规则

### 10.4.2 Phodal 的 Harness 工程

Phodal（著有《AI Coding 时代》等）在 Routa 项目中实践了完整的 Harness 工程：

**核心理念**：不是"让 AI 少做事"，而是"让 AI 做正确的事"。

**Harness 四要素**：
- **Spec**：需求层面的约束（人类意图）
- **Hook**：触发规则（什么条件下执行什么）
- **Review**：审查点（人类介入的时机）
- **Gate**：质量门禁（自动化验收标准）

---

## 10.5 约束效果的量化评估

| 失控类型 | 主要约束手段 | 预期降低幅度 |
|----------|-------------|-------------|
| 过度工程化 | PR 文件数量上限 + CI diff 检查 | 70%+ |
| 范围蔓延 | Branch 策略 + Out-of-scope 声明 | 80%+ |
| 复用失灵 | 代码库结构文档 + 显式告知已有工具 | 60%+ |
| 幻觉自信 | 强制 CI 测试通过 + Human Review | 90%+ |
| 上下文耗尽 | 任务拆解 + Spec 分阶段 | 75%+ |
| 审美越界 | 行数上限 + 风格检查 | 85%+ |
| 规范失配 | Lint + Review 清单 | 80%+ |

---

## 10.6 本章小结

1. **AI 开发的七大失控类型**是设计约束机制的前提。每种失控都有典型的代码特征，识别它们是 Human Review 的关键。

2. **PR 是核心约束层**。Branch 策略定义任务边界，PR 模板声明 Out-of-Scope，CI 检查强制质量门禁，Human Review 保留最终决策权。

3. **Git Worktree 是多 Agent 并行工作的基础设施**。共享 `.git` 可合并，独立工作目录无冲突，Claude Code 原生支持开箱即用。

4. **约束要量化**。没有量化的约束等于没有约束。每个失控类型都要有对应的检查手段和预期降低幅度。

5. **人始终是最终决策者**。AI 可以执行，但不能决定。Human-in-the-loop 是不可省略的环节。

---

## 延伸阅读

- [Martin Fowler - Harness Engineering](https://martinfowler.com/articles/harness-engineering-for-llm-agents/)
- [Anthropic - Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)
- [Phodal - AI Coding 时代的研发协作](https://github.com/phodal/routa)
- [harness-init - Agent-ready 项目初始化](https://github.com/Gizele1/harness-init)

---

*（本章完）*
