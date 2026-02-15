"""
Pressure Engine - Intelligent Interruption Coordination
STEP 3.2: Upgraded with content-aware interruption analysis
"""
from datetime import datetime
from llm_service import get_llm_response
from prompts import clean_question_output

# ============================================
# STEP 3.2: NEW INTELLIGENT IMPORTS
# ============================================
from engines.interruption_analyzer import get_interruption_analyzer
from engines.live_warning_generator import get_warning_generator
from models.interruption_models import InterruptionReason

# ============================================
# INTELLIGENT INTERRUPTION SYSTEM
# ============================================

def check_interruption_trigger(
    recording_duration,
    audio_analysis_report,
    session_id,
    question_number=1
):
    """
    STEP 3.2: NEW - Intelligent content-aware interruption detection
    
    Args:
        recording_duration: How long user has been speaking (seconds)
        audio_analysis_report: Analysis from frontend AudioAnalyzer
        session_id: Current session ID
        question_number: Current question number (for progressive difficulty)
    
    Returns:
        Dict with interruption data or warning data
    """
    
    analyzer = get_interruption_analyzer()
    warning_generator = get_warning_generator()
    
    # Analyze audio patterns (pause detection, confidence, hesitation)
    analysis_result = analyzer.analyze_audio_patterns(
        audio_report=audio_analysis_report,
        session_id=session_id
    )
    
    if not analysis_result:
        # No issues detected
        return {
            "should_interrupt": False,
            "should_warn": False,
            "reason": None
        }
    
    # Check if should interrupt or just warn
    should_interrupt = analysis_result.get("should_interrupt", False)
    action = analysis_result.get("action", "warn")
    
    if should_interrupt and action == "interrupt":
        # INTERRUPT immediately
        reason = analysis_result.get("reason")
        phrase = analyzer.generate_interruption_phrase(reason)
        
        return {
            "should_interrupt": True,
            "should_warn": False,
            "reason": reason,
            "interruption_phrase": phrase,
            "triggered_at": recording_duration,
            "priority": analysis_result.get("priority"),
            "evidence": analysis_result.get("evidence")
        }
    
    elif action == "warn":
        # WARN only (non-interrupting)
        warning_data = warning_generator.generate_warning(
            analysis_result,
            session_id
        )
        
        if warning_data:
            return {
                "should_interrupt": False,
                "should_warn": True,
                "warning": warning_data,
                "reason": analysis_result.get("reason")
            }
    
    return {
        "should_interrupt": False,
        "should_warn": False,
        "reason": None
    }

# ============================================
# GENERATE INTERRUPTION QUESTION
# ============================================

def generate_interruption_question(
    partial_answer,
    interruption_reason,
    session_data,
    current_question_text=None
):
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
        
        # Build context-aware prompt based on interruption reason
        reason_prompts = {
            "EXCESSIVE_PAUSING": "They're struggling with long pauses. Ask a more specific sub-question to help them focus.",
            "HIGH_HESITATION": "They seem very uncertain. Ask for concrete details they're more confident about.",
            "RAMBLING": "They're rambling with filler words. Ask for a specific example or metric.",
            "OFF_TOPIC": "They're avoiding the question. Redirect them back to what was actually asked.",
            "DODGING_QUESTION": "They're deflecting. Push for a direct answer.",
            "VAGUE_CLAIM": "They made a vague claim. Ask for specifics and evidence.",
            "SPEAKING_TOO_LONG": "They've been speaking too long. Ask them to summarize in one sentence.",
            "FALSE_CLAIM": "They said something incorrect. Point it out and ask them to clarify.",
            "CONTRADICTION": "They contradicted themselves. Highlight the contradiction and ask for clarification."
        }
        
        context = reason_prompts.get(interruption_reason, "Ask a sharp follow-up question.")
        
        interruption_prompt = f"""The candidate is CURRENTLY answering this question:
"{current_question_text}"

Their partial answer before interruption:
"{partial_answer}"

Interruption reason: {context}

Generate ONE sharp follow-up question that:
1. Relates ONLY to the current question they're answering
2. Asks for clarification or more specifics about what they just said
3. Is brief and direct (1 sentence max)
4. Maintains professional but firm tone

Output ONLY the question text, nothing else."""
        
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
            "EXCESSIVE_PAUSING": "Let me help you focus - what specific result did you achieve?",
            "RAMBLING": "Can you give me a concrete example with numbers?",
            "OFF_TOPIC": "Wait - can you address the actual question I asked?",
            "DODGING_QUESTION": "Let me stop you there - answer the question directly.",
            "VAGUE_CLAIM": "Be more specific - what exactly did you do?",
            "SPEAKING_TOO_LONG": "Summarize that in one sentence for me.",
            "FALSE_CLAIM": "Hold on - that doesn't sound right. Can you clarify?",
            "CONTRADICTION": "You just contradicted yourself. Which is it?"
        }
        
        return fallbacks.get(interruption_reason, "Can you clarify that point?")

# ============================================
# PROCESS INTERRUPTION
# ============================================

def process_interruption(
    session_data,
    partial_answer,
    interruption_data,
    current_question_text=None
):
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
        current_question_text
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
        "triggered_at_seconds": interruption_data["triggered_at"],
        "priority": interruption_data.get("priority"),
        "evidence": interruption_data.get("evidence")
    })
    
    print(f"🔥 INTELLIGENT INTERRUPTION! Reason: {reason} (Priority: {interruption_data.get('priority')})")
    print(f"   Evidence: {interruption_data.get('evidence')}")
    print(f"   Phrase: {interruption_phrase}")
    print(f"   Follow-up: {followup_question}")
    
    return {
        "interrupted": True,
        "interruption_phrase": interruption_phrase,
        "reason": reason,
        "followup_question": followup_question,
        "partial_answer_received": partial_answer,
        "priority": interruption_data.get("priority"),
        "evidence": interruption_data.get("evidence")
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
        "completion_status": "interrupted",
        "priority": interruption_data.get("priority"),
        "evidence": interruption_data.get("evidence")
    }
    
    if "answers" not in session_data:
        session_data["answers"] = []
    
    session_data["answers"].append(qa_pair)

# ============================================
# TESTING FUNCTION
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("INTELLIGENT PRESSURE ENGINE TEST")
    print("=" * 60)
    
    # Test with audio analysis report (simulated)
    print("\n1. Testing excessive pausing detection:")
    audio_report = {
        "recording_duration": 15.0,
        "excessive_pause_count": 3,
        "pause_ratio": 0.45,
        "detected_issues": [
            {
                "type": "EXCESSIVE_PAUSING",
                "severity": "critical",
                "evidence": "3 pauses over 3 seconds",
                "priority": 3
            }
        ]
    }
    
    result = check_interruption_trigger(
        recording_duration=15.0,
        audio_analysis_report=audio_report,
        session_id="test_session",
        question_number=2
    )
    
    print(f"   Should interrupt: {result.get('should_interrupt')}")
    print(f"   Reason: {result.get('reason')}")
    if result.get('should_interrupt'):
        print(f"   Phrase: {result.get('interruption_phrase')}")
    
    print("\n2. Testing warning (rambling):")
    audio_report_warn = {
        "recording_duration": 20.0,
        "detected_issues": [
            {
                "type": "HIGH_HESITATION",
                "severity": "high",
                "evidence": "40% of time spent pausing",
                "priority": 5
            }
        ]
    }
    
    result2 = check_interruption_trigger(
        recording_duration=20.0,
        audio_analysis_report=audio_report_warn,
        session_id="test_session_2",
        question_number=1
    )
    
    print(f"   Should warn: {result2.get('should_warn')}")
    if result2.get('warning'):
        print(f"   Warning: {result2['warning'].get('message')}")
    
    print("\n✅ Intelligent pressure engine test complete!")