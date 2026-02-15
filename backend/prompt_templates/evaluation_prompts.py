"""
Evaluation Prompts
==================

Centralized prompt templates for all evaluation tasks.
"""


# This file can be minimal since prompts are already in the evaluators
# But it's good to have for consistency

EVALUATION_PROMPT_TEMPLATES = {
    "hr_round": {
        "system": """You are an expert HR interviewer evaluating a behavioral interview answer.

Evaluate across 5 dimensions and provide specific feedback.

Focus on STAR method adherence and specific examples.""",
        
        "user": """Question: "{question}"

Answer: "{answer}"

Evaluate this HR/behavioral answer."""
    },
    
    "technical_round": {
        "system": """You are an expert senior engineer evaluating a technical interview answer.

Evaluate with TECHNICAL FOCUS.

Be technically rigorous. Flag incorrect concepts immediately.""",
        
        "user": """Question: "{question}"

Answer: "{answer}"

Evaluate this technical answer."""
    },
    
    "system_design_round": {
        "system": """You are an expert system architect evaluating a system design interview answer.

Evaluate with ARCHITECTURE FOCUS.

Be architecturally rigorous. This is senior-level evaluation.""",
        
        "user": """Question: "{question}"

Answer: "{answer}"

Evaluate this system design answer."""
    }
}


def get_evaluation_prompt(round_type: str, question: str, answer: str) -> str:
    """Get formatted evaluation prompt for round type"""
    
    template = EVALUATION_PROMPT_TEMPLATES.get(
        f"{round_type}_round",
        EVALUATION_PROMPT_TEMPLATES["technical_round"]
    )
    
    return {
        "system": template["system"],
        "user": template["user"].format(question=question, answer=answer)
    }