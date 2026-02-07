"""
LLM Service - Unified interface for all LLM providers
Works with: Ollama, OpenAI (and easy to extend)
"""

from openai import OpenAI
import config
from typing import List, Dict

# ============================================
# LLM CLIENT INITIALIZATION
# ============================================

def get_llm_client():
    """
    Get the appropriate LLM client based on config
    
    Returns:
        OpenAI client (works for both Ollama and OpenAI!)
    """
    if config.LLM_PROVIDER == "ollama":
        # Ollama uses OpenAI-compatible API
        return OpenAI(
            base_url=config.OLLAMA_BASE_URL,
            api_key="ollama"  # Ollama doesn't need real API key
        )
    
    elif config.LLM_PROVIDER == "openai":
        if not config.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY not found! "
                "Please set it in .env file or switch to ollama in config.py"
            )
        return OpenAI(api_key=config.OPENAI_API_KEY)
    
    else:
        raise ValueError(f"Unknown LLM provider: {config.LLM_PROVIDER}")

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
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        temperature: Randomness (0-1). None uses config default
        max_tokens: Max response length. None uses config default
        
    Returns:
        String response from LLM
        
    Raises:
        Exception: If LLM call fails
    """
    try:
        # Get client
        client = get_llm_client()
        
        # Get settings based on provider
        if config.LLM_PROVIDER == "ollama":
            model = config.OLLAMA_MODEL
            temp = temperature or config.OLLAMA_TEMPERATURE
            max_tok = max_tokens or config.OLLAMA_MAX_TOKENS
        else:  # openai
            model = config.OPENAI_MODEL
            temp = temperature or config.OPENAI_TEMPERATURE
            max_tok = max_tokens or config.OPENAI_MAX_TOKENS
        
        # Make API call
        print(f"🤖 Calling {config.LLM_PROVIDER} ({model})...")
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temp,
            max_tokens=max_tok
        )
        
        # Extract response text
        response_text = response.choices[0].message.content.strip()
        
        print(f"✅ LLM Response: {response_text[:100]}...")
        
        return response_text
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ LLM Error: {error_msg}")
        
        # Provide helpful error messages
        if config.LLM_PROVIDER == "ollama":
            if "Connection" in error_msg or "refused" in error_msg:
                raise Exception(
                    "Cannot connect to Ollama. "
                    "Make sure Ollama is running: 'ollama serve'"
                )
            elif "model" in error_msg.lower():
                raise Exception(
                    f"Model '{config.OLLAMA_MODEL}' not found. "
                    f"Install it: 'ollama pull {config.OLLAMA_MODEL}'"
                )
        
        elif config.LLM_PROVIDER == "openai":
            if "api_key" in error_msg.lower():
                raise Exception(
                    "Invalid OpenAI API key. "
                    "Check your .env file or config.py"
                )
            elif "quota" in error_msg.lower() or "rate_limit" in error_msg.lower():
                raise Exception(
                    "OpenAI quota/rate limit exceeded. "
                    "Check your usage or try ollama instead"
                )
        
        # Re-raise original error if we don't have a specific message
        raise Exception(f"LLM call failed: {error_msg}")

# ============================================
# TESTING FUNCTION
# ============================================

def test_llm_connection():
    """
    Test if LLM is working correctly
    
    Returns:
        Tuple: (success: bool, message: str)
    """
    try:
        print(f"Testing {config.LLM_PROVIDER} connection...")
        
        # Simple test message
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

# ============================================
# MAIN (for testing)
# ============================================

if __name__ == "__main__":
    print("=" * 50)
    print("LLM SERVICE TEST")
    print("=" * 50)
    success, message = test_llm_connection()
    print("\n" + message)