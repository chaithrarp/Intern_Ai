"""
AI Interview Engine
Handles interview flow and question generation using LLM
"""

from llm_service import get_llm_response
from prompts import (
    build_conversation_history,
    get_first_question_prompt,
    get_followup_question_prompt,
    clean_question_output
)
import config

# ============================================
# GENERATE FIRST QUESTION
# ============================================

def generate_first_question(resume_context: str = None):
    """
    Generate the opening interview question
    
    Args:
        resume_context: Optional resume context for personalized questions
    
    Returns:
        String: The first question
    """
    try:
        if resume_context:
            print(f"📄 Resume context received! Length: {len(resume_context)} characters")
            print(f"   First 200 chars: {resume_context[:200]}...")
        else:
            print("⚠️ No resume context - using generic questions")
        # Base system prompt
        system_prompt = """You are a professional behavioral interviewer. 
Ask ONE opening question to start the interview. 
The question should ask the candidate to introduce themselves.
Output ONLY the question text, nothing else."""
        
        # Add resume context if provided
        if resume_context:
            system_prompt += f"\n\n{resume_context}"
            system_prompt += """

Based on the candidate's resume above, ask a personalized opening question that:
1. Acknowledges something specific from their background
2. Asks them to elaborate on their most relevant experience
3. Feels natural and conversational

For example: "I see you have experience with [technology/company]. Can you walk me through your background and what led you to that role?" """
        
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": get_first_question_prompt()
            }
        ]
        
        raw_response = get_llm_response(messages)
        cleaned_question = clean_question_output(raw_response)
        
        return cleaned_question
    
    except Exception as e:
        print(f"Error generating first question: {str(e)}")
        # Fallback question if LLM fails
        if resume_context:
            return "I've reviewed your resume. Can you walk me through your background and highlight your most relevant experiences?"
        return "Tell me about yourself and your background in software engineering."
# ============================================
# GENERATE NEXT QUESTION
# ============================================

def generate_next_question(session_data):
    """
    Generate next interview question based on conversation history
    
    Args:
        session_data: Dictionary containing interview session data
            Must have 'answers' list with previous Q&A pairs
            May have 'resume_context' for personalized questions
    
    Returns:
        String: The next question
    """
    try:
        # Build conversation history
        messages = build_conversation_history(session_data)
        
        # Add resume context to system message if available
        if session_data.get("resume_context"):
            # Find the system message and enhance it
            for msg in messages:
                if msg["role"] == "system":
                    msg["content"] += f"\n\n{session_data['resume_context']}"
                    msg["content"] += """

Remember to reference the candidate's resume when appropriate. Ask follow-up questions about:
- Specific projects or technologies mentioned in their resume
- Their role and responsibilities at companies they've worked for
- Skills they've listed and how they've applied them
- Any gaps or transitions in their career path

Make the interview feel personalized and realistic."""
                    break
        
        # Get the last answer
        if session_data.get("answers"):
            last_answer = session_data["answers"][-1].get("answer", "")
            followup_prompt = get_followup_question_prompt(last_answer)
        else:
            # No answers yet, ask first question
            followup_prompt = get_first_question_prompt()
        
        # Add the prompt for next question
        messages.append({
            "role": "user",
            "content": followup_prompt
        })
        
        # Get LLM response
        raw_response = get_llm_response(messages)
        cleaned_question = clean_question_output(raw_response)
        
        return cleaned_question
    
    except Exception as e:
        print(f"Error generating next question: {str(e)}")
        # Fallback questions if LLM fails
        fallback_questions = [
            "Can you describe a challenging project you worked on recently?",
            "How do you approach debugging complex issues?",
            "Tell me about a time you had to learn a new technology quickly.",
            "How do you handle disagreements with team members?",
            "What's your approach to code review and maintaining code quality?"
        ]
        
        # Pick a fallback based on how many questions asked
        question_number = len(session_data.get("answers", []))
        fallback_index = question_number % len(fallback_questions)
        
        return fallback_questions[fallback_index]

# ============================================
# CHECK IF INTERVIEW SHOULD END
# ============================================

def should_end_interview(session_data):
    """
    Determine if interview should end
    
    Args:
        session_data: Dictionary containing interview session data
    
    Returns:
        Boolean: True if interview should end
    """
    num_questions = len(session_data.get("answers", []))
    return num_questions >= config.MAX_QUESTIONS_PER_SESSION

# ============================================
# START AI INTERVIEW
# ============================================

def start_ai_interview(session_id, resume_context: str = None):
    """
    Initialize AI interview session
    
    Args:
        session_id: String session identifier
        resume_context: Optional resume context for personalized questions
        
    Returns:
        Dictionary with session data and first question
    """
    try:
        # Generate first question (with resume context if provided)
        first_question = generate_first_question(resume_context)
        
        # Log if using resume
        if resume_context:
            print(f"📄 Starting resume-based interview for session: {session_id}")
            print(f"   Resume length: {len(resume_context)} chars")
        
        return {
            "session_id": session_id,
            "question": {
                "id": 1,
                "question": first_question,
                "category": "opening_resume" if resume_context else "opening"
            },
            "question_number": 1,
            "total_questions": config.MAX_QUESTIONS_PER_SESSION,
            "ai_generated": True,
            "resume_based": resume_context is not None
        }
    
    except Exception as e:
        print(f"Error starting AI interview: {str(e)}")
        raise

# ============================================
# PROCESS ANSWER AND GET NEXT QUESTION
# ============================================

def process_answer_and_continue(session_data, question_id, answer_text):
    """
    Process answer and generate next question
    
    Args:
        session_data: Current session data
        question_id: ID of question being answered
        answer_text: The answer text
        
    Returns:
        Dictionary with next question or completion status
    """
    try:
        # Get current question text (if exists)
        current_question = ""
        if "current_question_text" in session_data:
            current_question = session_data["current_question_text"]
        
        # Store the Q&A pair
        qa_pair = {
            "question_id": question_id,
            "question": current_question,
            "answer": answer_text
        }
        
        if "answers" not in session_data:
            session_data["answers"] = []
        
        session_data["answers"].append(qa_pair)
        
        # Check if interview should end
        if should_end_interview(session_data):
            return {
                "completed": True,
                "message": "Interview completed!",
                "total_answers": len(session_data["answers"])
            }
        
        # Generate next question
        next_question_text = generate_next_question(session_data)
        next_question_id = len(session_data["answers"]) + 1
        
        # Store current question text for next iteration
        session_data["current_question_text"] = next_question_text
        
        return {
            "completed": False,
            "question": {
                "id": next_question_id,
                "question": next_question_text,
                "category": "ai_generated"
            },
            "question_number": next_question_id,
            "total_questions": config.MAX_QUESTIONS_PER_SESSION,
            "ai_generated": True
        }
    
    except Exception as e:
        print(f"Error processing answer: {str(e)}")
        raise