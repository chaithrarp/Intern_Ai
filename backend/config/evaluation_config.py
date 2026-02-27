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

DIMENSION_WEIGHTS = {
    "technical_depth": 0.30,
    "concept_accuracy": 0.25,
    "structured_thinking": 0.20,
    "communication_clarity": 0.15,
    "confidence_consistency": 0.10
}


# ============================================
# SCORING THRESHOLDS
# ============================================

class ScoreLevel:
    EXCELLENT = 85
    GOOD = 70
    AVERAGE = 50
    NEEDS_WORK = 0


def get_performance_level(score: int) -> str:
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

DIFFICULTY_EXPECTATIONS = {
    "easy": {"pass_threshold": 50, "good_threshold": 65, "excellent_threshold": 80},
    "medium": {"pass_threshold": 55, "good_threshold": 70, "excellent_threshold": 85},
    "hard": {"pass_threshold": 60, "good_threshold": 75, "excellent_threshold": 90},
    "expert": {"pass_threshold": 65, "good_threshold": 80, "excellent_threshold": 95}
}


# ============================================
# ADAPTIVE DIFFICULTY RULES
# ============================================

class DifficultyAdjustment:
    INCREASE_THRESHOLD = 75
    DECREASE_THRESHOLD = 50
    MIN_QUESTIONS_BEFORE_ADJUSTMENT = 2

    DIFFICULTY_LEVELS = {
        1: "easy", 2: "easy", 3: "easy",
        4: "medium", 5: "medium", 6: "medium",
        7: "hard", 8: "hard",
        9: "expert", 10: "expert"
    }

    @staticmethod
    def get_difficulty_label(level: int) -> str:
        return DifficultyAdjustment.DIFFICULTY_LEVELS.get(level, "medium")

    @staticmethod
    def should_increase_difficulty(average_score: float, questions_answered: int) -> bool:
        if questions_answered < DifficultyAdjustment.MIN_QUESTIONS_BEFORE_ADJUSTMENT:
            return False
        return average_score >= DifficultyAdjustment.INCREASE_THRESHOLD

    @staticmethod
    def should_decrease_difficulty(average_score: float, questions_answered: int) -> bool:
        if questions_answered < DifficultyAdjustment.MIN_QUESTIONS_BEFORE_ADJUSTMENT:
            return False
        return average_score < DifficultyAdjustment.DECREASE_THRESHOLD


# ============================================
# FOLLOW-UP TRIGGERS
# ============================================

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

CLAIM_PRIORITY_RULES = {
    "metrics": {"priority": 9, "reason": "Quantitative claims need verification"},
    "architecture": {"priority": 8, "reason": "System design claims are critical"},
    "scale": {"priority": 8, "reason": "Scale claims often exaggerated"},
    "tools": {"priority": 6, "reason": "Tool expertise should be verified"},
    "role": {"priority": 5, "reason": "Role responsibilities should align"}
}


# ============================================
# RED FLAG DETECTION
# ============================================

RED_FLAG_PATTERNS = {
    "unrealistic_metrics": {
        "severity": "high",
        "examples": [
            "100% uptime without explaining HA strategy",
            "10M requests/day from single server",
            "Zero bugs in production"
        ]
    },
    "contradiction": {"severity": "high"},
    "vague_optimization": {
        "severity": "medium",
        "keywords": ["optimized", "improved", "enhanced"]
    },
    "responsibility_inflation": {"severity": "medium"},
    "technology_buzzwords": {
        "severity": "low",
        "keywords": ["AI", "ML", "blockchain", "quantum"],
        "without_depth": True
    }
}


# ============================================
# CLAIM EXTRACTION CONFIGURATION
# ============================================

SKIP_CLAIM_EXTRACTION_FOR_QUESTIONS = [0, 1, 2]


# ============================================
# FOLLOW-UP RULES  ← KEY FIX: much stricter thresholds
# ============================================

FOLLOWUP_RULES = {
    # ── Hard caps ────────────────────────────────────────────────
    "max_followups_per_session": 1,       # CHANGED: was 2 — only 1 follow-up allowed total
    "max_consecutive_followups": 1,        # Never follow-up a follow-up answer

    # ── Cooldown ─────────────────────────────────────────────────
    "followup_cooldown_questions": 2,      # If Q2 has follow-up, skip Q3-4 for follow-ups

    # ── Score threshold ──────────────────────────────────────────
    # CHANGED: was 55 — now only follow-up on truly bad answers
    "followup_score_threshold": 40,

    # ── Word count ───────────────────────────────────────────────
    # REMOVED short-answer trigger: a 20-word answer to a simple Q is fine.
    # Only follow up if score is critically low AND answer is very short.
    "followup_word_count_threshold": 0,    # CHANGED: was 30 — disabled (0 = never trigger on length alone)

    # ── Eligible questions ───────────────────────────────────────
    "followup_eligible_questions": [2, 5], # Only Q2 and Q5 can have follow-ups

    # Q2 follow-up blocks Q3 and Q4
    "if_q2_has_followup_block": [3, 4],

    # Q5 follow-up based on claims from earlier questions
    "q5_followup_based_on_questions": [3, 4, 5],
    "q5_followup_priority": "claims"
}


# ============================================
# PHASE TRANSITION RULES
# ============================================

# ========================================
# 🎯 DEMO MODE (ACTIVE) - 6 Questions Total
# ========================================

PHASE_TRANSITION_RULES = {
    "resume_deep_dive": {
        "min_questions": 2,
        "max_questions": 2,
        "transition_score": 0,
        "force_transition_after": 2,
        "skip_if_no_claims": False
    },
    "core_skill_assessment": {
        "min_questions": 3,
        "max_questions": 3,
        "transition_score": 0,
        "force_transition_after": 3,
        "skip_if_no_claims": False
    },
    "scenario_solving": {
        "min_questions": 0,
        "max_questions": 0,
        "transition_score": 0,
        "force_transition_after": 0,
        "skip_if_no_claims": False
    },
    "stress_testing": {
        "min_questions": 0,
        "max_questions": 0,
        "transition_score": 0,
        "force_transition_after": 0,
        "skip_if_no_claims": False
    },
    "claim_verification": {
        "min_questions": 0,
        "max_questions": 0,
        "transition_score": 0,
        "force_transition_after": 0,
        "skip_if_no_claims": True
    },
    "wrap_up": {
        "min_questions": 0,
        "max_questions": 0,
        "transition_score": 0,
        "force_transition_after": 0,
        "skip_if_no_claims": False
    }
}


# ========================================
# 🏭 PRODUCTION MODE (DISABLED)
# ========================================
# PHASE_TRANSITION_RULES = {
#     "resume_deep_dive": {
#         "min_questions": 4, "max_questions": 5,
#         "transition_score": 65, "force_transition_after": 6,
#         "skip_if_no_claims": False
#     },
#     "core_skill_assessment": {
#         "min_questions": 5, "max_questions": 7,
#         "transition_score": 70, "force_transition_after": 8,
#         "skip_if_no_claims": False
#     },
#     "scenario_solving": {
#         "min_questions": 2, "max_questions": 4,
#         "transition_score": 70, "force_transition_after": 5,
#         "skip_if_no_claims": False
#     },
#     "stress_testing": {
#         "min_questions": 1, "max_questions": 2,
#         "transition_score": 65, "force_transition_after": 3,
#         "skip_if_no_claims": False
#     },
#     "claim_verification": {
#         "min_questions": 0, "max_questions": 2,
#         "transition_score": 0, "force_transition_after": 2,
#         "skip_if_no_claims": True
#     },
#     "wrap_up": {
#         "min_questions": 1, "max_questions": 1,
#         "transition_score": 0, "force_transition_after": 1,
#         "skip_if_no_claims": False
#     }
# }
# SKIP_CLAIM_EXTRACTION_FOR_QUESTIONS = [0, 1, 2, 3, 4]


# ============================================
# INTERRUPTION CONFIGURATION
# ============================================

PHASE_INTERRUPTION_PROBABILITY = {
    "resume_deep_dive": 0.15,
    "core_skill_assessment": 0.35,
    "scenario_solving": 0.50,
    "stress_testing": 0.70,
    "claim_verification": 0.60,
    "wrap_up": 0.05
}


# ============================================
# FINAL REPORT CONFIGURATION
# ============================================

class ReportConfig:
    STRENGTH_THRESHOLD = 75
    IMPROVEMENT_THRESHOLD = 65
    MAX_RECOMMENDED_TOPICS = 5
    MAX_CRITICAL_MISTAKES = 3

    PROFICIENCY_LEVELS = {
        (85, 100): "expert",
        (70, 84): "advanced",
        (55, 69): "intermediate",
        (0, 54): "beginner"
    }

    @staticmethod
    def get_proficiency_level(score: int) -> str:
        for (min_score, max_score), level in ReportConfig.PROFICIENCY_LEVELS.items():
            if min_score <= score <= max_score:
                return level
        return "beginner"


# ============================================
# MODE INDICATOR
# ============================================

def get_current_mode() -> str:
    resume_max = PHASE_TRANSITION_RULES.get("resume_deep_dive", {}).get("max_questions", 0)
    if resume_max == 2:
        return "DEMO MODE (Q0 + 5 questions: 2 resume + 3 round-specific)"
    elif resume_max >= 4:
        return "PRODUCTION MODE (Full interview with ~12-15 questions)"
    else:
        return "CUSTOM MODE"


if __name__ == "__main__":
    print("=" * 60)
    print("EVALUATION CONFIGURATION TEST")
    print("=" * 60)
    print(f"\n🎯 Current Mode: {get_current_mode()}")
    print(f"\n📋 Follow-up Rules:")
    print(f"   Max per session: {FOLLOWUP_RULES['max_followups_per_session']}")
    print(f"   Score threshold: {FOLLOWUP_RULES['followup_score_threshold']}")
    print(f"   Word count trigger: {'disabled' if FOLLOWUP_RULES['followup_word_count_threshold'] == 0 else FOLLOWUP_RULES['followup_word_count_threshold']}")
    total = sum(c['max_questions'] for c in PHASE_TRANSITION_RULES.values())
    print(f"\n✅ Max questions: {total} + 1 intro = {total + 1} total")
    print("=" * 60)