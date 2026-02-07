"""
Pressure Modes - Interviewer Personas
Defines different interviewer behaviors and pressure patterns
"""

import random

# ============================================
# INTERRUPTION PHRASES
# ============================================

INTERRUPTION_PHRASES = {
    "aggressive": [
        "Let me stop you there.",
        "Hold on - that's not what I asked.",
        "Wait, wait. Let me jump in here.",
        "I'm going to cut you off for a second.",
        "Pause. I need you to clarify something.",
        "Stop right there. Back up a moment.",
        "Let me interrupt you - that doesn't answer my question.",
        "Hold that thought. You're going off track.",
    ],
    
    "gentle": [
        "Sorry to interrupt, but I want to understand something.",
        "Can I pause you there for a moment?",
        "Let me just jump in quickly.",
        "I want to make sure I understand - can I ask something?",
        "Before you continue, could you clarify...",
        "I don't mean to cut you off, but...",
    ],
    
    "neutral": [
        "Let me stop you there.",
        "Can I interrupt for a second?",
        "Hold on, I have a quick question.",
        "Before you go further...",
        "Let me pause you here.",
    ]
}

# ============================================
# FOLLOW-UP QUESTION PROMPTS (After Interruption)
# ============================================

def get_interruption_followup_prompt(partial_answer, interruption_reason):
    """
    Generate prompt for follow-up question after interruption
    
    Args:
        partial_answer: What the user said before interruption
        interruption_reason: Why we interrupted (rambling, time, clarification)
    
    Returns:
        String prompt for LLM
    """
    
    if interruption_reason == "rambling":
        return f"""The candidate was rambling and going off-topic. Their partial answer was:
"{partial_answer}"

Generate ONE sharp follow-up question that:
1. Redirects them to answer the original question
2. Asks for a specific, concrete example
3. Is brief and direct (1 sentence max)

Remember: Output ONLY the question text, nothing else."""

    elif interruption_reason == "clarification":
        return f"""The candidate said:
"{partial_answer}"

Generate ONE clarifying question that:
1. Asks them to explain a specific term or concept they mentioned
2. OR asks for more detail on something vague they said
3. Is conversational but direct (1 sentence max)

Remember: Output ONLY the question text, nothing else."""

    elif interruption_reason == "time":
        return f"""The candidate has been speaking for a while. Their answer so far:
"{partial_answer}"

Generate ONE question that:
1. Acknowledges what they said briefly
2. Asks them to be more concise or focus on one aspect
3. Keeps the pressure up (1 sentence max)

Remember: Output ONLY the question text, nothing else."""
    
    else:  # random interruption
        return f"""The candidate was interrupted mid-answer. They said:
"{partial_answer}"

Generate ONE follow-up question that:
1. Relates to something they mentioned
2. Probes deeper or asks for clarification
3. Maintains interview pressure (1 sentence max)

Remember: Output ONLY the question text, nothing else."""

# ============================================
# PRESSURE MODE SELECTOR
# ============================================

def select_pressure_mode():
    """
    Randomly select a pressure mode for this moment
    
    Returns:
        String: "aggressive", "gentle", or "neutral"
    """
    # 40% aggressive, 30% neutral, 30% gentle
    return random.choices(
        ["aggressive", "gentle", "neutral"],
        weights=[0.4, 0.3, 0.3]
    )[0]

def get_interruption_phrase(mode=None):
    """
    Get a random interruption phrase for the given mode
    
    Args:
        mode: "aggressive", "gentle", or "neutral" (None = random)
    
    Returns:
        String: Interruption phrase
    """
    if mode is None:
        mode = select_pressure_mode()
    
    return random.choice(INTERRUPTION_PHRASES[mode])

# ============================================
# ADAPTIVE RAMBLING DETECTION
# ============================================

def detect_rambling(transcript_text):
    """
    Detect if user is rambling or going off-topic
    
    Args:
        transcript_text: The user's answer so far
    
    Returns:
        Boolean: True if likely rambling
    """
    # Simple heuristics (can be improved with NLP later)
    
    # Check for filler words
    filler_words = ["um", "uh", "like", "you know", "basically", "actually", "literally"]
    filler_count = sum(transcript_text.lower().count(word) for word in filler_words)
    
    # Check word count
    word_count = len(transcript_text.split())
    
    # Check for repetition (same word multiple times)
    words = transcript_text.lower().split()
    unique_ratio = len(set(words)) / len(words) if words else 1
    
    # Rambling indicators:
    # - High filler word count (>5 in a short answer)
    # - Very long answer (>100 words without finishing)
    # - Low unique word ratio (<0.5, lots of repetition)
    
    is_rambling = (
        (filler_count > 5) or
        (word_count > 100) or
        (unique_ratio < 0.5 and word_count > 30)
    )
    
    return is_rambling

# ============================================
# SHOULD INTERRUPT LOGIC
# ============================================

def should_interrupt(answer_duration_seconds, transcript_text):
    """
    Determine if we should interrupt based on time and content
    
    Args:
        answer_duration_seconds: How long they've been speaking
        transcript_text: What they've said so far
    
    Returns:
        Tuple: (should_interrupt: bool, reason: str)
    """
    # 30% chance of interruption
    if random.random() > 0.3:
        return False, None
    
    # Don't interrupt too early (wait at least 5 seconds)
    if answer_duration_seconds < 5:
        return False, None
    
    # Adaptive: Check if rambling
    if detect_rambling(transcript_text):
        return True, "rambling"
    
    # Random interruption window: 8-20 seconds
    if 8 <= answer_duration_seconds <= 20:
        # Higher chance as time goes on
        interrupt_probability = (answer_duration_seconds - 8) / 12  # 0 to 1
        if random.random() < interrupt_probability:
            # Decide reason
            reasons = ["clarification", "time", "random"]
            reason = random.choice(reasons)
            return True, reason
    
    return False, None

# ============================================
# TESTING FUNCTION
# ============================================

if __name__ == "__main__":
    print("=" * 50)
    print("PRESSURE MODES TEST")
    print("=" * 50)
    
    # Test interruption phrases
    print("\n1. Testing interruption phrases:")
    for mode in ["aggressive", "gentle", "neutral"]:
        phrase = get_interruption_phrase(mode)
        print(f"  {mode.upper()}: {phrase}")
    
    # Test rambling detection
    print("\n2. Testing rambling detection:")
    normal_answer = "I worked on a React project where we built a dashboard for analytics."
    rambling_answer = "Um, so like, basically, I was working on this project, you know, and like, it was about React, and um, basically we were building something, you know, like a dashboard kind of thing, and um, actually it was for analytics, basically."
    
    print(f"  Normal answer rambling? {detect_rambling(normal_answer)}")
    print(f"  Rambling answer rambling? {detect_rambling(rambling_answer)}")
    
    # Test interruption logic
    print("\n3. Testing interruption logic (30% chance):")
    for i in range(10):
        should_int, reason = should_interrupt(12, "I worked on a project with my team")
        if should_int:
            print(f"  Test {i+1}: INTERRUPT ({reason})")
        else:
            print(f"  Test {i+1}: Continue")
    
    print("\n✅ Pressure modes test complete!")