from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
import uuid
import os
from typing import Optional
import asyncio  # ← NEW: For parallel processing

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

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router
app.include_router(auth_router)

# ============================================
# STARTUP
# ============================================
@app.on_event("startup")
async def startup_event():
    """Initialize everything on startup"""
    init_database()
    init_auth_database()
    
    # Initialize singletons
    orchestrator = get_interview_orchestrator()
    feedback_gen = get_immediate_feedback_generator()
    report_gen = get_final_report_generator()
    
    print("✅ Database initialized")
    print("✅ Authentication database initialized")
    print("✅ Interview system initialized")

# ============================================
# REQUEST MODELS
# ============================================
class StartInterviewRequest(BaseModel):
    round_type: str = "hr"
    resume_context: Optional[str] = None

class AnswerSubmitRequest(BaseModel):
    session_id: str
    question_id: int
    answer_text: str
    recording_duration: float = 0
    was_interrupted: bool = False
    is_followup_answer: bool = False  # ← NEW: Track if this is answering a follow-up

class InterruptionCheckRequest(BaseModel):
    session_id: str
    recording_duration: float
    partial_transcript: str = ""
    audio_metrics: Optional[dict] = None

# ============================================
# HEALTH CHECK
# ============================================
@app.get("/")
def read_root():
    return {
        "message": "InternAI Intelligent Interview System",
        "version": "2.0 OPTIMIZED",
        "features": ["Round-based evaluation", "Intelligent interruptions", "Phase progression", "Smart follow-ups"]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "InternAI API v2.0 OPTIMIZED"}

# ============================================
# RESUME UPLOAD (UNCHANGED)
# ============================================
@app.post("/upload-resume")
async def upload_resume(
    resume: UploadFile = File(...),
    session_id: str = Form(None)
):
    """Upload and parse resume"""
    try:
        # Validate file type
        allowed_types = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword',
            'text/plain'
        ]
        
        if resume.content_type not in allowed_types:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Invalid file type"}
            )
        
        # Read file
        contents = await resume.read()
        if len(contents) > 5 * 1024 * 1024:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "File too large (max 5MB)"}
            )
        
        # Generate session ID if needed
        if not session_id:
            session_id = f"resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
        
        # Save file
        os.makedirs("resume_uploads", exist_ok=True)
        file_extension = resume.filename.split('.')[-1]
        filename = f"{session_id}.{file_extension}"
        file_path = os.path.join("resume_uploads", filename)
        
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        print(f"📄 Resume uploaded: {filename}")
        
        # Parse resume
        parsed_data = resume_parser.parse_resume(file_path)
        
        if not parsed_data["success"]:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Failed to parse resume"}
            )
        
        # Generate context
        resume_context = resume_question_gen.create_resume_context(parsed_data["raw_text"])
        
        print(f"✅ Resume parsed successfully")
        
        return {
            "success": True,
            "session_id": session_id,
            "resume_context": resume_context,
            "resume_summary": parsed_data["summary"],
            "filename": resume.filename
        }
        
    except Exception as e:
        print(f"❌ Error uploading resume: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# ============================================
# START INTERVIEW
# ============================================
@app.post("/interview/start")
async def start_interview(request: StartInterviewRequest):
    """
    Start new interview with round-based system
    
    Returns first question and session info
    """
    try:
        orchestrator = get_interview_orchestrator()
        
        # Generate session ID
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
        
        # Start interview
        result = orchestrator.start_interview(
            session_id=session_id,
            round_type=request.round_type,
            resume_context=request.resume_context
        )
        
        # Save to database
        db_create_session(session_id, ai_powered=True, pressure_enabled=True)
        
        print(f"✅ Started interview: {session_id}")
        print(f"   Round: {request.round_type}")
        print(f"   Phase: {result['current_phase']}")
        print(f"   Introduction: {result.get('introduction', 'N/A')[:60]}...")
        
        return {
            "success": True,
            **result  # Includes 'introduction' field now
        }
        
    except Exception as e:
        print(f"❌ Error starting interview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# OPTIMIZED ANSWER SUBMISSION
# ============================================
@app.post("/interview/answer")
async def submit_answer(request: AnswerSubmitRequest):
    """
    ⚡ FIXED: Submit answer and get evaluation + next question
    
    FIXES:
    1. Removed duplicate follow-up generation logic
    2. Trust orchestrator's follow-up decisions
    3. Properly track is_followup_answer flag
    """
    try:
        orchestrator = get_interview_orchestrator()
        feedback_gen = get_immediate_feedback_generator()
        
        # Get session
        session = orchestrator.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get current question text
        question_text = session.current_question_text or "Question"
        
        print(f"\n📝 Processing answer for session: {request.session_id}")
        print(f"   Question ID: {request.question_id}")
        print(f"   Round: {session.current_round_type.value}")
        print(f"   Is Follow-up Answer: {request.is_followup_answer}")
        
        # Skip claim extraction for early questions (optimization)
        skip_claims = request.question_id <= 3
        if skip_claims:
            print(f"   🚀 FAST MODE: Skipping claim extraction (Q{request.question_id})")
        
        # ========================================
        # CRITICAL: Process through orchestrator
        # The orchestrator handles ALL follow-up logic
        # ========================================
        result = orchestrator.process_answer(
            state=session,
            question_id=request.question_id,
            question_text=question_text,
            answer_text=request.answer_text,
            round_type=session.current_round_type.value,
            skip_claim_extraction=skip_claims,
            is_followup_answer=request.is_followup_answer
        )
        
        # Save to database (async)
        answer_id = db_save_answer(
            session_id=request.session_id,
            question_id=request.question_id,
            question_text=question_text,
            answer_text=request.answer_text,
            recording_duration=request.recording_duration,
            was_interrupted=request.was_interrupted
        )
        
        # Get evaluation
        evaluation = result.get("evaluation")
        
        # Convert dict to AnswerEvaluation if needed
        if isinstance(evaluation, dict):
            from models.evaluation_models import AnswerEvaluation
            evaluation_obj = AnswerEvaluation(**evaluation)
        else:
            evaluation_obj = evaluation
        
        # Generate immediate feedback
        immediate_feedback = feedback_gen.generate_feedback(
            evaluation=evaluation_obj,
            round_type=session.current_round_type.value
        )
        
        if result.get("completed"):
            session.current_phase = InterviewPhase.COMPLETED
            session.completed_at = datetime.now()
            
            print(f"🎉 Interview completed!")
            
            return {
                "success": True,
                "completed": True,
                "session_id": request.session_id,
                "evaluation": evaluation if isinstance(evaluation, dict) else evaluation.dict(),
                "immediate_feedback": immediate_feedback
            }
        
        # Handle follow-ups (if orchestrator decided to trigger one)
        if result.get("requires_followup"):
            print(f"\n🔍 Follow-up required: {result.get('followup_reason')}")
            
            return {
                "success": True,
                "completed": False,
                "requires_followup": True,
                "followup_question": result["followup_question"],
                "followup_reason": result.get("followup_reason"),
                "evaluation": evaluation if isinstance(evaluation, dict) else evaluation.dict(),
                "immediate_feedback": immediate_feedback,
                "session_id": request.session_id
            }
        
        # Interview continues normally
        print(f"✅ Answer processed successfully")
        print(f"   Overall Score: {evaluation_obj.overall_score}/100")
        print(f"   Next Phase: {result['current_phase']}")
        
        return {
            "success": True,
            "completed": False,
            "question": result["next_question"],
            "question_number": len(session.conversation_history) + 1,
            "total_questions": 6,
            "evaluation": evaluation if isinstance(evaluation, dict) else evaluation.dict(),
            "immediate_feedback": immediate_feedback,
            "current_phase": result["current_phase"],
            "phase_info": result.get("phase_info"),
            "session_id": request.session_id
        }
        
    except Exception as e:
        print(f"❌ Error processing answer: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

def _generate_smart_followup(evaluation: AnswerEvaluation, question_text: str, answer_text: str) -> str:
    """
    Generate smart follow-up question based on evaluation
    
    Args:
        evaluation: Answer evaluation
        question_text: Original question
        answer_text: User's answer
        
    Returns:
        Follow-up question text
    """
    from llm_service import get_llm_response
    
    # Build prompt
    weaknesses_str = ", ".join(evaluation.weaknesses[:2]) if evaluation.weaknesses else "unclear response"
    
    prompt = [
        {
            "role": "system",
            "content": f"""You are an interviewer asking a brief follow-up question.

ORIGINAL QUESTION: {question_text}

CANDIDATE'S ANSWER: {answer_text[:200]}...

ISSUES DETECTED: {weaknesses_str}

Generate ONE short follow-up question (1 sentence) that:
1. Asks for specific details they missed
2. Clarifies vague points
3. Probes deeper into their answer

Keep it BRIEF and DIRECT. Output ONLY the question."""
        },
        {
            "role": "user",
            "content": "Generate the follow-up question."
        }
    ]
    
    response = get_llm_response(prompt, temperature=0.7)
    
    # Clean response
    question = response.strip().replace("**", "").replace("*", "")
    if question.startswith('"'):
        question = question[1:-1]
    
    return question


@app.post("/interview/check-interruption")
async def check_interruption(request: InterruptionCheckRequest):
    """
    Enhanced interruption check with multi-layer analysis
    """
    try:
        orchestrator = get_interview_orchestrator()
        analyzer = get_enhanced_interruption_analyzer()
        followup_gen = get_followup_generator()
        
        # Get session
        session = orchestrator.get_session(request.session_id)
        if not session:
            return {"should_interrupt": False, "reason": "session_not_found"}
        
        # Check max interruptions
        if session.total_interruptions >= session.max_interruptions:
            return {"should_interrupt": False, "reason": "max_interruptions_reached"}
        
        # If transcript is empty or very short, skip analysis
        if not request.partial_transcript or len(request.partial_transcript.strip()) < 10:
            if not request.audio_metrics or not request.audio_metrics.get('detected_issues'):
                return {"should_interrupt": False, "should_warn": False}
        
        print(f"\n🔍 Multi-layer interruption check...")
        
        # Multi-layer analysis
        analysis = analyzer.analyze_for_interruption(
            session_id=request.session_id,
            partial_transcript=request.partial_transcript or "",
            audio_metrics=request.audio_metrics or {},
            question_text=session.current_question_text or "",
            conversation_history=session.conversation_history,
            recording_duration=request.recording_duration
        )
        
        if not analysis:
            return {"should_interrupt": False, "should_warn": False}
        
        action = analysis.get("action", "none")
        should_interrupt = analysis.get("should_interrupt", False)
        reason = analysis.get("reason", "")
        
        # INTERRUPT
        if should_interrupt and action == "interrupt":
            phrase = analyzer.generate_interruption_phrase(reason)
            
            followup = followup_gen.generate_followup(
                interruption_reason=reason,
                partial_answer=request.partial_transcript or "",
                original_question=session.current_question_text or "",
                conversation_history=session.conversation_history,
                evidence=analysis.get("evidence", "")
            )
            
            session.total_interruptions += 1
            session.interruptions.append({
                "timestamp": datetime.now().isoformat(),
                "reason": reason,
                "partial_answer": request.partial_transcript or "",
                "triggered_at": request.recording_duration,
                "weight": analysis.get("weight"),
                "evidence": analysis.get("evidence"),
                "all_triggers": analysis.get("all_triggers", [])
            })
            
            save_interruption(
                session_id=request.session_id,
                reason=reason,
                triggered_at=request.recording_duration,
                partial_transcript=request.partial_transcript or ""
            )
            
            print(f"🔥 INTERRUPTION!")
            print(f"   Reason: {reason}")
            
            return {
                "should_interrupt": True,
                "interruption_phrase": phrase,
                "followup_question": followup,
                "reason": reason,
                "weight": analysis.get("weight"),
                "evidence": analysis.get("evidence"),
                "interruption_count": session.total_interruptions,
                "max_interruptions": session.max_interruptions,
                "all_triggers": analysis.get("all_triggers", [])
            }
        
        # WARN
        elif action == "warn":
            print(f"⚠️  Warning: {reason}")
            
            return {
                "should_interrupt": False,
                "should_warn": True,
                "warning": {
                    "message": f"{reason.replace('_', ' ').title()}",
                    "reason": reason,
                    "evidence": analysis.get("evidence", ""),
                    "occurrence": analysis.get("occurrence_count", 1),
                    "threshold": analysis.get("threshold", 2)
                },
                "reason": reason
            }
        
        return {"should_interrupt": False, "should_warn": False}
        
    except Exception as e:
        print(f"❌ Error in interruption check: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"should_interrupt": False, "error": str(e)}


@app.get("/interview/final-report/{session_id}")
async def get_final_report(session_id: str):
    """Generate comprehensive final report"""
    try:
        orchestrator = get_interview_orchestrator()
        report_gen = get_final_report_generator()
        
        session = orchestrator.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.current_phase != InterviewPhase.COMPLETED:
            session.current_phase = InterviewPhase.COMPLETED
            session.completed_at = datetime.now()
        
        from models.evaluation_models import SessionEvaluation
        
        session_eval = SessionEvaluation(
            session_id=session_id,
            average_scores=session.average_scores,
            score_progression=[
                {"question": i+1, "overall": score}
                for i, score in enumerate(session.overall_score_progression)
            ],
            round_performance={},
            phases_completed=[p.value for p in session.phases_completed],
            total_interruptions=session.total_interruptions,
            interruption_reasons={},
            total_claims_made=len(session.extracted_claims),
            claims_verified=len(session.verified_claims),
            unverified_claims=session.unverified_claims[:5],
            total_duration_seconds=(
                (session.completed_at - session.started_at).total_seconds()
                if session.completed_at else 0
            )
        )
        
        report = report_gen.generate_report(session, session_eval)
        
        print(f"📋 Generated final report for session: {session_id}")
        
        return {
            "success": True,
            "report": report.dict()
        }
        
    except Exception as e:
        print(f"❌ Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# AUDIO UPLOAD (UNCHANGED)
# ============================================
@app.post("/interview/upload-audio")
async def upload_audio(
    session_id: str,
    question_id: int,
    audio_file: UploadFile = File(...)
):
    """Upload audio file and transcribe"""
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
        
        print(f"🔄 Starting transcription...")
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

@app.get("/metrics/summary/{session_id}")
async def get_metrics_summary(session_id: str):
    """Get session metrics summary for feedback screen"""
    try:
        orchestrator = get_interview_orchestrator()
        
        session = orchestrator.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        avg_scores = session.average_scores if session.average_scores else {
            'technical_depth': 0,
            'concept_accuracy': 0,
            'structured_thinking': 0,
            'communication_clarity': 0,
            'confidence_consistency': 0
        }
        
        overall_avg = sum(avg_scores.values()) / len(avg_scores) if avg_scores else 0
        
        score_progression = [
            {"question": i+1, "score": score}
            for i, score in enumerate(session.overall_score_progression)
        ]
        
        interruption_reasons = {}
        for interruption in session.interruptions:
            reason = interruption.get('reason', 'unknown')
            interruption_reasons[reason] = interruption_reasons.get(reason, 0) + 1
        
        phase_performance = {}
        for phase in session.phases_completed:
            phase_performance[phase.value] = {
                "completed": True,
                "questions_answered": len([
                    qa for qa in session.conversation_history
                ])
            }
        
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
            "phase_performance": phase_performance,
            "current_phase": session.current_phase.value,
            "started_at": session.started_at.isoformat(),
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
            "red_flags": session.red_flag_answers[:5] if hasattr(session, 'red_flag_answers') else []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error generating metrics summary: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# TEST ENDPOINTS
# ============================================
@app.get("/test/llm")
def test_llm():
    """Test LLM connection"""
    try:
        from llm_service import test_llm_connection
        success, message = test_llm_connection()
        return {"success": success, "message": message}
    except Exception as e:
        return {"success": False, "message": str(e)}