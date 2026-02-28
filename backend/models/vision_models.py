"""
vision_models.py
Pydantic models for vision analysis data (posture, expressions, gaze, head pose).
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class PostureState(str, Enum):
    UPRIGHT = "upright"
    SLOUCHING = "slouching"
    LEANING_FORWARD = "leaning_forward"
    LEANING_BACK = "leaning_back"
    UNKNOWN = "unknown"


class GazeState(str, Enum):
    DIRECT = "direct"          # looking at camera
    LOOKING_AWAY = "looking_away"
    LOOKING_DOWN = "looking_down"
    LOOKING_UP = "looking_up"
    UNKNOWN = "unknown"


class HeadPoseState(str, Enum):
    NEUTRAL = "neutral"
    NODDING = "nodding"
    SHAKING = "shaking"
    TILTED_LEFT = "tilted_left"
    TILTED_RIGHT = "tilted_right"
    TURNED_AWAY = "turned_away"
    UNKNOWN = "unknown"


class ExpressionState(str, Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    NERVOUS = "nervous"
    CONFUSED = "confused"
    ANGRY = "angry"
    SAD = "sad"
    SURPRISED = "surprised"
    UNKNOWN = "unknown"


class FrameAnalysis(BaseModel):
    """Result of analyzing a single frame."""
    timestamp: float
    session_id: str
    posture: PostureState = PostureState.UNKNOWN
    gaze: GazeState = GazeState.UNKNOWN
    head_pose: HeadPoseState = HeadPoseState.UNKNOWN
    expression: ExpressionState = ExpressionState.UNKNOWN
    posture_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    gaze_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    expression_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    # Raw landmark counts for overlay rendering
    face_detected: bool = False
    pose_detected: bool = False
    # Derived warning message for live overlay (empty = no warning)
    live_warning: str = ""
    # Normalized score 0-100 for this frame (higher = better body language)
    frame_score: float = Field(default=50.0, ge=0.0, le=100.0)


class AnswerVisionSummary(BaseModel):
    """Aggregated vision metrics for one answer."""
    answer_index: int
    session_id: str
    total_frames_analyzed: int = 0
    # Posture breakdown (% of frames in each state)
    posture_upright_pct: float = 0.0
    posture_slouching_pct: float = 0.0
    # Gaze breakdown
    gaze_direct_pct: float = 0.0
    gaze_away_pct: float = 0.0
    # Head pose
    head_neutral_pct: float = 0.0
    head_away_pct: float = 0.0
    # Dominant expression
    dominant_expression: ExpressionState = ExpressionState.UNKNOWN
    expression_breakdown: dict = Field(default_factory=dict)
    # Aggregate score
    overall_vision_score: float = Field(default=50.0, ge=0.0, le=100.0)
    # Human-readable feedback lines
    feedback_lines: List[str] = Field(default_factory=list)
    # Short headline for FeedbackScreen
    headline: str = ""


class SessionVisionReport(BaseModel):
    """Full session vision report included in FinalReport."""
    session_id: str
    total_frames_analyzed: int = 0
    answer_summaries: List[AnswerVisionSummary] = Field(default_factory=list)
    # Session-level aggregates
    avg_posture_score: float = 0.0
    avg_gaze_score: float = 0.0
    avg_expression_score: float = 0.0
    overall_vision_score: float = 0.0
    # Top strengths and improvements
    strengths: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    summary: str = ""


class VisionWebSocketMessage(BaseModel):
    """Message sent from frontend over WebSocket."""
    session_id: str
    answer_index: int
    # Base64 encoded JPEG frame
    frame_b64: str
    timestamp: float


class VisionWebSocketResponse(BaseModel):
    """Message sent back to frontend over WebSocket."""
    frame_analysis: FrameAnalysis
    # Overlay landmarks as list of (x,y) normalized coords for canvas drawing
    face_landmarks_2d: List[List[float]] = Field(default_factory=list)
    pose_landmarks_2d: List[List[float]] = Field(default_factory=list)