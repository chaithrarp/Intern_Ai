"""
Evaluation Configuration
=========================

Defines scoring thresholds, weights, and evaluation rules.
Centralizes all evaluation constants for easy tuning.

NEW FLOW:
- DEMO MODE: Q0 (Intro) + Q1-Q2 (Resume, no claims) + Q3-Q5 (Round-specific, WITH claims)
- PRODUCTION MODE: Same structure but with more questions per phase

To switch modes: Comment/uncomment the PHASE_TRANSITION_RULES sections below
"""

from typing import Dict


# ============================================
# DIMENSION WEIGHTS
# ============================================

# How much each dimension contributes to overall score
DIMENSION_WEIGHTS = {
    "technical_depth": 0.30,        # 30% - Most important
    "concept_accuracy": 0.25,       # 25% - Critical
    "structured_thinking": 0.20,    # 20% - Important
    "communication_clarity": 0.15,  # 15% - Moderate
    "confidence_consistency": 0.10  # 10% - Supporting
}


# ============================================
# SCORING THRESHOLDS
# ============================================

class ScoreLevel:
    """Score range definitions"""
    EXCELLENT = 85      # 85-100: Excellent
    GOOD = 70           # 70-84: Good
    AVERAGE = 50        # 50-69: Average
    NEEDS_WORK = 0      # 0-49: Needs Improvement


# Performance level labels
def get_performance_level(score: int) -> str:
    """Convert score to performance level"""
    if score >= ScoreLevel.EXCELLENT:
        return "Excellent"
    elif score >= ScoreLevel.GOOD:
        return "Good"
    elif score >= ScoreLevel.AVERAGE:
        return "Average"
    else:
        return "Needs Improvement"


# ============================================
# ROUND-SPECIFIC EVALUATION CRITERIA
# ============================================

# What to emphasize in each round type
ROUND_EVALUATION_FOCUS = {
    "hr": {
        "primary_dimensions": ["structured_thinking", "communication_clarity"],
        "secondary_dimensions": ["confidence_consistency"],
        "key_elements": [
            "STAR format (Situation, Task, Action, Result)",
            "Specific metrics and outcomes",
            "Ownership and accountability",
            "Lessons learned"
        ],
        "red_flags": [
            "No specific examples",
            "Blaming others",
            "Vague generalizations",
            "No measurable results"
        ]
    },
    
    "technical": {
        "primary_dimensions": ["technical_depth", "concept_accuracy"],
        "secondary_dimensions": ["structured_thinking"],
        "key_elements": [
            "Correct technical concepts",
            "Trade-off analysis",
            "Edge case consideration",
            "Time/space complexity awareness",
            "Real-world constraints"
        ],
        "red_flags": [
            "Incorrect fundamental concepts",
            "No mention of trade-offs",
            "Ignoring edge cases",
            "Unrealistic assumptions"
        ]
    },
    
    "system_design": {
        "primary_dimensions": ["technical_depth", "structured_thinking"],
        "secondary_dimensions": ["concept_accuracy"],
        "key_elements": [
            "Scalability considerations",
            "Component breakdown",
            "Bottleneck identification",
            "Data flow understanding",
            "Monitoring and observability"
        ],
        "red_flags": [
            "No scaling strategy",
            "Missing critical components",
            "No failure handling",
            "Unrealistic architecture"
        ]
    }
}


# ============================================
# DIFFICULTY SCALING
# ============================================

# How difficulty affects scoring expectations
DIFFICULTY_EXPECTATIONS = {
    "easy": {
        "pass_threshold": 50,
        "good_threshold": 65,
        "excellent_threshold": 80
    },
    "medium": {
        "pass_threshold": 55,
        "good_threshold": 70,
        "excellent_threshold": 85
    },
    "hard": {
        "pass_threshold": 60,
        "good_threshold": 75,
        "excellent_threshold": 90
    },
    "expert": {
        "pass_threshold": 65,
        "good_threshold": 80,
        "excellent_threshold": 95
    }
}


# ============================================
# ADAPTIVE DIFFICULTY RULES
# ============================================

class DifficultyAdjustment:
    """Rules for when to increase/decrease difficulty"""
    
    # If average score in phase > threshold, increase difficulty
    INCREASE_THRESHOLD = 75
    
    # If average score in phase < threshold, decrease difficulty
    DECREASE_THRESHOLD = 50
    
    # Minimum questions before adjusting
    MIN_QUESTIONS_BEFORE_ADJUSTMENT = 2
    
    # Difficulty level mapping (1-10 scale)
    DIFFICULTY_LEVELS = {
        1: "easy",
        2: "easy",
        3: "easy",
        4: "medium",
        5: "medium",
        6: "medium",
        7: "hard",
        8: "hard",
        9: "expert",
        10: "expert"
    }
    
    @staticmethod
    def get_difficulty_label(level: int) -> str:
        """Convert numeric level (1-10) to difficulty label"""
        return DifficultyAdjustment.DIFFICULTY_LEVELS.get(level, "medium")
    
    @staticmethod
    def should_increase_difficulty(average_score: float, questions_answered: int) -> bool:
        """Check if difficulty should increase"""
        if questions_answered < DifficultyAdjustment.MIN_QUESTIONS_BEFORE_ADJUSTMENT:
            return False
        return average_score >= DifficultyAdjustment.INCREASE_THRESHOLD
    
    @staticmethod
    def should_decrease_difficulty(average_score: float, questions_answered: int) -> bool:
        """Check if difficulty should decrease"""
        if questions_answered < DifficultyAdjustment.MIN_QUESTIONS_BEFORE_ADJUSTMENT:
            return False
        return average_score < DifficultyAdjustment.DECREASE_THRESHOLD


# ============================================
# FOLLOW-UP TRIGGERS
# ============================================

# When to ask follow-up questions
FOLLOWUP_TRIGGERS = {
    "low_score": {
        "threshold": 60,
        "reason": "Answer scored below 60 - needs clarification"
    },
    "vague_claim": {
        "keywords": ["optimized", "improved", "enhanced", "better", "faster"],
        "reason": "Used vague optimization terms without specifics"
    },
    "missing_metrics": {
        "keywords": ["performance", "scale", "users", "requests", "load"],
        "reason": "Mentioned scale/performance without metrics"
    },
    "no_trade_offs": {
        "context": "technical",
        "reason": "Didn't discuss trade-offs in technical decision"
    },
    "incomplete_star": {
        "context": "hr",
        "missing_elements": ["situation", "task", "action", "result"],
        "reason": "STAR method incomplete"
    },
    "contradiction": {
        "reason": "Statement contradicts previous answer"
    }
}


# ============================================
# CLAIM VERIFICATION PRIORITY
# ============================================

# How to prioritize which claims to verify
CLAIM_PRIORITY_RULES = {
    "metrics": {
        "priority": 9,
        "reason": "Quantitative claims need verification",
        "examples": ["10M requests", "99.99% uptime", "50% improvement"]
    },
    "architecture": {
        "priority": 8,
        "reason": "System design claims are critical",
        "examples": ["microservices", "distributed system", "event-driven"]
    },
    "scale": {
        "priority": 8,
        "reason": "Scale claims often exaggerated",
        "examples": ["millions of users", "enterprise scale", "global distribution"]
    },
    "tools": {
        "priority": 6,
        "reason": "Tool expertise should be verified",
        "examples": ["expert in X", "deep knowledge of Y"]
    },
    "role": {
        "priority": 5,
        "reason": "Role responsibilities should align",
        "examples": ["led team of 10", "owned entire backend"]
    }
}


# ============================================
# RED FLAG DETECTION
# ============================================

# Patterns that should trigger red flags
RED_FLAG_PATTERNS = {
    "unrealistic_metrics": {
        "severity": "high",
        "examples": [
            "100% uptime without explaining HA strategy",
            "10M requests/day from single server",
            "Zero bugs in production"
        ]
    },
    "contradiction": {
        "severity": "high",
        "examples": [
            "Said team size was 5, now says 20",
            "Claimed solo project, now mentions team lead"
        ]
    },
    "vague_optimization": {
        "severity": "medium",
        "keywords": ["optimized", "improved", "enhanced"],
        "without": ["specific technique", "metrics", "bottleneck analysis"]
    },
    "responsibility_inflation": {
        "severity": "medium",
        "patterns": [
            "Intern claiming architect role",
            "Junior claiming senior decisions"
        ]
    },
    "technology_buzzwords": {
        "severity": "low",
        "keywords": ["AI", "ML", "blockchain", "quantum"],
        "without_depth": True
    }
}


# ============================================
# CLAIM EXTRACTION CONFIGURATION
# ============================================

# Skip claim extraction for these questions to save time (Q0, Q1, Q2)
# Extract claims for Q3, Q4, Q5 (round-specific questions)
SKIP_CLAIM_EXTRACTION_FOR_QUESTIONS = [0, 1, 2]


# ============================================
# FOLLOW-UP RULES
# ============================================

FOLLOWUP_RULES = {
    "max_followups_per_session": 2,  # Maximum 2 follow-ups in entire interview
    "max_consecutive_followups": 1,  # Never follow-up a follow-up answer
    "followup_cooldown_questions": 2,  # If Q2 has follow-up, skip Q3-4 for follow-ups
    "followup_score_threshold": 55,  # Follow-up if score < 55
    "followup_word_count_threshold": 30,  # Follow-up if answer < 30 words
    
    # Which questions CAN have follow-ups
    "followup_eligible_questions": [2, 5],  # Only Q2 and Q5 can have follow-ups
    
    # Q2 follow-up blocks Q3 and Q4
    "if_q2_has_followup_block": [3, 4],  # If Q2 had follow-up, Q3 and Q4 cannot
    
    # Q5 follow-up based on claims from earlier questions
    "q5_followup_based_on_questions": [3, 4, 5],  # Q5 can follow-up on claims from Q3, Q4, Q5
    "q5_followup_priority": "claims"  # Prioritize claim-based follow-ups for Q5
}


# ============================================
# PHASE TRANSITION RULES
# ============================================
# Toggle between DEMO MODE and PRODUCTION MODE here

# ========================================
# 🎯 DEMO MODE (ACTIVE) - 6 Questions Total
# ========================================
# Flow: Q0 (Intro) + Q1-Q2 (Resume, fast) + Q3-Q5 (Round-specific, with claims)
# Total questions: 6 (Q0 intro + 5 actual questions)
# Demo duration: ~5-7 minutes
# Perfect for presentations and quick testing

PHASE_TRANSITION_RULES = {
    "resume_deep_dive": {
        "min_questions": 2,  # Exactly Q1-Q2 (resume-based, no claim extraction)
        "max_questions": 2,
        "transition_score": 0,  # Always transition after 2 questions
        "force_transition_after": 2,
        "skip_if_no_claims": False
    },
    "core_skill_assessment": {
        "min_questions": 3,  # Exactly Q3-Q5 (round-specific, WITH claim extraction)
        "max_questions": 3,
        "transition_score": 0,  # Always transition after 3 questions
        "force_transition_after": 3,
        "skip_if_no_claims": False
    },
    "scenario_solving": {
        "min_questions": 0,  # SKIP - Not used in demo
        "max_questions": 0,
        "transition_score": 0,
        "force_transition_after": 0,
        "skip_if_no_claims": False
    },
    "stress_testing": {
        "min_questions": 0,  # SKIP - Not used in demo
        "max_questions": 0,
        "transition_score": 0,
        "force_transition_after": 0,
        "skip_if_no_claims": False
    },
    "claim_verification": {
        "min_questions": 0,  # SKIP - Claims extracted during Q3-Q5
        "max_questions": 0,
        "transition_score": 0,
        "force_transition_after": 0,
        "skip_if_no_claims": True
    },
    "wrap_up": {
        "min_questions": 0,  # SKIP - Interview ends after Q5
        "max_questions": 0,
        "transition_score": 0,
        "force_transition_after": 0,
        "skip_if_no_claims": False
    }
}

# ========================================
# 🏭 PRODUCTION MODE (DISABLED) - Full Interview
# ========================================
# To enable PRODUCTION MODE:
# 1. Comment out the DEMO MODE section above
# 2. Uncomment this section below (rename to PHASE_TRANSITION_RULES)
# 3. Restart the backend server

# Flow: Q0 (Intro) + Q1-Q4 (Resume, fast) + Q5-Q11 (Round-specific, with claims)
# Total: ~12-15 questions with follow-ups
# Duration: ~15-20 minutes

# PHASE_TRANSITION_RULES = {
#     "resume_deep_dive": {
#         "min_questions": 4,  # Q1-Q4 (resume-based, no claim extraction)
#         "max_questions": 5,
#         "transition_score": 65,  # Move on if performing well
#         "force_transition_after": 6,
#         "skip_if_no_claims": False
#     },
#     "core_skill_assessment": {
#         "min_questions": 5,  # Q5-Q9 (round-specific fundamentals, WITH claims)
#         "max_questions": 7,
#         "transition_score": 70,
#         "force_transition_after": 8,
#         "skip_if_no_claims": False
#     },
#     "scenario_solving": {
#         "min_questions": 2,  # Q10-Q11 (real-world scenarios, WITH claims)
#         "max_questions": 4,
#         "transition_score": 70,
#         "force_transition_after": 5,
#         "skip_if_no_claims": False
#     },
#     "stress_testing": {
#         "min_questions": 1,  # Q12+ (pressure testing, WITH claims)
#         "max_questions": 2,
#         "transition_score": 65,
#         "force_transition_after": 3,
#         "skip_if_no_claims": False
#     },
#     "claim_verification": {
#         "min_questions": 0,  # Adaptive based on suspicious claims
#         "max_questions": 2,
#         "transition_score": 0,
#         "force_transition_after": 2,
#         "skip_if_no_claims": True  # Skip if no unverified claims
#     },
#     "wrap_up": {
#         "min_questions": 1,  # Final question
#         "max_questions": 1,
#         "transition_score": 0,
#         "force_transition_after": 1,
#         "skip_if_no_claims": False
#     }
# }

# PRODUCTION MODE CLAIM EXTRACTION:
# Uncomment and use this in production mode instead
# SKIP_CLAIM_EXTRACTION_FOR_QUESTIONS = [0, 1, 2, 3, 4]  # Only skip intro + first 4 resume Qs


# ============================================
# INTERRUPTION CONFIGURATION
# ============================================

# Base interruption probabilities by phase
# These are used by the interruption analyzer
PHASE_INTERRUPTION_PROBABILITY = {
    "resume_deep_dive": 0.15,       # Very low early on
    "core_skill_assessment": 0.35,  # Moderate
    "scenario_solving": 0.50,       # Higher
    "stress_testing": 0.70,         # Very high
    "claim_verification": 0.60,     # High (challenging claims)
    "wrap_up": 0.05                 # Very low for final question
}


# ============================================
# FINAL REPORT CONFIGURATION
# ============================================

class ReportConfig:
    """Configuration for final report generation"""
    
    # Minimum score to be considered a strength
    STRENGTH_THRESHOLD = 75
    
    # Maximum score to be considered an improvement area
    IMPROVEMENT_THRESHOLD = 65
    
    # Number of recommended topics to suggest
    MAX_RECOMMENDED_TOPICS = 5
    
    # Number of specific mistakes to highlight
    MAX_CRITICAL_MISTAKES = 3
    
    # Skill proficiency levels
    PROFICIENCY_LEVELS = {
        (85, 100): "expert",
        (70, 84): "advanced",
        (55, 69): "intermediate",
        (0, 54): "beginner"
    }
    
    @staticmethod
    def get_proficiency_level(score: int) -> str:
        """Get proficiency level from score"""
        for (min_score, max_score), level in ReportConfig.PROFICIENCY_LEVELS.items():
            if min_score <= score <= max_score:
                return level
        return "beginner"


# ============================================
# MODE INDICATOR
# ============================================

def get_current_mode() -> str:
    """
    Returns the current configuration mode
    Useful for debugging and logging
    """
    # Check resume_deep_dive phase for mode detection
    resume_max = PHASE_TRANSITION_RULES.get("resume_deep_dive", {}).get("max_questions", 0)
    
    if resume_max == 2:
        return "DEMO MODE (Q0 + 5 questions: 2 resume + 3 round-specific)"
    elif resume_max >= 4:
        return "PRODUCTION MODE (Full interview with ~12-15 questions)"
    else:
        return "CUSTOM MODE"


# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("EVALUATION CONFIGURATION TEST")
    print("=" * 60)
    
    print(f"\n🎯 Current Mode: {get_current_mode()}")
    
    print("\n📋 Phase Transition Rules:")
    print("-" * 60)
    for phase, config in PHASE_TRANSITION_RULES.items():
        if config['max_questions'] > 0:  # Only show active phases
            print(f"\n{phase}:")
            print(f"  Min Questions: {config['min_questions']}")
            print(f"  Max Questions: {config['max_questions']}")
            print(f"  Force Transition After: {config['force_transition_after']}")
            print(f"  Transition Score: {config['transition_score']}")
    
    total_questions = sum(
        config['max_questions'] 
        for config in PHASE_TRANSITION_RULES.values()
    )
    
    print("\n📊 Claim Extraction:")
    print("-" * 60)
    print(f"Skip for questions: {SKIP_CLAIM_EXTRACTION_FOR_QUESTIONS}")
    print(f"Extract for: Q{max(SKIP_CLAIM_EXTRACTION_FOR_QUESTIONS) + 1} onwards")
    
    print("\n🔄 Follow-up Rules:")
    print("-" * 60)
    print(f"Eligible questions: {FOLLOWUP_RULES['followup_eligible_questions']}")
    print(f"Max per session: {FOLLOWUP_RULES['max_followups_per_session']}")
    print(f"Q2 follow-up blocks: {FOLLOWUP_RULES['if_q2_has_followup_block']}")
    
    print("\n" + "=" * 60)
    print(f"Total Questions (not counting Q0 intro): {total_questions}")
    print(f"Total with intro: {total_questions + 1}")
    print("=" * 60)