"""
Thin Harness - The Core Agent Loop
==================================

Garry Tan's core insight: "The harness is the program that runs the LLM.
It does four things: runs the model in a loop, reads and writes your files,
manages context, and enforces safety. That's the 'thin'."

Mario Zechner's core insight: "200行就够了"

This implementation is ~150 lines of core loop logic.
"""

import os
from pathlib import Path
from typing import Optional

from .resolver import TransparentResolver, Context
from .session import Session
from .tools import execute_tool, MINIMAL_TOOLS, ToolTracer


# === Message types ===

class Message:
    """Base message class."""
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


class SystemMessage(Message):
    def __init__(self, content: str):
        super().__init__("system", content)


class UserMessage(Message):
    def __init__(self, content: str):
        super().__init__("user", content)


class AssistantMessage(Message):
    def __init__(self, content: str, tool_calls: Optional[list] = None):
        super().__init__("assistant", content)
        self.tool_calls = tool_calls or []


class ToolMessage(Message):
    def __init__(self, tool_name: str, args: dict, result: str):
        content = f"[Tool: {tool_name}]\nArgs: {args}\nResult: {result[:200]}..."
        super().__init__("tool", content)
        self.tool_name = tool_name
        self.args = args
        self.result = result


# === Skill loading ===

def load_skill(skill_path: str) -> dict:
    """
    Load a skill file (markdown format).

    Garry Tan's concept: Skill File is a reusable markdown procedure.
    It's not a prompt - it's a METHOD CALL with parameters.

    Example skill structure:
        # /skill_name
        Description...

        ## Parameters
        - TARGET: description
        - QUESTION: description

        ## Steps
        1. Step one...
        2. Step two...
    """
    try:
        path = Path(skill_path)
        if not path.exists():
            return {"error": f"Skill not found: {skill_path}"}

        content = path.read_text(encoding="utf-8")
        return parse_skill(content)
    except Exception as e:
        return {"error": str(e)}


def parse_skill(skill_content: str) -> dict:
    """Parse a skill markdown file into a structured dict."""
    lines = skill_content.strip().split("\n")

    # Extract skill name (first # heading)
    name = "unknown"
    for line in lines:
        if line.strip().startswith("#"):
            name = line.strip().lstrip("#").strip()
            break

    # Extract description (first paragraph after title)
    description = ""
    in_description = False
    for line in lines[1:]:
        if line.strip() and not line.strip().startswith("#"):
            description = line.strip()
            break

    # Extract parameters (lines like - TARGET: description)
    parameters = {}
    for line in lines:
        if line.strip().startswith("- ") and ":" in line:
            parts = line.strip()[2:].split(":", 1)
            if len(parts) == 2:
                parameters[parts[0].strip()] = parts[1].strip()

    return {
        "name": name,
        "description": description,
        "parameters": parameters,
        "raw": skill_content,
    }


def load_skills_from_dir(skills_dir: str) -> dict[str, dict]:
    """Load all skill files from a directory."""
    skills = {}
    skills_path = Path(skills_dir)

    if not skills_path.exists():
        return skills

    for skill_file in skills_path.glob("*.md"):
        skill = load_skill(str(skill_file))
        if "error" not in skill:
            skill_name = skill_file.stem
            skills[skill_name] = skill

    return skills


# === Thin Harness Core ===

class ThinHarness:
    """
    The thin harness - Garry Tan's architecture.

    ~150 lines of core loop that:
    1. Runs the model in a loop
    2. Reads and writes files
    3. Manages context
    4. Enforces safety

    The key principle: Skills are FAT (domain knowledge),
    Harness is THIN (just orchestration).
    """

    def __init__(
        self,
        skills_dir: str = "skills",
        model: str = "claude",
        system_prompt: Optional[str] = None,
    ):
        # CORE COMPONENTS - thin, focused
        self.resolver = TransparentResolver()
        self.session = Session()
        self.tracer = ToolTracer()

        # Skills are FAT - loaded from markdown files
        self.skills = load_skills_from_dir(skills_dir)

        # Tools are THIN - just 4 core tools
        self.available_tools = list(MINIMAL_TOOLS.keys())

        # System prompt is minimal
        self.system_prompt = system_prompt or self._build_system_prompt()

        # Model config
        self.model = model

        # Execution stats
        self.stats = {
            "total_calls": 0,
            "tool_calls": 0,
            "latent_calls": 0,
            "deterministic_calls": 0,
        }

    def _build_system_prompt(self) -> str:
        """
        Build minimal system prompt.

        Mario's insight: "主流agent中最短的system prompt"
        Model already knows it's a coding agent through RL training.
        """
        return f"""You are a coding agent with access to minimal tools.

AVAILABLE TOOLS (exactly 4):
{', '.join(self.available_tools)}

PRINCIPLES:
- Be precise and deterministic when possible
- Use tools for file operations and shell commands
- When uncertain, state what you don't know

TRANSPARENCY: All tool calls are logged and visible to the user."""

    def is_deterministic(self, task: str) -> bool:
        """
        Determine if a task is DETERMINISTIC or requires LATENT reasoning.

        Garry Tan's core insight: separate Latent from Deterministic.

        DETERMINISTIC: Same input → Same output (lookups, calculations)
        LATENT: Requires judgment, synthesis, reasoning (analysis, design)
        """
        task_lower = task.lower()

        # Clearly deterministic patterns
        deterministic_keywords = [
            "list", "show", "get", "find", "search",
            "count", "sum", "calculate", "compute",
            "read", "cat", "grep", "wc",
        ]

        # Clearly latent patterns (need judgment)
        latent_keywords = [
            "analyze", "investigate", "judge", "evaluate",
            "design", "architect", "suggest", "recommend",
            "compare", "assess", "review", "decide",
        ]

        for kw in deterministic_keywords:
            if kw in task_lower:
                return True

        for kw in latent_keywords:
            if kw in task_lower:
                return False

        # Default to latent (safer - don't over-confident in determinism)
        return False

    def run_deterministic(self, task: str) -> str:
        """
        Run a deterministic task WITHOUT LLM involvement.

        This is Garry Tan's principle: "Push execution DOWN into deterministic tooling"
        """
        self.stats["deterministic_calls"] += 1

        # Parse simple commands
        task_lower = task.lower().strip()

        if task_lower.startswith(("ls", "list")):
            # List files
            path = task_lower.split(" ", 1)[-1] if " " in task_lower else "."
            return execute_tool("bash", {"command": f"ls -la {path}"})

        elif any(task_lower.startswith(kw) for kw in ["cat ", "read ", "show "]):
            # Read file
            parts = task.split(" ", 1)
            if len(parts) > 1:
                return execute_tool("read", {"path": parts[1]})

        elif task_lower.startswith("find "):
            # Search files
            parts = task.split(" ", 1)
            if len(parts) > 1:
                return execute_tool("bash", {"command": f"find {parts[1]}"})

        # Default: use bash
        return execute_tool("bash", {"command": task})

    def run_latent(self, task: str) -> str:
        """
        Run a latent task requiring LLM judgment.

        This uses the full Thin Harness loop:
        1. Resolve context
        2. Execute tools
        3. Synthesize results
        """
        self.stats["latent_calls"] += 1

        # Step 1: Resolve context (who am I? what to load?)
        ctx = self.resolver.route(task)
        self.session.add_message("system", f"Task type: {ctx.task_type}")

        # Step 2: Build prompt with context
        prompt = self._build_prompt(task, ctx)

        # Step 3: Simulate LLM response (in production, call actual LLM)
        response = self._simulate_llm(prompt, ctx)

        return response

    def _build_prompt(self, task: str, ctx: Context) -> str:
        """Build the full prompt with context."""
        lines = [self.system_prompt, "", f"Task: {task}", ""]

        if ctx.documents:
            lines.append("CONTEXT:")
            for doc in ctx.documents:
                lines.append(f"--- {doc['path']} ---")
                lines.append(doc["content"])
            lines.append("")

        lines.append("Response:")
        return "\n".join(lines)

    def _simulate_llm(self, prompt: str, ctx: Context) -> str:
        """
        Simulate LLM response for demo.

        In production, this would call actual LLM API.
        """
        # For demo, we'll show what the LLM would see
        return f"""[Simulated LLM Response]

Based on the task type '{ctx.task_type}' and loaded context,
the LLM would analyze the request and potentially call tools.

In production, the LLM would return:
- Text response, and/or
- Tool calls (from the 4 minimal tools)

All tool executions are traced for transparency."""

    def run(self, task: str) -> str:
        """
        Main entry point - the thin harness loop.

        Determines: deterministic or latent?
        Then routes to appropriate handler.
        """
        self.stats["total_calls"] += 1
        self.session.add_message("user", task)

        print(f"\n{'='*60}")
        print(f"ThinHarness: {task[:50]}...")
        print(f"{'='*60}")

        if self.is_deterministic(task):
            print("→ Routing to DETERMINISTIC handler (no LLM)")
            result = self.run_deterministic(task)
        else:
            print("→ Routing to LATENT handler (LLM + tools)")
            result = self.run_latent(task)

        self.session.add_message("assistant", result)
        return result

    def run_with_skill(self, skill_name: str, parameters: dict) -> str:
        """
        Run a skill with parameters.

        Garry Tan's key insight: "Skill File works like a METHOD CALL"

        Same skill, different parameters = completely different capability.
        """
        if skill_name not in self.skills:
            return f"Error: Skill '{skill_name}' not found. Available: {list(self.skills.keys())}"

        skill = self.skills[skill_name]

        print(f"\n{'='*60}")
        print(f"Executing Skill: {skill_name}")
        print(f"Parameters: {parameters}")
        print(f"{'='*60}")

        # Build skill execution prompt
        prompt = self._build_skill_prompt(skill, parameters)

        # Run as latent task
        return self.run(prompt)

    def _build_skill_prompt(self, skill: dict, parameters: dict) -> str:
        """Build prompt from skill file with parameters."""
        lines = [
            f"Execute skill: {skill['name']}",
            f"Description: {skill['description']}",
            "",
            "Parameters:",
        ]

        for key, value in parameters.items():
            lines.append(f"  - {key}: {value}")

        lines.append("")
        lines.append("Skill Steps:")
        lines.append(skill["raw"])

        return "\n".join(lines)

    def get_stats(self) -> dict:
        """Get execution statistics."""
        return self.stats.copy()

    def summary(self) -> str:
        """Get full session summary."""
        return self.session.summary()
