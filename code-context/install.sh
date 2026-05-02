#!/bin/bash
#
# code-context 安装脚本
#

set -e

echo "============================================"
echo "  code-context 安装脚本"
echo "============================================"
echo ""

# 1. 检查环境
if [ ! -d "$HOME/bin" ]; then
    echo "📁 创建 ~/bin 目录..."
    mkdir -p "$HOME/bin"
fi

# 2. 添加到 PATH
BASHRC="$HOME/.bashrc"
ZSHRC="$HOME/.zshrc"

if ! grep -q 'export PATH="\$HOME/bin:\$PATH"' "$BASHRC" 2>/dev/null; then
    echo "📝 添加 ~/bin 到 PATH..."
    echo '' >> "$BASHRC"
    echo '# code-context' >> "$BASHRC"
    echo 'export PATH="$HOME/bin:$PATH"' >> "$BASHRC"
fi

# 3. 复制 CLI 工具
echo "📦 安装 code-context CLI..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp "$SCRIPT_DIR/bin/code-context" "$HOME/bin/code-context"
chmod +x "$HOME/bin/code-context"

# 4. 安装 npm 依赖
echo ""
echo "📦 安装 npm 依赖..."
if command -v npm &> /dev/null; then
    npm install -g claude-context gitnexus 2>/dev/null || {
        echo "⚠️ npm 依赖安装失败（可选）"
        echo "   可以稍后手动执行: npm install -g claude-context gitnexus"
    }
else
    echo "⚠️ npm 未安装，跳过"
fi

# 5. 初始化
echo ""
echo "🔧 初始化..."
export PATH="$HOME/bin:$PATH"
code-context status

echo ""
echo "============================================"
echo "  安装完成！"
echo "============================================"
echo ""
echo "快速开始："
echo "  code-context status    # 查看状态"
echo "  code-context index     # 建立索引"
echo "  code-context search    # 搜索代码"
echo ""
echo "别忘了将 skills/SKILL.md 添加到你的 AI 项目规范中。"
echo ""
