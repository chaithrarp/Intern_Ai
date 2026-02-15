"""
Evaluation Models - Define What We're Measuring
================================================

5 Core Measurable Dimensions:
1. Technical Depth (0-100)
2. Concept Accuracy (0-100)
3. Structured Thinking (0-100)
4. Communication Clarity (0-100)
5. Confidence & Consistency (0-100)

Each answer gets scored across all dimensions.
Session aggregates scores and generates final report.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


# ============================================
# EVALUATION SCORE - Single Dimension
# ============================================

class EvaluationScore(BaseModel):
    """
    Single dimension score with evidence
    
    Example:
        {
            "dimension": "technical_depth",
            "score": 75,
            "evidence": "Explained database indexing with B-tree details",
            "improvement": "Could discuss trade-offs between index types"
        }
    """
    dimension: str = Field(..., description="Which dimension (technical_depth, concept_accuracy, etc)")
    score: int = Field(..., ge=0, le=100, description="Score 0-100")
    evidence: str = Field(..., description="What justified this score")
    improvement: Optional[str] = Field(None, description="How to improve (if score < 70)")
    
    @validator('dimension')
    def validate_dimension(cls, v):
        valid_dimensions = [
            'technical_depth',
            'concept_accuracy', 
            'structured_thinking',
            'communication_clarity',
            'confidence_consistency'
        ]
        if v not in valid_dimensions:
            raise ValueError(f"Invalid dimension. Must be one of: {valid_dimensions}")
        return v


# ============================================
# ANSWER EVALUATION - Complete Answer Analysis
# ============================================

class AnswerEvaluation(BaseModel):
    """
    Complete evaluation of a single answer
    
    This is what the LLM returns after analyzing an answer.
    Contains scores across all 5 dimensions + qualitative feedback.
    """
    
    # Identification
    question_id: int = Field(..., description="Which question was answered")
    round_type: str = Field(..., description="Which round (hr, technical, system_design)")
    
    # Multi-Dimensional Scores (0-100 each)
    scores: Dict[str, int] = Field(
        ..., 
        description="Scores for each dimension",
        example={
            "technical_depth": 75,
            "concept_accuracy": 82,
            "structured_thinking": 68,
            "communication_clarity": 70,
            "confidence_consistency": 65
        }
    )
    
    # Detailed Score Breakdown
    score_details: List[EvaluationScore] = Field(
        ...,
        description="Detailed explanation for each dimension"
    )
    
    # Overall Assessment
    overall_score: int = Field(..., ge=0, le=100, description="Weighted average of all dimensions")
    
    # Qualitative Feedback
    strengths: List[str] = Field(..., description="What the candidate did well")
    weaknesses: List[str] = Field(..., description="Areas needing improvement")
    
    # Red Flags (Critical Issues)
    red_flags: List[str] = Field(
        default_factory=list,
        description="Critical issues (false claims, contradictions, major gaps)",
        example=["Claimed 10M requests but couldn't explain caching strategy"]
    )
    
    # Follow-up Decision
    requires_followup: bool = Field(..., description="Should we probe deeper?")
    followup_reason: Optional[str] = Field(
        None,
        description="Why follow-up is needed",
        example="Vague explanation of 'optimization' without specifics"
    )
    suggested_followup: Optional[str] = Field(
        None,
        description="AI-suggested next question if followup required"
    )
    
    # Difficulty Adjustment
    difficulty_adjustment: str = Field(
        ...,
        description="Should next question be easier/same/harder",
        example="increase"  # Options: decrease, maintain, increase
    )
    
    @validator('scores')
    def validate_scores(cls, v):
        required_dimensions = [
            'technical_depth',
            'concept_accuracy',
            'structured_thinking', 
            'communication_clarity',
            'confidence_consistency'
        ]
        
        for dim in required_dimensions:
            if dim not in v:
                raise ValueError(f"Missing required dimension: {dim}")
            if not (0 <= v[dim] <= 100):
                raise ValueError(f"Score for {dim} must be between 0-100")
        
        return v
    
    @validator('difficulty_adjustment')
    def validate_difficulty(cls, v):
        valid_adjustments = ['decrease', 'maintain', 'increase']
        if v not in valid_adjustments:
            raise ValueError(f"difficulty_adjustment must be one of: {valid_adjustments}")
        return v


# ============================================
# SESSION EVALUATION - Aggregated Performance
# ============================================

class SessionEvaluation(BaseModel):
    """
    Aggregated evaluation across entire interview session
    
    Tracks performance over time and across different rounds.
    """
    
    session_id: str
    
    # Aggregated Scores (across all answers)
    average_scores: Dict[str, float] = Field(
        ...,
        description="Average score for each dimension across session"
    )
    
    # Performance Trend
    score_progression: List[Dict[str, int]] = Field(
        ...,
        description="How scores changed over time",
        example=[
            {"question": 1, "overall": 65},
            {"question": 2, "overall": 72},
            {"question": 3, "overall": 68}
        ]
    )
    
    # Round Breakdown
    round_performance: Dict[str, Dict[str, float]] = Field(
        ...,
        description="Average scores per round type",
        example={
            "hr_round": {"technical_depth": 70, "communication_clarity": 75},
            "technical_round": {"technical_depth": 82, "concept_accuracy": 78}
        }
    )
    
    # Phase Completion
    phases_completed: List[str] = Field(
        ...,
        description="Which interview phases were completed"
    )
    
    # Interruption Statistics
    total_interruptions: int = Field(0, description="Number of times interrupted")
    interruption_reasons: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of each interruption type",
        example={"rambling": 2, "vague_claim": 1, "off_topic": 1}
    )
    
    # Claim Analysis
    total_claims_made: int = Field(0, description="Number of claims extracted")
    claims_verified: int = Field(0, description="Number of claims successfully verified")
    unverified_claims: List[str] = Field(
        default_factory=list,
        description="Claims that couldn't be verified"
    )
    
    # Time Metrics
    total_duration_seconds: float = Field(0, description="Total interview duration")
    average_answer_duration: float = Field(0, description="Average time per answer")
    
    # Behavioral Metrics
    filler_word_rate: float = Field(0, description="Average filler words per minute")
    pause_frequency: float = Field(0, description="Long pauses per minute")
    
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================
# FINAL REPORT - End of Interview Dashboard
# ============================================

class SkillAssessment(BaseModel):
    """Assessment of a specific skill area"""
    skill_name: str
    proficiency_level: str = Field(..., description="beginner/intermediate/advanced/expert")
    evidence: List[str] = Field(..., description="Quotes or examples demonstrating level")
    score: int = Field(..., ge=0, le=100)


class FinalReport(BaseModel):
    """
    Comprehensive final report shown after interview
    
    This is what powers the final feedback dashboard.
    """
    
    session_id: str
    candidate_name: Optional[str] = None
    
    # === OVERALL PERFORMANCE ===
    overall_score: int = Field(..., ge=0, le=100, description="Weighted final score")
    overall_assessment: str = Field(
        ...,
        description="One-sentence summary",
        example="Strong technical depth but needs work on communication clarity under pressure"
    )
    
    # === DIMENSION SCORES (for radar chart) ===
    dimension_scores: Dict[str, int] = Field(
        ...,
        description="Final score for each of 5 dimensions",
        example={
            "technical_depth": 78,
            "concept_accuracy": 82,
            "structured_thinking": 70,
            "communication_clarity": 65,
            "confidence_consistency": 72
        }
    )
    
    # === SKILL HEATMAP ===
    skill_assessments: List[SkillAssessment] = Field(
        ...,
        description="Detailed assessment of specific skills mentioned/tested"
    )
    
    # === STRONG AREAS ===
    strong_areas: List[str] = Field(
        ...,
        description="What candidate excelled at",
        example=["System Design", "Database Optimization", "Problem Decomposition"]
    )
    
    # === IMPROVEMENT AREAS ===
    improvement_areas: List[str] = Field(
        ...,
        description="Clear areas needing work",
        example=["STAR Method Structure", "Handling Interruptions", "Concise Communication"]
    )
    
    # === SPECIFIC MISTAKES DETECTED ===
    critical_mistakes: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Specific errors with evidence",
        example=[
            {
                "mistake": "Claimed database handles 10M req/day but couldn't explain caching",
                "question": "Q3: Database Performance",
                "impact": "Suggests lack of hands-on experience with scale"
            }
        ]
    )
    
    # === EVIDENCE-BASED FEEDBACK ===
    detailed_feedback: Dict[str, List[str]] = Field(
        ...,
        description="Specific feedback by category",
        example={
            "technical_depth": [
                "✅ Correctly explained B-tree indexing internals",
                "❌ Missed discussing index write amplification trade-offs"
            ],
            "communication": [
                "⚠️ Used 15 filler words in Q4 (above average)",
                "✅ Clear STAR structure in Q2"
            ]
        }
    )
    
    # === ROUND PERFORMANCE BREAKDOWN ===
    round_breakdown: Dict[str, Dict] = Field(
        ...,
        description="Performance in each interview round",
        example={
            "hr_round": {
                "score": 72,
                "strengths": ["Good storytelling", "Clear ownership"],
                "weaknesses": ["Lacked specific metrics"]
            },
            "technical_round": {
                "score": 80,
                "strengths": ["Deep algorithm knowledge"],
                "weaknesses": ["Struggled with time complexity analysis"]
            }
        }
    )
    
    # === RECOMMENDED FOCUS TOPICS ===
    recommended_topics: List[str] = Field(
        ...,
        description="Specific topics to study/practice",
        example=[
            "Practice STAR method with specific metrics",
            "Study distributed systems caching strategies",
            "Work on reducing filler words under pressure"
        ]
    )
    
    # === INTERRUPTION ANALYSIS ===
    interruption_summary: Dict = Field(
        default_factory=dict,
        description="Why interruptions happened and how candidate recovered",
        example={
            "total_interruptions": 3,
            "primary_trigger": "rambling",
            "recovery_quality": "good",
            "notes": "Initially struggled but adapted well by Q5"
        }
    )
    
    # === CLAIM VERIFICATION REPORT ===
    claim_report: Dict = Field(
        default_factory=dict,
        description="Claims made vs claims verified",
        example={
            "total_claims": 8,
            "verified": 6,
            "unverified": ["10M requests/day without infrastructure details"],
            "red_flags": ["Contradicted earlier statement about team size"]
        }
    )
    
    # === NEXT STEPS ===
    next_steps: List[str] = Field(
        ...,
        description="Concrete action items",
        example=[
            "Take 3 more mock interviews focusing on system design",
            "Record yourself answering and count filler words",
            "Prepare 5 STAR stories with specific metrics"
        ]
    )
    
    # === METADATA ===
    interview_duration: float = Field(..., description="Total time in seconds")
    questions_asked: int
    phases_completed: List[str]
    difficulty_reached: str = Field(..., description="easy/medium/hard/expert")
    
    generated_at: datetime = Field(default_factory=datetime.now)


# ============================================
# SCORING THRESHOLDS
# ============================================

class ScoringThresholds(BaseModel):
    """
    Define what score ranges mean
    
    Used for interpreting scores and generating feedback
    """
    
    excellent_threshold: int = 85  # 85+ = Excellent
    good_threshold: int = 70       # 70-84 = Good
    average_threshold: int = 50    # 50-69 = Average
    # Below 50 = Needs Improvement
    
    # Dimension-specific weights for overall score
    dimension_weights: Dict[str, float] = {
        "technical_depth": 0.30,        # 30% weight
        "concept_accuracy": 0.25,       # 25% weight
        "structured_thinking": 0.20,    # 20% weight
        "communication_clarity": 0.15,  # 15% weight
        "confidence_consistency": 0.10  # 10% weight
    }
    
    @classmethod
    def calculate_weighted_score(cls, scores: Dict[str, int]) -> int:
        """Calculate weighted average score"""
        weights = cls().dimension_weights
        total = sum(scores[dim] * weights[dim] for dim in scores)
        return int(total)
    
    @classmethod
    def get_performance_level(cls, score: int) -> str:
        """Convert score to performance level"""
        thresholds = cls()
        if score >= thresholds.excellent_threshold:
            return "Excellent"
        elif score >= thresholds.good_threshold:
            return "Good"
        elif score >= thresholds.average_threshold:
            return "Average"
        else:
            return "Needs Improvement"