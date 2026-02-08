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
# Change this to switch between providers
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")  # Default to ollama

# ============================================
# OLLAMA SETTINGS
# ============================================
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_MODEL = "llama3"  # Your installed model
OLLAMA_TEMPERATURE = 0.7
OLLAMA_MAX_TOKENS = 300

# ============================================
# OPENAI SETTINGS
# ============================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o-mini"  # Fast and cheap: $0.15 per 1M tokens
OPENAI_TEMPERATURE = 0.7
OPENAI_MAX_TOKENS = 300

# ============================================
# INTERVIEW SETTINGS
# ============================================
MAX_QUESTIONS_PER_SESSION = 5  # How many questions in one interview
INTERVIEW_DOMAIN = "software engineering"  # Can be changed later
ENABLE_CONTEXT_MEMORY = True  # Remember previous answers

# ============================================
# PHASE 5: PRESSURE SETTINGS
# ============================================
ENABLE_INTERRUPTIONS = True  # Enable pressure interruptions
INTERRUPTION_PROBABILITY = 0.5  # 50% chance of interruption
MIN_INTERRUPTION_TIME = 5  # Minimum seconds before interruption
MAX_INTERRUPTION_TIME = 20  # Maximum seconds before interruption
ENABLE_RAMBLING_DETECTION = True  # Adaptive interruption on rambling
PRESSURE_MODE = "random"  # always random (aggressive/gentle/neutral mix)

# Add this to backend/config.py

# ============================================
# PHASE 5: INTERRUPTION SETTINGS
# ============================================

# Maximum interruptions per interview session
MAX_INTERRUPTIONS_PER_SESSION = 2  # Realistic: 0-2 interruptions max

# Enable/disable interruptions globally
ENABLE_INTERRUPTIONS = True

# Interruption probability multiplier (1.0 = normal, 0.5 = half as likely)
INTERRUPTION_PROBABILITY = 1.0

# Pressure mode (not used yet, for future phases)
PRESSURE_MODE = "adaptive"

# ============================================
# VALIDATION
# ============================================
if LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
    print("⚠️  WARNING: LLM_PROVIDER is 'openai' but OPENAI_API_KEY is not set!")
    print("   Either:")
    print("   1. Create a .env file with OPENAI_API_KEY=your-key-here")
    print("   2. Change LLM_PROVIDER to 'ollama' in config.py")
    print("   3. Set environment variable: export OPENAI_API_KEY=your-key")

print(f"✅ LLM Provider: {LLM_PROVIDER}")
if LLM_PROVIDER == "ollama":
    print(f"   Model: {OLLAMA_MODEL}")
elif LLM_PROVIDER == "openai":
    print(f"   Model: {OPENAI_MODEL}")