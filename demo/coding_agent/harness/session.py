"""
Session Management - Tree Structure
=================================

Mario Zechner's insight: "Session为树结构，非线性的聊天记录"

Unlike linear chat sessions (where each message follows the previous),
a tree structure allows:
- Branching: explore different approaches in parallel
- Backtracking: return to previous states
- History: see the full decision tree, not just the final path
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Message:
    """A single message in the session tree."""
    role: str  # "user", "assistant", "tool", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    parent_id: Optional[str] = None
    id: str = field(default_factory=lambda: f"msg_{id}")


class SessionNode:
    """
    A node in the session tree.

    Each node represents a state in the conversation.
    The tree structure allows non-linear exploration.
    """

    def __init__(self, message: Message):
        self.message = message
        self.id = message.id
        self.parent_id = message.parent_id
        self.children: list["SessionNode"] = []
        self.metadata: dict = {}

    def add_child(self, message: Message) -> "SessionNode":
        """Add a child message (branching)."""
        message.parent_id = self.id
        child = SessionNode(message)
        self.children.append(child)
        return child

    def get_path(self) -> list["SessionNode"]:
        """Get the path from root to this node."""
        path = []
        current = self
        while current:
            path.insert(0, current)
            current = session_db.get(current.parent_id) if current.parent_id else None
        return path

    def __repr__(self):
        return f"SessionNode({self.message.role}: {self.message.content[:30]}...)"


# Global session database (in production, would be persistent)
session_db: dict[str, SessionNode] = {}


class Session:
    """
    Session tree for non-linear conversation tracking.

    Mario Zechner's principle:
    - Linear sessions lose information (only final path visible)
    - Tree sessions preserve the full decision history

    Usage:
        session = Session()
        session.add_message("user", "Fix the login bug")
        session.add_message("assistant", "I'll investigate...")
        session.add_message("tool", "read file: auth.py")
        # Can branch here to try a different approach
        session.branch()
        session.add_message("assistant", "Alternative: check JWT...")
    """

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.root: Optional[SessionNode] = None
        self.current: Optional[SessionNode] = None
        self.branches: list[SessionNode] = []  # Branch points

    def add_message(self, role: str, content: str) -> SessionNode:
        """Add a message to the current path."""
        message = Message(role=role, content=content)

        if self.root is None:
            self.root = SessionNode(message)
            self.current = self.root
            session_db[self.current.id] = self.current
        else:
            self.current = self.current.add_child(message)
            session_db[self.current.id] = self.current

        return self.current

    def branch(self) -> SessionNode:
        """
        Create a branch point.

        After branching, new messages go down the new branch.
        The original branch is preserved for backtracking.
        """
        if self.current:
            self.branches.append(self.current)
        return self.current

    def backtrack(self) -> bool:
        """Move back to the parent node (branch point)."""
        if self.current and self.current.parent_id:
            self.current = session_db[self.current.parent_id]
            return True
        return False

    def get_tree_string(self, node: Optional[SessionNode] = None, indent: int = 0) -> str:
        """Get a string representation of the session tree."""
        if node is None:
            node = self.root
        if node is None:
            return "(empty session)"

        lines = []
        prefix = "  " * indent
        marker = "→" if node == self.current else " "
        lines.append(f"{marker}{prefix}[{node.message.role}] {node.message.content[:50]}...")

        for child in node.children:
            lines.append(self.get_tree_string(child, indent + 1))

        return "\n".join(lines)

    def summary(self) -> str:
        """Get a summary of the session."""
        if self.root is None:
            return "Empty session"

        # Count nodes
        total = len(session_db)
        branch_count = len(self.branches)

        return f"""Session '{self.session_id}':
  Total messages: {total}
  Branch points: {branch_count}
  Current depth: {len(self.current.get_path()) if self.current else 0}
  Structure:
{self.get_tree_string()}"""


class ToolCall:
    """Records a tool call for the session tree."""

    def __init__(self, tool_name: str, args: dict, result: str):
        self.tool_name = tool_name
        self.args = args
        self.result = result
        self.success = not result.startswith("Error:")
