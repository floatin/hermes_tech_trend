#!/usr/bin/env python3
"""
Thin Harness, Fat Skills - Demo Runner
======================================

Demonstrates the core concepts from:
- Garry Tan: "Thin Harness, Fat Skills"
- Mario Zechner: "写了17年开源代码，我为什么认为Coding Agents堆功能是在瞎折腾？"

Run:
    python run_demo.py
"""

import sys
from pathlib import Path

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from harness import ThinHarness, MINIMAL_TOOLS, execute_tool, ToolTracer


def demo_minimal_tools():
    """Demonstrate Mario's 4 minimal tools."""
    print("\n" + "=" * 60)
    print("DEMO 1: Mario's Minimal Tools (4 tools, no more)")
    print("=" * 60)

    print("\nMario Zechner's insight: '不需要文件工具，不需要子agent，不需要联网搜索'")
    print(f"\nOur implementation has exactly {len(MINIMAL_TOOLS)} tools:")
    for tool in MINIMAL_TOOLS:
        print(f"  - {tool}")

    print("\n--- Tool Execution Demo ---")

    # Create a test file
    result = execute_tool("write", {"path": "/tmp/test.txt", "content": "Hello, Thin Harness!"})
    print(f"write: {result}")

    # Read it back
    result = execute_tool("read", {"path": "/tmp/test.txt"})
    print(f"read: {result}")

    # Edit it
    result = execute_tool("edit", {"path": "/tmp/test.txt", "old": "Hello", "new": "Greetings"})
    print(f"edit: {result}")

    # Bash
    result = execute_tool("bash", {"command": "cat /tmp/test.txt"})
    print(f"bash: {result}")

    print("\n✓ These 4 tools cover all file and system operations")


def demo_thin_harness():
    """Demonstrate the Thin Harness core."""
    print("\n" + "=" * 60)
    print("DEMO 2: Thin Harness (~150 lines of core loop)")
    print("=" * 60)

    print("\nGarry Tan's insight: 'The harness is the program that runs the LLM...'")
    print("It does four things: runs the model in a loop, reads and writes your files,")
    print("manages context, and enforces safety. That's the 'thin'.")

    # Create harness
    harness = ThinHarness(skills_dir="skills")

    print(f"\nHarness created with:")
    print(f"  - {len(harness.skills)} skills loaded")
    print(f"  - {len(harness.available_tools)} tools available")
    print(f"  - System prompt: {len(harness.system_prompt)} chars")

    # Show stats
    stats = harness.get_stats()
    print(f"\nInitial stats: {stats}")


def demo_latent_vs_deterministic():
    """Demonstrate Latent vs Deterministic separation."""
    print("\n" + "=" * 60)
    print("DEMO 3: Latent vs Deterministic Separation")
    print("=" * 60)

    print("\nGarry Tan's insight:")
    print("  - Latent space: where intelligence lives (LLM)")
    print("  - Deterministic: where trust lives (same input, same output)")

    harness = ThinHarness(skills_dir="skills")

    # Deterministic tasks
    print("\n--- Deterministic Tasks (no LLM needed) ---")
    tasks = [
        "list /tmp",
        "cat /tmp/test.txt",
        "find /tmp -name '*.txt'",
    ]

    for task in tasks:
        is_det = harness.is_deterministic(task)
        print(f"  '{task}' → {'DETERMINISTIC' if is_det else 'LATENT'}")

    # Run a deterministic task
    result = harness.run("list /tmp")
    print(f"\n  Result: {result[:100]}...")

    # Latent tasks
    print("\n--- Latent Tasks (requires LLM judgment) ---")
    tasks = [
        "Analyze the security implications of this code",
        "Design a better architecture for our system",
        "Should we hire this candidate?",
    ]

    for task in tasks:
        is_det = harness.is_deterministic(task)
        print(f"  '{task}' → {'DETERMINISTIC' if is_det else 'LATENT'}")


def demo_resolver():
    """Demonstrate Context Resolver."""
    print("\n" + "=" * 60)
    print("DEMO 4: Context Resolver (Transparent Routing)")
    print("=" * 60)

    print("\nGarry Tan's insight:")
    print("  'Skills say HOW. Resolver says WHAT to load WHEN.'")
    print("\nMario Zechner's insight:")
    print("  '无后台注入，所有上下文修改可追溯'")

    from harness import TransparentResolver

    resolver = TransparentResolver()

    # Test routing
    tasks = [
        "investigate a potential data breach",
        "refactor the authentication module",
        "architect a new microservices system",
    ]

    print("\n--- Routing Examples ---")
    for task in tasks:
        print(f"\nTask: '{task}'")
        ctx = resolver.route(task)
        print(f"  → Loaded {len(ctx.documents)} documents for type '{ctx.task_type}'")

    # Show transparency
    print("\n--- Full Routing History (for debugging) ---")
    history = resolver.get_routing_history()
    for i, entry in enumerate(history, 1):
        print(f"  {i}. {entry['task'][:40]}... → {entry['task_type']}")
        print(f"     Files: {entry['loaded_files']}")


def demo_skill_file():
    """Demonstrate Skill File as method call."""
    print("\n" + "=" * 60)
    print("DEMO 5: Skill File = Method Call with Parameters")
    print("=" * 60)

    print("\nGarry Tan's KEY insight:")
    print("  'A skill file works like a METHOD CALL.'")
    print("  'It takes parameters. You invoke it with different arguments.'")
    print("  'The same procedure produces RADICALLY DIFFERENT capabilities.'")

    harness = ThinHarness(skills_dir="skills")

    print(f"\n{harness.skills['investigate']['name']}")
    print(f"Description: {harness.skills['investigate']['description']}")
    print(f"Parameters: {harness.skills['investigate']['parameters']}")

    print("\n--- Same Skill, Different Parameters ---")
    print("\n  Invocation 1 (医学研究分析师):")
    print("    /investigate TARGET='Dr. Sarah Chen' QUESTION='研究是否被噤声' DATASET='./emails/'")

    print("\n  Invocation 2 (取证调查员):")
    print("    /investigate TARGET='Pacific Corp' QUESTION='是否协调捐款' DATASET='./fec/'")

    print("\n  Invocation 3 (合规审计员):")
    print("    /investigate TARGET='Acme Corp' QUESTION='是否合规' DATASET='./regulatory/'")


def demo_session_tree():
    """Demonstrate non-linear session tree."""
    print("\n" + "=" * 60)
    print("DEMO 6: Non-Linear Session Tree")
    print("=" * 60)

    print("\nMario Zechner's insight:")
    print("  'Session为树结构，非线性的聊天记录'")

    from harness import Session

    session = Session()

    # Build a conversation tree
    session.add_message("user", "Fix the login bug")
    session.add_message("assistant", "I'll investigate the auth module...")
    session.add_message("tool", "Reading auth.py...")

    # Branch 1: Hypothesis A
    print("\n--- Branching: Try Hypothesis A ---")
    session.branch()
    session.add_message("assistant", "Hypothesis A: JWT token expiry issue")
    session.add_message("tool", "Found: token refreshed every 30s without persistence")

    # Branch 2: Backtrack and try Hypothesis B
    print("\n--- Backtrack: Try Hypothesis B ---")
    session.backtrack()
    session.branch()
    session.add_message("assistant", "Hypothesis B: Session cookie not set properly")
    session.add_message("tool", "Confirmed: SameSite=Strict blocking cross-origin")

    print("\n" + session.summary())


def demo_transparency():
    """Demonstrate full transparency."""
    print("\n" + "=" * 60)
    print("DEMO 7: Full Transparency (No Hidden Operations)")
    print("=" * 60)

    print("\nMario Zechner's warning:")
    print("  '当你发现AI在背地里偷偷修改你的上下文，而你却对此一无所知时,'")
    print("  '这种掌控感的丧失是极其危险的。'")

    tracer = ToolTracer()

    # Execute some tools with tracing
    execute_tool("write", {"path": "/tmp/demo.txt", "content": "test"})
    tracer.trace("write", {"path": "/tmp/demo.txt", "content": "test"}, "Success: 4 bytes")

    execute_tool("read", {"path": "/tmp/demo.txt"})
    tracer.trace("read", {"path": "/tmp/demo.txt"}, "test")

    execute_tool("bash", {"command": "echo hello"})
    tracer.trace("bash", {"command": "echo hello"}, "hello")

    print(tracer.summary())


def demo_fat_skills_vs_thin():
    """Compare Fat Skills vs Fat Harness."""
    print("\n" + "=" * 60)
    print("DEMO 8: Fat Skills vs Fat Harness (The Key Insight)")
    print("=" * 60)

    print("\n❌ FAT HARNESS, THIN SKILLS (Anti-pattern)")
    print("   Mario: '功能多得像宇宙飞船，90%是无人知晓的暗物质'")
    print("   Example: Claude Code with 40+ tools")

    fat_harness_tools = [
        "read", "write", "edit", "bash",
        "web_search", "web_fetch", "browser_open", "browser_click", "browser_type",
        "code_search", "git_log", "git_diff", "git_status", "git_blame",
        "db_query", "db_insert", "db_update", "db_delete",
        "file_tree", "file_glob", "file_watch", "file_hash",
        "subagent_spawn", "subagent_result", "subagent_kill",
        "eval_run", "eval_result", "eval_compare",
        "context_expand", "context_shrink", "context_search", "context_summary",
        # ... 40+ total
    ]

    print(f"\n   Tools count: {len(fat_harness_tools)}")
    print("   Problems:")
    print("     - Context window flooded")
    print("     - Model attention scattered")
    print("     - 'Dark matter' features nobody knows")
    print("     - Hidden state modifications")

    print("\n✓ THIN HARNESS, FAT SKILLS (Garry + Mario's pattern)")
    print("   Example: Our implementation")

    thin_harness_tools = ["read", "write", "edit", "bash"]
    skills = ["investigate.md", "enrich.md", "match.md"]

    print(f"\n   Tools count: {len(thin_harness_tools)} (4)")
    print(f"   Skills count: {len(skills)} (extensible)")
    print("   Benefits:")
    print("     - Minimal context footprint")
    print("     - Skills provide domain knowledge")
    print("     - Same tools, different skills = different capabilities")
    print("     - Full transparency")


def main():
    print("=" * 60)
    print("Thin Harness, Fat Skills - Demo Suite")
    print("=" * 60)
    print("\nDemonstrating concepts from:")
    print("  1. Garry Tan: 'Thin Harness, Fat Skills'")
    print("  2. Mario Zechner: '堆功能是在瞎折腾'")
    print()

    demos = [
        ("Minimal Tools (Mario's 4 tools)", demo_minimal_tools),
        ("Thin Harness Core", demo_thin_harness),
        ("Latent vs Deterministic", demo_latent_vs_deterministic),
        ("Context Resolver", demo_resolver),
        ("Skill File = Method Call", demo_skill_file),
        ("Non-Linear Session Tree", demo_session_tree),
        ("Full Transparency", demo_transparency),
        ("Fat Skills vs Thin", demo_fat_skills_vs_thin),
    ]

    if len(sys.argv) > 1:
        # Run specific demo
        idx = int(sys.argv[1]) - 1
        if 0 <= idx < len(demos):
            demos[idx][1]()
        else:
            print(f"Invalid demo number. Choose 1-{len(demos)}")
    else:
        # Run all demos
        for i, (name, func) in enumerate(demos, 1):
            try:
                func()
            except Exception as e:
                print(f"\n  [Error in demo {i}]: {e}")

    print("\n" + "=" * 60)
    print("All demos completed!")
    print("=" * 60)

    print("\nKey Takeaways:")
    print("  1. Tools should be minimal (4), skills should be fat")
    print("  2. Latent/Deterministic separation is critical")
    print("  3. Context routing should be transparent")
    print("  4. Skill files are method calls with parameters")
    print("  5. Session tree > linear chat for complex tasks")


if __name__ == "__main__":
    main()
