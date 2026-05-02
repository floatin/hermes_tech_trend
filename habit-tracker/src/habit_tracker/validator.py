"""
HabitValidator: Validates AI actions against known habits.

This is the core mechanism for AI adapting to human preferences.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

from .models import Habit, HabitPriority, HabitType
from .storage import MemoryStorage


class ValidationResult(Enum):
    PASS = "pass"
    WARN = "warn"      # Should check, but not critical
    FAIL = "fail"      # Violates a P0 habit


@dataclass
class ActionCheck:
    """A check against a habit."""
    habit_id: str
    habit_name: str
    description: str
    result: ValidationResult
    message: str
    suggestion: Optional[str] = None


@dataclass
class ValidationReport:
    """Report of validating an action."""
    action: str
    passed: bool
    checks: List[ActionCheck]
    summary: str
    
    def has_warnings(self) -> bool:
        return any(c.result == ValidationResult.WARN for c in self.checks)
    
    def has_failures(self) -> bool:
        return any(c.result == ValidationResult.FAIL for c in self.checks)


# Patterns that might trigger habit checks
ACTION_PATTERNS = {
    # File deletion
    "delete_file": [
        (r"rm\s+", r"delete", r"unlink"),
    ],
    # Database changes
    "db_migration": [
        (r"migrate", r"alter\s+table", r"drop\s+table"),
    ],
    # New dependencies
    "new_dependency": [
        (r"pip\s+install", r"npm\s+install", r"go\s+get", r"cargo\s+add"),
    ],
    # Git operations
    "git_push": [
        (r"git\s+push", r"git\s+commit.*-m"),
    ],
    # Code changes
    "code_change": [
        (r"rewrite", r"refactor", r"change.*api"),
    ],
}


class HabitValidator:
    """
    Validates AI actions against known human habits.
    
    Usage:
        validator = HabitValidator(storage)
        
        # Before executing a potentially risky action
        report = validator.validate_action(
            action="rm -rf src/legacy",
            context={"files": ["src/legacy"]}
        )
        
        if report.has_failures():
            print(f"Cannot proceed: {report.summary}")
            # Ask human for confirmation
        elif report.has_warnings():
            print(f"Note: {report.summary}")
    """
    
    def __init__(self, storage: MemoryStorage):
        self.storage = storage
    
    def validate_action(
        self, 
        action: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationReport:
        """
        Validate an action against all relevant habits.
        
        Args:
            action: Description of the action being considered
            context: Additional context about the action
            
        Returns:
            ValidationReport with all checks
        """
        checks = []
        context = context or {}
        
        # Get P0 habits (red lines) for human
        p0_habits = self.storage.get_p0_habits(subject="human")
        
        for habit in p0_habits:
            check = self._check_habit(habit, action, context)
            if check:
                checks.append(check)
        
        # Check for action-specific patterns
        action_type = self._classify_action(action)
        if action_type:
            relevant_habits = self._get_relevant_habits(action_type)
            for habit in relevant_habits:
                check = self._check_habit(habit, action, context)
                if check:
                    checks.append(check)
        
        # Generate summary
        failures = [c for c in checks if c.result == ValidationResult.FAIL]
        warnings = [c for c in checks if c.result == ValidationResult.WARN]
        
        if failures:
            summary = f"Action violates {len(failures)} P0 habit(s)"
        elif warnings:
            summary = f"Action may conflict with {len(warnings)} preference(s)"
        else:
            summary = "Action OK"
        
        return ValidationReport(
            action=action,
            passed=len(failures) == 0,
            checks=checks,
            summary=summary
        )
    
    def _classify_action(self, action: str) -> Optional[str]:
        """Classify an action into a known type."""
        for action_type, patterns in ACTION_PATTERNS.items():
            for pattern_group in patterns:
                for pattern in pattern_group:
                    if re.search(pattern, action, re.IGNORECASE):
                        return action_type
        return None
    
    def _get_relevant_habits(self, action_type: str) -> List[Habit]:
        """Get habits relevant to an action type."""
        # Map action types to habit types
        type_map = {
            "delete_file": HabitType.RED_LINE,
            "new_dependency": HabitType.TECHNICAL_PREFERENCE,
            "code_change": HabitType.TECHNICAL_PREFERENCE,
        }
        
        habit_type = type_map.get(action_type)
        if habit_type:
            return self.storage.get_habits_by_type(habit_type)
        return []
    
    def _check_habit(
        self, 
        habit: Habit, 
        action: str, 
        context: Dict[str, Any]
    ) -> Optional[ActionCheck]:
        """Check if an action violates a habit."""
        
        # Check based on habit name
        if habit.name == "no_delete_without_confirm":
            if self._action_involves_deletion(action):
                return ActionCheck(
                    habit_id=habit.id,
                    habit_name=habit.name,
                    description=habit.description,
                    result=ValidationResult.FAIL,
                    message=f"Action involves deletion: '{action}'",
                    suggestion="Ask for confirmation before proceeding"
                )
        
        elif habit.name == "requires_approval":
            if self._action_needs_approval(action):
                return ActionCheck(
                    habit_id=habit.id,
                    habit_name=habit.name,
                    description=habit.description,
                    result=ValidationResult.FAIL,
                    message=f"Action requires approval: '{action}'",
                    suggestion="Get human approval before proceeding"
                )
        
        elif habit.name == "no_staging_push":
            if "staging" in action.lower() or "main" in action.lower():
                return ActionCheck(
                    habit_id=habit.id,
                    habit_name=habit.name,
                    description=habit.description,
                    result=ValidationResult.FAIL,
                    message="Direct push to main/staging is not allowed",
                    suggestion="Use a PR instead"
                )
        
        elif habit.name == "testing_required":
            if self._action_is_code_change(action):
                return ActionCheck(
                    habit_id=habit.id,
                    habit_name=habit.name,
                    description=habit.description,
                    result=ValidationResult.WARN,
                    message="Code change detected, tests may be required",
                    suggestion="Ensure tests are included or explain why not needed"
                )
        
        elif habit.name == "tech_stack_preference":
            # Check if new dependency conflicts with known preferences
            pass  # Complex pattern matching
        
        return None
    
    def _action_involves_deletion(self, action: str) -> bool:
        """Check if action involves deletion."""
        delete_patterns = [r"rm\s+", r"delete\s+", r"unlink\s+", r"rmdir\s+", r"drop\s+table"]
        return any(re.search(p, action, re.IGNORECASE) for p in delete_patterns)
    
    def _action_needs_approval(self, action: str) -> bool:
        """Check if action typically needs approval."""
        approval_patterns = [
            r"git\s+push\s+.*main",
            r"git\s+push\s+.*master", 
            r"deploy",
            r"drop\s+table",
            r"alter\s+table.*drop",
            r"force\s+push",
        ]
        return any(re.search(p, action, re.IGNORECASE) for p in approval_patterns)
    
    def _action_is_code_change(self, action: str) -> bool:
        """Check if action is a code change."""
        change_patterns = [r"edit\s+", r"change\s+", r"modify\s+", r"update\s+", r"refactor"]
        return any(re.search(p, action, re.IGNORECASE) for p in change_patterns)
    
    def check_before_action(self, action: str) -> bool:
        """
        Simple boolean check if action is allowed.
        
        Returns True if action passes all checks, False otherwise.
        """
        report = self.validate_action(action)
        return report.passed


class ContextFormatter:
    """
    Formats validation results for human consumption.
    """
    
    def __init__(self):
        self.emoji = {
            ValidationResult.PASS: "✅",
            ValidationResult.WARN: "⚠️",
            ValidationResult.FAIL: "❌",
        }
    
    def format_report(self, report: ValidationReport) -> str:
        """Format a validation report as a readable message."""
        lines = [
            f"# Action Validation: `{report.action}`",
            "",
            f"**Status**: {self.emoji[ValidationResult.PASS if report.passed else ValidationResult.FAIL]} {report.summary}",
            "",
        ]
        
        if report.checks:
            lines.append("## Checks")
            lines.append("")
            
            for check in report.checks:
                emoji = self.emoji[check.result]
                lines.append(f"{emoji} **{check.habit_name}**")
                lines.append(f"   {check.message}")
                if check.suggestion:
                    lines.append(f"   💡 Suggestion: {check.suggestion}")
                lines.append("")
        
        return "\n".join(lines)
