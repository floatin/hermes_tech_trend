"""
Storage layer for habit memory.

Currently uses JSON file storage, designed to be extensible to MemPalace.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import asdict

from .models import Habit, HabitSuggestion, HabitSource, HabitPriority, HabitType


class MemoryStorage:
    """
    Persistent storage for habits and suggestions.
    
    Currently uses JSON files, but designed to be swapped with MemPalace
    or other backends.
    
    Storage Structure:
        ~/.habit-tracker/
            habits.json       # List of confirmed habits
            suggestions.json  # Pending habit suggestions
            interactions.json # Recent interactions (for context)
            config.json       # User configuration
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            self.storage_dir = Path.home() / ".habit-tracker"
        
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.habits_file = self.storage_dir / "habits.json"
        self.suggestions_file = self.storage_dir / "suggestions.json"
        self.interactions_file = self.storage_dir / "interactions.json"
        self.config_file = self.storage_dir / "config.json"
    
    # === Habit CRUD ===
    
    def save_habit(self, habit: Habit) -> None:
        """Save or update a habit."""
        habits = self.get_all_habits()
        
        # Update existing or add new
        existing_idx = None
        for i, h in enumerate(habits):
            if h.id == habit.id:
                existing_idx = i
                break
        
        if existing_idx is not None:
            habits[existing_idx] = habit
        else:
            habits.append(habit)
        
        self._save_habits(habits)
    
    def get_habit(self, habit_id: str) -> Optional[Habit]:
        """Get a habit by ID."""
        habits = self.get_all_habits()
        for h in habits:
            if h.id == habit_id:
                return h
        return None
    
    def get_all_habits(self) -> List[Habit]:
        """Get all habits."""
        if not self.habits_file.exists():
            return []
        
        with open(self.habits_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return [Habit.from_dict(h) for h in data]
    
    def delete_habit(self, habit_id: str) -> bool:
        """Delete a habit."""
        habits = self.get_all_habits()
        original_count = len(habits)
        habits = [h for h in habits if h.id != habit_id]
        
        if len(habits) < original_count:
            self._save_habits(habits)
            return True
        return False
    
    def _save_habits(self, habits: List[Habit]) -> None:
        """Save habits to file."""
        with open(self.habits_file, 'w', encoding='utf-8') as f:
            json.dump([h.to_dict() for h in habits], f, indent=2, ensure_ascii=False)
    
    # === Query methods ===
    
    def get_habits_by_subject(self, subject: str) -> List[Habit]:
        """Get all habits for a specific subject."""
        return [h for h in self.get_all_habits() if h.subject == subject]
    
    def get_habits_by_type(self, habit_type: HabitType) -> List[Habit]:
        """Get all habits of a specific type."""
        return [h for h in self.get_all_habits() if h.type == habit_type]
    
    def get_habits_by_priority(self, priority: HabitPriority) -> List[Habit]:
        """Get all habits of a specific priority."""
        return [h for h in self.get_all_habits() if h.priority == priority]
    
    def get_p0_habits(self, subject: str = "human") -> List[Habit]:
        """Get P0 (critical) habits for a subject."""
        habits = self.get_habits_by_subject(subject)
        return [h for h in habits if h.priority == HabitPriority.P0_CRITICAL]
    
    def search_habits(self, query: str, subject: Optional[str] = None) -> List[Habit]:
        """Search habits by name or description."""
        habits = self.get_all_habits()
        if subject:
            habits = [h for h in habits if h.subject == subject]
        
        query_lower = query.lower()
        return [
            h for h in habits
            if query_lower in h.name.lower() or query_lower in h.description.lower()
        ]
    
    # === Suggestions ===
    
    def save_suggestion(self, suggestion: HabitSuggestion) -> None:
        """Save a habit suggestion."""
        suggestions = self.get_all_suggestions()
        
        existing_idx = None
        for i, s in enumerate(suggestions):
            if s.id == suggestion.id:
                existing_idx = i
                break
        
        if existing_idx is not None:
            suggestions[existing_idx] = suggestion
        else:
            suggestions.append(suggestion)
        
        self._save_suggestions(suggestions)
    
    def get_all_suggestions(self) -> List[HabitSuggestion]:
        """Get all suggestions."""
        if not self.suggestions_file.exists():
            return []
        
        with open(self.suggestions_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return [HabitSuggestion(**s) for s in data]
    
    def get_pending_suggestions(self) -> List[HabitSuggestion]:
        """Get suggestions pending confirmation."""
        return [s for s in self.get_all_suggestions() if s.status == "pending"]
    
    def confirm_suggestion(self, suggestion_id: str) -> Optional[Habit]:
        """Confirm a suggestion, converting it to a habit."""
        suggestions = self.get_all_suggestions()
        
        for i, s in enumerate(suggestions):
            if s.id == suggestion_id:
                s.status = "confirmed"
                suggestions[i] = s
                self._save_suggestions(suggestions)
                
                # Create habit from suggestion
                habit = Habit(
                    id=f"habit_{s.suggested_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    subject=s.subject,
                    type=s.suggested_type,
                    name=s.suggested_name,
                    description=s.suggested_description,
                    source=HabitSource.HUMAN_DIRECT,
                    confidence=0.7,
                    priority=s.suggested_priority
                )
                habit.confirm()  # Human confirmed, so boost confidence
                self.save_habit(habit)
                
                return habit
        
        return None
    
    def reject_suggestion(self, suggestion_id: str) -> None:
        """Reject a suggestion."""
        suggestions = self.get_all_suggestions()
        
        for i, s in enumerate(suggestions):
            if s.id == suggestion_id:
                s.status = "rejected"
                suggestions[i] = s
                self._save_suggestions(suggestions)
                return
    
    def _save_suggestions(self, suggestions: List[HabitSuggestion]) -> None:
        """Save suggestions to file."""
        with open(self.suggestions_file, 'w', encoding='utf-8') as f:
            json.dump([s.to_dict() for s in suggestions], f, indent=2, ensure_ascii=False)
    
    # === Config ===
    
    def get_config(self) -> Dict[str, Any]:
        """Get configuration."""
        if not self.config_file.exists():
            return self._default_config()
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """Update configuration."""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration."""
        return {
            "version": "0.1.0",
            "human_name": "Developer",
            "ai_name": "claude-code",
            "auto_observe": True,
            "suggestion_threshold": 0.15,
            "auto_save_interval": 10,  # Save every N interactions
        }
    
    # === Utility ===
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of stored data."""
        habits = self.get_all_habits()
        suggestions = self.get_all_suggestions()
        
        human_habits = [h for h in habits if h.subject == "human"]
        ai_habits = [h for h in habits if h.subject.startswith("ai-")]
        
        return {
            "total_habits": len(habits),
            "human_habits": len(human_habits),
            "ai_habits": len(ai_habits),
            "p0_habits": len([h for h in human_habits if h.priority == HabitPriority.P0_CRITICAL]),
            "pending_suggestions": len([s for s in suggestions if s.status == "pending"]),
            "storage_dir": str(self.storage_dir)
        }
    
    def export_to_mempalace_format(self) -> Dict[str, Any]:
        """
        Export habits in a format suitable for MemPalace.
        
        This generates the markdown content for MemPalace's identity.txt
        and room structures.
        """
        habits = self.get_all_habits()
        human_habits = [h for h in habits if h.subject == "human"]
        
        # Group by type
        by_type: Dict[str, List[Habit]] = {}
        for h in human_habits:
            type_name = h.type.value
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append(h)
        
        # Generate MemPalace-style content
        lines = [
            "# Human Context",
            "",
            f"Generated: {datetime.now().isoformat()}",
            "",
        ]
        
        for habit_type, type_habits in sorted(by_type.items()):
            lines.append(f"## {habit_type.replace('_', ' ').title()}")
            for h in type_habits:
                priority_marker = "🔴" if h.priority == HabitPriority.P0_CRITICAL else "🟡" if h.priority == HabitPriority.P1_IMPORTANT else "⚪"
                lines.append(f"- {priority_marker} **{h.name}**: {h.description}")
            lines.append("")
        
        return {
            "content": "\n".join(lines),
            "habits": [h.to_dict() for h in human_habits],
            "format": "mempalace-compatible"
        }
    
    def clear_all(self) -> None:
        """Clear all stored data (use with caution!)."""
        for f in [self.habits_file, self.suggestions_file, self.interactions_file]:
            if f.exists():
                f.unlink()
