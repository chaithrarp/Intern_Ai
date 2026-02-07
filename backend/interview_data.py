# interview_data.py
# Hardcoded interview questions for Phase 1

INTERVIEW_QUESTIONS = [
    {
        "id": 1,
        "question": "Tell me about yourself and why you're interested in this role.",
        "category": "introduction"
    },
    {
        "id": 2,
        "question": "Describe a challenging project you worked on. What was your role and what was the outcome?",
        "category": "experience"
    },
    {
        "id": 3,
        "question": "How do you handle tight deadlines and pressure situations?",
        "category": "behavioral"
    },
    {
        "id": 4,
        "question": "Where do you see yourself in 5 years?",
        "category": "career_goals"
    },
    {
        "id": 5,
        "question": "Do you have any questions for me?",
        "category": "closing"
    }
]

def get_question_by_id(question_id: int):
    """Get a specific question by ID"""
    for q in INTERVIEW_QUESTIONS:
        if q["id"] == question_id:
            return q
    return None

def get_total_questions():
    """Return total number of questions"""
    return len(INTERVIEW_QUESTIONS)