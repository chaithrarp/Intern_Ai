"""
Pressure Modes - Interruption Detection Logic with Personas
PHASE 8: Added 3 interviewer personas with different pressure levels
"""

import random

# ============================================
# PHASE 8: PERSONA DEFINITIONS
# ============================================

PERSONAS = {
    "friendly_coach": {
        "name": "Friendly Coach",
        "emoji": "🟢",
        "description": "Supportive and encouraging - perfect for practice",
        "interruption_probability": 0.20,  # 20% chance
        "interruption_phrases": [
            "Let me pause you there for a moment...",
            "That's interesting! Can I ask a quick follow-up?",
            "I appreciate that answer. Let me dig deeper...",
            "Great start! I'd love to hear more about...",
            "That's a good point. Could you clarify...",
        ],
        "tone": "supportive"
    },
    "standard_professional": {
        "name": "Standard Professional",
        "emoji": "🟡",
        "description": "Realistic interview simulation - balanced pressure",
        "interruption_probability": 0.50,  # 50% chance (default)
        "interruption_phrases": [
            "Hold on - let me stop you there.",
            "Wait - can you clarify that?",
            "I need to interrupt you for a second.",
            "Let me ask you something specific about that.",
            "Pause for a moment - I have a follow-up.",
        ],
        "tone": "neutral"
    },
    "aggressive_challenger": {
        "name": "Aggressive Challenger",
        "emoji": "🔴",
        "description": "High-pressure stress test - maximum difficulty",
        "interruption_probability": 0.80,  # 80% chance
        "interruption_phrases": [
            "Stop right there. That doesn't answer my question.",
            "I'm going to cut you off - you're rambling.",
            "No, no, no. Be more specific.",
            "Let me stop you. You're not addressing the core issue.",
            "I need a straight answer. What exactly did you do?",
            "That's too vague. Give me concrete details.",
        ],
        "tone": "aggressive"
    }
}

# Default persona if none specified
DEFAULT_PERSONA = "standard_professional"

# ============================================
# FILLER WORD DETECTION
# ============================================

FILLER_WORDS = ['um', 'uh', 'like', 'you know', 'basically', 'actually', 'literally', 'kind of', 'sort of', 'i mean']

def detect_rambling(text):
    """
    Detect if transcript contains excessive filler words (rambling indicator)
    """
    if not text or len(text) < 20:
        return False
    
    text_lower = text.lower()
    words = text_lower.split()
    
    if len(words) < 5:
        return False
    
    # Count filler words
    filler_count = sum(1 for word in words if word in FILLER_WORDS)
    
    # Check for multi-word fillers
    for filler in ['you know', 'i mean', 'kind of', 'sort of']:
        filler_count += text_lower.count(filler)
    
    # If more than 30% of words are fillers, it's rambling
    filler_ratio = filler_count / len(words)
    
    return filler_ratio > 0.25  # Lowered threshold for more sensitivity

# ============================================
# INTERRUPTION DECISION LOGIC
# ============================================

def should_interrupt(recording_duration, partial_transcript, question_number=1, persona="standard_professional"):
    """
    Determine if interruption should happen based on persona and conditions
    
    Args:
        recording_duration: How long user has been speaking (seconds)
        partial_transcript: What they've said so far
        question_number: Current question number (for progressive difficulty)
        persona: One of 'friendly_coach', 'standard_professional', 'aggressive_challenger'
    
    Returns:
        Tuple: (should_interrupt: bool, reason: str)
    """
    
    # Get persona configuration
    persona_config = PERSONAS.get(persona, PERSONAS[DEFAULT_PERSONA])
    base_probability = persona_config["interruption_probability"]
    
    # Progressive difficulty: Increase probability as interview progresses
    difficulty_multiplier = 1.0 + (question_number - 1) * 0.1  # +10% per question
    adjusted_probability = min(base_probability * difficulty_multiplier, 0.95)  # Cap at 95%
    
    # Condition 1: Rambling detection (high priority for all personas)
    if detect_rambling(partial_transcript):
        # Even friendly coach interrupts rambling (but with lower chance)
        rambling_chance = adjusted_probability * 1.5  # 50% boost
        if random.random() < rambling_chance:
            return (True, "rambling")
    
    # Condition 2: Speaking too long (time-based)
    # Friendly: 25+ seconds, Standard: 18+ seconds, Aggressive: 12+ seconds
    time_thresholds = {
        "friendly_coach": 25,
        "standard_professional": 18,
        "aggressive_challenger": 12
    }
    
    time_threshold = time_thresholds.get(persona, 18)
    
    if recording_duration >= time_threshold:
        if random.random() < adjusted_probability:
            return (True, "time")
    
    # Condition 3: Random interruption (for realism)
    # Only after minimum speaking time
    min_time_thresholds = {
        "friendly_coach": 15,
        "standard_professional": 10,
        "aggressive_challenger": 6
    }
    
    min_time = min_time_thresholds.get(persona, 10)
    
    if recording_duration >= min_time:
        # Random chance based on persona probability
        if random.random() < (adjusted_probability * 0.3):  # 30% of base probability
            return (True, "clarification")
    
    return (False, None)

# ============================================
# GET INTERRUPTION PHRASE BY PERSONA
# ============================================

def get_interruption_phrase(persona="standard_professional"):
    """
    Get a random interruption phrase for the specified persona
    
    Args:
        persona: Persona identifier
    
    Returns:
        String: Interruption phrase
    """
    persona_config = PERSONAS.get(persona, PERSONAS[DEFAULT_PERSONA])
    return random.choice(persona_config["interruption_phrases"])

def get_interruption_followup_prompt(partial_answer, interruption_reason, persona="standard_professional"):
    """
    Generate prompt for LLM to create interruption follow-up question
    Tailored to persona tone
    
    Args:
        partial_answer: What the user said before interruption
        interruption_reason: Why we interrupted
        persona: Persona identifier
    
    Returns:
        String: Prompt for LLM
    """
    persona_config = PERSONAS.get(persona, PERSONAS[DEFAULT_PERSONA])
    tone = persona_config["tone"]
    
    tone_instructions = {
        "supportive": "Be encouraging and constructive. Frame the follow-up as helping them improve their answer.",
        "neutral": "Be professional and direct. Ask for specific clarification or examples.",
        "aggressive": "Be sharp and demanding. Push for concrete details and challenge vague statements."
    }
    
    tone_instruction = tone_instructions.get(tone, tone_instructions["neutral"])
    
    reason_context = {
        "rambling": f"They were using too many filler words and seemed to be rambling. {tone_instruction}",
        "time": f"They've been speaking for too long without getting to the point. {tone_instruction}",
        "clarification": f"Ask for more specific details about what they just mentioned. {tone_instruction}",
        "random": f"Challenge them with a sharp follow-up to test their thinking. {tone_instruction}"
    }
    
    context = reason_context.get(interruption_reason, reason_context["clarification"])
    
    return f"""The candidate just said: "{partial_answer}"

Reason for interruption: {context}

Generate ONE sharp follow-up question that:
1. Directly relates to what they just said
2. Asks for clarification, specifics, or challenges their statement
3. Is brief and direct (1 sentence max)
4. Matches a {tone} tone

Output ONLY the question text, nothing else."""

# ============================================
# GET ALL PERSONAS (for frontend)
# ============================================

def get_all_personas():
    """
    Return all persona configurations for frontend
    """
    return PERSONAS

# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    print("=" * 50)
    print("TESTING PRESSURE MODES WITH PERSONAS")
    print("=" * 50)
    
    test_transcript = "Um, so like, I was basically working on this project, you know, and it was kind of challenging..."
    
    print("\n1. Testing rambling detection:")
    is_rambling = detect_rambling(test_transcript)
    print(f"   Rambling detected: {is_rambling}")
    
    print("\n2. Testing interruption logic across personas:")
    for persona_id, persona_config in PERSONAS.items():
        print(f"\n   Persona: {persona_config['emoji']} {persona_config['name']}")
        print(f"   Base probability: {persona_config['interruption_probability']*100}%")
        
        # Test at different durations
        for duration in [8, 15, 20]:
            should_int, reason = should_interrupt(duration, test_transcript, question_number=1, persona=persona_id)
            status = "INTERRUPT" if should_int else "Continue"
            print(f"   - At {duration}s: {status} ({reason if reason else 'N/A'})")
    
    print("\n3. Testing interruption phrases:")
    for persona_id, persona_config in PERSONAS.items():
        phrase = get_interruption_phrase(persona_id)
        print(f"   {persona_config['emoji']} {persona_config['name']}: \"{phrase}\"")
    
    print("\n✅ Persona test complete!")