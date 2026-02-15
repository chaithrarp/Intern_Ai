"""
Database Schema for InternAI
Stores interview sessions, answers, and behavioral metrics
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict, List
import os

# Database file path
DB_PATH = "internai.db"

# ============================================
# DATABASE INITIALIZATION
# ============================================

def init_database():
    """
    Initialize SQLite database with all required tables
    Creates tables if they don't exist
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table 1: Interview Sessions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            started_at TIMESTAMP NOT NULL,
            completed_at TIMESTAMP,
            total_questions INTEGER DEFAULT 0,
            total_interruptions INTEGER DEFAULT 0,
            ai_powered BOOLEAN DEFAULT 1,
            pressure_enabled BOOLEAN DEFAULT 1,
            status TEXT DEFAULT 'active'
        )
    """)
    
    # Table 2: Interview Answers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            question_id INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            answer_text TEXT NOT NULL,
            recording_duration REAL NOT NULL,
            was_interrupted BOOLEAN DEFAULT 0,
            answered_at TIMESTAMP NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    
    # Table 3: Behavioral Metrics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            answer_id INTEGER NOT NULL,
            
            -- Pause Metrics
            total_pauses INTEGER DEFAULT 0,
            long_pauses INTEGER DEFAULT 0,
            avg_pause_duration REAL DEFAULT 0.0,
            max_pause_duration REAL DEFAULT 0.0,
            
            -- Filler Word Metrics
            filler_word_count INTEGER DEFAULT 0,
            filler_words_list TEXT,
            filler_word_rate REAL DEFAULT 0.0,
            
            -- Recovery Metrics (for interrupted answers)
            recovery_time REAL,
            resumed_speaking_at REAL,
            
            -- Speaking Metrics
            words_per_minute REAL DEFAULT 0.0,
            total_words INTEGER DEFAULT 0,
            
            -- Confidence Indicators
            hesitation_score REAL DEFAULT 0.0,
            
            created_at TIMESTAMP NOT NULL,
            
            FOREIGN KEY (session_id) REFERENCES sessions(session_id),
            FOREIGN KEY (answer_id) REFERENCES answers(id)
        )
    """)
    
    # Table 4: Interruption Events
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interruptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            answer_id INTEGER,
            triggered_at_seconds REAL NOT NULL,
            interruption_reason TEXT NOT NULL,
            interruption_phrase TEXT NOT NULL,
            followup_question TEXT NOT NULL,
            partial_answer TEXT,
            recovery_time REAL,
            occurred_at TIMESTAMP NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id),
            FOREIGN KEY (answer_id) REFERENCES answers(id)
        )
    """)
    
    # Table 5: Audio Files (for reference)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audio_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            question_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            uploaded_at TIMESTAMP NOT NULL,
            transcript_language TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Database initialized: {DB_PATH}")

# ============================================
# SESSION OPERATIONS
# ============================================

def create_session(session_id: str, ai_powered: bool = True, pressure_enabled: bool = True):
    """Create a new interview session"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO sessions (session_id, started_at, ai_powered, pressure_enabled)
        VALUES (?, ?, ?, ?)
    """, (session_id, datetime.now(), ai_powered, pressure_enabled))
    
    conn.commit()
    conn.close()
    print(f"✅ Session created: {session_id}")

def complete_session(session_id: str, total_questions: int, total_interruptions: int):
    """Mark session as complete"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE sessions 
        SET completed_at = ?, 
            total_questions = ?, 
            total_interruptions = ?,
            status = 'completed'
        WHERE session_id = ?
    """, (datetime.now(), total_questions, total_interruptions, session_id))
    
    conn.commit()
    conn.close()
    print(f"✅ Session completed: {session_id}")

def get_session(session_id: str) -> Optional[Dict]:
    """Retrieve session data"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

# ============================================
# ANSWER OPERATIONS
# ============================================

def save_answer(
    session_id: str,
    question_id: int,
    question_text: str,
    answer_text: str,
    recording_duration: float,
    was_interrupted: bool = False
) -> int:
    """Save an answer and return its ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO answers (
            session_id, question_id, question_text, answer_text, 
            recording_duration, was_interrupted, answered_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id, question_id, question_text, answer_text,
        recording_duration, was_interrupted, datetime.now()
    ))
    
    answer_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    print(f"✅ Answer saved: ID={answer_id}")
    return answer_id

# ============================================
# AUDIO FILE OPERATIONS
# ============================================

def save_audio_file(
    session_id: str,
    question_id: int,
    filename: str,
    file_path: str,
    file_size: int,
    language: str
):
    """Save audio file metadata"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO audio_files (
            session_id, question_id, filename, file_path, 
            file_size, uploaded_at, transcript_language
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id, question_id, filename, file_path,
        file_size, datetime.now(), language
    ))
    
    conn.commit()
    conn.close()

# ============================================
# UTILITY FUNCTIONS
# ============================================

def check_database_exists() -> bool:
    """Check if database file exists"""
    return os.path.exists(DB_PATH)

def get_database_stats() -> Dict:
    """Get database statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = {}
    
    cursor.execute("SELECT COUNT(*) FROM sessions")
    stats['total_sessions'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM answers")
    stats['total_answers'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM metrics")
    stats['total_metrics'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM interruptions")
    stats['total_interruptions'] = cursor.fetchone()[0]
    
    conn.close()
    return stats



# Add these functions to database.py

def save_evaluation(
    session_id: str,
    answer_id: int,
    evaluation_data: dict
):
    """Save answer evaluation to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            answer_id INTEGER NOT NULL,
            round_type TEXT NOT NULL,
            overall_score INTEGER NOT NULL,
            scores TEXT NOT NULL,
            strengths TEXT,
            weaknesses TEXT,
            red_flags TEXT,
            difficulty_adjustment TEXT,
            created_at TIMESTAMP NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id),
            FOREIGN KEY (answer_id) REFERENCES answers(id)
        )
    """)
    
    import json
    
    cursor.execute("""
        INSERT INTO evaluations (
            session_id, answer_id, round_type, overall_score,
            scores, strengths, weaknesses, red_flags,
            difficulty_adjustment, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        answer_id,
        evaluation_data.get("round_type"),
        evaluation_data.get("overall_score"),
        json.dumps(evaluation_data.get("scores")),
        json.dumps(evaluation_data.get("strengths")),
        json.dumps(evaluation_data.get("weaknesses")),
        json.dumps(evaluation_data.get("red_flags")),
        evaluation_data.get("difficulty_adjustment"),
        datetime.now()
    ))
    
    conn.commit()
    conn.close()

def get_session_evaluations(session_id: str) -> List[Dict]:
    """Get all evaluations for a session"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM evaluations 
        WHERE session_id = ?
        ORDER BY created_at
    """, (session_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    import json
    
    evaluations = []
    for row in rows:
        eval_dict = dict(row)
        eval_dict["scores"] = json.loads(eval_dict["scores"])
        eval_dict["strengths"] = json.loads(eval_dict["strengths"])
        eval_dict["weaknesses"] = json.loads(eval_dict["weaknesses"])
        eval_dict["red_flags"] = json.loads(eval_dict["red_flags"])
        evaluations.append(eval_dict)
    
    return evaluations


# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    print("=" * 50)
    print("TESTING DATABASE MODULE")
    print("=" * 50)
    
    # Initialize database
    print("\n1. Initializing database...")
    init_database()
    
    # Create test session
    print("\n2. Creating test session...")
    test_session_id = "test_session_001"
    create_session(test_session_id, ai_powered=True, pressure_enabled=True)
    
    # Save test answer
    print("\n3. Saving test answer...")
    answer_id = save_answer(
        session_id=test_session_id,
        question_id=1,
        question_text="Tell me about yourself.",
        answer_text="I am a software engineer with 3 years of experience...",
        recording_duration=45.5,
        was_interrupted=False
    )
    
    # Get session
    print("\n4. Retrieving session...")
    session = get_session(test_session_id)
    print(f"   Session: {session}")
    
    # Get stats
    print("\n5. Database statistics:")
    stats = get_database_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Database test complete!")