# test_whisper.py
# Quick test to verify Whisper works

from whisper_service import get_model_info, transcribe_audio
import os

print("=" * 50)
print("WHISPER TEST")
print("=" * 50)

# Test 1: Check model loaded
info = get_model_info()
print(f"\n✅ Model Info: {info}")

# Test 2: Check if we have any audio files
audio_dir = "audio_uploads"
if os.path.exists(audio_dir):
    audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.webm')]
    
    if audio_files:
        # Test transcription on first audio file
        test_file = os.path.join(audio_dir, audio_files[0])
        print(f"\n🎤 Testing transcription on: {audio_files[0]}")
        
        result = transcribe_audio(test_file)
        
        if result:
            print(f"\n✅ TRANSCRIPTION SUCCESS!")
            print(f"Text: {result['text']}")
            print(f"Language: {result['language']}")
        else:
            print("\n❌ Transcription failed")
    else:
        print("\n⚠️  No audio files found. Record something first!")
else:
    print("\n⚠️  audio_uploads folder not found")

print("\n" + "=" * 50)