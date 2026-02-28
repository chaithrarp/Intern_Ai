"""
vision_analyzer.py
Core vision analysis engine — compatible with mediapipe >= 0.10.x

FIXES APPLIED:
  - _estimate_gaze: corrected iris horizontal ratio direction for mirrored camera
    (frontend captures raw/unmirrored frames; display is scaleX(-1) but captured
     canvas is NOT mirrored — so LEFT_EYE_IN is actually on the right side of screen)
"""

from __future__ import annotations
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_tasks
from mediapipe.tasks.python import vision as mp_vision
from mediapipe.tasks.python.vision import RunningMode
import base64
import time
import logging
import math
import os
import urllib.request
from collections import deque, defaultdict
from typing import Any, Optional, Tuple, Dict, List

from models.vision_models import (
    FrameAnalysis, PostureState, GazeState, HeadPoseState, ExpressionState,
    AnswerVisionSummary, SessionVisionReport,
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
DEEPFACE_INTERVAL_SECONDS = 5.0
MAX_FRAME_BUFFER          = 300
MODELS_DIR                = os.path.join(os.path.dirname(__file__), "mp_models")

FACE_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task"
POSE_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"

FACE_MODEL_PATH = os.path.join(MODELS_DIR, "face_landmarker.task")
POSE_MODEL_PATH = os.path.join(MODELS_DIR, "pose_landmarker_lite.task")


# ──────────────────────────────────────────────
# Model download helper
# ──────────────────────────────────────────────
def _ensure_models():
    os.makedirs(MODELS_DIR, exist_ok=True)
    for path, url in [(FACE_MODEL_PATH, FACE_MODEL_URL), (POSE_MODEL_PATH, POSE_MODEL_URL)]:
        if not os.path.exists(path):
            logger.info(f"[Vision] Downloading model: {os.path.basename(path)} ...")
            try:
                urllib.request.urlretrieve(url, path)
                logger.info(f"[Vision] Downloaded: {path}")
            except Exception as e:
                logger.error(f"[Vision] Failed to download {path}: {e}")
                raise RuntimeError(
                    f"Could not download MediaPipe model from {url}. "
                    "Check your internet connection or manually place the file at: " + path
                )


# ──────────────────────────────────────────────
# Lazy singleton landmarkers
# ──────────────────────────────────────────────
_face_landmarker: Optional[Any] = None
_pose_landmarker: Optional[Any] = None


def _get_face_landmarker() -> Any:
    global _face_landmarker
    if _face_landmarker is None:
        _ensure_models()
        options = mp_vision.FaceLandmarkerOptions(
            base_options=mp_tasks.BaseOptions(model_asset_path=FACE_MODEL_PATH),
            running_mode=RunningMode.IMAGE,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
        )
        _face_landmarker = mp_vision.FaceLandmarker.create_from_options(options)
        logger.info("[Vision] FaceLandmarker initialized")
    return _face_landmarker


def _get_pose_landmarker() -> Any:
    global _pose_landmarker
    if _pose_landmarker is None:
        _ensure_models()
        options = mp_vision.PoseLandmarkerOptions(
            base_options=mp_tasks.BaseOptions(model_asset_path=POSE_MODEL_PATH),
            running_mode=RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        _pose_landmarker = mp_vision.PoseLandmarker.create_from_options(options)
        logger.info("[Vision] PoseLandmarker initialized")
    return _pose_landmarker


# ──────────────────────────────────────────────
# Landmark index constants
# ──────────────────────────────────────────────
NOSE_TIP       = 1
CHIN           = 152
LEFT_EYE_OUT   = 33
RIGHT_EYE_OUT  = 263
LEFT_EYE_IN    = 133
RIGHT_EYE_IN   = 362
LEFT_EAR       = 234
RIGHT_EAR      = 454
LEFT_UPPER_LID = 159
LEFT_LOWER_LID = 145
LEFT_IRIS      = 468
RIGHT_IRIS     = 473

LEFT_SHOULDER  = 11
RIGHT_SHOULDER = 12
LEFT_HIP       = 23
RIGHT_HIP      = 24
LEFT_EAR_POSE  = 7
RIGHT_EAR_POSE = 8
NOSE_POSE      = 0


# ──────────────────────────────────────────────
# Per-session state
# ──────────────────────────────────────────────
class _SessionVisionState:
    def __init__(self, session_id: str):
        self.session_id         = session_id
        self.frame_buffer       = deque(maxlen=MAX_FRAME_BUFFER)
        self.last_deepface_time = 0.0
        self.last_expression    = ExpressionState.UNKNOWN
        self.answer_frames: Dict[int, List[FrameAnalysis]] = defaultdict(list)

    def add_frame(self, answer_index: int, fa: FrameAnalysis):
        self.frame_buffer.append(fa)
        self.answer_frames[answer_index].append(fa)


_sessions: Dict[str, _SessionVisionState] = {}


def get_or_create_session(session_id: str) -> _SessionVisionState:
    if session_id not in _sessions:
        _sessions[session_id] = _SessionVisionState(session_id)
    return _sessions[session_id]


def remove_session(session_id: str):
    _sessions.pop(session_id, None)


# ──────────────────────────────────────────────
# Frame decoding
# ──────────────────────────────────────────────
def decode_frame(frame_b64: str) -> Optional[np.ndarray]:
    try:
        data = base64.b64decode(frame_b64)
        arr  = np.frombuffer(data, dtype=np.uint8)
        img  = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        logger.warning(f"[Vision] Frame decode error: {e}")
        return None


# ──────────────────────────────────────────────
# Head pose estimation
# ──────────────────────────────────────────────
def _estimate_head_pose(landmarks, w: int, h: int) -> Tuple[HeadPoseState, float]:
    try:
        def lm(idx):
            pt = landmarks[idx]
            return np.array([pt.x * w, pt.y * h])

        nose      = lm(NOSE_TIP)
        left_ear  = lm(LEFT_EAR)
        right_ear = lm(RIGHT_EAR)

        dist_left  = abs(nose[0] - left_ear[0])
        dist_right = abs(nose[0] - right_ear[0])
        total      = dist_left + dist_right
        if total < 1:
            return HeadPoseState.UNKNOWN, 0.0

        yaw_ratio = (dist_right - dist_left) / total
        yaw_deg   = yaw_ratio * 60

        if abs(yaw_deg) > 25:
            return HeadPoseState.TURNED_AWAY, yaw_deg

        left_eye_y  = landmarks[LEFT_EYE_OUT].y * h
        right_eye_y = landmarks[RIGHT_EYE_OUT].y * h
        tilt        = left_eye_y - right_eye_y
        if abs(tilt) > h * 0.05:
            return (HeadPoseState.TILTED_LEFT if tilt > 0 else HeadPoseState.TILTED_RIGHT), yaw_deg

        return HeadPoseState.NEUTRAL, yaw_deg
    except Exception:
        return HeadPoseState.UNKNOWN, 0.0


# ──────────────────────────────────────────────
# Gaze estimation — FIX: corrected for unmirrored captured frames
#
# The frontend video element uses CSS `transform: scaleX(-1)` for display,
# but the canvas capture (drawImage from video) produces an UNMIRRORED frame.
# This means in the captured frame:
#   - The person's actual LEFT eye appears on the RIGHT side of the image (high x)
#   - The person's actual RIGHT eye appears on the LEFT side (low x)
#
# MediaPipe landmark indices are defined anatomically (LEFT = person's left).
# So LEFT_IRIS (468) will appear at HIGH x values in the captured frame,
# and LEFT_EYE_IN (133, inner corner) will appear at HIGH x relative to LEFT_EYE_OUT (33).
#
# FIX: Use abs() eye span and clamp ratio symmetrically so horizontal gaze
# works correctly regardless of mirror orientation. We compare iris position
# relative to the eye center, not the inner-to-outer direction.
# ──────────────────────────────────────────────
def _estimate_gaze(landmarks, w: int, h: int) -> Tuple[GazeState, float]:
    try:
        if len(landmarks) < 474:
            return GazeState.UNKNOWN, 0.5

        def lmxy(idx):
            pt = landmarks[idx]
            return np.array([pt.x * w, pt.y * h])

        l_iris  = lmxy(LEFT_IRIS)
        r_iris  = lmxy(RIGHT_IRIS)
        l_inner = lmxy(LEFT_EYE_IN)
        l_outer = lmxy(LEFT_EYE_OUT)
        r_inner = lmxy(RIGHT_EYE_IN)
        r_outer = lmxy(RIGHT_EYE_OUT)

        # ── FIX: compute iris offset from eye CENTER, not from inner corner ──
        # This is mirror-agnostic: if iris is near center → looking forward,
        # if iris is near either edge → looking sideways.
        def center_ratio(iris, corner_a, corner_b):
            """Returns 0.0 when iris is at center, ±1.0 when at an edge."""
            eye_center_x = (corner_a[0] + corner_b[0]) / 2.0
            half_span    = abs(corner_b[0] - corner_a[0]) / 2.0
            if half_span < 1:
                return 0.0
            return (iris[0] - eye_center_x) / half_span  # [-1, +1]

        l_ratio = center_ratio(l_iris, l_inner, l_outer)
        r_ratio = center_ratio(r_iris, r_inner, r_outer)

        # Average signed offset — looking left/right produces a consistent sign
        avg_offset = (l_ratio + r_ratio) / 2.0
        # abs gives "how far from center" regardless of direction
        abs_offset = abs(avg_offset)

        # Threshold: if iris is more than 30% away from eye center → looking away
        if abs_offset > 0.30:
            return GazeState.LOOKING_AWAY, abs_offset

        # Vertical gaze using lid landmarks
        eye_h         = abs(landmarks[LEFT_LOWER_LID].y - landmarks[LEFT_UPPER_LID].y) * h
        iris_v_offset = l_iris[1] - landmarks[LEFT_UPPER_LID].y * h
        v_ratio       = iris_v_offset / max(eye_h, 1)

        if v_ratio < 0.2:
            return GazeState.LOOKING_UP, abs_offset
        if v_ratio > 0.8:
            return GazeState.LOOKING_DOWN, abs_offset

        return GazeState.DIRECT, abs_offset

    except Exception:
        return GazeState.UNKNOWN, 0.5


# ──────────────────────────────────────────────
# Posture estimation
# ──────────────────────────────────────────────
def _estimate_posture(pose_landmarks) -> Tuple[PostureState, float]:
    try:
        def lm(idx):
            pt = pose_landmarks[idx]
            return np.array([pt.x, pt.y, pt.z]), pt.visibility

        l_shoulder, l_vis  = lm(LEFT_SHOULDER)
        r_shoulder, r_vis  = lm(RIGHT_SHOULDER)
        l_hip,      lh_vis = lm(LEFT_HIP)
        r_hip,      rh_vis = lm(RIGHT_HIP)
        l_ear,      le_vis = lm(LEFT_EAR_POSE)
        r_ear,      re_vis = lm(RIGHT_EAR_POSE)

        min_vis = min(l_vis, r_vis, lh_vis, rh_vis)
        if min_vis < 0.5:
            return PostureState.UNKNOWN, float(min_vis)

        mid_shoulder = (l_shoulder + r_shoulder) / 2
        mid_hip      = (l_hip + r_hip) / 2
        mid_ear      = (l_ear + r_ear) / 2

        spine       = mid_hip - mid_shoulder
        spine_angle = math.degrees(math.atan2(abs(spine[0]), abs(spine[1])))

        ear_forward_offset = abs(mid_ear[0] - mid_shoulder[0])

        if spine_angle > 20 or ear_forward_offset > 0.08:
            return PostureState.SLOUCHING, float(min_vis)

        lean = mid_shoulder[0] - mid_hip[0]
        if lean > 0.08:
            return PostureState.LEANING_FORWARD, float(min_vis)
        if lean < -0.08:
            return PostureState.LEANING_BACK, float(min_vis)

        return PostureState.UPRIGHT, float(min_vis)
    except Exception:
        return PostureState.UNKNOWN, 0.0


# ──────────────────────────────────────────────
# DeepFace expression (throttled)
# ──────────────────────────────────────────────
_DEEPFACE_MAP = {
    "happy":    ExpressionState.HAPPY,
    "neutral":  ExpressionState.NEUTRAL,
    "sad":      ExpressionState.SAD,
    "angry":    ExpressionState.ANGRY,
    "fear":     ExpressionState.NERVOUS,
    "surprise": ExpressionState.SURPRISED,
    "disgust":  ExpressionState.CONFUSED,
}


def _run_deepface(img_bgr: np.ndarray) -> ExpressionState:
    try:
        from deepface import DeepFace
        result   = DeepFace.analyze(img_bgr, actions=["emotion"], enforce_detection=False, silent=True)
        if isinstance(result, list):
            result = result[0]
        dominant = result.get("dominant_emotion", "neutral").lower()
        return _DEEPFACE_MAP.get(dominant, ExpressionState.NEUTRAL)
    except Exception as e:
        logger.debug(f"[Vision] DeepFace error: {e}")
        return ExpressionState.UNKNOWN


# ──────────────────────────────────────────────
# Warning builder
# ──────────────────────────────────────────────
def _build_live_warning(posture, gaze, head_pose, expression) -> str:
    if posture    == PostureState.SLOUCHING:      return "⚠️ Sit up straight — posture matters!"
    if gaze       == GazeState.LOOKING_AWAY:      return "👁️ Maintain eye contact with the camera"
    if gaze       == GazeState.LOOKING_DOWN:      return "👁️ Look up — keep eye contact"
    if head_pose  == HeadPoseState.TURNED_AWAY:   return "🙂 Face the camera directly"
    if expression == ExpressionState.NERVOUS:     return "😌 Take a breath — you're doing great!"
    if expression == ExpressionState.CONFUSED:    return "🤔 Show confidence in your answer"
    return ""


# ──────────────────────────────────────────────
# Frame score
# ──────────────────────────────────────────────
def _compute_frame_score(posture, gaze, head_pose, expression) -> float:
    score = 100.0
    if posture == PostureState.SLOUCHING:                                           score -= 25
    elif posture in (PostureState.LEANING_FORWARD, PostureState.LEANING_BACK):     score -= 10
    elif posture == PostureState.UNKNOWN:                                           score -= 5

    if gaze == GazeState.LOOKING_AWAY:                                             score -= 20
    elif gaze == GazeState.LOOKING_DOWN:                                           score -= 15
    elif gaze == GazeState.LOOKING_UP:                                             score -= 10
    elif gaze == GazeState.UNKNOWN:                                                score -= 5

    if head_pose == HeadPoseState.TURNED_AWAY:                                     score -= 15
    elif head_pose in (HeadPoseState.TILTED_LEFT, HeadPoseState.TILTED_RIGHT):     score -= 5

    if expression == ExpressionState.NERVOUS:                                      score -= 10
    elif expression == ExpressionState.CONFUSED:                                   score -= 10
    elif expression == ExpressionState.ANGRY:                                      score -= 15
    elif expression == ExpressionState.HAPPY:                                      score += 5

    return max(0.0, min(100.0, score))


# ──────────────────────────────────────────────
# Main analysis function
# ──────────────────────────────────────────────
def analyze_frame(
    frame_b64: str,
    session_id: str,
    answer_index: int,
    timestamp: float,
) -> Tuple[FrameAnalysis, List[List[float]], List[List[float]]]:

    state = get_or_create_session(session_id)

    img = decode_frame(frame_b64)
    if img is None:
        fa = FrameAnalysis(timestamp=timestamp, session_id=session_id)
        return fa, [], []

    h, w = img.shape[:2]

    rgb      = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    posture       = PostureState.UNKNOWN
    gaze          = GazeState.UNKNOWN
    head_pose     = HeadPoseState.UNKNOWN
    expression    = state.last_expression
    posture_conf  = 0.0
    gaze_conf     = 0.0
    face_detected = False
    pose_detected = False
    face_lm_2d: List[List[float]] = []
    pose_lm_2d: List[List[float]] = []

    # ── Face landmarker ──────────────────────────────────────────────────────
    try:
        face_result = _get_face_landmarker().detect(mp_image)
        if face_result.face_landmarks:
            face_detected    = True
            lms              = face_result.face_landmarks[0]
            head_pose, _     = _estimate_head_pose(lms, w, h)
            gaze, gaze_conf  = _estimate_gaze(lms, w, h)
            face_lm_2d = [[lms[i].x, lms[i].y] for i in range(0, len(lms), 5)]
    except Exception as e:
        logger.debug(f"[Vision] Face landmarker error: {e}")

    # ── Pose landmarker ──────────────────────────────────────────────────────
    try:
        pose_result = _get_pose_landmarker().detect(mp_image)
        if pose_result.pose_landmarks:
            pose_detected         = True
            plms                  = pose_result.pose_landmarks[0]
            posture, posture_conf = _estimate_posture(plms)
            key_indices = [LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_HIP, RIGHT_HIP,
                           LEFT_EAR_POSE, RIGHT_EAR_POSE, NOSE_POSE]
            pose_lm_2d = [[plms[i].x, plms[i].y] for i in key_indices if i < len(plms)]
    except Exception as e:
        logger.debug(f"[Vision] Pose landmarker error: {e}")

    # ── DeepFace (throttled) ─────────────────────────────────────────────────
    now = time.time()
    if (now - state.last_deepface_time) >= DEEPFACE_INTERVAL_SECONDS:
        expression               = _run_deepface(img)
        state.last_deepface_time = now
        state.last_expression    = expression

    warning = _build_live_warning(posture, gaze, head_pose, expression)
    score   = _compute_frame_score(posture, gaze, head_pose, expression)

    fa = FrameAnalysis(
        timestamp=timestamp,
        session_id=session_id,
        posture=posture,
        gaze=gaze,
        head_pose=head_pose,
        expression=expression,
        posture_confidence=posture_conf,
        gaze_confidence=gaze_conf,
        expression_confidence=0.8 if expression != ExpressionState.UNKNOWN else 0.0,
        face_detected=face_detected,
        pose_detected=pose_detected,
        live_warning=warning,
        frame_score=score,
    )

    state.add_frame(answer_index, fa)
    return fa, face_lm_2d, pose_lm_2d


# ──────────────────────────────────────────────
# Answer-level aggregation
# ──────────────────────────────────────────────
def get_answer_vision_summary(session_id: str, answer_index: int) -> AnswerVisionSummary:
    state  = get_or_create_session(session_id)
    frames = state.answer_frames.get(answer_index, [])
    base   = AnswerVisionSummary(answer_index=answer_index, session_id=session_id)

    if not frames:
        base.headline = "No video data captured for this answer."
        return base

    n = len(frames)
    base.total_frames_analyzed = n

    base.posture_upright_pct   = sum(1 for f in frames if f.posture == PostureState.UPRIGHT)   / n * 100
    base.posture_slouching_pct = sum(1 for f in frames if f.posture == PostureState.SLOUCHING)  / n * 100
    base.gaze_direct_pct       = sum(1 for f in frames if f.gaze   == GazeState.DIRECT)         / n * 100
    base.gaze_away_pct         = sum(1 for f in frames if f.gaze   == GazeState.LOOKING_AWAY)   / n * 100
    base.head_neutral_pct      = sum(1 for f in frames if f.head_pose == HeadPoseState.NEUTRAL)  / n * 100
    base.head_away_pct         = sum(1 for f in frames if f.head_pose == HeadPoseState.TURNED_AWAY) / n * 100

    expr_counts: Dict[str, int] = defaultdict(int)
    for f in frames:
        expr_counts[f.expression.value] += 1
    base.expression_breakdown = {k: round(v / n * 100, 1) for k, v in expr_counts.items()}
    dominant = max(expr_counts, key=expr_counts.get) if expr_counts else "unknown"
    base.dominant_expression  = ExpressionState(dominant)

    base.overall_vision_score = sum(f.frame_score for f in frames) / n

    lines = []
    if base.posture_slouching_pct > 40:
        lines.append(f"You were slouching {base.posture_slouching_pct:.0f}% of the time — work on your posture.")
    elif base.posture_upright_pct > 70:
        lines.append("Great posture maintained throughout your answer! ✅")

    if base.gaze_direct_pct > 60:
        lines.append("Good eye contact with the camera. ✅")
    elif base.gaze_away_pct > 40:
        lines.append(f"You looked away {base.gaze_away_pct:.0f}% of the time — maintain camera eye contact.")

    if base.head_away_pct > 25:
        lines.append("You turned away from the camera frequently.")

    expr_label = base.dominant_expression.value
    if expr_label == "nervous":
        lines.append("You appeared nervous — take a breath and project confidence.")
    elif expr_label == "happy":
        lines.append("Your expression was positive and engaging. ✅")
    elif expr_label == "confused":
        lines.append("Your expression appeared uncertain — practice delivering with more confidence.")

    base.feedback_lines = lines or ["Body language was acceptable for this answer."]

    score = base.overall_vision_score
    base.headline = (
        "Excellent body language! 🌟"                        if score >= 80 else
        "Good body language with minor areas to improve."    if score >= 60 else
        "Body language needs some work — see details below." if score >= 40 else
        "Body language requires significant improvement."
    )
    return base


# ──────────────────────────────────────────────
# Session-level report
# ──────────────────────────────────────────────
def get_session_vision_report(session_id: str) -> SessionVisionReport:
    state  = get_or_create_session(session_id)
    report = SessionVisionReport(session_id=session_id)

    all_frames = list(state.frame_buffer)
    report.total_frames_analyzed = len(all_frames)

    if not all_frames:
        report.summary = "No video data was captured during this session."
        return report

    for ans_idx in sorted(state.answer_frames.keys()):
        report.answer_summaries.append(get_answer_vision_summary(session_id, ans_idx))

    if report.answer_summaries:
        report.avg_posture_score    = sum(s.posture_upright_pct    for s in report.answer_summaries) / len(report.answer_summaries)
        report.avg_gaze_score       = sum(s.gaze_direct_pct        for s in report.answer_summaries) / len(report.answer_summaries)
        report.overall_vision_score = sum(s.overall_vision_score   for s in report.answer_summaries) / len(report.answer_summaries)

    strengths, improvements = [], []
    if report.avg_posture_score >= 70:
        strengths.append("Consistently maintained upright posture")
    else:
        improvements.append("Work on maintaining upright posture throughout interviews")

    if report.avg_gaze_score >= 65:
        strengths.append("Good camera eye contact throughout session")
    else:
        improvements.append("Practice maintaining eye contact with the camera")

    dominant_exprs = [s.dominant_expression.value for s in report.answer_summaries]
    if dominant_exprs.count("happy")   >= len(dominant_exprs) // 2:
        strengths.append("Positive and engaging facial expressions")
    if dominant_exprs.count("nervous") > 1:
        improvements.append("Manage nervous expressions — practice mock interviews to build confidence")

    report.strengths    = strengths
    report.improvements = improvements

    score = report.overall_vision_score
    report.summary = (
        "Excellent overall body language and presence throughout the interview."  if score >= 80 else
        "Good body language overall with a few areas to refine."                  if score >= 60 else
        "Body language was inconsistent — review the per-answer feedback below."  if score >= 40 else
        "Body language needs significant work. Focus on posture, gaze, and expressions."
    )
    return report