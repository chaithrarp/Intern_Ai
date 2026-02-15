"""
State Models - Interview Phases & Session State
================================================

Manages interview progression through phases instead of fixed question count.

Interview Flow:
Phase 1: Resume Deep Dive (2-3 questions)
Phase 2: Core Skill Assessment (3-4 questions)
Phase 3: Scenario/Problem Solving (2-3 questions)
Phase 4: Stress/Edge Case Testing (1-2 questions)
Phase 5: Claim Verification (adaptive)
Phase 6: Wrap-up (1 question)
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


# ============================================
# INTERVIEW PHASES
# ============================================

class InterviewPhase(str, Enum):
    """
    State-based interview phases
    
    Replace fixed "5 questions" with intelligent phase progression.
    """
    
    NOT_STARTED = "not_started"
    RESUME_DEEP_DIVE = "resume_deep_dive"           # Phase 1: Verify resume claims
    CORE_SKILL_ASSESSMENT = "core_skill_assessment" # Phase 2: Test fundamentals
    SCENARIO_SOLVING = "scenario_solving"           # Phase 3: Real-world problems
    STRESS_TESTING = "stress_testing"               # Phase 4: Pressure + edge cases
    CLAIM_VERIFICATION = "claim_verification"       # Phase 5: Follow up on vague claims
    WRAP_UP = "wrap_up"                             # Phase 6: Final question
    COMPLETED = "completed"


class RoundType(str, Enum):
    """
    Type of interview round (determines evaluation criteria)
    """
    HR = "hr"                       # STAR method, emotional intelligence
    TECHNICAL = "technical"         # Depth, accuracy, trade-offs
    SYSTEM_DESIGN = "system_design" # Architecture, scalability


# ============================================
# PHASE CONFIGURATION
# ============================================

class PhaseConfig(BaseModel):
    """
    Configuration for each interview phase
    
    Defines min/max questions, transition criteria, etc.
    """
    
    phase: InterviewPhase
    
    # Question Limits
    min_questions: int = Field(..., description="Minimum questions in this phase")
    max_questions: int = Field(..., description="Maximum questions in this phase")
    
    # Transition Criteria
    average_score_threshold: int = Field(
        60,
        description="Average score needed to progress (otherwise extend phase)"
    )
    
    # Round Type
    primary_round_type: RoundType = Field(..., description="Main evaluation style for this phase")
    
    # Phase Description
    description: str = Field(..., description="What this phase tests")
    
    # Interruption Settings
    interruption_probability: float = Field(
        0.3,
        ge=0.0,
        le=1.0,
        description="Base probability of interruption in this phase"
    )
    
    # Difficulty
    base_difficulty: str = Field(
        "medium",
        description="Starting difficulty for this phase"
    )


# Default phase configurations
DEFAULT_PHASE_CONFIGS = {
    InterviewPhase.RESUME_DEEP_DIVE: PhaseConfig(
        phase=InterviewPhase.RESUME_DEEP_DIVE,
        min_questions=2,
        max_questions=3,
        average_score_threshold=60,
        primary_round_type=RoundType.HR,
        description="Verify resume claims and establish baseline",
        interruption_probability=0.2,  # Low interruption early on
        base_difficulty="easy"
    ),
    
    InterviewPhase.CORE_SKILL_ASSESSMENT: PhaseConfig(
        phase=InterviewPhase.CORE_SKILL_ASSESSMENT,
        min_questions=3,
        max_questions=5,
        average_score_threshold=65,
        primary_round_type=RoundType.TECHNICAL,
        description="Test fundamental technical knowledge",
        interruption_probability=0.4,  # Moderate interruption
        base_difficulty="medium"
    ),
    
    InterviewPhase.SCENARIO_SOLVING: PhaseConfig(
        phase=InterviewPhase.SCENARIO_SOLVING,
        min_questions=2,
        max_questions=4,
        average_score_threshold=65,
        primary_round_type=RoundType.TECHNICAL,
        description="Real-world problem solving and debugging",
        interruption_probability=0.5,  # Higher interruption
        base_difficulty="medium"
    ),
    
    InterviewPhase.STRESS_TESTING: PhaseConfig(
        phase=InterviewPhase.STRESS_TESTING,
        min_questions=1,
        max_questions=2,
        average_score_threshold=60,
        primary_round_type=RoundType.SYSTEM_DESIGN,
        description="Pressure testing with edge cases",
        interruption_probability=0.7,  # High interruption
        base_difficulty="hard"
    ),
    
    InterviewPhase.CLAIM_VERIFICATION: PhaseConfig(
        phase=InterviewPhase.CLAIM_VERIFICATION,
        min_questions=0,  # Adaptive based on claims
        max_questions=3,
        average_score_threshold=70,
        primary_round_type=RoundType.TECHNICAL,
        description="Verify vague/suspicious claims from earlier",
        interruption_probability=0.6,
        base_difficulty="medium"
    ),
    
    InterviewPhase.WRAP_UP: PhaseConfig(
        phase=InterviewPhase.WRAP_UP,
        min_questions=1,
        max_questions=1,
        average_score_threshold=0,  # No threshold for final question
        primary_round_type=RoundType.HR,
        description="Final opportunity to shine",
        interruption_probability=0.1,  # Very low
        base_difficulty="medium"
    )
}


# ============================================
# SESSION STATE
# ============================================

class SessionState(BaseModel):
    """
    Complete interview session state
    
    This is the central state object shared across all components.
    Tracks everything happening in the interview.
    """
    
    # === IDENTIFICATION ===
    session_id: str = Field(..., description="Unique session identifier")
    user_id: Optional[str] = Field(None, description="User ID if authenticated")
    
    # === INTERVIEW PHASE ===
    current_phase: InterviewPhase = Field(
        default=InterviewPhase.NOT_STARTED,
        description="Current interview phase"
    )
    phases_completed: List[InterviewPhase] = Field(
        default_factory=list,
        description="Phases already completed"
    )
    
    # === RESUME CONTEXT ===
    resume_context: Optional[str] = Field(
        None,
        description="Parsed resume content for AI context"
    )
    resume_uploaded: bool = Field(False, description="Whether resume was provided")
    
    # === CONVERSATION HISTORY ===
    conversation_history: List[Dict] = Field(
        default_factory=list,
        description="Complete Q&A history with metadata"
    )
    
    # === CURRENT QUESTION ===
    current_question_id: Optional[str] = None
    current_question_text: Optional[str] = None
    current_round_type: Optional[RoundType] = None
    current_difficulty: str = Field(default="medium")
    
    # === EXTRACTED CLAIMS ===
    extracted_claims: List[Dict] = Field(
        default_factory=list,
        description="All claims extracted from answers"
    )
    unverified_claims: List[str] = Field(
        default_factory=list,
        description="Claims that need verification"
    )
    verified_claims: List[str] = Field(
        default_factory=list,
        description="Claims that have been verified"
    )
    
    # === SKILL TRACKING ===
    skill_scores: Dict[str, List[int]] = Field(
        default_factory=dict,
        description="Running scores for each skill dimension",
        example={
            "technical_depth": [70, 75, 82],
            "communication_clarity": [65, 68, 70]
        }
    )
    
    # === PERFORMANCE METRICS ===
    average_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Current average for each dimension"
    )
    
    overall_score_progression: List[int] = Field(
        default_factory=list,
        description="Overall score after each question"
    )
    
    # === INTERRUPTION TRACKING ===
    interruptions: List[Dict] = Field(
        default_factory=list,
        description="All interruptions that occurred"
    )
    total_interruptions: int = Field(0)
    max_interruptions: int = Field(5, description="Max interruptions allowed")
    
    # === PHASE PROGRESS ===
    questions_in_current_phase: int = Field(
        0,
        description="How many questions asked in current phase"
    )
    
    # === ADAPTIVE DIFFICULTY ===
    difficulty_level: int = Field(
        5,
        ge=1,
        le=10,
        description="Current difficulty level (1=easiest, 10=hardest)"
    )
    
    # === RED FLAGS ===
    red_flags: List[Dict] = Field(
        default_factory=list,
        description="Critical issues detected during interview",
        example=[
            {
                "type": "false_claim",
                "description": "Claimed 10M requests but couldn't explain caching",
                "question_id": "q_003"
            }
        ]
    )
    
    # === BEHAVIORAL METRICS ===
    total_filler_words: int = Field(0)
    total_long_pauses: int = Field(0)
    total_speaking_time: float = Field(0.0, description="Total seconds spent answering")
    
    # === METADATA ===
    started_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # === AI SETTINGS ===
    ai_powered: bool = Field(True)
    pressure_enabled: bool = Field(True)
    persona: Optional[str] = Field(None, description="Interviewer persona if selected")
    
    # === ADDITIONAL CONFIG ===
    config: Dict = Field(
        default_factory=dict,
        description="Custom configuration overrides"
    )
    
    
    # === HELPER METHODS ===
    
    def add_answer_scores(self, scores: Dict[str, int]):
        """Add scores from latest answer to running totals"""
        for dimension, score in scores.items():
            if dimension not in self.skill_scores:
                self.skill_scores[dimension] = []
            self.skill_scores[dimension].append(score)
    
    def calculate_average_scores(self) -> Dict[str, float]:
        """Calculate current average for each dimension"""
        averages = {}
        for dimension, scores in self.skill_scores.items():
            if scores:
                averages[dimension] = sum(scores) / len(scores)
        self.average_scores = averages
        return averages
    
    def get_phase_average_score(self, phase: InterviewPhase) -> float:
        """Get average score for a specific phase"""
        phase_questions = [
            item for item in self.conversation_history
            if item.get("phase") == phase.value
        ]
        
        if not phase_questions:
            return 0.0
        
        scores = [
            item.get("evaluation", {}).get("overall_score", 0)
            for item in phase_questions
        ]
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def should_transition_phase(self) -> bool:
        """
        Check if should transition to next phase
        """
        from config.evaluation_config import PHASE_TRANSITION_RULES
        
        config = PHASE_TRANSITION_RULES.get(self.current_phase.value)
        if not config:
            return False
        
        # Skip claim verification if no claims
        if self.current_phase == InterviewPhase.CLAIM_VERIFICATION:
            if config.get("skip_if_no_claims") and len(self.unverified_claims) == 0:
                return True
        
        # Force transition after max questions
        if self.questions_in_current_phase >= config["force_transition_after"]:
            return True
        
        # Minimum questions met?
        if self.questions_in_current_phase < config["min_questions"]:
            return False
        
        # Check if reached max
        if self.questions_in_current_phase >= config["max_questions"]:
            return True
        
        # ========================================
        # DEMO MODE FIX: If transition_score is 0, always transition
        # ========================================
        if config["transition_score"] == 0 and self.questions_in_current_phase >= config["min_questions"]:
            return True
        
        # Check average score in phase
        phase_avg = self.get_phase_average_score(self.current_phase)
        if phase_avg >= config["transition_score"] and config["transition_score"] > 0:
            return True
        
        return False
    
    def get_next_phase(self) -> InterviewPhase:
        """Determine next phase based on current state"""
        phase_order = [
            InterviewPhase.RESUME_DEEP_DIVE,
            InterviewPhase.CORE_SKILL_ASSESSMENT,
            InterviewPhase.SCENARIO_SOLVING,
            InterviewPhase.STRESS_TESTING,
            InterviewPhase.CLAIM_VERIFICATION,
            InterviewPhase.WRAP_UP,
            InterviewPhase.COMPLETED
        ]
        
        try:
            current_index = phase_order.index(self.current_phase)
            
            # Skip claim verification if no unverified claims
            if phase_order[current_index + 1] == InterviewPhase.CLAIM_VERIFICATION:
                if not self.unverified_claims:
                    return phase_order[current_index + 2]  # Skip to wrap-up
            
            return phase_order[current_index + 1]
        except (ValueError, IndexError):
            return InterviewPhase.COMPLETED
    
    def add_claim(self, claim: Dict):
        """Add extracted claim to state"""
        self.extracted_claims.append(claim)
        if claim.get("requires_verification"):
            self.unverified_claims.append(claim["claim_id"])
    
    def mark_claim_verified(self, claim_id: str):
        """Mark claim as verified"""
        if claim_id in self.unverified_claims:
            self.unverified_claims.remove(claim_id)
            self.verified_claims.append(claim_id)
    
    def add_red_flag(self, flag_type: str, description: str, question_id: str):
        """Add critical issue to red flags"""
        self.red_flags.append({
            "type": flag_type,
            "description": description,
            "question_id": question_id,
            "timestamp": datetime.now().isoformat()
        })
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()