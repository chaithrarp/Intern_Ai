from fastapi import FastAPI, UploadFile, File, Form, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
import uuid
import os
from typing import Optional
import asyncio

# ============================================
# NEW IMPORTS - Integrated System
# ============================================
from engines.interview_orchestrator import get_interview_orchestrator
from engines.immediate_feedback import get_immediate_feedback_generator
from engines.final_report import get_final_report_generator
from engines.interruption_analyzer import get_enhanced_interruption_analyzer
from engines.followup_generator import get_followup_generator
from engines.live_warning_generator import get_warning_generator
from models.state_models import SessionState, RoundType, InterviewPhase
from models.evaluation_models import AnswerEvaluation

# ============================================
# VISION IMPORTS
# ============================================
from vision_websocket import vision_websocket_endpoint
from vision_database import (
    init_vision_database,
    save_answer_vision_summary,
    save_session_vision_report,
)
from vision_analyzer import get_answer_vision_summary, get_session_vision_report
from models.vision_models import SessionVisionReport

# ============================================
# LEGACY IMPORTS (keeping for resume/audio/auth)
# ============================================
from auth_endpoints import auth_router
from auth_database import init_auth_database
from database import (
    init_database,
    create_session as db_create_session,
    save_answer as db_save_answer,
    save_audio_file as db_save_audio_file
)
from resume_parser import ResumeParser
from resume_question_generator import ResumeQuestionGenerator
from whisper_service import transcribe_audio
from metrics_analyzer import analyze_complete_metrics
from metrics_storage import save_metrics, save_interruption
import config

# ============================================
# APP INITIALIZATION
# ============================================
app = FastAPI(title="InternAI - Intelligent Interview System")
resume_parser = ResumeParser()
resume_question_gen = ResumeQuestionGenerator()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

# ============================================
# VISION WEBSOCKET ROUTE
# ============================================
app.add_api_websocket_route("/ws/vision/{session_id}", vision_websocket_endpoint)

# ============================================
# VISION REST ROUTER
# ============================================
vision_router = APIRouter(prefix="/vision", tags=["vision"])

@vision_router.get("/report/{session_id}")
async def get_vision_report_endpoint(session_id: str):
    """
    Returns aggregated vision report for a completed session.
    Called by the FinalReport screen after interview ends.
    """
    try:
        report = get_session_vision_report(session_id)
        save_session_vision_report(report)
        return {"success": True, "report": report.dict()}
    except Exception as e:
        print(f"❌ Error fetching vision report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@vision_router.get("/answer-summary/{session_id}/{answer_index}")
async def get_answer_vision_endpoint(session_id: str, answer_index: int):
    """
    Returns per-answer vision summary.
    Called by FeedbackScreen after each answer is submitted.
    """
    try:
        summary = get_answer_vision_summary(session_id, answer_index)
        save_answer_vision_summary(summary)
        return {"success": True, "summary": summary.dict()}
    except Exception as e:
        print(f"❌ Error fetching answer vision summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


app.include_router(vision_router)

# ============================================
# STARTUP
# ============================================
@app.on_event("startup")
async def startup_event():
    init_database()
    init_auth_database()
    init_vision_database()                   # ← Vision DB tables
    get_interview_orchestrator()
    get_immediate_feedback_generator()
    get_final_report_generator()
    print("✅ Database initialized")
    print("✅ Authentication database initialized")
    print("✅ Vision database initialized")
    print("✅ Interview system initialized")

# ============================================
# REQUEST MODELS
# ============================================
class StartInterviewRequest(BaseModel):
    round_type: str = "hr"
    resume_context: Optional[str] = None

class PersonaInterviewRequest(BaseModel):
    persona: str = "standard_professional"
    resume_context: Optional[str] = None

class AnswerSubmitRequest(BaseModel):
    session_id: str
    question_id: int
    answer_text: str
    recording_duration: float = 0
    was_interrupted: bool = False
    is_followup_answer: bool = False

class InterruptionCheckRequest(BaseModel):
    session_id: str
    question_id: int = 0
    recording_duration: float
    partial_transcript: str = ""
    current_question_text: str = ""
    audio_metrics: Optional[dict] = None

# ============================================
# HEALTH CHECK
# ============================================
@app.get("/")
def read_root():
    return {
        "message": "InternAI Intelligent Interview System",
        "version": "2.0",
        "features": [
            "Round-based evaluation",
            "Intelligent interruptions",
            "Phase progression",
            "Smart follow-ups",
            "Real-time vision analysis",       # ← NEW
        ]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "InternAI API v2.0"}

# ============================================
# RESUME UPLOAD
# ============================================
@app.post("/upload-resume")
async def upload_resume(
    resume: UploadFile = File(...),
    session_id: str = Form(None)
):
    try:
        allowed_types = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword',
            'text/plain'
        ]

        if resume.content_type not in allowed_types:
            return JSONResponse(status_code=400, content={"success": False, "error": "Invalid file type"})

        contents = await resume.read()
        if len(contents) > 5 * 1024 * 1024:
            return JSONResponse(status_code=400, content={"success": False, "error": "File too large (max 5MB)"})

        if not session_id:
            session_id = f"resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"

        os.makedirs("resume_uploads", exist_ok=True)
        file_extension = resume.filename.split('.')[-1]
        filename = f"{session_id}.{file_extension}"
        file_path = os.path.join("resume_uploads", filename)

        with open(file_path, 'wb') as f:
            f.write(contents)

        print(f"📄 Resume uploaded: {filename}")

        parsed_data = resume_parser.parse_resume(file_path)

        if not parsed_data["success"]:
            return JSONResponse(status_code=400, content={"success": False, "error": "Failed to parse resume"})

        resume_context = resume_question_gen.create_resume_context(parsed_data["raw_text"])

        print("✅ Resume parsed successfully")

        return {
            "success": True,
            "session_id": session_id,
            "resume_context": resume_context,
            "resume_summary": parsed_data["summary"],
            "filename": resume.filename
        }

    except Exception as e:
        print(f"❌ Error uploading resume: {str(e)}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

# ============================================
# START INTERVIEW (direct round_type)
# ============================================
@app.post("/interview/start")
async def start_interview(request: StartInterviewRequest):
    try:
        orchestrator = get_interview_orchestrator()
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"

        result = orchestrator.start_interview(
            session_id=session_id,
            round_type=request.round_type,
            resume_context=request.resume_context
        )

        db_create_session(session_id, ai_powered=True, pressure_enabled=True)

        print(f"✅ Started interview: {session_id} | Round: {request.round_type}")

        return {"success": True, **result}

    except Exception as e:
        print(f"❌ Error starting interview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# START INTERVIEW WITH PERSONA
# ============================================
@app.post("/interview/start-with-persona")
async def start_interview_with_persona(request: PersonaInterviewRequest):
    try:
        orchestrator = get_interview_orchestrator()
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"

        persona_to_round = {
            "hr_manager": "hr",
            "senior_engineer": "technical",
            "architect": "system_design",
            "startup_founder": "hr",
            "standard_professional": "hr",
        }
        round_type = persona_to_round.get(request.persona, request.persona)

        result = orchestrator.start_interview(
            session_id=session_id,
            round_type=round_type,
            resume_context=request.resume_context
        )

        db_create_session(session_id, ai_powered=True, pressure_enabled=True)

        print(f"✅ Started interview with persona: {request.persona} | Session: {session_id}")

        return {
            "success": True,
            **result,
            "persona": {
                "id": request.persona,
                "name": request.persona.replace("_", " ").title(),
                "emoji": "🤖"
            }
        }

    except Exception as e:
        print(f"❌ Error starting interview with persona: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# SUBMIT ANSWER
# ============================================
@app.post("/interview/answer")
async def submit_answer(request: AnswerSubmitRequest):
    try:
        orchestrator = get_interview_orchestrator()
        feedback_gen = get_immediate_feedback_generator()

        session = orchestrator.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        question_text = session.current_question_text or "Question"

        # Current answer index = number of completed Q&A pairs so far
        answer_index = len(session.conversation_history)

        print(f"\n📝 Processing answer for session: {request.session_id}")
        print(f"   Question ID: {request.question_id}")
        print(f"   Answer index: {answer_index}")
        print(f"   Round: {session.current_round_type.value}")
        print(f"   Is Follow-up: {request.is_followup_answer}")

        skip_claims = request.question_id <= 3

        result = orchestrator.process_answer(
            state=session,
            question_id=request.question_id,
            question_text=question_text,
            answer_text=request.answer_text,
            round_type=session.current_round_type.value,
            skip_claim_extraction=skip_claims,
            is_followup_answer=request.is_followup_answer
        )

        db_save_answer(
            session_id=request.session_id,
            question_id=request.question_id,
            question_text=question_text,
            answer_text=request.answer_text,
            recording_duration=request.recording_duration,
            was_interrupted=request.was_interrupted
        )

        # ── Q0 intro: no evaluation, just move to Q1 ──
        if result.get("is_intro_response"):
            return {
                "success": True,
                "is_intro_response": True,
                "next_question": result.get("next_question"),
                "question_number": result.get("question_number", 1),
                "current_phase": result.get("current_phase"),
                "phase_info": result.get("phase_info"),
                "completed": False
            }

        evaluation = result.get("evaluation")

        if isinstance(evaluation, dict):
            evaluation_obj = AnswerEvaluation(**evaluation)
        else:
            evaluation_obj = evaluation

        immediate_feedback = feedback_gen.generate_feedback(
            evaluation=evaluation_obj,
            round_type=session.current_round_type.value
        ) if evaluation_obj else None

        # ── Vision: fetch & persist per-answer summary ──────────────────────
        vision_feedback = None
        try:
            vision_summary = get_answer_vision_summary(request.session_id, answer_index)
            save_answer_vision_summary(vision_summary)
            vision_feedback = vision_summary.dict()
            print(f"👁️  Vision summary for answer {answer_index}: score={vision_summary.overall_vision_score:.1f}")
        except Exception as ve:
            print(f"⚠️  Vision summary error (non-fatal): {ve}")
        # ────────────────────────────────────────────────────────────────────

        if result.get("completed"):
            session.current_phase = InterviewPhase.COMPLETED
            session.completed_at = datetime.now()

            # ── Vision: persist full session report on completion ────────────
            try:
                session_vision_report = get_session_vision_report(request.session_id)
                save_session_vision_report(session_vision_report)
                print(f"👁️  Session vision report saved: overall={session_vision_report.overall_vision_score:.1f}")
            except Exception as ve:
                print(f"⚠️  Session vision report error (non-fatal): {ve}")
            # ────────────────────────────────────────────────────────────────

            print("🎉 Interview completed!")

            return {
                "success": True,
                "completed": True,
                "session_id": request.session_id,
                "evaluation": evaluation if isinstance(evaluation, dict) else evaluation.dict(),
                "immediate_feedback": immediate_feedback,
                "vision_feedback": vision_feedback,        # ← NEW
            }

        if result.get("requires_followup"):
            print(f"🔍 Follow-up required: {result.get('followup_reason')}")
            return {
                "success": True,
                "completed": False,
                "requires_followup": True,
                "followup_question": result["followup_question"],
                "followup_reason": result.get("followup_reason"),
                "evaluation": evaluation if isinstance(evaluation, dict) else evaluation.dict(),
                "immediate_feedback": immediate_feedback,
                "vision_feedback": vision_feedback,        # ← NEW
                "session_id": request.session_id
            }

        print(f"✅ Answer processed | Score: {evaluation_obj.overall_score}/100")

        return {
            "success": True,
            "completed": False,
            "question": result.get("next_question"),
            "question_number": result.get("question_number"),
            "total_questions": 6,
            "evaluation": evaluation if isinstance(evaluation, dict) else evaluation.dict(),
            "immediate_feedback": immediate_feedback,
            "vision_feedback": vision_feedback,            # ← NEW
            "current_phase": result.get("current_phase"),
            "phase_info": result.get("phase_info"),
            "session_id": request.session_id
        }

    except Exception as e:
        print(f"❌ Error processing answer: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# CHECK INTERRUPTION
# ============================================
@app.post("/interview/check-interruption")
async def check_interruption(request: InterruptionCheckRequest):
    try:
        orchestrator = get_interview_orchestrator()
        analyzer = get_enhanced_interruption_analyzer()
        followup_gen = get_followup_generator()

        session = orchestrator.get_session(request.session_id)
        if not session:
            return {"should_interrupt": False, "reason": "session_not_found"}

        MAX_INTERRUPTIONS = getattr(config, 'MAX_INTERRUPTIONS_PER_SESSION', 2)

        if session.total_interruptions >= MAX_INTERRUPTIONS:
            return {
                "should_interrupt": False,
                "should_warn": False,
                "reason": "max_interruptions_reached",
            }

        transcript = (request.partial_transcript or "").strip()
        min_chars = getattr(config, 'MIN_TRANSCRIPT_LENGTH_FOR_ANALYSIS', 80)
        if len(transcript) < min_chars and not (request.audio_metrics or {}).get('detected_issues'):
            return {"should_interrupt": False, "should_warn": False}

        question_text = request.current_question_text or session.current_question_text or ""

        analysis = analyzer.analyze_for_interruption(
            session_id=request.session_id,
            partial_transcript=transcript,
            audio_metrics=request.audio_metrics or {},
            question_text=question_text,
            conversation_history=session.conversation_history,
            recording_duration=request.recording_duration,
            question_id=request.question_id,
            current_interruption_count=session.total_interruptions,
        )

        if not analysis:
            return {"should_interrupt": False, "should_warn": False}

        action = analysis.get("action", "none")
        reason = analysis.get("reason", "")
        display_reason = analysis.get("display_reason", analyzer.get_display_reason(reason))

        # ── INTERRUPT path ────────────────────────────────────────────────────
        if action == "interrupt":
            phrase = analysis.get("interruption_phrase") or analyzer.generate_interruption_phrase(reason)

            followup = followup_gen.generate_followup(
                interruption_reason=reason,
                partial_answer=transcript,
                original_question=question_text,
                conversation_history=session.conversation_history,
                evidence=analysis.get("evidence", ""),
            )

            session.total_interruptions += 1
            session.interruptions.append({
                "timestamp": datetime.now().isoformat(),
                "reason": reason,
                "display_reason": display_reason,
                "partial_answer": transcript[:300],
                "triggered_at": request.recording_duration,
            })

            save_interruption(
                session_id=request.session_id,
                answer_id=None,
                triggered_at_seconds=request.recording_duration,
                interruption_reason=reason,
                interruption_phrase=phrase,
                followup_question=followup,
                partial_answer=transcript,
                recovery_time=None,
            )

            print(f"🔥 INTERRUPTION fired | reason={reason} | display='{display_reason}' | "
                  f"total={session.total_interruptions}/{MAX_INTERRUPTIONS}")

            return {
                "should_interrupt": True,
                "interruption_phrase": phrase,
                "followup_question": followup,
                "reason": reason,
                "display_reason": display_reason,
                "icon": analysis.get("icon", "⚠️"),
                "interruption_count": session.total_interruptions,
                "max_interruptions": MAX_INTERRUPTIONS,
            }

        # ── WARN path ─────────────────────────────────────────────────────────
        elif action == "warn":
            warn_phrase = analysis.get("warn_phrase") or analyzer.generate_warn_phrase(reason)

            severity_map = {
                "COMPLETELY_OFF_TOPIC":  "high",
                "DODGING_QUESTION":      "high",
                "FILLER_HEAVY":          "medium",
                "EXCESSIVE_RAMBLING":    "medium",
                "STRUGGLING":            "high",
                "CONTRADICTION":         "high",
                "VAGUE_EVASION":         "medium",
                "MANIPULATION_ATTEMPT":  "high",
                "FALSE_CLAIM":           "critical",
                "LONG_PAUSE":            "low",
                "SPEAKING_TOO_LONG":     "low",
                "MINOR_UNCERTAINTY":     "low",
            }
            severity = severity_map.get(reason, "medium")
            icon = analysis.get("icon", "⚠️")

            print(f"⚠️  WARNING | reason={reason} | message: {warn_phrase}")

            return {
                "should_interrupt": False,
                "should_warn": True,
                "warning": {
                    "message": warn_phrase,
                    "reason": reason,
                    "display_reason": display_reason,
                    "severity": severity,
                    "icon": icon,
                    "show_duration": 4,
                },
            }

        return {"should_interrupt": False, "should_warn": False}

    except Exception as e:
        print(f"❌ Error in check-interruption: {e}")
        import traceback
        traceback.print_exc()
        return {"should_interrupt": False, "error": str(e)}

# ============================================
# FINAL REPORT
# ============================================
@app.get("/interview/final-report/{session_id}")
async def get_final_report(session_id: str):
    try:
        orchestrator = get_interview_orchestrator()
        report_gen = get_final_report_generator()

        session = orchestrator.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session.current_phase != InterviewPhase.COMPLETED:
            session.current_phase = InterviewPhase.COMPLETED
            session.completed_at = datetime.now()

        report = report_gen.generate_report(session)

        # ── Attach vision report to final report ──────────────────────────────
        vision_report_data = None
        try:
            vision_report = get_session_vision_report(session_id)
            save_session_vision_report(vision_report)
            vision_report_data = vision_report.dict()
            print(f"👁️  Vision report attached to final report | score={vision_report.overall_vision_score:.1f}")
        except Exception as ve:
            print(f"⚠️  Vision report fetch error (non-fatal): {ve}")
        # ────────────────────────────────────────────────────────────────────

        print(f"📋 Generated final report for session: {session_id}")

        report_dict = report.dict()
        report_dict["vision_report"] = vision_report_data   # ← NEW field

        return {"success": True, "report": report_dict}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error generating report: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# SESSION HISTORY
# ============================================
@app.get("/interview/sessions/history")
async def get_sessions_history():
    try:
        orchestrator = get_interview_orchestrator()
        history = []

        for session_id, state in orchestrator.sessions.items():
            if not state.conversation_history:
                continue

            overall_avg = 0
            if state.overall_score_progression:
                overall_avg = int(sum(state.overall_score_progression) / len(state.overall_score_progression))

            history.append({
                "session_id": session_id,
                "round_type": state.current_round_type.value,
                "overall_score": overall_avg,
                "dimension_scores": {k: int(v) for k, v in (state.average_scores or {}).items()},
                "total_questions": len(state.conversation_history),
                "total_interruptions": state.total_interruptions,
                "duration_seconds": (
                    (state.completed_at - state.started_at).total_seconds()
                    if state.completed_at else
                    (datetime.now() - state.started_at).total_seconds()
                ),
                "started_at": state.started_at.isoformat() if state.started_at else None,
                "completed_at": state.completed_at.isoformat() if state.completed_at else None,
                "current_phase": state.current_phase.value,
            })

        history.sort(key=lambda x: x["completed_at"] or x["started_at"] or "", reverse=True)

        return {"success": True, "history": history, "total": len(history)}

    except Exception as e:
        print(f"❌ Error fetching session history: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# METRICS HISTORY (for SessionHistory.js dashboard)
# ============================================
@app.get("/metrics/history")
async def get_metrics_history(limit: int = 20):
    try:
        orchestrator = get_interview_orchestrator()
        history = []

        for session_id, state in orchestrator.sessions.items():
            if not state.conversation_history:
                continue

            interruption_count = state.total_interruptions
            avg_score = (
                sum(state.overall_score_progression) / len(state.overall_score_progression)
                if state.overall_score_progression else 0
            )

            avg_hesitation_score = max(0, round(100 - avg_score + (interruption_count * 5), 1))

            total_words = 0
            total_filler_words = 0

            for qa in state.conversation_history:
                answer = qa.get("answer", "")
                total_words += len(answer.split())
                answer_lower = answer.lower()
                for filler in ["um", "uh", "like", "you know", "basically", "literally", "actually"]:
                    total_filler_words += answer_lower.count(f" {filler} ")

            duration_seconds = (
                (state.completed_at - state.started_at).total_seconds()
                if state.completed_at and state.started_at
                else (datetime.now() - state.started_at).total_seconds()
                if state.started_at else 0
            )
            avg_wpm = round((total_words / (duration_seconds / 60)), 1) if duration_seconds > 0 else 0

            history.append({
                "session_id": session_id,
                "started_at": state.started_at.isoformat() if state.started_at else None,
                "completed_at": state.completed_at.isoformat() if state.completed_at else None,
                "total_questions": len(state.conversation_history),
                "avg_hesitation_score": avg_hesitation_score,
                "avg_words_per_minute": avg_wpm,
                "total_filler_words": total_filler_words,
                "interruption_count": interruption_count,
                "round_type": state.current_round_type.value,
                "overall_score": int(avg_score),
            })

        history.sort(
            key=lambda x: x["completed_at"] or x["started_at"] or "",
            reverse=True
        )
        history = history[:limit]

        return {"success": True, "history": history, "total": len(history)}

    except Exception as e:
        print(f"❌ Error fetching metrics history: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# METRICS SUMMARY (per session)
# ============================================
@app.get("/metrics/summary/{session_id}")
async def get_metrics_summary(session_id: str):
    try:
        orchestrator = get_interview_orchestrator()

        session = orchestrator.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        avg_scores = session.average_scores or {
            'technical_depth': 0,
            'concept_accuracy': 0,
            'structured_thinking': 0,
            'communication_clarity': 0,
            'confidence_consistency': 0
        }

        overall_avg = sum(avg_scores.values()) / len(avg_scores) if avg_scores else 0

        score_progression = [
            {"question": i + 1, "score": score}
            for i, score in enumerate(session.overall_score_progression)
        ]

        interruption_reasons = {}
        for interruption in session.interruptions:
            reason = interruption.get('reason', 'unknown')
            interruption_reasons[reason] = interruption_reasons.get(reason, 0) + 1

        # ── Attach vision summary ─────────────────────────────────────────────
        vision_summary_data = None
        try:
            vision_report = get_session_vision_report(session_id)
            vision_summary_data = {
                "overall_vision_score": vision_report.overall_vision_score,
                "avg_posture_score":    vision_report.avg_posture_score,
                "avg_gaze_score":       vision_report.avg_gaze_score,
                "strengths":            vision_report.strengths,
                "improvements":         vision_report.improvements,
                "summary":              vision_report.summary,
            }
        except Exception as ve:
            print(f"⚠️  Vision data for metrics summary (non-fatal): {ve}")
        # ────────────────────────────────────────────────────────────────────

        print(f"📊 Generated metrics summary for session: {session_id}")

        return {
            "success": True,
            "session_id": session_id,
            "round_type": session.current_round_type.value,
            "overall_score": int(overall_avg),
            "dimension_scores": avg_scores,
            "score_progression": score_progression,
            "total_questions": len(session.conversation_history),
            "total_interruptions": session.total_interruptions,
            "interruption_breakdown": interruption_reasons,
            "phases_completed": [p.value for p in session.phases_completed],
            "current_phase": session.current_phase.value,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "duration_seconds": (
                (session.completed_at - session.started_at).total_seconds()
                if session.completed_at else
                (datetime.now() - session.started_at).total_seconds()
            ),
            "claims": {
                "total_extracted": len(session.extracted_claims),
                "verified": len(session.verified_claims),
                "unverified": session.unverified_claims[:5]
            },
            "red_flags": session.red_flag_answers[:5] if hasattr(session, 'red_flag_answers') else [],
            "vision": vision_summary_data,              # ← NEW field
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error generating metrics summary: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# AUDIO UPLOAD
# ============================================
@app.post("/interview/upload-audio")
async def upload_audio(
    session_id: str,
    question_id: int,
    audio_file: UploadFile = File(...)
):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = audio_file.filename.split('.')[-1]
        filename = f"{session_id}_q{question_id}_{timestamp}.{file_extension}"

        os.makedirs("audio_uploads", exist_ok=True)
        file_path = os.path.join("audio_uploads", filename)

        contents = await audio_file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        print(f"🎤 Audio file saved: {filename}")

        transcription_result = transcribe_audio(file_path)

        if not transcription_result:
            return {"success": False, "error": "Transcription failed"}

        transcript_text = transcription_result["text"]
        language = transcription_result["language"]
        segments = transcription_result.get("segments", [])

        print(f"✅ Transcription complete: {transcript_text[:100]}...")

        recording_duration = segments[-1]["end"] if segments else 0

        metrics = analyze_complete_metrics(
            transcript_text=transcript_text,
            segments=segments,
            recording_duration=recording_duration,
            was_interrupted=False,
            interruption_time=None
        )

        db_save_audio_file(
            session_id=session_id,
            question_id=question_id,
            filename=filename,
            file_path=file_path,
            file_size=len(contents),
            language=language
        )

        return {
            "success": True,
            "transcript": transcript_text,
            "language": language,
            "metrics": metrics,
            "filename": filename
        }

    except Exception as e:
        print(f"❌ Error processing audio: {str(e)}")
        return {"success": False, "error": str(e)}

# ============================================
# TRANSCRIBE CHUNK
# ============================================
from whisper_service import transcribe_chunk as whisper_transcribe_chunk

@app.post("/interview/transcribe-chunk")
async def transcribe_chunk_endpoint(
    session_id: str,
    question_id: int,
    chunk_index: int,
    audio_chunk: UploadFile = File(...)
):
    """
    Transcribe a short audio chunk in near real-time.
    Called every 6s during recording by AudioRecorder.js.
    Uses tiny Whisper model (fast) instead of base (slow).
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{session_id}_q{question_id}_chunk{chunk_index}_{timestamp}.webm"

        os.makedirs("audio_uploads/chunks", exist_ok=True)
        file_path = os.path.join("audio_uploads/chunks", filename)

        contents = await audio_chunk.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        result = whisper_transcribe_chunk(file_path)

        try:
            os.remove(file_path)
        except Exception:
            pass

        if not result or not result.get("text"):
            return {"success": True, "text": "", "elapsed": 0}

        return {
            "success": True,
            "text": result["text"],
            "elapsed": result.get("elapsed", 0),
            "chunk_index": chunk_index
        }

    except Exception as e:
        print(f"❌ Chunk transcription error: {e}")
        return {"success": False, "text": "", "error": str(e)}

# ============================================
# TEST ENDPOINTS
# ============================================
@app.get("/test/llm")
def test_llm():
    try:
        from llm_service import test_llm_connection
        success, message = test_llm_connection()
        return {"success": success, "message": message}
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.get("/test/vision")
def test_vision():
    """Quick check that vision analyzer imports and MediaPipe loads correctly."""
    try:
        from vision_analyzer import _mp_face_mesh, _mp_pose
        return {
            "success": True,
            "message": "Vision system (MediaPipe + DeepFace) loaded successfully",
            "mediapipe_face_mesh": "ok",
            "mediapipe_pose": "ok",
        }
    except Exception as e:
        return {"success": False, "message": str(e)}