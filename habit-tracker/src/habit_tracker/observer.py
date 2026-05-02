"""
HabitObserver: Extracts habits from interactions.

This module analyzes interactions between human and AI to identify
recurring patterns that become "habits".
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .models import (
    Habit, HabitSource, HabitType, HabitPriority,
    Interaction, HabitSuggestion
)


# Patterns that indicate specific habit types
HUMAN_HABIT_PATTERNS = {
    # Communication patterns
    (r"(?i)直接说|别绕弯|直说",): HabitType.COMMUNICATION_STYLE,
    (r"(?i)能帮忙|可以.*吗|能否",): HabitType.COMMUNICATION_STYLE,
    
    # Red lines
    (r"(?i)不要删|别删|禁止删",): HabitType.RED_LINE,
    (r"(?i)必须确认|先问|需要批准",): HabitType.RED_LINE,
    (r"(?i)不要.*commit|不要.*push",): HabitType.RED_LINE,
    
    # Technical preferences
    (r"(?i)用.*不用|不要.*用",): HabitType.TECHNICAL_PREFERENCE,
    (r"(?i)需要.*测试|要写测试",): HabitType.TECHNICAL_PREFERENCE,
    (r"(?i)不要.*依赖|别加.*库",): HabitType.TECHNICAL_PREFERENCE,
    
    # Decision patterns
    (r"(?i)给我.*选项|列出.*方案",): HabitType.DECISION_PATTERN,
    (r"(?i)你决定|你来选",): HabitType.DECISION_PATTERN,
    (r"(?i)质量优先|慢慢改",): HabitType.DECISION_PATTERN,
}

# AI behavior patterns
AI_HABIT_PATTERNS = {
    (r"(?i)我会|我来帮你",): HabitType.AI_BEHAVIOR,
    (r"(?i)根据.*习惯|按照.*偏好",): HabitType.AI_BEHAVIOR,
    
    # Failure patterns
    (r"(?i)抱歉|对不起|我错了",): HabitType.AI_FAILURE_MODE,
    (r"(?i)不确定|我需要更多信息",): HabitType.AI_CAPABILITY,
}


@dataclass
class ExtractedHabit:
    """A habit extracted from an interaction."""
    habit_type: HabitType
    name: str
    description: str
    confidence_boost: float  # How much this observation boosts confidence
    evidence_text: str


class HabitObserver:
    """
    Observes interactions and extracts habits.
    
    Usage:
        observer = HabitObserver()
        
        # Record an interaction
        observer.observe(Interaction(
            speaker="human",
            content="直接说，别绕弯",
            timestamp=datetime.now()
        ))
        
        # Get extracted habits
        habits = observer.extract_habits()
        
        # Get suggestions for human confirmation
        suggestions = observer.get_suggestions()
    """
    
    def __init__(self):
        self.interactions: List[Interaction] = []
        self.extracted_habits: Dict[str, ExtractedHabit] = {}
        self._pattern_cache: Dict[str, List[Habit]] = {}
    
    def observe(self, interaction: Interaction) -> List[ExtractedHabit]:
        """
        Observe an interaction and extract any habits.
        
        Returns list of newly extracted habits.
        """
        self.interactions.append(interaction)
        
        if interaction.speaker == "human":
            return self._observe_human(interaction)
        else:
            return self._observe_ai(interaction)
    
    def _observe_human(self, interaction: Interaction) -> List[ExtractedHabit]:
        """Extract habits from human's behavior."""
        extracted = []
        content = interaction.content
        
        for (patterns, habit_type) in HUMAN_HABIT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content):
                    habit = self._process_pattern_match(
                        interaction, habit_type, pattern, content
                    )
                    if habit:
                        extracted.append(habit)
        
        # Check for implicit patterns (longer interactions)
        if len(content) > 100:
            # Long detailed messages might indicate preference for thoroughness
            if "为什么" in content or "原因" in content:
                habit = ExtractedHabit(
                    habit_type=HabitType.DECISION_PATTERN,
                    name="explains_reason",
                    description="Asks for explanations before proceeding",
                    confidence_boost=0.1,
                    evidence_text=content[:100]
                )
                extracted.append(habit)
        
        # Update internal state
        for h in extracted:
            key = f"{h.habit_type.value}:{h.name}"
            self.extracted_habits[key] = h
        
        return extracted
    
    def _observe_ai(self, interaction: Interaction) -> List[ExtractedHabit]:
        """Extract habits from AI's behavior."""
        extracted = []
        
        # Check for common AI behavior patterns
        content = interaction.content
        
        # Check for apology/confession pattern (learning opportunity)
        if re.search(r"(?i)抱歉|对不起|我错了", content):
            habit = ExtractedHabit(
                habit_type=HabitType.AI_FAILURE_MODE,
                name="admits_mistakes",
                description="AI acknowledges errors when pointed out",
                confidence_boost=0.15,
                evidence_text=content[:100]
            )
            extracted.append(habit)
        
        # Check for asking clarification pattern
        if re.search(r"(?i)能再说一下|我需要确认|不确定", content):
            habit = ExtractedHabit(
                habit_type=HabitType.AI_CAPABILITY,
                name="asks_for_clarification",
                description="AI asks for clarification when uncertain",
                confidence_boost=0.1,
                evidence_text=content[:100]
            )
            extracted.append(habit)
        
        return extracted
    
    def _process_pattern_match(
        self, 
        interaction: Interaction, 
        habit_type: HabitType,
        pattern: str,
        content: str
    ) -> Optional[ExtractedHabit]:
        """Process a pattern match into an ExtractedHabit."""
        
        # Map patterns to habit names
        habit_names = {
            (r"(?i)直接说|别绕弯|直说",): "direct_communication",
            (r"(?i)不要删|别删|禁止删",): "no_delete_without_confirm",
            (r"(?i)必须确认|先问|需要批准",): "requires_approval",
            (r"(?i)用.*不用|不要.*用",): "tech_stack_preference",
            (r"(?i)需要.*测试|要写测试",): "testing_required",
            (r"(?i)给我.*选项|列出.*方案",): "wants_options",
            (r"(?i)质量优先|慢慢改",): "quality_over_speed",
        }
        
        name = None
        description = None
        
        for (p,) in habit_names:
            if p == pattern:
                name = habit_names[(p,)]
                break
        
        if name is None:
            return None
        
        # Generate description from content
        description = f"Observed from: '{content[:50]}...'"
        
        return ExtractedHabit(
            habit_type=habit_type,
            name=name,
            description=description,
            confidence_boost=0.2,
            evidence_text=content[:100]
        )
    
    def extract_habits(self) -> List[Habit]:
        """
        Convert extracted patterns into Habit objects.
        
        This is called periodically to create formal Habit records.
        """
        habits = []
        
        for key, extracted in self.extracted_habits.items():
            # Generate ID from name
            habit_id = f"{extracted.habit_type.value}_{extracted.name}_{datetime.now().strftime('%Y%m%d')}"
            
            habit = Habit(
                id=habit_id,
                subject="human",  # Default to human, can be modified
                type=extracted.habit_type,
                name=extracted.name,
                description=extracted.description,
                source=HabitSource.OBSERVATION,
                confidence=min(extracted.confidence_boost, 0.5)
            )
            habit.add_evidence(extracted.evidence_text)
            
            habits.append(habit)
        
        return habits
    
    def get_suggestions(self) -> List[HabitSuggestion]:
        """
        Get habit suggestions that need human confirmation.
        
        These are habits inferred by the AI that should be verified.
        """
        suggestions = []
        
        for key, extracted in self.extracted_habits.items():
            if extracted.confidence_boost >= 0.15:  # Threshold for suggestion
                suggestion = HabitSuggestion(
                    id=f"sug_{key}_{datetime.now().strftime('%H%M%S')}",
                    subject="human",
                    inferred_from=f"Pattern: {extracted.name}",
                    suggested_name=extracted.name,
                    suggested_type=extracted.habit_type,
                    suggested_description=extracted.description,
                    suggested_priority=HabitPriority.P1_IMPORTANT,
                    evidence=[extracted.evidence_text]
                )
                suggestions.append(suggestion)
        
        return suggestions
    
    def get_interaction_summary(self) -> Dict[str, Any]:
        """Get a summary of observed interactions."""
        human_count = sum(1 for i in self.interactions if i.speaker == "human")
        ai_count = sum(1 for i in self.interactions if i.speaker == "ai")
        
        return {
            "total_interactions": len(self.interactions),
            "human_interactions": human_count,
            "ai_interactions": ai_count,
            "extracted_habits": len(self.extracted_habits),
            "latest_interaction": self.interactions[-1].to_dict() if self.interactions else None
        }
