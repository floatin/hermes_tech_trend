"""
Habit Tracker: Human-AI Collaborative Memory System
====================================================

A system for tracking and managing habits of both humans and AI agents
in a collaborative development environment.

Core Concepts:
- Habit: A observed pattern with confidence and priority
- HabitObserver: Extracts habits from interactions
- HabitValidator: Validates AI actions against known habits
- MemoryStorage: Persists habits (initially in-memory, extensible to MemPalace)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any
import json
import os

__version__ = "0.1.0"
