"""
Metrics Storage Layer
Handles saving and retrieving behavioral metrics from database
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

DB_PATH = "internai.db"

# ============================================
# SAVE METRICS
# ============================================

def save_metrics(
    session_id: str,
    answer_id: int,
    metrics: Dict
) -> int:
    """
    Save behavioral metrics to database
    
    Args:
        session_id: Interview session ID
        answer_id: Answer ID this metric belongs to
        metrics: Dictionary of metrics from metrics_analyzer
    
    Returns:
        metrics_id: ID of saved metrics record
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO metrics (
            session_id,
            answer_id,
            total_pauses,
            long_pauses,
            avg_pause_duration,
            max_pause_duration,
            filler_word_count,
            filler_words_list,
            filler_word_rate,
            recovery_time,
            resumed_speaking_at,
            words_per_minute,
            total_words,
            hesitation_score,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        answer_id,
        metrics.get("total_pauses", 0),
        metrics.get("long_pauses", 0),
        metrics.get("avg_pause_duration", 0.0),
        metrics.get("max_pause_duration", 0.0),
        metrics.get("filler_word_count", 0),
        metrics.get("filler_words_list", ""),
        metrics.get("filler_word_rate", 0.0),
        metrics.get("recovery_time"),
        metrics.get("resumed_speaking_at"),
        metrics.get("words_per_minute", 0.0),
        metrics.get("total_words", 0),
        metrics.get("hesitation_score", 0.0),
        datetime.now()
    ))
    
    metrics_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    print(f"✅ Metrics saved: ID={metrics_id}")
    return metrics_id

# ============================================
# SAVE INTERRUPTION EVENT
# ============================================

def save_interruption(
    session_id: str,
    answer_id: Optional[int],
    triggered_at_seconds: float,
    interruption_reason: str,
    interruption_phrase: str,
    followup_question: str,
    partial_answer: str = "",
    recovery_time: Optional[float] = None
) -> int:
    """
    Save interruption event to database
    
    Args:
        session_id: Interview session ID
        answer_id: Answer ID (may be None if not yet saved)
        triggered_at_seconds: When interruption occurred
        interruption_reason: Why interrupted (rambling, time, etc.)
        interruption_phrase: What AI said during interruption
        followup_question: Follow-up question asked
        partial_answer: What user said before interruption
        recovery_time: How long to resume (if known)
    
    Returns:
        interruption_id: ID of saved interruption record
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO interruptions (
            session_id,
            answer_id,
            triggered_at_seconds,
            interruption_reason,
            interruption_phrase,
            followup_question,
            partial_answer,
            recovery_time,
            occurred_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        answer_id,
        triggered_at_seconds,
        interruption_reason,
        interruption_phrase,
        followup_question,
        partial_answer,
        recovery_time,
        datetime.now()
    ))
    
    interruption_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    print(f"✅ Interruption saved: ID={interruption_id}")
    return interruption_id

# ============================================
# RETRIEVE METRICS
# ============================================

def get_session_metrics(session_id: str) -> List[Dict]:
    """
    Get all metrics for a session
    
    Args:
        session_id: Interview session ID
    
    Returns:
        List of metric dictionaries
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT m.*, a.question_text, a.answer_text, a.recording_duration
        FROM metrics m
        JOIN answers a ON m.answer_id = a.id
        WHERE m.session_id = ?
        ORDER BY a.answered_at
    """, (session_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_answer_metrics(answer_id: int) -> Optional[Dict]:
    """
    Get metrics for a specific answer
    
    Args:
        answer_id: Answer ID
    
    Returns:
        Metrics dictionary or None
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM metrics WHERE answer_id = ?", (answer_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

# ============================================
# RETRIEVE INTERRUPTIONS
# ============================================

def get_session_interruptions(session_id: str) -> List[Dict]:
    """
    Get all interruptions for a session
    
    Args:
        session_id: Interview session ID
    
    Returns:
        List of interruption dictionaries
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM interruptions
        WHERE session_id = ?
        ORDER BY occurred_at
    """, (session_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

# ============================================
# SESSION SUMMARY
# ============================================

def get_session_summary(session_id: str) -> Dict:
    """
    Get complete session summary with aggregated metrics
    
    Args:
        session_id: Interview session ID
    
    Returns:
        Dictionary with session summary
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get session info
    cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
    session = cursor.fetchone()
    
    if not session:
        conn.close()
        return None
    
    # Get aggregated metrics
    cursor.execute("""
        SELECT 
            COUNT(*) as total_answers,
            AVG(hesitation_score) as avg_hesitation,
            SUM(filler_word_count) as total_fillers,
            SUM(long_pauses) as total_long_pauses,
            AVG(words_per_minute) as avg_wpm,
            AVG(recovery_time) as avg_recovery_time
        FROM metrics
        WHERE session_id = ?
    """, (session_id,))
    
    metrics_summary = cursor.fetchone()
    
    # Get interruption count
    cursor.execute("""
        SELECT COUNT(*) as interruption_count
        FROM interruptions
        WHERE session_id = ?
    """, (session_id,))
    
    interruption_count = cursor.fetchone()["interruption_count"]
    
    conn.close()
    
    return {
        "session_id": session_id,
        "started_at": session["started_at"],
        "completed_at": session["completed_at"],
        "status": session["status"],
        "total_questions": session["total_questions"],
        "total_answers": metrics_summary["total_answers"],
        "total_interruptions": interruption_count,
        "avg_hesitation_score": round(metrics_summary["avg_hesitation"] or 0, 2),
        "total_filler_words": metrics_summary["total_fillers"] or 0,
        "total_long_pauses": metrics_summary["total_long_pauses"] or 0,
        "avg_words_per_minute": round(metrics_summary["avg_wpm"] or 0, 1),
        "avg_recovery_time": round(metrics_summary["avg_recovery_time"] or 0, 2) if metrics_summary["avg_recovery_time"] else None
    }

# ============================================
# PERFORMANCE COMPARISON
# ============================================

def get_user_performance_history(limit: int = 10) -> List[Dict]:
    """
    Get recent session summaries for trend analysis
    
    Args:
        limit: Number of recent sessions to retrieve
    
    Returns:
        List of session summaries
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            s.session_id,
            s.started_at,
            s.completed_at,
            s.total_questions,
            AVG(m.hesitation_score) as avg_hesitation,
            SUM(m.filler_word_count) as total_fillers,
            AVG(m.words_per_minute) as avg_wpm,
            COUNT(i.id) as interruption_count
        FROM sessions s
        LEFT JOIN metrics m ON s.session_id = m.session_id
        LEFT JOIN interruptions i ON s.session_id = i.session_id
        WHERE s.status = 'completed'
        GROUP BY s.session_id
        ORDER BY s.completed_at DESC
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            "session_id": row["session_id"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
            "total_questions": row["total_questions"],
            "avg_hesitation_score": round(row["avg_hesitation"] or 0, 2),
            "total_filler_words": row["total_fillers"] or 0,
            "avg_words_per_minute": round(row["avg_wpm"] or 0, 1),
            "interruption_count": row["interruption_count"] or 0
        })
    
    return history

# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    print("=" * 50)
    print("TESTING METRICS STORAGE")
    print("=" * 50)
    
    # First, ensure database exists
    from database import init_database, create_session, save_answer
    init_database()
    
    # Create test session and answer
    print("\n1. Creating test session and answer...")
    test_session_id = "test_storage_session"
    create_session(test_session_id, ai_powered=True, pressure_enabled=True)
    
    answer_id = save_answer(
        session_id=test_session_id,
        question_id=1,
        question_text="Tell me about yourself.",
        answer_text="Um, so like, I am a developer, you know, with experience in Python.",
        recording_duration=15.5,
        was_interrupted=False
    )
    
    # Save test metrics
    print("\n2. Saving test metrics...")
    test_metrics = {
        "total_pauses": 3,
        "long_pauses": 2,
        "avg_pause_duration": 1.8,
        "max_pause_duration": 3.2,
        "filler_word_count": 4,
        "filler_words_list": "um,so,like,you know",
        "filler_word_rate": 0.25,
        "recovery_time": None,
        "resumed_speaking_at": None,
        "words_per_minute": 77.4,
        "total_words": 20,
        "hesitation_score": 45.5
    }
    
    metrics_id = save_metrics(test_session_id, answer_id, test_metrics)
    
    # Save test interruption
    print("\n3. Saving test interruption...")
    interruption_id = save_interruption(
        session_id=test_session_id,
        answer_id=answer_id,
        triggered_at_seconds=10.5,
        interruption_reason="rambling",
        interruption_phrase="Hold on a second...",
        followup_question="Can you be more specific?",
        partial_answer="Um, so like, I am a developer...",
        recovery_time=2.3
    )
    
    # Retrieve metrics
    print("\n4. Retrieving session metrics...")
    session_metrics = get_session_metrics(test_session_id)
    print(f"   Found {len(session_metrics)} metric records")
    
    # Get session summary
    print("\n5. Getting session summary...")
    summary = get_session_summary(test_session_id)
    print(f"   Summary:")
    for key, value in summary.items():
        print(f"   - {key}: {value}")
    
    # Get interruptions
    print("\n6. Getting interruptions...")
    interruptions = get_session_interruptions(test_session_id)
    print(f"   Found {len(interruptions)} interruptions")
    
    print("\n✅ Metrics storage test complete!")