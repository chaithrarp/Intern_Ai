from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from interview_data import get_question_by_id, get_total_questions
from whisper_service import transcribe_audio
import os
from datetime import datetime
import asyncio

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
import config

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# DATA MODELS
# ============================================

class AnswerSubmission(BaseModel):
    question_id: int
    answer_text: str
    was_interrupted: bool = False  # PHASE 5: Track if interrupted
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
    session_id = f"session_{len(sessions) + 1}"
    
    try:
        interview_data = start_ai_interview(session_id)
        
        # Initialize session data with pressure tracking
        sessions[session_id] = {
            "current_question": 1,
            "current_question_text": interview_data["question"]["question"],
            "answers": [],
            "completed": False,
            "ai_powered": True,
            "pressure_enabled": config.ENABLE_INTERRUPTIONS,  # PHASE 5
            "interruptions": [],  # PHASE 5: Track interruptions
            "interruption_scheduled": None  # PHASE 5: Pending interruption
        }
        
        print(f"✅ Started AI interview with pressure: {session_id}")
        print(f"   First question: {interview_data['question']['question']}")
        
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

@app.post("/interview/answer")
async def submit_answer(session_id: str, submission: AnswerSubmission):
    """
    Submit an answer and get the next AI-generated question
    PHASE 5: Handles interruptions
    """
    if session_id not in sessions:
        return {"error": "Invalid session ID"}
    
    session = sessions[session_id]
    
    if session["completed"]:
        return {"error": "Interview already completed"}
    
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
        
        # PHASE 5: Add 1-second delay for smoother transition
        await asyncio.sleep(1)
        
        if result["completed"]:
            session["completed"] = True
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
    Upload audio file, transcribe it, and return transcript
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
        
        print(f"Transcription complete: {transcript_text[:50]}...")
        
        audio_metadata = {
            "question_id": question_id,
            "filename": filename,
            "file_path": file_path,
            "file_size": len(contents),
            "uploaded_at": timestamp,
            "transcript": transcript_text,
            "language": language
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
            "language": language
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
    partial_transcript: str = ""
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
    
    # Check interruption trigger
    interruption_data = check_interruption_trigger(
        recording_duration,
        partial_transcript
    )
    
    if interruption_data["should_interrupt"]:
        # Generate interruption question
        interruption_result = process_interruption(
            session_data=session,
            partial_answer=partial_transcript,
            interruption_data=interruption_data
        )
        
        # Store the interrupted answer
        store_interrupted_answer(
            session,
            question_id,
            partial_transcript,
            interruption_data
        )
        
        # Update current question to the interruption follow-up
        session["current_question_text"] = interruption_result["followup_question"]
        
        return {
            "should_interrupt": True,
            "interruption_phrase": interruption_result["interruption_phrase"],
            "followup_question": interruption_result["followup_question"],
            "reason": interruption_result["reason"]
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