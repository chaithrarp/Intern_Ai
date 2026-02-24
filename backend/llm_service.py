"""
LLM Service - Unified interface for all LLM providers
Works with: Ollama, OpenAI (and easy to extend)
"""

from openai import OpenAI
import config
from typing import List, Dict

# ============================================
# CACHED LLM CLIENT (singleton - avoid recreating every call)
# ============================================
_llm_client = None

def get_llm_client():
    """
    Get the appropriate LLM client based on config.
    Cached as singleton to avoid overhead on every call.
    """
    global _llm_client
    if _llm_client is not None:
        return _llm_client

    if config.LLM_PROVIDER == "ollama":
        _llm_client = OpenAI(
            base_url=config.OLLAMA_BASE_URL,
            api_key="ollama"
        )
    elif config.LLM_PROVIDER == "openai":
        if not config.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY not found! "
                "Please set it in .env file or switch to ollama in config.py"
            )
        _llm_client = OpenAI(api_key=config.OPENAI_API_KEY)
    else:
        raise ValueError(f"Unknown LLM provider: {config.LLM_PROVIDER}")

    return _llm_client

# ============================================
# MAIN LLM FUNCTION
# ============================================

def get_llm_response(
    messages: List[Dict[str, str]], 
    temperature: float = None,
    max_tokens: int = None
) -> str:
    """
    Get response from LLM (works with any provider)
    """
    try:
        client = get_llm_client()
        
        if config.LLM_PROVIDER == "ollama":
            model = config.OLLAMA_MODEL
            temp = temperature if temperature is not None else config.OLLAMA_TEMPERATURE
            max_tok = max_tokens or config.OLLAMA_MAX_TOKENS
        else:
            model = config.OPENAI_MODEL
            temp = temperature if temperature is not None else config.OPENAI_TEMPERATURE
            max_tok = max_tokens or config.OPENAI_MAX_TOKENS
        
        print(f"🤖 Calling {config.LLM_PROVIDER} ({model})...")
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temp,
            max_tokens=max_tok
        )
        
        response_text = response.choices[0].message.content.strip()
        print(f"✅ LLM Response: {response_text[:100]}...")
        
        return response_text
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ LLM Error: {error_msg}")
        
        if config.LLM_PROVIDER == "ollama":
            if "Connection" in error_msg or "refused" in error_msg:
                raise Exception("Cannot connect to Ollama. Make sure Ollama is running: 'ollama serve'")
            elif "model" in error_msg.lower():
                raise Exception(f"Model '{config.OLLAMA_MODEL}' not found. Install it: 'ollama pull {config.OLLAMA_MODEL}'")
        elif config.LLM_PROVIDER == "openai":
            if "api_key" in error_msg.lower():
                raise Exception("Invalid OpenAI API key. Check your .env file or config.py")
            elif "quota" in error_msg.lower() or "rate_limit" in error_msg.lower():
                raise Exception("OpenAI quota/rate limit exceeded.")
        
        raise Exception(f"LLM call failed: {error_msg}")

# ============================================
# TESTING FUNCTION
# ============================================

def test_llm_connection():
    try:
        print(f"Testing {config.LLM_PROVIDER} connection...")
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello, InternAI is working!' and nothing else."}
        ]
        response = get_llm_response(test_messages, temperature=0.1, max_tokens=50)
        print(f"✅ Test successful! Response: {response}")
        return True, f"Success! {config.LLM_PROVIDER} is working. Response: {response}"
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False, f"Failed: {str(e)}"

if __name__ == "__main__":
    print("=" * 50)
    print("LLM SERVICE TEST")
    print("=" * 50)
    success, message = test_llm_connection()
    print("\n" + message)