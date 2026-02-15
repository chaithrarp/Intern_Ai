"""
Configuration Package
=====================

Contains evaluation rules, thresholds, and constants
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .evaluation_config import (
    DIMENSION_WEIGHTS,
    ScoreLevel,
    get_performance_level,
    ROUND_EVALUATION_FOCUS,
    DIFFICULTY_EXPECTATIONS,
    DifficultyAdjustment,
    FOLLOWUP_TRIGGERS,
    CLAIM_PRIORITY_RULES,
    RED_FLAG_PATTERNS,
    PHASE_TRANSITION_RULES,
    PHASE_INTERRUPTION_PROBABILITY,
    ReportConfig
)

# ============================================
# LLM PROVIDER SELECTION
# ============================================
# Options: "ollama" or "openai"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")

# ============================================
# OLLAMA SETTINGS
# ============================================
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_MODEL = "llama3"
OLLAMA_TEMPERATURE = 0.7
OLLAMA_MAX_TOKENS = 300

# ============================================
# OPENAI SETTINGS
# ============================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_TEMPERATURE = 0.7
OPENAI_MAX_TOKENS = 300

# ============================================
# INTERVIEW SETTINGS
# ============================================
MAX_QUESTIONS_PER_SESSION = 5
INTERVIEW_DOMAIN = "software engineering"
ENABLE_CONTEXT_MEMORY = True

# ============================================
# INTERRUPTION SETTINGS
# ============================================
ENABLE_INTERRUPTIONS = True
MAX_INTERRUPTIONS_PER_SESSION = 5
INTERRUPTION_PROBABILITY = 1.0
MIN_INTERRUPTION_TIME = 5
MAX_INTERRUPTION_TIME = 90
ENABLE_RAMBLING_DETECTION = True
PRESSURE_MODE = "adaptive"

__all__ = [
    # Evaluation config
    "DIMENSION_WEIGHTS",
    "ScoreLevel",
    "get_performance_level",
    "ROUND_EVALUATION_FOCUS",
    "DIFFICULTY_EXPECTATIONS",
    "DifficultyAdjustment",
    "FOLLOWUP_TRIGGERS",
    "CLAIM_PRIORITY_RULES",
    "RED_FLAG_PATTERNS",
    "PHASE_TRANSITION_RULES",
    "PHASE_INTERRUPTION_PROBABILITY",
    "ReportConfig",
    # LLM Settings
    "LLM_PROVIDER",
    "OLLAMA_BASE_URL",
    "OLLAMA_MODEL",
    "OLLAMA_TEMPERATURE",
    "OLLAMA_MAX_TOKENS",
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
    "OPENAI_TEMPERATURE",
    "OPENAI_MAX_TOKENS",
    # Interview Settings
    "MAX_QUESTIONS_PER_SESSION",
    "INTERVIEW_DOMAIN",
    "ENABLE_CONTEXT_MEMORY",
    # Interruption Settings
    "ENABLE_INTERRUPTIONS",
    "MAX_INTERRUPTIONS_PER_SESSION",
    "INTERRUPTION_PROBABILITY",
    "MIN_INTERRUPTION_TIME",
    "MAX_INTERRUPTION_TIME",
    "ENABLE_RAMBLING_DETECTION",
    "PRESSURE_MODE"
]