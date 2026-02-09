"""
Authentication Database Schema
Adds user management to InternAI database
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DB_PATH = "internai.db"

# ============================================
# USER TABLE INITIALIZATION
# ============================================

def init_auth_database():
    """
    Add users table and update sessions table with user_id
    Safe to run multiple times (won't delete existing data)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table: Users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            full_name TEXT,
            created_at TIMESTAMP NOT NULL,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    """)
    
    # Check if user_id column exists in sessions table
    cursor.execute("PRAGMA table_info(sessions)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'user_id' not in columns:
        print("➕ Adding user_id column to sessions table...")
        cursor.execute("""
            ALTER TABLE sessions 
            ADD COLUMN user_id INTEGER
        """)
        print("✅ user_id column added")
    
    conn.commit()
    conn.close()
    
    print("✅ Authentication database initialized")

# ============================================
# USER OPERATIONS
# ============================================

def create_user(username: str, email: str, password: str, full_name: str = None) -> Optional[int]:
    """
    Create a new user with hashed password
    
    Args:
        username: Unique username
        email: Unique email
        password: Plain text password (will be hashed)
        full_name: Optional full name
    
    Returns:
        user_id if successful, None if user already exists
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if username or email already exists
    cursor.execute(
        "SELECT id FROM users WHERE username = ? OR email = ?",
        (username, email)
    )
    
    if cursor.fetchone():
        conn.close()
        return None
    
    # Hash password
    hashed_password = pwd_context.hash(password)
    
    try:
        cursor.execute("""
            INSERT INTO users (username, email, hashed_password, full_name, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (username, email, hashed_password, full_name, datetime.now()))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ User created: {username} (ID: {user_id})")
        return user_id
    
    except sqlite3.IntegrityError:
        conn.close()
        return None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_username(username: str) -> Optional[Dict]:
    """Get user by username"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def get_user_by_email(email: str) -> Optional[Dict]:
    """Get user by email"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Get user by ID"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def update_last_login(user_id: int):
    """Update user's last login timestamp"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE users 
        SET last_login = ?
        WHERE id = ?
    """, (datetime.now(), user_id))
    
    conn.commit()
    conn.close()

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """
    Authenticate user with username and password
    
    Args:
        username: Username or email
        password: Plain text password
    
    Returns:
        User dict if authentication successful, None otherwise
    """
    # Try to get user by username or email
    user = get_user_by_username(username)
    if not user:
        user = get_user_by_email(username)
    
    if not user:
        return None
    
    # Verify password
    if not verify_password(password, user["hashed_password"]):
        return None
    
    # Check if user is active
    if not user.get("is_active", True):
        return None
    
    # Update last login
    update_last_login(user["id"])
    
    return user

# ============================================
# SESSION OPERATIONS WITH USER
# ============================================

def create_user_session(session_id: str, user_id: int, ai_powered: bool = True, pressure_enabled: bool = True):
    """Create a new interview session linked to a user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO sessions (session_id, user_id, started_at, ai_powered, pressure_enabled)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, user_id, datetime.now(), ai_powered, pressure_enabled))
    
    conn.commit()
    conn.close()
    print(f"✅ Session created for user {user_id}: {session_id}")

def get_user_sessions(user_id: int, limit: int = 10) -> list:
    """Get all sessions for a specific user"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM sessions 
        WHERE user_id = ?
        ORDER BY started_at DESC
        LIMIT ?
    """, (user_id, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_user_performance_history_by_user(user_id: int, limit: int = 10) -> list:
    """Get performance history for a specific user"""
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
        WHERE s.status = 'completed' AND s.user_id = ?
        GROUP BY s.session_id
        ORDER BY s.completed_at DESC
        LIMIT ?
    """, (user_id, limit))
    
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
    print("TESTING AUTHENTICATION DATABASE")
    print("=" * 50)
    
    # Initialize
    print("\n1. Initializing auth database...")
    init_auth_database()
    
    # Create test user
    print("\n2. Creating test user...")
    user_id = create_user(
        username="testuser",
        email="test@internai.com",
        password="password123",
        full_name="Test User"
    )
    print(f"   User ID: {user_id}")
    
    # Authenticate user
    print("\n3. Testing authentication...")
    user = authenticate_user("testuser", "password123")
    if user:
        print(f"   ✅ Authentication successful: {user['username']}")
    else:
        print("   ❌ Authentication failed")
    
    # Test wrong password
    print("\n4. Testing wrong password...")
    user = authenticate_user("testuser", "wrongpassword")
    if user:
        print("   ❌ Should have failed!")
    else:
        print("   ✅ Correctly rejected wrong password")
    
    print("\n✅ Authentication test complete!")