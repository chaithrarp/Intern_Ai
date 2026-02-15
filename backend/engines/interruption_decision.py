"""
Interruption Decision Engine
============================

Makes the final decision about whether to interrupt based on multiple inputs:
- Audio metrics from frontend
- Content analysis
- Interruption history
- Current phase

This is the CENTRAL decision point for all interruptions.
"""

from typing import Dict, Optional
from models.interruption_models import InterruptionDecision, InterruptionReason, SeverityLevel, ActionType
from engines.interruption_analyzer import get_interruption_analyzer
from engines.live_warning_generator import get_warning_generator

# ============================================
# DECISION ENGINE
# ============================================

def check_interruption_trigger(
    audio_metrics: Dict,
    session_id: str,
    current_phase: str = "core_skill_assessment",
    interruption_count: int = 0,
    max_interruptions: int = 5
) -> Optional[InterruptionDecision]:
    """
    Main decision function - should we interrupt?
    
    This is called by pressure_engine.py
    
    Args:
        audio_metrics: Audio analysis from frontend
        session_id: Current session ID
        current_phase: Interview phase
        interruption_count: How many interruptions so far
        max_interruptions: Maximum allowed
        
    Returns:
        InterruptionDecision object or None
    """
    
    # Check if we've hit max interruptions
    if interruption_count >= max_interruptions:
        return None
    
    # Get analyzer and warning generator
    analyzer = get_interruption_analyzer()
    warning_gen = get_warning_generator()
    
    # Analyze audio patterns
    analysis_result = analyzer.analyze_audio_patterns(audio_metrics, session_id)
    
    if not analysis_result:
        return None
    
    # Determine action
    should_interrupt = analysis_result.get('should_interrupt', False)
    action = analysis_result.get('action', 'none')
    reason = analysis_result.get('reason')
    priority = analysis_result.get('priority', 10)
    severity = analysis_result.get('severity', 'low')
    evidence = analysis_result.get('evidence', '')
    warning_count = analysis_result.get('warning_count', 0)
    
    # Build decision
    decision = InterruptionDecision(
        should_interrupt=should_interrupt,
        action=action,
        reason=reason,
        priority=priority,
        severity=severity,
        evidence=evidence,
        triggered_at_seconds=audio_metrics.get('recording_duration', 0),
        warning_count=warning_count
    )
    
    # If action is warn, generate warning data
    if action == "warn":
        warning = warning_gen.generate_warning(analysis_result, session_id)
        if warning:
            decision.warning_data = warning
    
    return decision


def should_interrupt_immediately(issue_type: str, priority: int) -> bool:
    """
    Check if this issue should trigger immediate interruption
    
    Args:
        issue_type: Type of issue detected
        priority: Priority level (1=highest, 12=lowest)
        
    Returns:
        True if should interrupt immediately
    """
    
    # Critical issues (priority 1-3) - interrupt immediately
    if priority <= 3:
        return True
    
    # False claims and contradictions - always interrupt
    if issue_type in ["FALSE_CLAIM", "CONTRADICTION"]:
        return True
    
    return False


def calculate_interruption_phrase(reason: str, partial_transcript: str) -> str:
    """
    Generate appropriate interruption phrase
    
    Args:
        reason: Interruption reason
        partial_transcript: What user said so far
        
    Returns:
        Interruption phrase
    """
    
    phrases = {
        "EXCESSIVE_PAUSING": "Let me stop you there. You seem to be struggling with this question.",
        "RAMBLING": "I'm going to cut you off - please get to the point.",
        "VAGUE_ANSWER": "Hold on. I need more specific details, not generalizations.",
        "AVOIDING_QUESTION": "Let me interrupt. You're not answering the question I asked.",
        "SPEAKING_TOO_LONG": "I need to stop you here. Please wrap up your point.",
        "FALSE_CLAIM": "Hold on. I think there's an issue with what you just said.",
        "CONTRADICTION": "Wait - that contradicts what you said earlier. Can you clarify?",
        "LACK_OF_SPECIFICS": "Wait. I need concrete examples, not abstract concepts.",
        "BUZZWORD_HEAVY": "Hold on - less buzzwords, more substance please.",
        "TECHNICAL_INACCURACY": "Let me stop you. That's not technically accurate.",
        "UNCLEAR_STRUCTURE": "Hold on. Your answer needs better structure.",
        "MISSING_IMPACT": "Wait - what was the actual impact or result?"
    }
    
    return phrases.get(reason, "Let me interrupt you for a moment.")


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_phase_interruption_multiplier(phase: str) -> float:
    """
    Get interruption probability multiplier for current phase
    
    Early phases: Lower interruption rate
    Later phases: Higher interruption rate
    
    Args:
        phase: Current interview phase
        
    Returns:
        Multiplier (0.0 to 2.0)
    """
    
    multipliers = {
        "resume_deep_dive": 0.5,       # 50% less likely
        "core_skill_assessment": 1.0,   # Normal
        "scenario_solving": 1.3,        # 30% more likely
        "stress_testing": 1.8,          # 80% more likely
        "claim_verification": 1.5,      # 50% more likely
        "wrap_up": 0.3                  # 70% less likely
    }
    
    return multipliers.get(phase, 1.0)


def is_interruption_appropriate(
    reason: str,
    phase: str,
    time_in_answer: float
) -> bool:
    """
    Check if interruption is appropriate given context
    
    Args:
        reason: Interruption reason
        phase: Current phase
        time_in_answer: How long they've been speaking
        
    Returns:
        True if appropriate to interrupt
    """
    
    # Don't interrupt too early (give them at least 10 seconds)
    if time_in_answer < 10 and reason not in ["FALSE_CLAIM", "CONTRADICTION"]:
        return False
    
    # Don't interrupt during wrap-up unless critical
    if phase == "wrap_up" and reason not in ["FALSE_CLAIM", "CONTRADICTION"]:
        return False
    
    # Don't interrupt for minor issues in early phases
    early_phases = ["resume_deep_dive"]
    minor_reasons = ["SPEAKING_TOO_LONG", "UNCLEAR_STRUCTURE", "MISSING_IMPACT"]
    
    if phase in early_phases and reason in minor_reasons:
        return False
    
    return True


# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("INTERRUPTION DECISION ENGINE TEST")
    print("=" * 60)
    
    # Test 1: Excessive pausing (should interrupt)
    print("\n1. Test: Excessive pausing")
    audio_metrics = {
        "recording_duration": 15.0,
        "excessive_pause_count": 3,
        "detected_issues": [
            {
                "type": "EXCESSIVE_PAUSING",
                "severity": "critical",
                "evidence": "3 pauses over 3 seconds",
                "priority": 3
            }
        ]
    }
    
    decision = check_interruption_trigger(
        audio_metrics=audio_metrics,
        session_id="test_session_1",
        current_phase="core_skill_assessment",
        interruption_count=0,
        max_interruptions=5
    )
    
    if decision:
        print(f"   Should interrupt: {decision.should_interrupt}")
        print(f"   Action: {decision.action}")
        print(f"   Reason: {decision.reason}")
        print(f"   Evidence: {decision.evidence}")
    
    # Test 2: Speaking too long (should warn only)
    print("\n2. Test: Speaking too long")
    audio_metrics = {
        "recording_duration": 95.0,
        "detected_issues": [
            {
                "type": "SPEAKING_TOO_LONG",
                "severity": "low",
                "evidence": "Speaking for 95 seconds",
                "priority": 10
            }
        ]
    }
    
    decision = check_interruption_trigger(
        audio_metrics=audio_metrics,
        session_id="test_session_2",
        current_phase="core_skill_assessment",
        interruption_count=0,
        max_interruptions=5
    )
    
    if decision:
        print(f"   Action: {decision.action}")
        print(f"   Reason: {decision.reason}")
        if decision.warning_data:
            print(f"   Warning: {decision.warning_data}")
    
    # Test 3: Max interruptions reached
    print("\n3. Test: Max interruptions reached")
    decision = check_interruption_trigger(
        audio_metrics=audio_metrics,
        session_id="test_session_3",
        current_phase="core_skill_assessment",
        interruption_count=5,
        max_interruptions=5
    )
    
    print(f"   Decision: {decision} (should be None)")
    
    print("\n✅ Interruption decision engine test complete!")