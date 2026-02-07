"""
Pressure Engine - Interruption Coordination
Handles timing and triggering of interruptions during interviews
"""

from datetime import datetime
from pressure_modes import (
    should_interrupt,
    get_interruption_phrase,
    get_interruption_followup_prompt
)
from llm_service import get_llm_response
from prompts import clean_question_output
import random

# ============================================
# INTERRUPTION TIMING
# ============================================

def calculate_interruption_time():
    """
    Calculate when to trigger an interruption (random 5-20 seconds)
    
    Returns:
        Float: Seconds to wait before interruption
    """
    # Random between 5-20 seconds
    return random.uniform(5, 20)

# ============================================
# CHECK IF INTERRUPTION SHOULD TRIGGER
# ============================================

def check_interruption_trigger(recording_duration, partial_transcript):
    """
    Check if we should interrupt based on duration and content
    
    Args:
        recording_duration: How long user has been speaking (seconds)
        partial_transcript: What they've said so far (if available)
    
    Returns:
        Dict with:
            - should_interrupt: bool
            - reason: str (rambling, time, clarification, random, or None)
            - interruption_phrase: str (what AI says when interrupting)
    """
    
    should_int, reason = should_interrupt(recording_duration, partial_transcript)
    
    if should_int:
        phrase = get_interruption_phrase()  # Random mode
        return {
            "should_interrupt": True,
            "reason": reason,
            "interruption_phrase": phrase,
            "triggered_at": recording_duration
        }
    
    return {
        "should_interrupt": False,
        "reason": None,
        "interruption_phrase": None,
        "triggered_at": None
    }

# ============================================
# GENERATE INTERRUPTION QUESTION
# ============================================

def generate_interruption_question(partial_answer, interruption_reason, session_data):
    """
    Generate follow-up question after interrupting user
    
    Args:
        partial_answer: What user said before being interrupted
        interruption_reason: Why we interrupted
        session_data: Current interview session data
    
    Returns:
        String: The interruption follow-up question
    """
    try:
        # Build conversation history
        from prompts import build_conversation_history
        messages = build_conversation_history(session_data)
        
        # Add interruption context
        interruption_prompt = get_interruption_followup_prompt(
            partial_answer,
            interruption_reason
        )
        
        messages.append({
            "role": "user",
            "content": interruption_prompt
        })
        
        # Get LLM response
        raw_response = get_llm_response(messages)
        cleaned_question = clean_question_output(raw_response)
        
        return cleaned_question
    
    except Exception as e:
        print(f"Error generating interruption question: {str(e)}")
        
        # Fallback interruption questions
        fallbacks = {
            "rambling": "Can you give me a more specific example?",
            "clarification": "Wait - can you explain that last part more clearly?",
            "time": "Let me stop you there. Can you summarize that in one sentence?",
            "random": "Hold on - can you elaborate on what you just mentioned?"
        }
        
        return fallbacks.get(interruption_reason, "Can you clarify that point?")

# ============================================
# PROCESS INTERRUPTION
# ============================================

def process_interruption(session_data, partial_answer, interruption_data):
    """
    Handle interruption event and generate response
    
    Args:
        session_data: Current interview session
        partial_answer: User's incomplete answer
        interruption_data: Data from check_interruption_trigger
    
    Returns:
        Dict with interruption details and next question
    """
    
    interruption_phrase = interruption_data["interruption_phrase"]
    reason = interruption_data["reason"]
    
    # Generate follow-up question
    followup_question = generate_interruption_question(
        partial_answer,
        reason,
        session_data
    )
    
    # Log interruption event
    if "interruptions" not in session_data:
        session_data["interruptions"] = []
    
    session_data["interruptions"].append({
        "timestamp": datetime.now().isoformat(),
        "partial_answer": partial_answer,
        "reason": reason,
        "interruption_phrase": interruption_phrase,
        "followup_question": followup_question,
        "triggered_at_seconds": interruption_data["triggered_at"]
    })
    
    print(f"🔥 INTERRUPTION! Reason: {reason}")
    print(f"   Phrase: {interruption_phrase}")
    print(f"   Follow-up: {followup_question}")
    
    return {
        "interrupted": True,
        "interruption_phrase": interruption_phrase,
        "reason": reason,
        "followup_question": followup_question,
        "partial_answer_received": partial_answer
    }

# ============================================
# STORE INTERRUPTED ANSWER
# ============================================

def store_interrupted_answer(session_data, question_id, partial_answer, interruption_data):
    """
    Store the partial answer that was interrupted
    
    Args:
        session_data: Current session
        question_id: ID of question being answered
        partial_answer: Incomplete answer
        interruption_data: Interruption details
    """
    
    # Get current question text
    current_question = session_data.get("current_question_text", "")
    
    # Store as interrupted Q&A pair
    qa_pair = {
        "question_id": question_id,
        "question": current_question,
        "answer": partial_answer,
        "interrupted": True,
        "interruption_reason": interruption_data["reason"],
        "completion_status": "interrupted"
    }
    
    if "answers" not in session_data:
        session_data["answers"] = []
    
    session_data["answers"].append(qa_pair)

# ============================================
# TESTING FUNCTION
# ============================================

if __name__ == "__main__":
    print("=" * 50)
    print("PRESSURE ENGINE TEST")
    print("=" * 50)
    
    # Test interruption timing
    print("\n1. Testing interruption timing:")
    for i in range(5):
        time_to_interrupt = calculate_interruption_time()
        print(f"  Attempt {i+1}: Interrupt at {time_to_interrupt:.1f} seconds")
    
    # Test interruption trigger
    print("\n2. Testing interruption trigger:")
    test_transcript = "Um, so like, I was working on this project, you know..."
    
    for duration in [3, 8, 12, 15, 20]:
        result = check_interruption_trigger(duration, test_transcript)
        if result["should_interrupt"]:
            print(f"  At {duration}s: INTERRUPT ({result['reason']}) - '{result['interruption_phrase']}'")
        else:
            print(f"  At {duration}s: Continue")
    
    print("\n✅ Pressure engine test complete!")