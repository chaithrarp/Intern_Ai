"""
vision_websocket.py
FastAPI WebSocket endpoint for real-time vision analysis.

Flow:
  1. Frontend connects: ws://localhost:8000/ws/vision/{session_id}
  2. Frontend sends JSON messages: { session_id, answer_index, frame_b64, timestamp }
  3. Backend responds with: { frame_analysis, face_landmarks_2d, pose_landmarks_2d }
  4. On special message { "action": "get_answer_summary", "answer_index": N }
     backend responds with AnswerVisionSummary JSON
  5. On special message { "action": "get_session_report" }
     backend responds with SessionVisionReport JSON
  6. Frontend disconnects when session ends
"""

import json
import time
import logging
from fastapi import WebSocket, WebSocketDisconnect

from vision_analyzer import (
    analyze_frame,
    get_answer_vision_summary,
    get_session_vision_report,
    remove_session,
)
from models.vision_models import VisionWebSocketResponse

logger = logging.getLogger(__name__)


async def vision_websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket handler. Mount this in main.py like:
        app.add_api_websocket_route("/ws/vision/{session_id}", vision_websocket_endpoint)
    """
    await websocket.accept()
    logger.info(f"[Vision WS] Session {session_id} connected")

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"error": "Invalid JSON"}))
                continue

            action = msg.get("action")

            # ── Special actions ──
            if action == "get_answer_summary":
                answer_index = int(msg.get("answer_index", 0))
                summary = get_answer_vision_summary(session_id, answer_index)
                await websocket.send_text(summary.model_dump_json())
                continue

            if action == "get_session_report":
                report = get_session_vision_report(session_id)
                await websocket.send_text(report.model_dump_json())
                continue

            if action == "cleanup":
                remove_session(session_id)
                await websocket.send_text(json.dumps({"status": "cleaned_up"}))
                continue

            # ── Frame analysis (default action) ──
            frame_b64    = msg.get("frame_b64", "")
            answer_index = int(msg.get("answer_index", 0))
            timestamp    = float(msg.get("timestamp", time.time()))

            if not frame_b64:
                await websocket.send_text(json.dumps({"error": "Missing frame_b64"}))
                continue

            fa, face_lm, pose_lm = analyze_frame(
                frame_b64=frame_b64,
                session_id=session_id,
                answer_index=answer_index,
                timestamp=timestamp,
            )

            response = VisionWebSocketResponse(
                frame_analysis=fa,
                face_landmarks_2d=face_lm,
                pose_landmarks_2d=pose_lm,
            )
            await websocket.send_text(response.model_dump_json())

    except WebSocketDisconnect:
        logger.info(f"[Vision WS] Session {session_id} disconnected")
    except Exception as e:
        logger.error(f"[Vision WS] Error in session {session_id}: {e}", exc_info=True)
        try:
            await websocket.send_text(json.dumps({"error": str(e)}))
        except Exception:
            pass