# whisper_service.py
# Speech-to-text using OpenAI Whisper

import whisper
import os
from typing import Optional

# Load Whisper model (using 'base' model for balance of speed/accuracy)
# Models available: tiny, base, small, medium, large
# 'base' is good for development (fast, decent accuracy)
print("Loading Whisper model...")
model = whisper.load_model("base")
print("Whisper model loaded successfully!")

def transcribe_audio(audio_file_path: str) -> Optional[dict]:
    """
    Transcribe audio file to text using Whisper
    
    Args:
        audio_file_path: Path to the audio file
        
    Returns:
        Dictionary with transcription result or None if failed
    """
    try:
        # Check if file exists
        if not os.path.exists(audio_file_path):
            print(f"Error: Audio file not found: {audio_file_path}")
            return None
        
        print(f"Transcribing: {audio_file_path}")
        
        # Transcribe audio
        result = model.transcribe(audio_file_path)
        
        # Extract text
        transcript_text = result["text"].strip()
        
        print(f"Transcription successful: {transcript_text[:50]}...")
        
        return {
            "text": transcript_text,
            "language": result.get("language", "unknown"),
            "segments": result.get("segments", [])
        }
    
    except Exception as e:
        print(f"Transcription error: {str(e)}")
        return None

def get_model_info():
    """Return information about the loaded Whisper model"""
    return {
        "model_name": "base",
        "status": "loaded"
    }