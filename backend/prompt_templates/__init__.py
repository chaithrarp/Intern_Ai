"""
Prompts Package
===============

Contains all LLM prompt templates and parsing utilities
"""

from .claim_prompts import (
    build_claim_extraction_prompt,
    build_contradiction_check_prompt,
    build_verification_questions_prompt,
    parse_claim_extraction_output,
    parse_contradiction_output,
    parse_verification_questions
)

from .interruption_prompts import (
    get_interruption_phrase,
    get_warning_config,
    get_priority,
    get_severity
)

# ============================================
# QUESTION CLEANING (from prompts.py)
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

__all__ = [
    "build_claim_extraction_prompt",
    "build_contradiction_check_prompt",
    "build_verification_questions_prompt",
    "parse_claim_extraction_output",
    "parse_contradiction_output",
    "parse_verification_questions",
    "get_interruption_phrase",
    "get_warning_config",
    "get_priority",
    "get_severity",
    "clean_question_output"
]