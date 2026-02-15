"""
Interview Models - Questions, Answers, Claims
==============================================

Defines the core data structures for interview content:
- Questions with metadata
- Answers with transcripts
- Extracted claims for verification
- Claim verification results
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


# ============================================
# QUESTION MODEL
# ============================================

class QuestionType(str, Enum):
    """Type of interview question"""
    OPENING = "opening"
    RESUME_BASED = "resume_based"
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"
    SYSTEM_DESIGN = "system_design"
    CLAIM_VERIFICATION = "claim_verification"
    FOLLOWUP = "followup"
    STRESS_TEST = "stress_test"
    CLOSING = "closing"


class DifficultyLevel(str, Enum):
    """Question difficulty"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class Question(BaseModel):
    """
    Interview question with metadata
    
    Example:
        {
            "id": "q_001",
            "question_text": "Tell me about a time you optimized system performance.",
            "question_type": "behavioral",
            "round_type": "technical",
            "difficulty": "medium",
            "expected_elements": ["situation", "metrics", "approach", "results"],
            "follow_up_triggers": ["vague_metrics", "no_trade_offs"]
        }
    """
    
    # Identification
    id: str = Field(..., description="Unique question identifier")
    question_text: str = Field(..., description="The actual question")
    
    # Classification
    question_type: QuestionType = Field(..., description="Type of question")
    round_type: str = Field(..., description="Which round: hr, technical, system_design")
    difficulty: DifficultyLevel = Field(..., description="Question difficulty level")
    
    # Interview Phase
    phase: Optional[str] = Field(None, description="Which interview phase this belongs to")
    
    # Evaluation Criteria
    expected_elements: List[str] = Field(
        default_factory=list,
        description="What a good answer should include",
        example=["situation context", "specific actions", "measurable results", "trade-offs considered"]
    )
    
    # Context (for AI-generated questions)
    context: Optional[Dict] = Field(
        None,
        description="Additional context for question generation",
        example={
            "previous_claim": "I built a system handling 10M requests",
            "verification_needed": "How did you handle caching at that scale?"
        }
    )
    
    # Follow-up Logic
    follow_up_triggers: List[str] = Field(
        default_factory=list,
        description="What should trigger follow-up questions",
        example=["vague_metrics", "missing_trade_offs", "unrealistic_claims"]
    )
    
    # Metadata
    generated_by: str = Field(default="ai", description="ai or template")
    parent_question_id: Optional[str] = Field(None, description="If this is a follow-up, reference parent")
    created_at: datetime = Field(default_factory=datetime.now)


# ============================================
# ANSWER MODEL
# ============================================

class Answer(BaseModel):
    """
    Candidate's answer with metadata
    
    Stores both raw transcript and processed information.
    """
    
    # Identification
    id: str = Field(..., description="Unique answer identifier")
    question_id: str = Field(..., description="Which question this answers")
    session_id: str = Field(..., description="Interview session ID")
    
    # Content
    answer_text: str = Field(..., description="Full transcript of answer")
    
    # Audio Metadata
    recording_duration: float = Field(..., description="How long they spoke (seconds)")
    audio_file_path: Optional[str] = Field(None, description="Path to audio file")
    language: str = Field(default="en", description="Detected language")
    
    # Behavioral Metrics (from Whisper segments)
    filler_word_count: int = Field(0, description="Number of um, uh, like, etc")
    long_pause_count: int = Field(0, description="Pauses > 2 seconds")
    words_per_minute: float = Field(0, description="Speaking rate")
    hesitation_score: int = Field(0, ge=0, le=100, description="0=confident, 100=very hesitant")
    
    # Interruption Data
    was_interrupted: bool = Field(False, description="Was this answer interrupted?")
    interruption_reason: Optional[str] = Field(None, description="Why interrupted")
    interruption_time: Optional[float] = Field(None, description="When interrupted (seconds into answer)")
    
    # Extracted Information (populated by claim extractor)
    extracted_claims: List[str] = Field(
        default_factory=list,
        description="Claims made in this answer"
    )
    technologies_mentioned: List[str] = Field(
        default_factory=list,
        description="Technologies/tools mentioned"
    )
    metrics_mentioned: List[str] = Field(
        default_factory=list,
        description="Quantitative metrics mentioned"
    )
    achievements_claimed: List[str] = Field(
        default_factory=list,
        description="Achievements the candidate claimed"
    )
    
    # Evaluation (populated after scoring)
    evaluation: Optional[Dict] = Field(
        None,
        description="AnswerEvaluation data (populated after LLM evaluates)"
    )
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


# ============================================
# EXTRACTED CLAIM MODEL
# ============================================

class ClaimType(str, Enum):
    """Type of claim made by candidate"""
    TECHNICAL_ACHIEVEMENT = "technical_achievement"
    METRIC = "metric"
    TOOL_EXPERTISE = "tool_expertise"
    ROLE_RESPONSIBILITY = "role_responsibility"
    PROJECT_SCALE = "project_scale"
    PROBLEM_SOLVED = "problem_solved"
    ARCHITECTURE_DECISION = "architecture_decision"


class ClaimVerifiability(str, Enum):
    """How easy is this claim to verify?"""
    VERIFIABLE = "verifiable"       # Can ask specific follow-ups
    VAGUE = "vague"                 # Too vague to verify
    SUSPICIOUS = "suspicious"       # Seems unrealistic
    CONTRADICTORY = "contradictory" # Contradicts previous statements


class ExtractedClaim(BaseModel):
    """
    A claim extracted from candidate's answer
    
    Example:
        {
            "claim_id": "claim_001",
            "claim_text": "I optimized the database to handle 10 million requests per day",
            "claim_type": "project_scale",
            "source_question_id": "q_003",
            "source_answer_id": "a_003",
            "verifiability": "verifiable",
            "verification_questions": [
                "What caching strategy did you use?",
                "How did you handle database connection pooling?",
                "What was the bottleneck before optimization?"
            ],
            "requires_verification": true
        }
    """
    
    # Identification
    claim_id: str = Field(..., description="Unique claim identifier")
    claim_text: str = Field(..., description="The actual claim made")
    claim_type: ClaimType = Field(..., description="Type of claim")
    
    # Source Tracking
    source_question_id: str = Field(..., description="Which question prompted this claim")
    source_answer_id: str = Field(..., description="Which answer contains this claim")
    session_id: str = Field(..., description="Interview session")
    
    # Verification Status
    verifiability: ClaimVerifiability = Field(..., description="How verifiable is this?")
    requires_verification: bool = Field(..., description="Should we ask follow-up?")
    
    # Suggested Verification Questions
    verification_questions: List[str] = Field(
        default_factory=list,
        description="AI-generated follow-ups to verify this claim",
        example=[
            "What specific optimizations did you implement?",
            "What metrics improved and by how much?",
            "What trade-offs did you consider?"
        ]
    )
    
    # Verification Priority
    priority: int = Field(
        default=5,
        ge=1,
        le=10,
        description="How important to verify (1=low, 10=critical)"
    )
    
    # Red Flags
    red_flags: List[str] = Field(
        default_factory=list,
        description="Concerns about this claim",
        example=["No specific metrics provided", "Contradicts earlier answer about team size"]
    )
    
    # Verification Result (populated after follow-up)
    verification_result: Optional[Dict] = Field(
        None,
        description="Result of verification attempt"
    )
    
    # Timestamps
    extracted_at: datetime = Field(default_factory=datetime.now)
    verified_at: Optional[datetime] = None


# ============================================
# CLAIM VERIFICATION RESULT
# ============================================

class VerificationStatus(str, Enum):
    """Result of claim verification"""
    VERIFIED = "verified"           # Candidate provided satisfactory evidence
    PARTIALLY_VERIFIED = "partial"  # Some evidence but gaps remain
    UNVERIFIED = "unverified"       # Could not verify
    CONTRADICTED = "contradicted"   # Contradicted by follow-up answer


class ClaimVerification(BaseModel):
    """
    Result of verifying a claim through follow-up questions
    
    Tracks whether candidate could back up their initial claim.
    """
    
    claim_id: str = Field(..., description="Which claim was verified")
    verification_question_id: str = Field(..., description="Follow-up question asked")
    verification_answer_id: str = Field(..., description="Answer to follow-up")
    
    status: VerificationStatus = Field(..., description="Verification outcome")
    
    # Evidence
    supporting_evidence: List[str] = Field(
        default_factory=list,
        description="Evidence that supports the claim",
        example=["Provided specific Redis caching strategy", "Mentioned connection pool size of 100"]
    )
    
    missing_evidence: List[str] = Field(
        default_factory=list,
        description="What's still missing",
        example=["No mention of monitoring/alerting", "Vague about actual performance improvement"]
    )
    
    # Contradictions
    contradictions: List[str] = Field(
        default_factory=list,
        description="Statements that contradict the original claim",
        example=["Originally said 10M req/day, now says 1M req/day"]
    )
    
    # Impact on Evaluation
    credibility_impact: str = Field(
        ...,
        description="How this affects overall credibility",
        example="neutral"  # Options: positive, neutral, negative
    )
    
    notes: Optional[str] = Field(None, description="Additional observations")
    
    verified_at: datetime = Field(default_factory=datetime.now)


# ============================================
# CONVERSATION HISTORY ITEM
# ============================================

class ConversationItem(BaseModel):
    """
    Single Q&A pair in conversation history
    
    Used for building LLM context.
    """
    
    question: str
    answer: str
    question_id: str
    answer_id: str
    was_interrupted: bool = False
    evaluation_summary: Optional[str] = None  # Brief summary of how answer was scored
    timestamp: datetime = Field(default_factory=datetime.now)