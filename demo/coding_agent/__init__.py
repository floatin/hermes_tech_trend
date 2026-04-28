"""
Coding Agent Demo: Thin Harness, Fat Skills
============================================

This module implements the core concepts from:
- Garry Tan: "Thin Harness, Fat Skills"
- Mario Zechner: "写了17年开源代码，我为什么认为Coding Agents堆功能是在瞎折腾？"

The code demonstrates:
1. Thin Harness (~150 lines of core loop)
2. Fat Skills (markdown process files)
3. Resolver (context routing)
4. Minimal tools (read/write/edit/bash)
5. Latent vs Deterministic separation
"""

from .harness import ThinHarness
from .tools import MINIMAL_TOOLS

__all__ = ["ThinHarness", "MINIMAL_TOOLS"]
