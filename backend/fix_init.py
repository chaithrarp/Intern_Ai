import os

# Read current file
with open('config/__init__.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if already there
if 'OLLAMA_FAST_MODEL' in content:
    print("OLLAMA_FAST_MODEL found in file")
    print("File is correct but Python not reading it")
    print("Trying to access it directly...")
    # Force reload
    import importlib
    import config
    importlib.reload(config)
    print("After reload:", hasattr(config, 'OLLAMA_FAST_MODEL'))
else:
    print("NOT FOUND - adding it now")
    # Add after OLLAMA_MAX_TOKENS line
    old = "OLLAMA_MAX_TOKENS = 300"
    new = """OLLAMA_MAX_TOKENS = 300
OLLAMA_FAST_MODEL = "phi3"
OLLAMA_FAST_MAX_TOKENS = 100
OLLAMA_FAST_TEMPERATURE = 0.7"""
    content = content.replace(old, new)
    with open('config/__init__.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Done - added successfully")