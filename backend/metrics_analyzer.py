"""
Behavioral Metrics Analyzer
Analyzes transcripts to detect pauses, filler words, and recovery patterns
"""

from typing import Dict, List, Tuple
import re

# ============================================
# CONFIGURATION
# ============================================

# Filler words to detect (case-insensitive)
FILLER_WORDS = [
    'um', 'uh', 'like', 'you know', 'basically', 'actually', 
    'literally', 'kind of', 'sort of', 'i mean', 'you see',
    'so', 'well', 'right', 'okay'
]

# Pause threshold (seconds)
LONG_PAUSE_THRESHOLD = 2.0

# ============================================
# PAUSE DETECTION
# ============================================

def analyze_pauses(segments: List[Dict]) -> Dict:
    """
    Analyze pauses between speech segments from Whisper
    
    Whisper segments format:
    [
        {"start": 0.0, "end": 2.5, "text": "Hello"},
        {"start": 5.0, "end": 7.2, "text": "world"},  # 2.5s pause before this
        ...
    ]
    
    Args:
        segments: List of Whisper transcript segments with timing
    
    Returns:
        Dict with pause metrics:
            - total_pauses: int
            - long_pauses: int (> 2 seconds)
            - avg_pause_duration: float
            - max_pause_duration: float
            - pause_details: List of (position, duration) tuples
    """
    if not segments or len(segments) < 2:
        return {
            "total_pauses": 0,
            "long_pauses": 0,
            "avg_pause_duration": 0.0,
            "max_pause_duration": 0.0,
            "pause_details": []
        }
    
    pauses = []
    long_pause_count = 0
    
    # Calculate gaps between segments
    for i in range(1, len(segments)):
        prev_end = segments[i-1]["end"]
        curr_start = segments[i]["start"]
        
        pause_duration = curr_start - prev_end
        
        # Only count as pause if gap > 0.3 seconds (ignore tiny gaps)
        if pause_duration > 0.3:
            pauses.append({
                "position": i,  # After which segment
                "duration": pause_duration,
                "before_text": segments[i-1]["text"].strip(),
                "after_text": segments[i]["text"].strip()
            })
            
            if pause_duration >= LONG_PAUSE_THRESHOLD:
                long_pause_count += 1
    
    # Calculate statistics
    if pauses:
        avg_pause = sum(p["duration"] for p in pauses) / len(pauses)
        max_pause = max(p["duration"] for p in pauses)
    else:
        avg_pause = 0.0
        max_pause = 0.0
    
    return {
        "total_pauses": len(pauses),
        "long_pauses": long_pause_count,
        "avg_pause_duration": round(avg_pause, 2),
        "max_pause_duration": round(max_pause, 2),
        "pause_details": pauses
    }

# ============================================
# FILLER WORD DETECTION
# ============================================

def detect_filler_words(text: str) -> Dict:
    """
    Count filler words in transcript (case-insensitive)
    
    Args:
        text: Full transcript text
    
    Returns:
        Dict with:
            - filler_word_count: int
            - filler_words_found: List of detected fillers
            - filler_positions: List of (filler, position) tuples
    """
    text_lower = text.lower()
    
    # Tokenize into words
    words = re.findall(r'\b\w+\b', text_lower)
    
    filler_count = 0
    filler_list = []
    filler_positions = []
    
    # Check for single-word fillers
    for i, word in enumerate(words):
        if word in FILLER_WORDS:
            filler_count += 1
            filler_list.append(word)
            filler_positions.append((word, i))
    
    # Check for multi-word fillers (e.g., "you know", "kind of")
    multi_word_fillers = [f for f in FILLER_WORDS if ' ' in f]
    for filler in multi_word_fillers:
        # Count occurrences in original text (case-insensitive)
        count = text_lower.count(filler)
        if count > 0:
            filler_count += count
            filler_list.extend([filler] * count)
    
    return {
        "filler_word_count": filler_count,
        "filler_words_found": filler_list,
        "filler_word_rate": round(filler_count / max(len(words), 1), 3),  # Fillers per word
        "unique_fillers": list(set(filler_list))
    }

# ============================================
# SPEAKING RATE ANALYSIS
# ============================================

def calculate_speaking_rate(text: str, duration_seconds: float) -> Dict:
    """
    Calculate words per minute and total words
    
    Args:
        text: Full transcript
        duration_seconds: Recording duration
    
    Returns:
        Dict with speaking metrics
    """
    words = re.findall(r'\b\w+\b', text)
    word_count = len(words)
    
    if duration_seconds > 0:
        wpm = (word_count / duration_seconds) * 60
    else:
        wpm = 0.0
    
    return {
        "total_words": word_count,
        "words_per_minute": round(wpm, 1),
        "duration_seconds": duration_seconds
    }

# ============================================
# HESITATION SCORE
# ============================================

def calculate_hesitation_score(
    filler_count: int,
    long_pauses: int,
    total_words: int
) -> float:
    """
    Calculate overall hesitation score (0-100)
    Higher = more hesitation
    
    Formula:
        - Filler rate: (fillers / words) * 50
        - Long pause penalty: long_pauses * 10
        - Capped at 100
    
    Args:
        filler_count: Number of filler words
        long_pauses: Number of pauses > 2 seconds
        total_words: Total words spoken
    
    Returns:
        Float score between 0-100
    """
    if total_words == 0:
        return 0.0
    
    # Filler contribution (0-50 points)
    filler_rate = filler_count / total_words
    filler_score = min(filler_rate * 100, 50)
    
    # Long pause contribution (10 points per pause, max 50)
    pause_score = min(long_pauses * 10, 50)
    
    # Total score
    hesitation = filler_score + pause_score
    
    return round(min(hesitation, 100), 2)

# ============================================
# RECOVERY TIME ANALYSIS
# ============================================

def calculate_recovery_time(
    interruption_time: float,
    segments: List[Dict]
) -> Dict:
    """
    Calculate how long it took to resume speaking after interruption
    
    Args:
        interruption_time: When interruption happened (seconds into recording)
        segments: Whisper segments with timing
    
    Returns:
        Dict with recovery metrics
    """
    if not segments:
        return {
            "recovery_time": None,
            "resumed_at": None,
            "recovery_status": "no_speech_detected"
        }
    
    # Find first segment that starts AFTER interruption
    resumed_at = None
    for segment in segments:
        if segment["start"] > interruption_time:
            resumed_at = segment["start"]
            break
    
    if resumed_at is None:
        # User never resumed speaking after interruption
        return {
            "recovery_time": None,
            "resumed_at": None,
            "recovery_status": "did_not_resume"
        }
    
    recovery_time = resumed_at - interruption_time
    
    return {
        "recovery_time": round(recovery_time, 2),
        "resumed_at": round(resumed_at, 2),
        "recovery_status": "resumed"
    }

# ============================================
# COMPLETE METRICS ANALYSIS
# ============================================

def analyze_complete_metrics(
    transcript_text: str,
    segments: List[Dict],
    recording_duration: float,
    was_interrupted: bool = False,
    interruption_time: float = None
) -> Dict:
    """
    Perform complete behavioral metrics analysis
    
    Args:
        transcript_text: Full transcript string
        segments: Whisper segments with timing data
        recording_duration: Total recording duration
        was_interrupted: Whether answer was interrupted
        interruption_time: When interruption occurred (if applicable)
    
    Returns:
        Complete metrics dictionary
    """
    # Analyze pauses
    pause_metrics = analyze_pauses(segments)
    
    # Detect filler words
    filler_metrics = detect_filler_words(transcript_text)
    
    # Calculate speaking rate
    speaking_metrics = calculate_speaking_rate(transcript_text, recording_duration)
    
    # Calculate hesitation score
    hesitation_score = calculate_hesitation_score(
        filler_metrics["filler_word_count"],
        pause_metrics["long_pauses"],
        speaking_metrics["total_words"]
    )
    
    # Calculate recovery time (if interrupted)
    recovery_metrics = None
    if was_interrupted and interruption_time is not None:
        recovery_metrics = calculate_recovery_time(interruption_time, segments)
    
    # Combine all metrics
    complete_metrics = {
        # Pause metrics
        "total_pauses": pause_metrics["total_pauses"],
        "long_pauses": pause_metrics["long_pauses"],
        "avg_pause_duration": pause_metrics["avg_pause_duration"],
        "max_pause_duration": pause_metrics["max_pause_duration"],
        
        # Filler word metrics
        "filler_word_count": filler_metrics["filler_word_count"],
        "filler_words_list": ",".join(filler_metrics["filler_words_found"]),
        "filler_word_rate": filler_metrics["filler_word_rate"],
        
        # Speaking metrics
        "words_per_minute": speaking_metrics["words_per_minute"],
        "total_words": speaking_metrics["total_words"],
        
        # Recovery metrics (if interrupted)
        "recovery_time": recovery_metrics["recovery_time"] if recovery_metrics else None,
        "resumed_speaking_at": recovery_metrics["resumed_at"] if recovery_metrics else None,
        
        # Overall score
        "hesitation_score": hesitation_score
    }
    
    return complete_metrics

# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    print("=" * 50)
    print("TESTING METRICS ANALYZER")
    print("=" * 50)
    
    # Test 1: Pause Detection
    print("\n1. Testing pause detection...")
    test_segments = [
        {"start": 0.0, "end": 2.5, "text": "Hello, my name is John"},
        {"start": 5.0, "end": 7.2, "text": "I work as a developer"},  # 2.5s pause
        {"start": 7.5, "end": 10.0, "text": "in a tech company"},     # 0.3s pause
        {"start": 13.0, "end": 15.5, "text": "for five years"}         # 3.0s pause
    ]
    
    pause_result = analyze_pauses(test_segments)
    print(f"   Total pauses: {pause_result['total_pauses']}")
    print(f"   Long pauses (>2s): {pause_result['long_pauses']}")
    print(f"   Avg pause: {pause_result['avg_pause_duration']}s")
    print(f"   Max pause: {pause_result['max_pause_duration']}s")
    
    # Test 2: Filler Word Detection
    print("\n2. Testing filler word detection...")
    test_text = "Um, so like, I was basically working on, you know, this project and, uh, it was actually quite challenging."
    
    filler_result = detect_filler_words(test_text)
    print(f"   Filler count: {filler_result['filler_word_count']}")
    print(f"   Fillers found: {filler_result['filler_words_found']}")
    print(f"   Filler rate: {filler_result['filler_word_rate']}")
    
    # Test 3: Speaking Rate
    print("\n3. Testing speaking rate...")
    speaking_result = calculate_speaking_rate(test_text, 15.5)
    print(f"   Total words: {speaking_result['total_words']}")
    print(f"   Words per minute: {speaking_result['words_per_minute']}")
    
    # Test 4: Hesitation Score
    print("\n4. Testing hesitation score...")
    score = calculate_hesitation_score(
        filler_count=8,
        long_pauses=2,
        total_words=20
    )
    print(f"   Hesitation score: {score}/100")
    
    # Test 5: Recovery Time
    print("\n5. Testing recovery time...")
    recovery_result = calculate_recovery_time(
        interruption_time=10.0,
        segments=test_segments
    )
    print(f"   Recovery time: {recovery_result['recovery_time']}s")
    print(f"   Resumed at: {recovery_result['resumed_at']}s")
    
    # Test 6: Complete Analysis
    print("\n6. Testing complete metrics analysis...")
    complete = analyze_complete_metrics(
        transcript_text=test_text,
        segments=test_segments,
        recording_duration=15.5,
        was_interrupted=True,
        interruption_time=10.0
    )
    
    print("\n   COMPLETE METRICS:")
    for key, value in complete.items():
        print(f"   - {key}: {value}")
    
    print("\n✅ Metrics analyzer test complete!")