content = """import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")

OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_MODEL = "llama3"
OLLAMA_TEMPERATURE = 0.7
OLLAMA_MAX_TOKENS = 300

OLLAMA_FAST_MODEL = "phi3"
OLLAMA_FAST_MAX_TOKENS = 100
OLLAMA_FAST_TEMPERATURE = 0.7

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_TEMPERATURE = 0.7
OPENAI_MAX_TOKENS = 300

MAX_QUESTIONS_PER_SESSION = 5
INTERVIEW_DOMAIN = "software engineering"
ENABLE_CONTEXT_MEMORY = True

ENABLE_INTERRUPTIONS = True
MAX_INTERRUPTIONS_PER_SESSION = 5
INTERRUPTION_PROBABILITY = 1.0
MIN_INTERRUPTION_TIME = 5
MAX_INTERRUPTION_TIME = 90
ENABLE_RAMBLING_DETECTION = True
PRESSURE_MODE = "adaptive"

print("Primary Model: " + OLLAMA_MODEL)
print("Fast Model: " + OLLAMA_FAST_MODEL)
"""

with open('config.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('config.py written successfully')