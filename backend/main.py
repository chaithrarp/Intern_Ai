from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from interview_data import get_question_by_id, get_total_questions
from whisper_service import transcribe_audio
import os
from datetime import datetime
import asyncio
import uuid
from resume_parser import ResumeParser
from resume_question_generator import ResumeQuestionGenerator
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from werkzeug.utils import secure_filename
from pydantic import BaseModel
from datetime import datetime
import uuid
from resume_parser import ResumeParser
from resume_question_generator import ResumeQuestionGenerator
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from werkzeug.utils import secure_filename
from pydantic import BaseModel

# ============================================
# AUTHENTICATION IMPORTS
# ============================================
from auth_endpoints import auth_router
from auth_database import (
    init_auth_database,
    create_user_session
)

from database import (
    init_database,
    create_session as db_create_session,
    complete_session as db_complete_session,
    save_answer as db_save_answer,
    save_audio_file as db_save_audio_file
)
from metrics_analyzer import analyze_complete_metrics
from metrics_storage import (
    save_metrics,
    save_interruption,
    get_session_metrics,
    get_session_summary,
    get_user_performance_history
)

# ============================================
# PHASE 4: AI INTERVIEW IMPORTS
# ============================================
from interview_engine import (
    start_ai_interview,
    process_answer_and_continue
)

# ============================================
# PHASE 5: PRESSURE ENGINE IMPORTS
# ============================================
from pressure_engine import (
    check_interruption_trigger,
    process_interruption,
    store_interrupted_answer
)

from auth import get_current_active_user, User
import config

app = FastAPI()
resume_parser = ResumeParser()
resume_question_gen = ResumeQuestionGenerator()

@app.on_event("startup")
async def startup_event():
    """Initialize database when backend starts"""
    init_database()
    init_auth_database() 
    
    print("✅ Database initialized")
    print("✅ Authentication database initialized")


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Include authentication endpoints
app.include_router(auth_router)


# ============================================
# DATA MODELS
# ============================================

class InterruptionCheckData(BaseModel):
    current_question_text: str = ""

class AnswerSubmission(BaseModel):
    question_id: int  # ← CHANGED: Accept floats for interruption follow-ups
    answer_text: str
    was_interrupted: bool = False
    recording_duration: float = 0  # PHASE 5: Track answer duration

# ============================================
# IN-MEMORY SESSION STORAGE
# (Later: Replace with database)
# ============================================

sessions = {}

# ============================================
# API ENDPOINTS
# ============================================

@app.get("/")
def read_root():
    return {
        "message": "InternAI Backend is running!", 
        "phase": 5, 
        "ai_enabled": True,
        "pressure_enabled": config.ENABLE_INTERRUPTIONS
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy", 
        "service": "InternAI API", 
        "phase": "Phase 5 - Interruptions & Pressure"
    }

# ============================================
# PHASE 5: AI INTERVIEW ENDPOINTS
# ============================================

@app.post("/interview/start")
def start_interview():
    """
    Start a new AI-powered interview session with pressure enabled
    """
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
    
    try:
        interview_data = start_ai_interview(session_id)
        
        # Initialize session data with pressure tracking
        sessions[session_id] = {
            "current_question": 1,
            "current_question_text": interview_data["question"]["question"],
            "answers": [],
            "completed": False,
            "ai_powered": True,
            "pressure_enabled": config.ENABLE_INTERRUPTIONS,
            "interruptions": [],
            "interruption_count": 0,  # PHASE 5: Track total interruptions
            "max_interruptions": 2,   # PHASE 5: Limit to 2 per session
            "interruption_scheduled": None
        }
        db_create_session(session_id, ai_powered=True, pressure_enabled=config.ENABLE_INTERRUPTIONS)
        
        print(f"✅ Started AI interview with pressure: {session_id}")
        print(f"   First question: {interview_data['question']['question']}")
        print(f"   Max interruptions allowed: 2")
        
        return interview_data
    
    except Exception as e:
        print(f"❌ Error starting AI interview: {str(e)}")
        return {
            "error": f"Failed to start AI interview: {str(e)}",
            "fallback": "Using fallback question",
            "session_id": session_id,
            "question": {
                "id": 1,
                "question": "Tell me about yourself and your background.",
                "category": "opening"
            },
            "question_number": 1,
            "total_questions": 5
        }
# ============================================
# RESUME UPLOAD ENDPOINT
# ============================================

@app.post("/upload-resume")
async def upload_resume(
    resume: UploadFile = File(...),
    session_id: str = Form(None)
):
    """
    Upload and parse resume to enable personalized interview questions
    
    Args:
        resume: Resume file (PDF, DOC, DOCX, or TXT)
        session_id: Optional existing session ID
    
    Returns:
        Resume context and suggested questions for AI interviewer
    """
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
                content={
                    "success": False, 
                    "error": "Invalid file type. Please upload PDF, DOC, DOCX, or TXT"
                }
            )
        
        # Validate file size (5MB limit)
        contents = await resume.read()
        if len(contents) > 5 * 1024 * 1024:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "File size too large. Maximum 5MB allowed"
                }
            )
        
        # Generate session ID if not provided
        if not session_id:
            session_id = f"resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
        
        # Create temporary file to save upload
        os.makedirs("resume_uploads", exist_ok=True)
        file_extension = resume.filename.split('.')[-1]
        filename = f"{session_id}.{file_extension}"
        file_path = os.path.join("resume_uploads", filename)
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        print(f"📄 Resume uploaded: {filename} ({len(contents)} bytes)")
        
        # Parse resume
        parsed_data = resume_parser.parse_resume(file_path)
        
        if not parsed_data["success"]:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": parsed_data.get("error", "Failed to parse resume")
                }
            )
        
        # Generate personalized questions
        questions = resume_question_gen.generate_questions(
            parsed_data["raw_text"], 
            num_questions=8
        )
        
        # Create resume context for LLM
        resume_context = resume_question_gen.create_resume_context(
            parsed_data["raw_text"]
        )
        
        print(f"✅ Resume parsed successfully")
        print(f"   - Text length: {len(parsed_data['raw_text'])} chars")
        print(f"   - Generated {len(questions)} personalized questions")
        
        return {
            "success": True,
            "session_id": session_id,
            "resume_context": resume_context,
            "suggested_questions": questions,
            "resume_summary": parsed_data["summary"],
            "filename": resume.filename,
            "message": "Resume uploaded and analyzed successfully"
        }
        
    except Exception as e:
        print(f"❌ Error uploading resume: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Server error: {str(e)}"
            }
        )


@app.post("/interview/answer")
async def submit_answer(session_id: str, submission: AnswerSubmission):
    """
    Submit an answer and get the next AI-generated question
    PHASE 6: Saves metrics and answers to database
    """
    if session_id not in sessions:
        return {"error": "Invalid session ID"}
    
    session = sessions[session_id]
    
    if session["completed"]:
        return {"error": "Interview already completed"}
    
    # PHASE 6: Get metrics from last audio upload
    last_metrics = None
    if session.get("audio_files"):
        last_audio = session["audio_files"][-1]
        last_metrics = last_audio.get("metrics")
    
    # PHASE 6: Save answer to database BEFORE processing next question
    current_q_text = session.get("current_question_text", "")
    
    answer_id = db_save_answer(
        session_id=session_id,
        question_id=submission.question_id,
        question_text=current_q_text,
        answer_text=submission.answer_text,
        recording_duration=submission.recording_duration,
        was_interrupted=submission.was_interrupted
    )
    
    # PHASE 6: Save metrics if available
    if last_metrics:
        save_metrics(session_id, answer_id, last_metrics)
    
    # PHASE 6: Save interruption to database if this was interrupted
    if submission.was_interrupted and session.get("interruptions"):
        last_int = session["interruptions"][-1]
        save_interruption(
            session_id=session_id,
            answer_id=answer_id,
            triggered_at_seconds=last_int.get("triggered_at_seconds", 0),
            interruption_reason=last_int.get("reason", "unknown"),
            interruption_phrase=last_int.get("interruption_phrase", ""),
            followup_question=last_int.get("followup_question", ""),
            partial_answer=last_int.get("partial_answer", ""),
            recovery_time=last_metrics.get("recovery_time") if last_metrics else None
        )

    try:
        # PHASE 5: Check if this was an interrupted answer
        if submission.was_interrupted:
            print(f"⚡ Processing interrupted answer (duration: {submission.recording_duration}s)")
            
            # The interruption question was already sent
            # Just update the partial answer in session
            if session.get("interruptions"):
                last_interruption = session["interruptions"][-1]
                last_interruption["user_stopped_at"] = submission.recording_duration
        
        # Process answer normally (even if interrupted)
        result = process_answer_and_continue(
            session_data=session,
            question_id=submission.question_id,
            answer_text=submission.answer_text
        )
        
        if result["completed"]:
            session["completed"] = True
            
            # PHASE 6: Complete session in database
            db_complete_session(
                session_id,
                total_questions=len(session.get("answers", [])),
                total_interruptions=len(session.get("interruptions", []))
            )
            
            print(f"✅ Interview completed: {session_id}")
            return {
                "session_id": session_id,
                "completed": True,
                "message": "Interview completed!",
                "total_answers": len(session["answers"]),
                "total_interruptions": len(session.get("interruptions", []))
            }
        else:
            session["current_question"] = result["question_number"]
            session["current_question_text"] = result["question"]["question"]
            
            print(f"✅ Next AI question: {result['question']['question']}")
            
            return {
                "session_id": session_id,
                "question": result["question"],
                "question_number": result["question_number"],
                "total_questions": result["total_questions"],
                "completed": False,
                "ai_generated": True
            }
    
    except Exception as e:
        print(f"❌ Error processing answer: {str(e)}")
        
        # Fallback to fixed questions
        next_question_id = session["current_question"] + 1
        
        if next_question_id > get_total_questions():
            session["completed"] = True
            db_complete_session(
                session_id,
                total_questions=len(session.get("answers", [])),
                total_interruptions=len(session.get("interruptions", []))
            )
            return {
                "session_id": session_id,
                "completed": True,
                "message": "Interview completed!",
                "total_answers": len(session["answers"])
            }
        
        fallback_question = get_question_by_id(next_question_id)
        session["current_question"] = next_question_id
        
        return {
            "session_id": session_id,
            "question": fallback_question,
            "question_number": next_question_id,
            "total_questions": get_total_questions(),
            "completed": False,
            "error": f"AI generation failed, using fallback: {str(e)}"
        }
    
@app.post("/interview/upload-audio")
async def upload_audio(
    session_id: str,
    question_id: int,
    audio_file: UploadFile = File(...)
):
    """
    Upload audio file, transcribe it, analyze metrics, and save to database
    """
    if session_id not in sessions:
        return {"error": "Invalid session ID"}
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = audio_file.filename.split('.')[-1]
    filename = f"{session_id}_q{question_id}_{timestamp}.{file_extension}"
    
    file_path = os.path.join("audio_uploads", filename)
    
    try:
        contents = await audio_file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        print(f"Audio file saved: {filename}")
        
        print(f"Starting transcription for: {filename}")
        transcription_result = transcribe_audio(file_path)
        
        if not transcription_result:
            return {
                "success": False,
                "error": "Transcription failed"
            }
        
        transcript_text = transcription_result["text"]
        language = transcription_result["language"]
        segments = transcription_result.get("segments", [])
        
        print(f"Transcription complete: {transcript_text[:50]}...")
        
        # PHASE 6: Analyze behavioral metrics
        session = sessions[session_id]
        
        # Check if this answer was interrupted
        was_interrupted = len(session.get("interruptions", [])) > 0
        interruption_time = None
        
        if was_interrupted and session["interruptions"]:
            last_interruption = session["interruptions"][-1]
            interruption_time = last_interruption.get("triggered_at_seconds")
        
        # Get recording duration (estimate from segments if not provided)
        recording_duration = segments[-1]["end"] if segments else 0
        
        # Analyze complete metrics
        metrics = analyze_complete_metrics(
            transcript_text=transcript_text,
            segments=segments,
            recording_duration=recording_duration,
            was_interrupted=was_interrupted,
            interruption_time=interruption_time
        )
        
        print(f"📊 Metrics analyzed:")
        print(f"   - Pauses: {metrics['total_pauses']} (long: {metrics['long_pauses']})")
        print(f"   - Fillers: {metrics['filler_word_count']}")
        print(f"   - Hesitation score: {metrics['hesitation_score']}/100")
        print(f"   - Words/min: {metrics['words_per_minute']}")
        
        # Save audio metadata
        db_save_audio_file(
            session_id=session_id,
            question_id=question_id,
            filename=filename,
            file_path=file_path,
            file_size=len(contents),
            language=language
        )
        
        # Store in session (for backward compatibility)
        audio_metadata = {
            "question_id": question_id,
            "filename": filename,
            "file_path": file_path,
            "file_size": len(contents),
            "uploaded_at": timestamp,
            "transcript": transcript_text,
            "language": language,
            "metrics": metrics  # PHASE 6: Add metrics to session
        }
        
        if "audio_files" not in sessions[session_id]:
            sessions[session_id]["audio_files"] = []
        
        sessions[session_id]["audio_files"].append(audio_metadata)
        
        return {
            "success": True,
            "message": "Audio uploaded and transcribed successfully",
            "filename": filename,
            "file_size": len(contents),
            "transcript": transcript_text,
            "language": language,
            "metrics": metrics  # PHASE 6: Return metrics to frontend
        }
    
    except Exception as e:
        print(f"Error processing audio: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to process audio: {str(e)}"
        }


# ============================================
# PHASE 5: INTERRUPTION ENDPOINTS
# ============================================

@app.post("/interview/check-interruption")
async def check_interruption(
    session_id: str,
    question_id: int,
    recording_duration: float,
    partial_transcript: str = "",
    data: InterruptionCheckData = None  # ← ADD THIS
):
    """
    Check if interruption should be triggered during recording
    
    Args:
        session_id: Current session
        question_id: Question being answered
        recording_duration: How long they've been speaking
        partial_transcript: What they've said (if available)
    
    Returns:
        Interruption data if should interrupt, else None
    """
    if session_id not in sessions:
        return {"error": "Invalid session ID"}
    
    session = sessions[session_id]
    
    # Check if pressure is enabled
    if not config.ENABLE_INTERRUPTIONS:
        return {"should_interrupt": False}
    
    # PHASE 5: Check if we've already hit max interruptions
    current_interruption_count = session.get("interruption_count", 0)
    max_interruptions = session.get("max_interruptions", 2)
    
    if current_interruption_count >= max_interruptions:
        print(f"⚠️ Max interruptions ({max_interruptions}) reached for session {session_id}")
        return {"should_interrupt": False, "reason": "max_reached"}
    
    # Get current question number from session
    current_question_number = session.get("current_question", 1)
    
    # PHASE 8: Get persona from session (default to standard if not set)
    persona = session.get("persona", "standard_professional")

    # Check interruption trigger WITH question number and persona
    interruption_data = check_interruption_trigger(
        recording_duration,
        partial_transcript,
        current_question_number,
        persona  # Pass persona to interruption logic
    )
        
    if interruption_data["should_interrupt"]:
        # PHASE 5: Use current question text from frontend (NOT from session)
        if data and data.current_question_text:
            # Temporarily override session question for interruption generation
            original_question = session.get("current_question_text", "")
            session["current_question_text"] = data.current_question_text
        
        # Get current question text from session
        current_q_text = session.get("current_question_text", "")
        
        # Generate interruption question WITH current question context
        interruption_result = process_interruption(
            session_data=session,
            partial_answer=partial_transcript,
            interruption_data=interruption_data,
            current_question_text=current_q_text  # ← ADD THIS
        )
        
        # Restore original question text
        if data and data.current_question_text:
            session["current_question_text"] = original_question
        
        # Store the interrupted answer
        store_interrupted_answer(
            session,
            question_id,
            partial_transcript,
            interruption_data
        )
        
        # PHASE 5: Increment interruption count
        session["interruption_count"] = current_interruption_count + 1
        
        print(f"🔥 Interruption triggered! Count: {session['interruption_count']}/{max_interruptions}")
        
        # Update current question to the interruption follow-up
        session["current_question_text"] = interruption_result["followup_question"]
        
        return {
            "should_interrupt": True,
            "interruption_phrase": interruption_result["interruption_phrase"],
            "followup_question": interruption_result["followup_question"],
            "reason": interruption_result["reason"],
            "interruption_count": session["interruption_count"],
            "max_interruptions": max_interruptions
        }
    
    return {"should_interrupt": False}

@app.get("/interview/session/{session_id}")
def get_session_data(session_id: str):
    """
    Get current session data (for debugging)
    """
    if session_id not in sessions:
        return {"error": "Session not found"}
    
    return sessions[session_id]

# ============================================
# PHASE 5: TEST ENDPOINTS
# ============================================

@app.get("/test/llm")
def test_llm():
    """
    Test if LLM is working (for debugging)
    """
    try:
        from llm_service import test_llm_connection
        success, message = test_llm_connection()
        return {
            "success": success,
            "message": message
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"LLM test failed: {str(e)}"
        }
@app.get("/metrics/session/{session_id}")
def get_metrics_for_session(session_id: str):
    """
    Get all metrics for a specific session
    """
    try:
        metrics = get_session_metrics(session_id)
        return {
            "success": True,
            "session_id": session_id,
            "metrics": metrics
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/metrics/summary/{session_id}")
def get_session_metrics_summary(session_id: str):
    """
    Get aggregated metrics summary for a session
    """
    try:
        summary = get_session_summary(session_id)
        if not summary:
            return {
                "success": False,
                "error": "Session not found"
            }
        return {
            "success": True,
            "summary": summary
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/metrics/history")
def get_performance_history(limit: int = 10):
    """
    Get performance history across all sessions
    """
    try:
        history = get_user_performance_history(limit)
        return {
            "success": True,
            "history": history,
            "total_sessions": len(history)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/metrics/database-stats")
def get_db_stats():
    """
    Get database statistics (for debugging)
    """
    try:
        from database import get_database_stats
        stats = get_database_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
# ============================================
# PHASE 8: PERSONA ENDPOINTS
# ============================================

@app.get("/personas/list")
def get_personas():
    """
    Get all available interviewer personas
    """
    from pressure_modes import get_all_personas
    personas = get_all_personas()
    return {
        "success": True,
        "personas": personas
    }

class InterviewStartRequest(BaseModel):
    persona: str = "standard_professional"
    resume_context: str = None

@app.post("/interview/start-with-persona")
def start_interview_with_persona(request: InterviewStartRequest):  # ← ADD request parameter
    """
    Start a new interview with a specific persona and optional resume
    
    Args:
        request: Contains persona and optional resume_context
    """
    from pressure_modes import PERSONAS, DEFAULT_PERSONA
    
    persona = request.persona
    resume_context = request.resume_context
    
    # Validate persona
    if persona not in PERSONAS:
        persona = DEFAULT_PERSONA
    
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
    
    try:
        # Pass resume context to interview engine if provided
        if resume_context:
            # Store resume context in session for AI to use
            interview_data = start_ai_interview(session_id, resume_context=resume_context)
            print(f"📄 Starting interview with resume-based questions")
        else:
            interview_data = start_ai_interview(session_id)
        
        # Initialize session with persona and resume flag
        sessions[session_id] = {
            "current_question": 1,
            "current_question_text": interview_data["question"]["question"],
            "answers": [],
            "completed": False,
            "ai_powered": True,
            "pressure_enabled": config.ENABLE_INTERRUPTIONS,
            "interruptions": [],
            "interruption_count": 0,
            "max_interruptions": 2,
            "interruption_scheduled": None,
            "persona": persona,
            "resume_context": resume_context  
        }
        
        db_create_session(session_id, ai_powered=True, pressure_enabled=config.ENABLE_INTERRUPTIONS)  # ← FIXED: Use db_create_session
        persona_config = PERSONAS[persona]
        
        print(f"✅ Started AI interview with persona: {persona_config['emoji']} {persona_config['name']}")
        print(f"   Session: {session_id}")
        print(f"   Resume-based: {resume_context is not None}")
        
        return {
            **interview_data,
            "persona": {
                "id": persona,
                "name": persona_config["name"],
                "emoji": persona_config["emoji"],
                "description": persona_config["description"]
            },
            "has_resume": resume_context is not None  # ← FIXED: Use resume_context variable
        }
    
    except Exception as e:
        print(f"❌ Error starting AI interview with persona: {str(e)}")
        return {
            "error": f"Failed to start AI interview: {str(e)}",
            "fallback": "Using fallback question",
            "session_id": session_id,
            "question": {
                "id": 1,
                "question": "Tell me about yourself and your background.",
                "category": "opening"
            },
            "question_number": 1,
            "total_questions": 5,
            "persona": {
                "id": persona,
                "name": "Standard Professional",
                "emoji": "🟡",
                "description": "Realistic interview simulation"
            },
            "has_resume": False
        }
    
@app.get("/test/pressure")
def test_pressure():
    """
    Test pressure engine (for debugging)
    """
    try:
        from pressure_modes import detect_rambling, should_interrupt
        
        test_rambling = "Um, so like, you know, I was basically working on, like, this project..."
        test_normal = "I worked on a React dashboard for analytics."
        
        rambling_detected = detect_rambling(test_rambling)
        normal_detected = detect_rambling(test_normal)
        
        interrupt_result = should_interrupt(12, test_rambling)
        
        return {
            "success": True,
            "rambling_detection": {
                "rambling_text": rambling_detected,
                "normal_text": normal_detected
            },
            "interruption_test": {
                "should_interrupt": interrupt_result[0],
                "reason": interrupt_result[1]
            },
            "config": {
                "interruptions_enabled": config.ENABLE_INTERRUPTIONS,
                "probability": config.INTERRUPTION_PROBABILITY,
                "pressure_mode": config.PRESSURE_MODE
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Pressure test failed: {str(e)}"
        }
@app.get("/test/resume")
def test_resume_parsing():
    """
    Test resume parsing (for debugging)
    """
    try:
        return {
            "success": True,
            "message": "Resume parser initialized",
            "supported_formats": ["PDF", "DOC", "DOCX", "TXT"],
            "max_file_size": "5MB",
            "upload_directory": "resume_uploads"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Resume parser test failed: {str(e)}"
        }
    