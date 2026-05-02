"""
Core data models for habit tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
import json


class HabitSource(Enum):
    """How a habit was discovered."""
    OBSERVATION = "observation"           # Observed from behavior
    HUMAN_DIRECT = "human_direct"         # Directly told by human
    AI_INFERENCE = "ai_inference"         # Inferred by AI
    FEEDBACK = "feedback"                 # From correction/feedback


class HabitPriority(Enum):
    """Habit priority levels."""
    P0_CRITICAL = 0   # Red lines - must follow
    P1_IMPORTANT = 1  # Important preferences
    P2_GENERAL = 2    # General habits


class HabitType(Enum):
    """Types of habits."""
    # Human habits about themselves
    COMMUNICATION_STYLE = "communication_style"
    TECHNICAL_PREFERENCE = "technical_preference"
    DECISION_PATTERN = "decision_pattern"
    WORKING_HABIT = "working_habit"
    RED_LINE = "red_line"
    
    # AI habits (from human's observation of AI)
    AI_BEHAVIOR = "ai_behavior"
    AI_FAILURE_MODE = "ai_failure_mode"
    AI_CAPABILITY = "ai_capability"


@dataclass
class Habit:
    """
    A habit is an observed pattern of behavior with confidence and priority.
    
    Attributes:
        id: Unique identifier
        subject: Who this habit belongs to ("human" or "ai-[name]")
        type: Category of habit
        name: Short name (e.g., "direct_communication", "no_delete_without_confirm")
        description: Human-readable description
        evidence: List of evidence/observations supporting this habit
        source: How this habit was discovered
        confidence: How confident we are (0.0 to 1.0)
        priority: P0/P1/P2
        created_at: When first observed
        updated_at: When last updated
        confirmed_at: When last confirmed by human
        confirmed_count: Number of times human confirmed
    """
    id: str
    subject: str                    # "human" or "ai-claude-code"
    type: HabitType
    name: str
    description: str
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    source: HabitSource = HabitSource.OBSERVATION
    confidence: float = 0.0
    priority: HabitPriority = HabitPriority.P2_GENERAL
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    confirmed_at: Optional[datetime] = None
    confirmed_count: int = 0
    tags: List[str] = field(default_factory=list)
    
    def add_evidence(self, observation: str, context: Optional[Dict] = None) -> None:
        """Add new evidence for this habit."""
        self.evidence.append({
            "observation": observation,
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        })
        self.updated_at = datetime.now()
        self._recalculate()
    
    def confirm(self) -> None:
        """Human confirmed this habit."""
        self.confirmed_count += 1
        self.confirmed_at = datetime.now()
        self._recalculate()
    
    def _recalculate(self) -> None:
        """Recalculate confidence and priority based on evidence and confirmations."""
        # Confidence: evidence * 0.15 + confirmations * 0.25 + recency bonus
        evidence_factor = min(len(self.evidence) * 0.15, 0.6)
        confirm_factor = min(self.confirmed_count * 0.25, 0.3)
        recency_bonus = 0.1
        self.confidence = min(evidence_factor + confirm_factor + recency_bonus, 0.95)
        
        # Priority based on confirmations
        if self.confirmed_count >= 3:
            self.priority = HabitPriority.P0_CRITICAL
        elif self.confirmed_count >= 1:
            self.priority = HabitPriority.P1_IMPORTANT
        else:
            self.priority = HabitPriority.P2_GENERAL
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "subject": self.subject,
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "evidence": self.evidence,
            "source": self.source.value,
            "confidence": self.confidence,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "confirmed_count": self.confirmed_count,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Habit":
        data = data.copy()
        data["type"] = HabitType(data["type"])
        data["source"] = HabitSource(data["source"])
        data["priority"] = HabitPriority(data["priority"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        if data.get("confirmed_at"):
            data["confirmed_at"] = datetime.fromisoformat(data["confirmed_at"])
        return cls(**data)


@dataclass
class Interaction:
    """
    A single interaction between human and AI.
    
    Used by HabitObserver to extract habits.
    """
    timestamp: datetime
    speaker: str                           # "human" or "ai"
    content: str
    action: Optional[str] = None           # What action was taken
    result: Optional[str] = None           # Outcome of the action
    context: Optional[Dict[str, Any]] = None
    feedback: Optional[str] = None        # Any feedback given
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "speaker": self.speaker,
            "content": self.content,
            "action": self.action,
            "result": self.result,
            "context": self.context,
            "feedback": self.feedback
        }


@dataclass 
class HabitSuggestion:
    """
    A suggested habit from AI inference, pending human confirmation.
    """
    id: str
    subject: str
    inferred_from: str                    # What interaction triggered this
    suggested_name: str
    suggested_type: HabitType
    suggested_description: str
    suggested_priority: HabitPriority
    evidence: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"              # pending/confirmed/rejected
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "subject": self.subject,
            "inferred_from": self.inferred_from,
            "suggested_name": self.suggested_name,
            "suggested_type": self.suggested_type.value,
            "suggested_description": self.suggested_description,
            "suggested_priority": self.suggested_priority.value,
            "evidence": self.evidence,
            "created_at": self.created_at.isoformat(),
            "status": self.status
        }
