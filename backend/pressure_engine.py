"""
Pressure Engine - Interruption Coordination
Handles timing and triggering of interruptions during interviews
"""
from pressure_modes import (
    should_interrupt,
    get_interruption_phrase,
    get_interruption_followup_prompt
)
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

def check_interruption_trigger(recording_duration, partial_transcript, question_number=1, persona="standard_professional"):
    """
    Check if we should interrupt based on duration, content, question number, and persona
    
    Args:
        recording_duration: How long user has been speaking (seconds)
        partial_transcript: What they've said so far (if available)
        question_number: Current question number (for progressive difficulty)
        persona: Interviewer persona (friendly_coach, standard_professional, aggressive_challenger)
    
    Returns:
        Dict with interruption data
    """
    
    should_int, reason = should_interrupt(recording_duration, partial_transcript, question_number, persona)
    
    if should_int:
        phrase = get_interruption_phrase(persona)  # Get persona-specific phrase
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

def generate_interruption_question(partial_answer, interruption_reason, session_data, current_question_text=None):
    """
    Generate follow-up question after interrupting user
    """
    try:
        from prompts import build_conversation_history
        messages = build_conversation_history(session_data)
        
        if current_question_text:
            messages.append({
                "role": "assistant",
                "content": f"INTERVIEWER ASKED: {current_question_text}"
            })
            messages.append({
                "role": "user", 
                "content": f"CANDIDATE WAS SAYING: {partial_answer} (then got interrupted)"
            })
        
        # PHASE 8: Get persona from session
        persona = session_data.get("persona", "standard_professional")
        
        interruption_prompt = get_interruption_followup_prompt(
            partial_answer,
            interruption_reason,
            persona  # Pass persona to prompt generation
        )
        
        # Override prompt to emphasize CURRENT question
        if current_question_text:
            interruption_prompt = f"""The candidate is CURRENTLY answering this question:
"{current_question_text}"

Their partial answer before interruption:
"{partial_answer}"

Generate ONE sharp follow-up question that:
1. Relates ONLY to the current question they're answering
2. Asks for clarification or more specifics about what they just said
3. Is brief and direct (1 sentence max)
4. Does NOT reference previous questions or topics

Remember: Output ONLY the question text, nothing else."""
        
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

def process_interruption(session_data, partial_answer, interruption_data, current_question_text=None):
    """
    Handle interruption event and generate response
    
    Args:
        session_data: Current interview session
        partial_answer: User's incomplete answer
        interruption_data: Data from check_interruption_trigger
        current_question_text: The actual question being answered NOW
    """
    
    interruption_phrase = interruption_data["interruption_phrase"]
    reason = interruption_data["reason"]
    
    # Generate follow-up question WITH current question context
    followup_question = generate_interruption_question(
        partial_answer,
        reason,
        session_data,
        current_question_text  # ← ADD THIS
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
    
    # Test interruption trigger with question numbers
    print("\n2. Testing interruption trigger (progressive):")
    test_transcript = "Um, so like, I was working on this project, you know..."
    
    for q_num in [1, 2, 3, 4, 5]:
        result = check_interruption_trigger(15, test_transcript, q_num)
        if result["should_interrupt"]:
            print(f"  Q{q_num} at 15s: INTERRUPT ({result['reason']}) - '{result['interruption_phrase']}'")
        else:
            print(f"  Q{q_num} at 15s: Continue")
    
    print("\n✅ Pressure engine test complete!")