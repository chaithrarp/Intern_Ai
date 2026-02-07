"""
Interview Prompts and System Instructions
Defines how the AI interviewer behaves
"""

# ============================================
# SYSTEM PROMPT - Defines AI Interviewer Behavior
# ============================================

INTERVIEWER_SYSTEM_PROMPT = """You are a professional behavioral interviewer conducting a mock interview for a software engineering position.

Your role:
- Ask ONE behavioral/technical question at a time
- Use the STAR method (Situation, Task, Action, Result) framework
- Ask follow-up questions based on the candidate's previous answers
- Be professional but conversational
- Keep questions clear and concise (1-2 sentences max)
- DO NOT give feedback or praise during the interview
- DO NOT ask multiple questions at once

Question types to focus on:
1. Past experiences and projects
2. Problem-solving scenarios
3. Teamwork and collaboration
4. Handling challenges and failures
5. Technical skills and tools
6. Career goals and motivations

Important rules:
- Output ONLY the question text, nothing else
- No preambles like "Here's my question:" or "Let me ask you:"
- No labels, bullet points, or formatting
- Just the raw question text
- Maximum 2 sentences per question

Example good outputs:
"Tell me about a time when you had to debug a complex issue under a tight deadline. How did you approach it?"
"I see you worked on a mobile app project. What was the biggest technical challenge you faced during development?"

Example bad outputs:
"Question: Tell me about..." (don't include "Question:")
"1. Tell me about..." (don't use numbering)
"Great! Now let me ask..." (no preambles)
"""

# ============================================
# CONVERSATION CONTEXT BUILDER
# ============================================

def build_conversation_history(session_data):
    """
    Build conversation history from session data
    
    Args:
        session_data: Dictionary containing 'answers' list
        
    Returns:
        List of message dictionaries for LLM
    """
    messages = []
    
    # Add system prompt
    messages.append({
        "role": "system",
        "content": INTERVIEWER_SYSTEM_PROMPT
    })
    
    # Add conversation history
    if "answers" in session_data:
        for qa_pair in session_data["answers"]:
            # Add the question that was asked
            messages.append({
                "role": "assistant",
                "content": qa_pair.get("question", "")
            })
            
            # Add the candidate's answer
            messages.append({
                "role": "user",
                "content": qa_pair.get("answer", "")
            })
    
    return messages

# ============================================
# FIRST QUESTION PROMPT
# ============================================

def get_first_question_prompt():
    """
    Prompt for generating the first question
    """
    return "Start the interview with an opening question that asks the candidate to introduce themselves and their background."

# ============================================
# FOLLOW-UP QUESTION PROMPT
# ============================================

def get_followup_question_prompt(previous_answer):
    """
    Prompt for generating follow-up questions
    
    Args:
        previous_answer: The candidate's last answer
        
    Returns:
        String prompt for generating next question
    """
    return f"""Based on the candidate's previous answer, ask a relevant follow-up question.

The candidate just said:
"{previous_answer}"

Generate ONE follow-up question that:
1. Explores their answer deeper (ask about specifics, challenges, or outcomes)
2. OR moves to a different behavioral/technical topic
3. Maintains natural interview flow

Remember: Output ONLY the question text, nothing else."""

# ============================================
# QUESTION VALIDATION
# ============================================

def clean_question_output(raw_output):
    """
    Clean up LLM output to ensure it's just the question
    
    Args:
        raw_output: Raw text from LLM
        
    Returns:
        Cleaned question text
    """
    # Remove common unwanted prefixes
    unwanted_prefixes = [
        "Question:",
        "Here's my question:",
        "Let me ask:",
        "Great!",
        "Excellent.",
        "Sure.",
        "Okay.",
    ]
    
    cleaned = raw_output.strip()
    
    for prefix in unwanted_prefixes:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
    
    # Remove numbering (e.g., "1. Tell me...")
    if cleaned and cleaned[0].isdigit() and '. ' in cleaned[:5]:
        cleaned = cleaned.split('. ', 1)[1]
    
    return cleaned.strip()