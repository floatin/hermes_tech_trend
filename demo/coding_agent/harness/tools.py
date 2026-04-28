"""
Minimal Tools Implementation
============================

Mario Zechner's core insight: "不需要文件工具，不需要子agent，不需要联网搜索"

We implement exactly 4 tools:
- read: Read file contents
- write: Write content to file
- edit: Edit specific parts of a file
- bash: Execute shell commands

These 4 tools are sufficient for all coding agent tasks.
Extension capabilities come from Fat Skills, not more tools.
"""

import subprocess
from pathlib import Path
from typing import Any


def read(path: str) -> str:
    """
    Read file contents.

    This is a DETERMINISTIC operation: same input (path) → same output (content)
    No LLM involvement needed.
    """
    try:
        file_path = Path(path).expanduser()
        if not file_path.exists():
            return f"Error: File not found: {path}"
        return file_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading {path}: {e}"


def write(path: str, content: str) -> str:
    """
    Write content to file.

    DETERMINISTIC: Creates parent dirs, overwrites existing.
    """
    try:
        file_path = Path(path).expanduser()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return f"Successfully wrote to {path} ({len(content)} bytes)"
    except Exception as e:
        return f"Error writing {path}: {e}"


def edit(path: str, old: str, new: str) -> str:
    """
    Edit a file by replacing 'old' string with 'new' string.

    DETERMINISTIC: Simple text replacement with validation.
    """
    try:
        file_path = Path(path).expanduser()
        if not file_path.exists():
            return f"Error: File not found: {path}"

        content = file_path.read_text(encoding="utf-8")

        if old not in content:
            return f"Error: Could not find the specified text in {path}"

        new_content = content.replace(old, new, 1)  # Replace first occurrence only
        file_path.write_text(new_content, encoding="utf-8")

        return f"Successfully edited {path}"
    except Exception as e:
        return f"Error editing {path}: {e}"


def bash(command: str) -> str:
    """
    Execute shell command and return output.

    DETERMINISTIC: Same command → same output (ignoring timing).
    Security: Should be sandboxed in production.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout if result.stdout else ""
        error = result.stderr if result.stderr else ""

        if result.returncode != 0:
            return f"[Exit code: {result.returncode}]\n{error}\n{output}".strip()
        return output.strip() if output else "Command executed successfully (no output)"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds"
    except Exception as e:
        return f"Error executing command: {e}"


# Tool registry - exactly 4 tools, no more
# Mario's principle: extension through Skills, not more tools
MINIMAL_TOOLS = {
    "read": read,
    "write": write,
    "edit": edit,
    "bash": bash,
}


def execute_tool(tool_name: str, args: dict) -> str:
    """
    Execute a tool by name with given arguments.

    This is the ONLY entry point for tool execution.
    All tools are deterministic operations.
    """
    if tool_name not in MINIMAL_TOOLS:
        available = ", ".join(MINIMAL_TOOLS.keys())
        return f"Error: Unknown tool '{tool_name}'. Available tools: {available}"

    tool_func = MINIMAL_TOOLS[tool_name]

    # Validate required arguments for each tool
    if tool_name == "read" and "path" not in args:
        return "Error: 'read' requires 'path' argument"
    elif tool_name == "write" and not all(k in args for k in ["path", "content"]):
        return "Error: 'write' requires 'path' and 'content' arguments"
    elif tool_name == "edit" and not all(k in args for k in ["path", "old", "new"]):
        return "Error: 'edit' requires 'path', 'old', and 'new' arguments"
    elif tool_name == "bash" and "command" not in args:
        return "Error: 'bash' requires 'command' argument"

    return tool_func(**args)


# === Tracing for observability (Mario's transparency principle) ===

class ToolExecution:
    """Records a single tool execution for traceability."""

    def __init__(self, tool_name: str, args: dict, result: str):
        self.tool_name = tool_name
        self.args = args
        self.result = result
        self.success = not result.startswith("Error:")

    def __repr__(self):
        status = "✓" if self.success else "✗"
        return f"[{status}] {self.tool_name}({self.args}) → {self.result[:50]}..."


class ToolTracer:
    """
    Records all tool executions for transparency.

    Mario Zechner's principle: "当你发现AI在背地里偷偷修改你的上下文，
    而你却对此一无所知时，这种掌控感的丧失是极其危险的。"

    This tracer ensures NO hidden operations - everything is logged.
    """

    def __init__(self):
        self.executions: list[ToolExecution] = []

    def trace(self, tool_name: str, args: dict, result: str):
        execution = ToolExecution(tool_name, args, result)
        self.executions.append(execution)
        print(f"  → {execution}")

    def summary(self) -> str:
        if not self.executions:
            return "No tools executed."

        lines = ["\n=== Tool Execution Summary ==="]
        lines.append(f"Total executions: {len(self.executions)}")
        successful = sum(1 for e in self.executions if e.success)
        lines.append(f"Successful: {successful}/{len(self.executions)}")
        lines.append("\nAll executions:")
        for i, e in enumerate(self.executions, 1):
            lines.append(f"  {i}. {e}")
        return "\n".join(lines)
