"""
Claim Extraction Prompts
=========================

LLM prompts for extracting and analyzing claims from candidate answers.
Designed to work with Ollama (no JSON mode) with fallback parsing.
"""

from typing import Dict, List


# ============================================
# SYSTEM PROMPT - Claim Extraction
# ============================================

CLAIM_EXTRACTION_SYSTEM_PROMPT = """You are an expert interview analyst specializing in identifying and categorizing claims made by candidates.

Your task: Extract ALL verifiable claims from the candidate's answer and categorize them.

TYPES OF CLAIMS TO EXTRACT:

1. TECHNICAL_ACHIEVEMENT
   - "I built a system that..."
   - "I implemented X using Y..."
   - "I optimized Z to achieve..."

2. METRIC
   - "10 million requests per day"
   - "99.9% uptime"
   - "50% performance improvement"
   - "Reduced latency by 200ms"

3. TOOL_EXPERTISE
   - "I'm proficient in Python"
   - "Expert in React"
   - "Deep knowledge of Kubernetes"

4. ROLE_RESPONSIBILITY
   - "I led a team of 5 engineers"
   - "I was responsible for the entire backend"
   - "I owned the architecture decisions"

5. PROJECT_SCALE
   - "Handled millions of users"
   - "Enterprise-scale system"
   - "Distributed across 10 regions"

6. PROBLEM_SOLVED
   - "Fixed a critical production bug"
   - "Resolved memory leak issues"
   - "Debugged race condition"

7. ARCHITECTURE_DECISION
   - "Chose microservices over monolith"
   - "Implemented event-driven architecture"
   - "Used Redis for caching"

IMPORTANT RULES:
- Extract EVERY claim, even small ones
- Do NOT add claims that weren't said
- Mark claims as VAGUE if they lack specifics
- Mark claims as SUSPICIOUS if they seem unrealistic
- Mark claims as CONTRADICTORY if they contradict conversation history

OUTPUT FORMAT (CRITICAL - FOLLOW EXACTLY):
For each claim, output in this exact format:

CLAIM: [the exact text of the claim]
TYPE: [one of: technical_achievement, metric, tool_expertise, role_responsibility, project_scale, problem_solved, architecture_decision]
VERIFIABILITY: [one of: verifiable, vague, suspicious, contradictory]
PRIORITY: [number 1-10, where 10 is most critical to verify]
VERIFICATION_QUESTION_1: [specific follow-up question]
VERIFICATION_QUESTION_2: [another specific follow-up question]
RED_FLAG: [optional - only if suspicious or contradictory, explain why]
---

Example:

CLAIM: I optimized the database to handle 10 million requests per day
TYPE: project_scale
VERIFIABILITY: verifiable
PRIORITY: 9
VERIFICATION_QUESTION_1: What specific caching strategy did you implement?
VERIFICATION_QUESTION_2: How did you handle database connection pooling at that scale?
RED_FLAG: 
---

CLAIM: I used machine learning
TYPE: tool_expertise
VERIFIABILITY: vague
PRIORITY: 7
VERIFICATION_QUESTION_1: What specific ML algorithm did you use?
VERIFICATION_QUESTION_2: What was the model architecture and training process?
RED_FLAG: Too vague - no details on what ML technique or problem solved
---

Now extract claims from the candidate's answer."""


# ============================================
# CLAIM EXTRACTION PROMPT BUILDER
# ============================================

def build_claim_extraction_prompt(
    answer_text: str,
    question_text: str,
    conversation_history: List[Dict] = None
) -> List[Dict]:
    """
    Build messages for claim extraction
    
    Args:
        answer_text: The candidate's answer to analyze
        question_text: The question they were answering
        conversation_history: Previous Q&A for contradiction detection
    
    Returns:
        List of message dicts for LLM
    """
    
    messages = [
        {
            "role": "system",
            "content": CLAIM_EXTRACTION_SYSTEM_PROMPT
        }
    ]
    
    # Add conversation history if provided (for contradiction detection)
    if conversation_history:
        history_context = "\n\nPREVIOUS CONVERSATION (for contradiction detection):\n"
        for i, item in enumerate(conversation_history[-3:], 1):  # Last 3 Q&A pairs
            history_context += f"\nQ{i}: {item.get('question', '')}\n"
            history_context += f"A{i}: {item.get('answer', '')}\n"
        
        messages[0]["content"] += history_context
    
    # Add the answer to analyze
    user_prompt = f"""QUESTION ASKED:
"{question_text}"

CANDIDATE'S ANSWER:
"{answer_text}"

Extract ALL claims from this answer using the exact format specified above.
If there are NO claims to extract, output: "NO_CLAIMS_FOUND"
"""
    
    messages.append({
        "role": "user",
        "content": user_prompt
    })
    
    return messages


# ============================================
# CONTRADICTION DETECTION PROMPT
# ============================================

CONTRADICTION_DETECTION_SYSTEM_PROMPT = """You are an expert at detecting contradictions in interview answers.

Your task: Check if the current answer contradicts ANY previous statements.

WHAT COUNTS AS A CONTRADICTION:
- Changed numbers (said 5 team members before, now says 10)
- Changed role (said "team member" before, now says "team lead")
- Changed technology (said used React before, now says used Vue)
- Changed timeline (said 2 years experience before, now says 6 months)
- Changed responsibility (said "contributed to" before, now says "owned")

WHAT DOES NOT COUNT:
- Providing more details (not a contradiction, just elaboration)
- Using different words for same concept (e.g., "database" vs "DB")

OUTPUT FORMAT:
If contradiction found:
CONTRADICTION_FOUND: yes
PREVIOUS_STATEMENT: [quote from earlier answer]
CURRENT_STATEMENT: [quote from current answer]
SEVERITY: [high/medium/low]
EXPLANATION: [why this is contradictory]

If NO contradiction:
CONTRADICTION_FOUND: no
"""


def build_contradiction_check_prompt(
    current_answer: str,
    conversation_history: List[Dict]
) -> List[Dict]:
    """
    Build messages for contradiction detection
    
    Args:
        current_answer: The answer to check
        conversation_history: All previous Q&A pairs
    
    Returns:
        List of message dicts for LLM
    """
    
    messages = [
        {
            "role": "system",
            "content": CONTRADICTION_DETECTION_SYSTEM_PROMPT
        }
    ]
    
    # Build history context
    history_text = "PREVIOUS CONVERSATION:\n\n"
    for i, item in enumerate(conversation_history, 1):
        history_text += f"Q{i}: {item.get('question', '')}\n"
        history_text += f"A{i}: {item.get('answer', '')}\n\n"
    
    user_prompt = f"""{history_text}

CURRENT ANSWER TO CHECK:
"{current_answer}"

Check if this current answer contradicts ANY previous statements.
"""
    
    messages.append({
        "role": "user",
        "content": user_prompt
    })
    
    return messages


# ============================================
# CLAIM VERIFICATION QUESTION GENERATOR
# ============================================

VERIFICATION_QUESTION_SYSTEM_PROMPT = """You are an expert interviewer who asks sharp follow-up questions to verify claims.

Your task: Generate 2-3 specific follow-up questions to verify a candidate's claim.

GOOD VERIFICATION QUESTIONS:
- Ask for specific details (not yes/no)
- Ask about trade-offs considered
- Ask about challenges faced
- Ask for measurable outcomes
- Ask about technical depth

BAD VERIFICATION QUESTIONS:
- Generic questions
- Yes/no questions
- Questions not related to the claim

OUTPUT FORMAT:
QUESTION_1: [first verification question]
QUESTION_2: [second verification question]
QUESTION_3: [optional third question]

Example:

CLAIM: "I optimized database performance"

QUESTION_1: What specific bottleneck did you identify in the database?
QUESTION_2: What optimization techniques did you implement and what were the trade-offs?
QUESTION_3: What metrics did you use to measure the performance improvement?
"""


def build_verification_questions_prompt(
    claim_text: str,
    claim_type: str
) -> List[Dict]:
    """
    Generate verification questions for a specific claim
    
    Args:
        claim_text: The claim to verify
        claim_type: Type of claim (technical_achievement, metric, etc)
    
    Returns:
        List of message dicts for LLM
    """
    
    messages = [
        {
            "role": "system",
            "content": VERIFICATION_QUESTION_SYSTEM_PROMPT
        }
    ]
    
    user_prompt = f"""CLAIM TO VERIFY:
"{claim_text}"

CLAIM TYPE: {claim_type}

Generate 2-3 sharp follow-up questions to verify this claim.
Focus on getting specific technical details and measurable outcomes.
"""
    
    messages.append({
        "role": "user",
        "content": user_prompt
    })
    
    return messages


# ============================================
# PARSING HELPERS
# ============================================

def parse_claim_extraction_output(raw_output: str) -> List[Dict]:
    """
    Parse LLM output into structured claim data
    
    Handles both structured and unstructured output from Ollama.
    
    Args:
        raw_output: Raw text from LLM
    
    Returns:
        List of claim dictionaries
    """
    
    if "NO_CLAIMS_FOUND" in raw_output:
        return []
    
    claims = []
    
    # Split by claim separator
    claim_blocks = raw_output.split("---")
    
    for block in claim_blocks:
        if not block.strip():
            continue
        
        claim_data = {
            "claim_text": "",
            "claim_type": "technical_achievement",  # default
            "verifiability": "verifiable",  # default
            "priority": 5,  # default
            "verification_questions": [],
            "red_flags": []
        }
        
        lines = block.strip().split("\n")
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("CLAIM:"):
                claim_data["claim_text"] = line.replace("CLAIM:", "").strip()
            
            elif line.startswith("TYPE:"):
                claim_data["claim_type"] = line.replace("TYPE:", "").strip()
            
            elif line.startswith("VERIFIABILITY:"):
                claim_data["verifiability"] = line.replace("VERIFIABILITY:", "").strip()
            
            elif line.startswith("PRIORITY:"):
                try:
                    priority = int(line.replace("PRIORITY:", "").strip())
                    claim_data["priority"] = max(1, min(10, priority))  # Clamp 1-10
                except:
                    claim_data["priority"] = 5
            
            elif line.startswith("VERIFICATION_QUESTION"):
                question = line.split(":", 1)[1].strip() if ":" in line else ""
                if question:
                    claim_data["verification_questions"].append(question)
            
            elif line.startswith("RED_FLAG:"):
                red_flag = line.replace("RED_FLAG:", "").strip()
                if red_flag:
                    claim_data["red_flags"].append(red_flag)
        
        # Only add if we got a claim text
        if claim_data["claim_text"]:
            claims.append(claim_data)
    
    return claims


def parse_contradiction_output(raw_output: str) -> Dict:
    """
    Parse contradiction detection output
    
    Args:
        raw_output: Raw text from LLM
    
    Returns:
        Dictionary with contradiction data
    """
    
    result = {
        "contradiction_found": False,
        "previous_statement": None,
        "current_statement": None,
        "severity": None,
        "explanation": None
    }
    
    lines = raw_output.strip().split("\n")
    
    for line in lines:
        line = line.strip()
        
        if line.startswith("CONTRADICTION_FOUND:"):
            found = line.replace("CONTRADICTION_FOUND:", "").strip().lower()
            result["contradiction_found"] = found == "yes"
        
        elif line.startswith("PREVIOUS_STATEMENT:"):
            result["previous_statement"] = line.replace("PREVIOUS_STATEMENT:", "").strip()
        
        elif line.startswith("CURRENT_STATEMENT:"):
            result["current_statement"] = line.replace("CURRENT_STATEMENT:", "").strip()
        
        elif line.startswith("SEVERITY:"):
            result["severity"] = line.replace("SEVERITY:", "").strip()
        
        elif line.startswith("EXPLANATION:"):
            result["explanation"] = line.replace("EXPLANATION:", "").strip()
    
    return result


def parse_verification_questions(raw_output: str) -> List[str]:
    """
    Parse verification questions from LLM output
    
    Args:
        raw_output: Raw text from LLM
    
    Returns:
        List of verification questions
    """
    
    questions = []
    lines = raw_output.strip().split("\n")
    
    for line in lines:
        line = line.strip()
        if line.startswith("QUESTION"):
            question = line.split(":", 1)[1].strip() if ":" in line else ""
            if question:
                questions.append(question)
    
    return questions