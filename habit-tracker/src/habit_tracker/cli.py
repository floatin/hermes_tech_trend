#!/usr/bin/env python3
"""
Habit Tracker CLI

Command-line interface for the Human-AI Collaborative Memory System.
"""

import argparse
import sys
import json
from datetime import datetime
from typing import Optional

from .models import Interaction, HabitPriority, HabitType, HabitSource
from .observer import HabitObserver
from .storage import MemoryStorage
from .validator import HabitValidator, ContextFormatter


def cmd_observe(args, storage: MemoryStorage, observer: HabitObserver):
    """Observe a new interaction."""
    interaction = Interaction(
        timestamp=datetime.now(),
        speaker=args.speaker,
        content=args.content,
        action=args.action,
        feedback=args.feedback,
        context={"source": "cli"}
    )
    
    extracted = observer.observe(interaction)
    
    if extracted:
        print(f"✅ Observed {len(extracted)} pattern(s):")
        for e in extracted:
            print(f"   - {e.habit_type.value}: {e.name}")
    else:
        print("📝 Interaction recorded (no patterns detected)")
    
    # Show interaction summary
    summary = observer.get_interaction_summary()
    print(f"\n📊 Session stats: {summary['human_interactions']} human, {summary['ai_interactions']} AI interactions")


def cmd_validate(args, storage: MemoryStorage, validator: HabitValidator):
    """Validate an action against known habits."""
    report = validator.validate_action(args.action, {"source": "cli"})
    formatter = ContextFormatter()
    print(formatter.format_report(report))


def cmd_habits(args, storage: MemoryStorage):
    """List and manage habits."""
    if args.list_all:
        habits = storage.get_all_habits()
        print(f"\n📋 All Habits ({len(habits)} total)\n")
        
        for h in sorted(habits, key=lambda x: (x.priority.value, -x.confidence)):
            priority_emoji = "🔴" if h.priority == HabitPriority.P0_CRITICAL else "🟡" if h.priority == HabitPriority.P1_IMPORTANT else "⚪"
            print(f"{priority_emoji} [{h.subject}] {h.name}")
            print(f"   {h.description}")
            print(f"   Confidence: {h.confidence:.0%} | Evidence: {len(h.evidence)} | Confirmed: {h.confirmed_count}x")
            print()
    
    elif args.p0:
        habits = storage.get_p0_habits()
        print(f"\n🔴 P0 Red Lines ({len(habits)} total)\n")
        for h in habits:
            print(f"   ⛔ {h.name}: {h.description}")
        print()
    
    elif args.add:
        # Add a habit directly
        from .models import Habit
        priority = HabitPriority(args.priority) if hasattr(args, 'priority') else HabitPriority.P2_GENERAL
        habit = Habit(
            id=f"manual_{args.add.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            subject="human",
            type=HabitType.TECHNICAL_PREFERENCE if "tech" in args.add else HabitType.DECISION_PATTERN,
            name=args.add.replace(' ', '_').lower(),
            description=args.add,
            source=HabitSource.HUMAN_DIRECT,
            confidence=1.0,
            priority=priority
        )
        habit.confirm()
        storage.save_habit(habit)
        print(f"✅ Added habit: {habit.name}")
    
    elif args.delete:
        if storage.delete_habit(args.delete):
            print(f"🗑️  Deleted habit: {args.delete}")
        else:
            print(f"❌ Habit not found: {args.delete}")


def cmd_suggestions(args, storage: MemoryStorage):
    """Manage habit suggestions."""
    suggestions = storage.get_pending_suggestions()
    
    if not suggestions:
        print("✅ No pending suggestions")
        return
    
    print(f"\n💡 Pending Suggestions ({len(suggestions)})\n")
    
    for i, s in enumerate(suggestions, 1):
        print(f"{i}. {s.suggested_name}")
        print(f"   Type: {s.suggested_type.value}")
        print(f"   Evidence: {s.evidence[0][:80] if s.evidence else 'N/A'}...")
        print()
    
    print("Use 'suggestions confirm <id>' or 'suggestions reject <id>'")


def cmd_export(args, storage: MemoryStorage):
    """Export habits to various formats."""
    if args.format == "mempalace":
        data = storage.export_to_mempalace_format()
        print(data["content"])
        
        if args.file:
            with open(args.file, 'w') as f:
                f.write(data["content"])
            print(f"\n✅ Exported to {args.file}")
    
    elif args.format == "json":
        habits = storage.get_all_habits()
        print(json.dumps([h.to_dict() for h in habits], indent=2, ensure_ascii=False))


def cmd_summary(args, storage: MemoryStorage):
    """Show summary of stored data."""
    summary = storage.get_summary()
    
    print("\n📊 Habit Tracker Summary")
    print("=" * 40)
    print(f"   Storage: {summary['storage_dir']}")
    print(f"   Total Habits: {summary['total_habits']}")
    print(f"   Human Habits: {summary['human_habits']}")
    print(f"   AI Habits: {summary['ai_habits']}")
    print(f"   🔴 P0 Red Lines: {summary['p0_habits']}")
    print(f"   💡 Pending Suggestions: {summary['pending_suggestions']}")
    print()


def cmd_identity(args, storage: MemoryStorage):
    """Manage human identity."""
    config = storage.get_config()
    
    if args.name:
        config["human_name"] = args.name
        storage.update_config(config)
        print(f"✅ Updated human name: {args.name}")
    
    if args.set_ai:
        config["ai_name"] = args.set_ai
        storage.update_config(config)
        print(f"✅ Updated AI name: {args.set_ai}")
    
    if not args.name and not args.set_ai:
        print(f"\n👤 Human: {config.get('human_name', 'Unknown')}")
        print(f"🤖 AI: {config.get('ai_name', 'Unknown')}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Human-AI Collaborative Memory System",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # observe command
    observe_parser = subparsers.add_parser("observe", help="Observe an interaction")
    observe_parser.add_argument("speaker", choices=["human", "ai"], help="Who is speaking")
    observe_parser.add_argument("content", help="The content of the interaction")
    observe_parser.add_argument("--action", help="Action taken")
    observe_parser.add_argument("--feedback", help="Feedback given")
    
    # validate command
    validate_parser = subparsers.add_parser("validate", help="Validate an action")
    validate_parser.add_argument("action", help="Action to validate")
    
    # habits command
    habits_parser = subparsers.add_parser("habits", help="Manage habits")
    habits_parser.add_argument("--list-all", "-l", action="store_true", help="List all habits")
    habits_parser.add_argument("--p0", action="store_true", help="Show only P0 red lines")
    habits_parser.add_argument("--add", metavar="NAME", help="Add a new habit")
    habits_parser.add_argument("--priority", type=int, choices=[0, 1, 2], default=2, help="Priority: 0=P0, 1=P1, 2=P2")
    habits_parser.add_argument("--delete", metavar="ID", help="Delete a habit by ID")
    
    # suggestions command
    suggestions_parser = subparsers.add_parser("suggestions", help="Manage suggestions")
    
    # export command
    export_parser = subparsers.add_parser("export", help="Export habits")
    export_parser.add_argument("--format", choices=["mempalace", "json"], default="mempalace", help="Export format")
    export_parser.add_argument("--file", "-f", help="Output file (default: stdout)")
    
    # summary command
    summary_parser = subparsers.add_parser("summary", help="Show summary")
    
    # identity command
    identity_parser = subparsers.add_parser("identity", help="Manage identity")
    identity_parser.add_argument("--name", help="Set human name")
    identity_parser.add_argument("--set-ai", help="Set AI name")
    
    args = parser.parse_args()
    
    # Initialize storage and observer
    storage = MemoryStorage()
    observer = HabitObserver()
    validator = HabitValidator(storage)
    
    # Route commands
    if args.command == "observe":
        cmd_observe(args, storage, observer)
    elif args.command == "validate":
        cmd_validate(args, storage, validator)
    elif args.command == "habits":
        cmd_habits(args, storage)
    elif args.command == "suggestions":
        cmd_suggestions(args, storage)
    elif args.command == "export":
        cmd_export(args, storage)
    elif args.command == "summary":
        cmd_summary(args, storage)
    elif args.command == "identity":
        cmd_identity(args, storage)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
