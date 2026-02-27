"""
LLM Service - Two model setup for speed
- llama3: evaluation (accurate, slower)
- phi3: question generation + interruption (fast, lightweight)
"""

from openai import OpenAI
import config
from typing import List, Dict

# ============================================
# CACHED CLIENTS (created once, reused)
# ============================================
_main_client = None
_fast_client = None


def get_main_client():
    """Primary client — llama3 for evaluation"""
    global _main_client
    if _main_client is None:
        if config.LLM_PROVIDER == "ollama":
            _main_client = OpenAI(
                base_url=config.OLLAMA_BASE_URL,
                api_key="ollama"
            )
        else:
            _main_client = OpenAI(api_key=config.OPENAI_API_KEY)
    return _main_client


def get_fast_client():
    """Fast client — phi3 for question gen + interruptions"""
    global _fast_client
    if _fast_client is None:
        # Same Ollama instance, just different model
        _fast_client = OpenAI(
            base_url=config.OLLAMA_BASE_URL,
            api_key="ollama"
        )
    return _fast_client


# ============================================
# MAIN LLM — for evaluation (llama3)
# ============================================

def get_llm_response(
    messages: List[Dict[str, str]],
    temperature: float = None,
    max_tokens: int = None
) -> str:
    """
    Main LLM call using llama3
    Use for: answer evaluation only
    """
    try:
        if config.LLM_PROVIDER == "openai":
            client = get_main_client()
            model = config.OPENAI_MODEL
            temp = temperature or config.OPENAI_TEMPERATURE
            max_tok = max_tokens or config.OPENAI_MAX_TOKENS
        else:
            client = get_main_client()
            model = config.OLLAMA_MODEL
            temp = temperature if temperature is not None else config.OLLAMA_TEMPERATURE
            max_tok = max_tokens or config.OLLAMA_MAX_TOKENS

        print(f"🤖 Main LLM ({model})...")

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temp,
            max_tokens=max_tok
        )

        result = response.choices[0].message.content.strip()
        print(f"✅ Main LLM done: {result[:80]}...")
        return result

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Main LLM Error: {error_msg}")

        if "Connection" in error_msg or "refused" in error_msg:
            raise Exception("Cannot connect to Ollama. Run: 'ollama serve'")
        elif "model" in error_msg.lower():
            raise Exception(f"Model '{config.OLLAMA_MODEL}' not found. Run: 'ollama pull {config.OLLAMA_MODEL}'")

        raise Exception(f"LLM call failed: {error_msg}")


# ============================================
# FAST LLM — for question gen + interruptions (phi3)
# ============================================

def get_fast_llm_response(
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = None
) -> str:
    """
    Fast LLM call using phi3
    Use for: question generation, interruption checks, followup questions
    phi3 is 3x faster than llama3 for short outputs
    """
    try:
        client = get_fast_client()
        max_tok = max_tokens or config.OLLAMA_FAST_MAX_TOKENS

        print(f"⚡ Fast LLM ({config.OLLAMA_FAST_MODEL})...")

        response = client.chat.completions.create(
            model=config.OLLAMA_FAST_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tok
        )

        result = response.choices[0].message.content.strip()
        print(f"✅ Fast LLM done: {result[:80]}...")
        return result

    except Exception as e:
        print(f"⚠️ Fast LLM failed, falling back to main llama3: {str(e)}")
        # Fallback to main model if phi3 fails
        return get_llm_response(messages, temperature, max_tokens)


# ============================================
# TEST
# ============================================

def test_llm_connection():
    try:
        print(f"Testing main LLM ({config.OLLAMA_MODEL})...")
        test_messages = [
            {"role": "user", "content": "Say 'working' and nothing else."}
        ]
        response = get_llm_response(test_messages, temperature=0.1, max_tokens=10)
        print(f"✅ Main LLM working: {response}")

        print(f"Testing fast LLM ({config.OLLAMA_FAST_MODEL})...")
        response2 = get_fast_llm_response(test_messages, temperature=0.1, max_tokens=10)
        print(f"✅ Fast LLM working: {response2}")

        return True, f"Both models working!"

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False, f"Failed: {str(e)}"


if __name__ == "__main__":
    success, message = test_llm_connection()
    print(message)