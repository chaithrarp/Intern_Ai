"""
Configuration file for InternAI Backend
Controls which LLM provider to use and settings
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

# ============================================
# VALIDATION
# ============================================
if LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
    print("⚠️  WARNING: LLM_PROVIDER is 'openai' but OPENAI_API_KEY is not set!")

print(f"✅ LLM Provider: {LLM_PROVIDER}")
print(f"✅ Interruptions: {'ENABLED' if ENABLE_INTERRUPTIONS else 'DISABLED'}")