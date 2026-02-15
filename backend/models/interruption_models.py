"""
Interruption Data Models
========================

Data classes for the intelligent interruption system
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum

# ============================================
# ENUMS
# ============================================

class InterruptionReason(Enum):
    """Reasons for interrupting the candidate"""
    # CRITICAL - Priority 1-3
    FALSE_CLAIM = "FALSE_CLAIM"
    CONTRADICTION = "CONTRADICTION"
    EXCESSIVE_PAUSING = "EXCESSIVE_PAUSING"
    
    # HIGH - Priority 4-6
    OFF_TOPIC = "OFF_TOPIC"
    DODGING_QUESTION = "DODGING_QUESTION"
    RAMBLING = "RAMBLING"
    
    # MEDIUM - Priority 7-9
    VAGUE_CLAIM = "VAGUE_CLAIM"
    LACK_OF_SPECIFICS = "LACK_OF_SPECIFICS"
    UNCERTAINTY = "UNCERTAINTY"
    
    # LOW - Priority 10
    SPEAKING_TOO_LONG = "SPEAKING_TOO_LONG"

class SeverityLevel(Enum):
    """Severity levels for interruptions"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ActionType(Enum):
    """Types of actions the system can take"""
    INTERRUPT = "interrupt"
    WARN = "warn"
    NONE = "none"


# ============================================
# INTERRUPTION DECISION
# ============================================

@dataclass
class InterruptionDecision:
    """
    Decision about whether to interrupt
    
    This is returned by the interruption_decision.py engine
    """
    
    should_interrupt: bool
    action: str  # "interrupt", "warn", or "none"
    
    # Reason for decision
    reason: Optional[str] = None
    priority: Optional[int] = None
    severity: Optional[str] = None
    
    # Evidence
    evidence: str = ""
    
    # Warning data (if action is WARN)
    warning_data: Optional[Dict] = None
    
    # Metadata
    triggered_at_seconds: float = 0
    warning_count: int = 0
    
    timestamp: datetime = field(default_factory=datetime.now)


# ============================================
# LIVE WARNING
# ============================================

@dataclass
class LiveWarning:
    """
    Real-time warning shown during recording
    """
    
    type: str  # Warning type
    message: str
    icon: str
    color: str
    severity: str
    evidence: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


# ============================================
# AUDIO METRICS
# ============================================

@dataclass
class AudioMetrics:
    """
    Audio analysis metrics from frontend
    """
    
    # Duration
    recording_duration: float
    
    # Pause analysis
    total_pauses: int = 0
    excessive_pause_count: int = 0
    average_pause_duration: float = 0
    
    # Speech patterns
    speech_rate: float = 0
    filler_word_count: int = 0
    
    # Confidence indicators
    hesitation_score: float = 0
    
    # Detected issues
    detected_issues: List[Dict] = field(default_factory=list)
    
    timestamp: datetime = field(default_factory=datetime.now)