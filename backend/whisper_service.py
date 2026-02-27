"""
whisper_service.py - UPGRADED TO faster-whisper
================================================
faster-whisper is 3-4x faster than openai-whisper on CPU.
Same accuracy, same interface, drop-in replacement.

Install:
    pip uninstall openai-whisper whisper -y
    pip install faster-whisper

Models: tiny | base | small | medium | large-v2
For real-time chunking: use 'tiny' (fastest, good enough for interruption detection)
For final transcription: use 'base' (more accurate)
"""

import os
import time
from typing import Optional
from faster_whisper import WhisperModel

# ── Load two models ───────────────────────────────────────────────────────────
# tiny  → for live chunks (fast, ~0.5s per 6s chunk on CPU)
# base  → for final full transcription after recording stops (accurate)

print("Loading Whisper models...")

_chunk_model = WhisperModel(
    "tiny",
    device="cpu",
    compute_type="int8"   # int8 quantization = 2x faster on CPU
)

_final_model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

print("✅ Whisper models loaded (tiny for chunks, base for final)")


# ── Final transcription (called after recording stops) ────────────────────────

def transcribe_audio(audio_file_path: str) -> Optional[dict]:
    """
    Full accurate transcription using base model.
    Called once after user stops recording.
    """
    try:
        if not os.path.exists(audio_file_path):
            print(f"❌ Audio file not found: {audio_file_path}")
            return None

        print(f"Transcribing: {audio_file_path}")
        t0 = time.time()

        segments, info = _final_model.transcribe(
            audio_file_path,
            beam_size=5,
            language="en",
            vad_filter=True,              # skip silent sections
            vad_parameters={"min_silence_duration_ms": 500}
        )

        # faster-whisper returns a generator — consume it
        segment_list = []
        full_text = ""
        for seg in segments:
            full_text += seg.text + " "
            segment_list.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip()
            })

        full_text = full_text.strip()
        elapsed = time.time() - t0

        print(f"✅ Transcription done in {elapsed:.1f}s: {full_text[:80]}...")

        return {
            "text": full_text,
            "language": info.language,
            "segments": segment_list
        }

    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return None


# ── Chunk transcription (called every 6s during recording) ────────────────────

def transcribe_chunk(audio_file_path: str) -> Optional[dict]:
    """
    Fast transcription of a short audio chunk using tiny model.
    Called repeatedly during recording for live transcript + interruption checks.

    Target: < 1.5s for a 6s audio chunk on CPU with int8.
    """
    try:
        if not os.path.exists(audio_file_path):
            print(f"❌ Chunk file not found: {audio_file_path}")
            return None

        t0 = time.time()

        segments, info = _chunk_model.transcribe(
            audio_file_path,
            beam_size=1,          # greedy decoding = faster (beam_size=1)
            language="en",        # skip language detection = faster
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 300}
        )

        text = " ".join(seg.text.strip() for seg in segments).strip()
        elapsed = time.time() - t0

        print(f"⚡ Chunk transcribed in {elapsed:.2f}s: '{text[:60]}'")

        return {
            "text": text,
            "language": info.language,
            "elapsed": elapsed
        }

    except Exception as e:
        print(f"❌ Chunk transcription error: {e}")
        return None


def get_model_info():
    return {
        "chunk_model": "tiny (int8)",
        "final_model": "base (int8)",
        "backend": "faster-whisper",
        "status": "loaded"
    }