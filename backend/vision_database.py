"""
vision_database.py
Database helpers for persisting vision analysis results.
Add this file alongside database.py and call init_vision_database() from main.py startup.

Schema additions:
  - vision_frame_events  : raw per-frame analysis log (pruned periodically)
  - vision_answer_summary: aggregated per-answer vision metrics
  - vision_session_report: final session-level vision report (JSON blob)
"""

import sqlite3
import json
import logging
from typing import Optional
from models.vision_models import AnswerVisionSummary, SessionVisionReport

logger = logging.getLogger(__name__)
DB_PATH = "internai.db"


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_vision_database():
    """Create vision tables if they don't exist. Call once on app startup."""
    conn = _get_conn()
    try:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS vision_frame_events (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id    TEXT NOT NULL,
                answer_index  INTEGER NOT NULL,
                timestamp     REAL NOT NULL,
                posture       TEXT,
                gaze          TEXT,
                head_pose     TEXT,
                expression    TEXT,
                frame_score   REAL,
                live_warning  TEXT,
                created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS vision_answer_summary (
                id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id              TEXT NOT NULL,
                answer_index            INTEGER NOT NULL,
                total_frames            INTEGER DEFAULT 0,
                posture_upright_pct     REAL DEFAULT 0,
                posture_slouching_pct   REAL DEFAULT 0,
                gaze_direct_pct         REAL DEFAULT 0,
                gaze_away_pct           REAL DEFAULT 0,
                head_neutral_pct        REAL DEFAULT 0,
                dominant_expression     TEXT,
                overall_vision_score    REAL DEFAULT 0,
                headline                TEXT,
                feedback_json           TEXT,
                created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(session_id, answer_index)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS vision_session_report (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id            TEXT UNIQUE NOT NULL,
                total_frames          INTEGER DEFAULT 0,
                avg_posture_score     REAL DEFAULT 0,
                avg_gaze_score        REAL DEFAULT 0,
                overall_vision_score  REAL DEFAULT 0,
                strengths_json        TEXT,
                improvements_json     TEXT,
                summary               TEXT,
                report_json           TEXT,
                created_at            DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        logger.info("[VisionDB] Vision tables initialized.")
    except Exception as e:
        logger.error(f"[VisionDB] init error: {e}")
    finally:
        conn.close()


def save_vision_frame_event(
    session_id: str,
    answer_index: int,
    timestamp: float,
    posture: str,
    gaze: str,
    head_pose: str,
    expression: str,
    frame_score: float,
    live_warning: str,
):
    """Persist a single frame analysis event. Call selectively (e.g. only when warning present) to keep DB small."""
    conn = _get_conn()
    try:
        conn.execute("""
            INSERT INTO vision_frame_events
              (session_id, answer_index, timestamp, posture, gaze, head_pose, expression, frame_score, live_warning)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (session_id, answer_index, timestamp, posture, gaze, head_pose, expression, frame_score, live_warning))
        conn.commit()
    except Exception as e:
        logger.error(f"[VisionDB] save_vision_frame_event error: {e}")
    finally:
        conn.close()


def save_answer_vision_summary(summary: AnswerVisionSummary):
    """Upsert an AnswerVisionSummary into the DB."""
    conn = _get_conn()
    try:
        conn.execute("""
            INSERT INTO vision_answer_summary
              (session_id, answer_index, total_frames, posture_upright_pct, posture_slouching_pct,
               gaze_direct_pct, gaze_away_pct, head_neutral_pct, dominant_expression,
               overall_vision_score, headline, feedback_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id, answer_index) DO UPDATE SET
              total_frames=excluded.total_frames,
              posture_upright_pct=excluded.posture_upright_pct,
              posture_slouching_pct=excluded.posture_slouching_pct,
              gaze_direct_pct=excluded.gaze_direct_pct,
              gaze_away_pct=excluded.gaze_away_pct,
              head_neutral_pct=excluded.head_neutral_pct,
              dominant_expression=excluded.dominant_expression,
              overall_vision_score=excluded.overall_vision_score,
              headline=excluded.headline,
              feedback_json=excluded.feedback_json
        """, (
            summary.session_id,
            summary.answer_index,
            summary.total_frames_analyzed,
            summary.posture_upright_pct,
            summary.posture_slouching_pct,
            summary.gaze_direct_pct,
            summary.gaze_away_pct,
            summary.head_neutral_pct,
            summary.dominant_expression.value,
            summary.overall_vision_score,
            summary.headline,
            json.dumps(summary.feedback_lines),
        ))
        conn.commit()
    except Exception as e:
        logger.error(f"[VisionDB] save_answer_vision_summary error: {e}")
    finally:
        conn.close()


def save_session_vision_report(report: SessionVisionReport):
    """Upsert a full SessionVisionReport."""
    conn = _get_conn()
    try:
        conn.execute("""
            INSERT INTO vision_session_report
              (session_id, total_frames, avg_posture_score, avg_gaze_score,
               overall_vision_score, strengths_json, improvements_json, summary, report_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
              total_frames=excluded.total_frames,
              avg_posture_score=excluded.avg_posture_score,
              avg_gaze_score=excluded.avg_gaze_score,
              overall_vision_score=excluded.overall_vision_score,
              strengths_json=excluded.strengths_json,
              improvements_json=excluded.improvements_json,
              summary=excluded.summary,
              report_json=excluded.report_json
        """, (
            report.session_id,
            report.total_frames_analyzed,
            report.avg_posture_score,
            report.avg_gaze_score,
            report.overall_vision_score,
            json.dumps(report.strengths),
            json.dumps(report.improvements),
            report.summary,
            report.model_dump_json(),
        ))
        conn.commit()
    except Exception as e:
        logger.error(f"[VisionDB] save_session_vision_report error: {e}")
    finally:
        conn.close()


def get_session_vision_report_from_db(session_id: str) -> Optional[dict]:
    """Retrieve stored SessionVisionReport JSON for a session."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT report_json FROM vision_session_report WHERE session_id = ?",
            (session_id,)
        ).fetchone()
        if row and row["report_json"]:
            return json.loads(row["report_json"])
        return None
    except Exception as e:
        logger.error(f"[VisionDB] get error: {e}")
        return None
    finally:
        conn.close()