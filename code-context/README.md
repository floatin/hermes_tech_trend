# code-context

统一代码上下文 CLI - 封装语义搜索和知识图谱查询，对外提供简洁接口。

## 安装

```bash
# 1. 下载 CLI 工具
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/code-context/main/bin/code-context \
  -o ~/bin/code-context

# 或手动复制
cp bin/code-context ~/bin/code-context
chmod +x ~/bin/code-context

# 2. 确保 ~/bin 在 PATH 中
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 3. 安装可选依赖
npm install -g claude-context gitnexus

# 4. 初始化
code-context index

# 5. 验证
code-context status
```

## 快速开始

```bash
# 语义搜索
code-context search "用户认证"

# 查询调用关系
code-context who-calls PaymentService

# 分析影响范围
code-context impact UserService

# 生成依赖图
code-context graph --focus auth/
```

## 依赖

| 依赖 | 用途 | 必需 |
|------|------|------|
| claude-context | 向量语义搜索 | 否（可用 grep 降级）|
| gitnexus | 知识图谱查询 | 否（可用 grep 降级）|
| npx | 运行 npm 包 | 是 |

## 与 SKILL.md 配合

将此仓库的 `skills/SKILL.md` 内容添加到你的 AI 编程助手的项目规范中，AI 就能学会使用这些命令。

## 项目结构

```
code-context/
├── bin/
│   └── code-context      # 主 CLI 工具
├── skills/
│   └── SKILL.md         # AI 使用的技能定义
├── README.md
└── install.sh           # 安装脚本
```
