# InternAI - Project Structure (Compact)

**AI-powered mock interview system** with voice recording, LLM multi-dimensional evaluation, intelligent real-time interruptions, behavioral analytics, and claim verification.

---

## 🔧 BACKEND (Python/FastAPI)

### Core Application
- **main.py**: FastAPI app with CORS setup, central hub for all REST endpoints (interview, auth, resume, session history), routes requests to appropriate services, enables cross-origin requests for frontend communication
- **config.py**: LLM provider configuration (Ollama local/OpenAI cloud), API key management, model selection, database path configuration, centralized settings for entire application
- **auth.py**: JWT token generation and validation, secret key management, token expiration (7 days), secure authentication mechanism for stateless API
- **auth_endpoints.py**: Authentication routes (`/auth/register`, `/auth/login`, `/auth/me`), credential validation, token issuance, user session management
- **auth_database.py**: User authentication database (SQLite), user account creation, credential verification, user lookup by username/email, password hashing

### Audio & Resume
- **whisper_service.py**: OpenAI Whisper speech-to-text transcription, loads pre-trained model, converts audio files (MP3/WAV) to text, enables voice-based interview input processing
- **resume_parser.py**: Extracts structured text from PDF/DOCX/TXT files, parses and categorizes resume content (companies, skills, projects, experience), enables resume-based question personalization
- **resume_question_generator.py**: Generates interview questions customized to candidate's resume, extracts keywords for contextual questioning, creates personalized deep-dive questions based on listed experience

### LLM & Database
- **llm_service.py**: Unified LLM interface abstraction, supports Ollama (local/free) or OpenAI (cloud/paid), handles API calls with consistent response format, enables provider switching without code changes
- **database.py**: SQLite schema and initialization, manages tables: sessions, answers, questions, audio_files, resume_data, metrics, persistence layer for all interview data
- **metrics_storage.py**: Stores and retrieves behavioral metrics (pause duration, filler word count, volume levels), interruption records, enables historical analysis and performance tracking
- **metrics_analyzer.py**: Analyzes audio/speech patterns (pause detection >2s, filler words "um/uh/like", volume fluctuations, speech rate), identifies behavioral indicators for confidence assessment

### Interview Engines
- **interview_orchestrator.py**: Main session orchestrator, manages 6-phase interview progression (resume deep dive → core skills → scenario → stress testing → claim verification → wrap-up), selects question rounds (HR/Tech/SysDesign), coordinates evaluation and feedback flow, persists session state
- **answer_analyzer.py**: Routes candidate answers to appropriate round evaluator (HR/Tech/SysDesign), orchestrates claim extraction, integrates evaluations across multiple analyzers, combines scores for comprehensive assessment
- **round_evaluators/hr_evaluator.py**: Behavioral evaluation on 5 scoring dimensions (tech depth, concept accuracy, structured thinking, communication clarity, confidence/consistency), scores 0-100 per dimension, provides behavioral insights
- **round_evaluators/technical_evaluator.py**: Technical depth evaluation, detects accuracy gaps and misconceptions, scores problem-solving approach, identifies overconfidence patterns, evaluates depth of knowledge
- **round_evaluators/sysdesign_evaluator.py**: System design evaluation, assesses architecture decisions, analyzes scalability and trade-off reasoning, evaluates design choices, provides design feedback
- **claim_extractor.py**: Extracts claims from answers and categorizes (technical facts, metrics, experience claims), assesses claim verifiability (verifiable/vague/suspicious/contradictory), generates verification questions for suspicious claims, **NEW FEATURE: Intelligent claim verification**
- **interruption_analyzer.py**: **NEW FEATURE: Multi-layer interruption detection** (audio pauses >2s, content rambling detection, context contradictions, behavioral uncertainty markers), assigns severity levels (CRITICAL/HIGH/MEDIUM/LOW), maintains interruption history per session
- **interruption_decision.py**: Consolidates multi-layer analysis (audio + content + interruption history), makes final interrupt decision, selects contextual interruption phrase, enforces max interruptions per session, prevents interrupt spam
- **followup_generator.py**: Generates contextual follow-up questions post-interruption, tailors to specific interruption reason (rambling/pause/contradiction), keeps responses brief and direct, maintains conversation flow
- **immediate_feedback.py**: Generates post-answer feedback (quick score 0-10, 2 top strengths with evidence, 2 improvement areas with actionable suggestions, red flags for disqualifiers), provides immediate coaching
- **live_warning_generator.py**: **NEW FEATURE: Non-interrupting real-time warnings** (pausing detection, filler word suggestions, vagueness alerts), auto-dismisses after 5s, respects cooldown to prevent alert spam, provides gentle coaching
- **final_report.py**: Comprehensive session report compilation, calculates overall score, provides dimension breakdown (5-dimension radar), generates skill heatmap, identifies top strengths/weaknesses with evidence quotes, exports report data

### Data Models
- **models/state_models.py**: InterviewPhase enum (6 phases: resume_deepdive, core_skills, scenario, stress_test, claim_verification, wrap_up), RoundType (HR/Technical/SysDesign), SessionState tracking (current phase, round type, question/answer history)
- **models/evaluation_models.py**: 5 core scoring dimensions (technical depth, concept accuracy, structured thinking, communication clarity, confidence/consistency), AnswerEvaluation (scores + evidence per dimension), FinalReport (overall score + heatmap), ScoringThresholds
- **models/interruption_models.py**: InterruptionReason enum (rambling, pausing, contradiction, uncertainty), SeverityLevel (CRITICAL/HIGH/MEDIUM/LOW), ActionType, InterruptionDecision (decision + reason + phrase + follow-up), **NEW: Behavioral markers for detection**
- **models/interview_models.py**: Question (text + category + phase), Answer (text + transcript + audio_path), ExtractedClaim (text + type + verifiability), ClaimType (technical/metrics/experience), ClaimVerifiability (verifiable/vague/suspicious/contradictory)

### Utilities
- **prompt_templates/evaluation_prompts.py**: LLM prompts for evaluating answers on 5 dimensions (HR/Tech/SysDesign rounds), JSON response parsing, scoring rubrics, dimension-specific evaluation criteria
- **prompt_templates/interruption_prompts.py**: LLM prompts for content analysis (contradiction detection, off-topic detection, rambling assessment), behavioral marker identification, severity reasoning
- **prompt_templates/claim_prompts.py**: LLM prompts for claim extraction, categorization, verifiability assessment, verification question generation
- **config/evaluation_config.py**: Evaluation thresholds (per dimension), scoring weights, claim priority rules, severity mapping thresholds

### Testing & Validation
- **test_whisper.py**: Unit tests for Whisper transcription, model loading, error handling, audio file format support
- **test_intelligent_interruptions.py**: Tests for claim extraction, contradiction detection, severity assignment, multi-layer interruption logic, **NEW: Tests for behavioral marker detection**
- **test_STANDALONE.py**: Full integration test, end-to-end interview simulation (upload → question → answer → evaluate → interrupt → report), validates entire flow
- **validate_integration.py**: Validates component imports, LLM service connectivity, database initialization, all endpoint definitions, startup validation script
- **backup_old_system/**: Archive of legacy code (previous interruption analyzer, pressure engine, old versions) for reference and system evolution tracking

---

## ⚛️ FRONTEND (React)

### Main Components
- **App.js**: Root component managing application state, auth state management (login/register/logout/JWT token), screen routing (welcome, resume upload, interview, session history), token persistence in localStorage for session continuity
- **Interview.js**: Main interview orchestrator on frontend, session creation and management, round/question display, audio recording integration, interruption handling (displaying alerts, handling retry/skip actions), feedback display post-answer, state tracking (sessionId, roundType, phase, aiState)
- **AudioRecorder.js**: **NEW FEATURE: Real-time audio metrics** - Records audio via MediaRecorder API, Web Speech API for real-time transcript, filler word detection ("um", "uh", "like"), silence/pause detection, pause counting (>2s), volume monitoring, transcription via Whisper, visual feedback for recording state

### Auth & Upload
- **Login.js**: Login form (username/password), API call to `/auth/login`, token storage in localStorage, error message display, redirect to interview on success
- **Register.js**: Registration form (username/email/password), validation (password strength, email format), API call to `/auth/register`, error handling, auto-redirect to login post-registration
- **ResumeUpload.js**: File drag-and-drop interface, PDF/DOCX/TXT format validation, upload to `/interview/upload-resume`, displays parsed resume content (skills, experience, projects)

### Interview UI
- **PersonaSelector.js**: Select interview round type (HR behavioral, Technical, System Design), displays round descriptions and difficulty indicators, enables candidates to choose interview focus
- **FeedbackScreen.js**: Displays post-answer feedback (numeric score 0-10), shows top 2 strengths with evidence, top 2 improvement areas with actionable suggestions, highlights red flags, auto-advance timer to next question
- **InterruptionAlert.js**: **NEW FEATURE: Intelligent interruption display** - Shows interruption message and reason (rambling/pausing/contradiction), generates follow-up question, provides options (retry answer/skip/end interview), visual alert styling with urgency indicators
- **LiveWarning.js**: **NEW FEATURE: Non-interrupting real-time coaching** - Displays warnings (pausing detected, filler words, vague language), auto-dismisses after 5s, icon indicators for warning type, gentle coaching without stopping flow

### Utilities & UI
- **AIInterviewer.js**: Animated AI avatar with state indicators (idle/listening/thinking/speaking), sound wave animations, expression changes during conversation transitions, visual engagement enhancement
- **MiniAIOrb.js**: Compact AI avatar version for corner/header display, state coloring (listening state = blue, thinking = yellow, speaking = green), space-efficient avatar
- **SoundToggle.js**: Toggle sound effects on/off, persists preference in localStorage, icon state indicating current setting
- **UserMenu.js**: Displays candidate username, navigation links (session history/profile/logout), user avatar display
- **SessionHistory.js**: Fetches user's interview sessions, lists sessions with date/round type/score/duration, filter options, delete sessions functionality
- **SessionDetail.js**: Final report view, displays overall score, dimension breakdown (5-dimension scoring), radar/heatmap chart data visualization, top strengths/weaknesses with evidence, complete Q&A history with individual scores, export/share report functionality
- **WelcomeScreen.js**: Greeting message, system explanation, action buttons (start interview/view previous sessions), interview tips and guidance
- **VoiceControls.js**: Visual recording control interface, microphone permission requests, elapsed time display, cancel/submit buttons, audio level visualization

### Utility Files
- **utils/apiUtils.js**: Helper functions (`getAuthHeaders()`, `apiGet()`, `apiPost()`, `apiPostFormData()`, `apiDelete()`), automatic JWT token handling in request headers, API base URL centralization, error response handling
- **utils/audioAnalyzer.js**: **NEW FEATURE: Advanced audio analysis** - Creates audio context, analyzes frequency/amplitude spectrum, pause detection (>2s threshold), long pause counting (>3s), sound segment analysis, volume history tracking, generates real-time metrics for behavioral analysis
- **utils/soundEffects.js**: Plays audio effects (start/stop beep, interruption alert sound, success/error feedback), respects sound toggle setting, preloads audio files for instant playback, feedback audio for user actions
- **utils/voiceService.js**: Text-to-speech synthesis via Web Speech API, configurable speaking rate/pitch/volume, voice selection, enables AI agent to speak feedback and prompts

---

## 📊 KEY DATA FLOWS

### Registration Flow
Candidate fills registration form → POST `/auth/register` → `auth_database` creates user account → JWT token response → redirect to login → Candidate is now registered in system

### Interview Flow
**NEW: Complete interview workflow with intelligent interruptions**
1. Upload resume → `resume_parser` extracts keywords
2. Select interview round (HR/Tech/SysDesign)
3. POST `/interview/start` → `interview_orchestrator` creates session, loads phase 1 (resume deep dive)
4. Get question returned to frontend
5. Record answer via `AudioRecorder` (captures real-time metrics: pauses, filler words, volume)
6. POST `/interview/submit-answer` with audio file
7. `whisper_service` transcribes audio → text
8. `answer_analyzer` routes answer to appropriate round evaluator (HR/Tech/SysDesign)
9. Round evaluator scores answer on 5 dimensions (0-100 each)
10. `claim_extractor` identifies and verifies claims from answer
11. `interruption_analyzer` performs multi-layer analysis (audio + content + history)
12. `interruption_decision` makes final interrupt decision + selects phrase
13. If interrupt: `followup_generator` creates follow-up question
14. `immediate_feedback` generates post-answer coaching feedback
15. Return evaluation + interruption (if any) + feedback to frontend
16. Display `FeedbackScreen` (score + strengths + improvements) or `InterruptionAlert` (if interrupted)
17. Repeat for next question or advance phase
18. After all phases complete: `final_report` compiles comprehensive report → Display `SessionDetail`

### **NEW: Intelligent Interruption Flow**
Answer submitted → Multi-layer analysis triggered:
- **Audio Layer**: Detects pauses >2s, volume drops, unnatural speech patterns
- **Content Layer**: `interruption_analyzer` detects rambling, contradictions with previous answers, off-topic responses, vague language
- **History Layer**: Checks interruption count (respects limit), identifies patterns in candidate behavior
→ Assigns severity (CRITICAL/HIGH/MEDIUM/LOW)
→ `interruption_decision` consolidates analysis → final interrupt decision
→ If interrupt: generate interruption phrase + follow-up question via `followup_generator`
→ Send to frontend → `InterruptionAlert` displays with options (retry/skip/end)
→ Candidate can retry answer or skip to next question

### **NEW: Live Warnings Flow**
During recording, `AudioRecorder` + `audioAnalyzer` detect behavioral issues:
- Pausing >2s → Show pause warning via `LiveWarning`
- Filler words detected → Show filler word suggestion
- Vague language detected → Show vagueness alert
→ Warnings auto-dismiss after 5s with cooldown to prevent spam
→ Non-interrupting coaching to help candidate improve

### Report Flow
Interview completes all phases → `final_report.py` triggered:
1. Aggregate all answer evaluations (5 dimensions × 3 rounds)
2. Calculate overall score (weighted average of all rounds)
3. Build skill heatmap (which skills scored high/low across rounds)
4. Identify top 3 strengths with evidence quotes from answers
5. Identify top 3 weaknesses with improvement suggestions
6. Generate radar chart data (5-dimension profile)
7. Compile full Q&A history with individual scores
8. Save complete report to database
9. Return to frontend → `SessionDetail` displays charts, report, full history, export options

---

## 🎯 5 CORE EVALUATION DIMENSIONS (0-100 each)

Each answer is scored on these 5 dimensions, providing comprehensive behavioral and technical assessment:

1. **Technical Depth**: Knowledge breadth demonstrated, depth vs surface-level understanding, industry specificity, advanced concepts mentioned, evidence of hands-on experience
2. **Concept Accuracy**: Correctness of stated technical concepts, proper terminology usage, no misconceptions or false claims, factual accuracy verification
3. **Structured Thinking**: Use of problem-solving frameworks (STAR method), logical flow of explanation, step-by-step problem breakdown, clear cause-effect reasoning
4. **Communication Clarity**: Articulation quality, ease of following explanation, appropriate pace (not rushed/slow), clear voice, minimal filler words
5. **Confidence & Consistency**: Tone and conviction level, no self-contradictions, consistency with previous answers, assurance in stated knowledge, body language confidence (if visible)

**Scoring Aggregate**: Dimension scores are weighted and aggregated across all rounds (HR/Technical/SysDesign) to create overall interview score and identify skill profile patterns.

---

## 🚀 TECH STACK

**Backend**: Python 3.8+, FastAPI (async REST framework), uvicorn (ASGI server), Pydantic (data validation), SQLite3 (local database)
**Frontend**: React.js (UI framework), Framer Motion (animations), localStorage (client-side persistence), CSS3 (styling)
**Speech Processing**: OpenAI Whisper (speech-to-text, high accuracy), Web Speech API (real-time browser transcription), MediaRecorder API (audio capture)
**LLM**: Ollama (self-hosted, free, local inference) OR OpenAI API (cloud-based GPT models, paid), configurable provider switching
**Authentication**: JWT tokens (jose library), password hashing (passlib with bcrypt), stateless auth
**File Parsing**: PyPDF2 (PDF text extraction), python-docx (DOCX file parsing), text file reading
**Data**: SQLite3 (lightweight, file-based persistence), JSON for API communication

---

## 📝 CONFIG FILES & DOCUMENTATION

- **.env**: Environment configuration - `LLM_PROVIDER` (ollama/openai), `OPENAI_API_KEY` (if using OpenAI), `OLLAMA_BASE_URL` (if using Ollama), `JWT_SECRET_KEY` (for auth), `FRONTEND_URL` (for CORS)
- **requirements.txt**: Python dependencies - `fastapi`, `uvicorn`, `openai`, `whisper`, `pydantic`, `python-jose`, `passlib`, `PyPDF2`, `python-docx`, `sqlite3`
- **setup.md**: Installation guide - Prerequisites, environment setup, dependency installation, server/frontend startup, troubleshooting common issues
- **readme.md**: Project overview - Description, key features, tech stack, quick start guide, usage instructions, contribution guidelines
- **package.json**: Frontend dependencies - React, Framer Motion, API client libraries, build/dev scripts

---

## 🔌 COMPONENT COMMUNICATION ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND (React - Browser)                                 │
│  ├─ App.js (Auth & Routing)                                │
│  ├─ Interview.js (Main Flow)                               │
│  │ ├─ AudioRecorder.js (Real-time metrics)                │
│  │ ├─ FeedbackScreen.js (Display evaluation)              │
│  │ ├─ InterruptionAlert.js (Interruption handling)        │
│  │ └─ LiveWarning.js (Non-interrupting coaching)          │
│  └─ utils/ (API calls, Audio analysis, Sound, Voice)      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                    REST API (JSON)
                               │
┌──────────────────────────────▼──────────────────────────────┐
│  BACKEND (FastAPI - Python)                                 │
│  ├─ main.py (Routes & Endpoints)                           │
│  ├─ auth_endpoints.py (Register/Login)                     │
│  ├─ interview_orchestrator.py (Session management)         │
│  ├─ answer_analyzer.py (Route to evaluators)              │
│  ├─ round_evaluators/ (HR/Tech/SysDesign scoring)         │
│  ├─ interruption_analyzer.py (Multi-layer detection)      │
│  ├─ claim_extractor.py (Claim verification)               │
│  ├─ llm_service.py (Ollama/OpenAI calls)                  │
│  ├─ whisper_service.py (Audio transcription)              │
│  ├─ database.py (SQLite persistence)                      │
│  └─ final_report.py (Report generation)                   │
└──────────────────────────────────────────────────────────────┘

**Audio Flow**: Frontend RecordedAudio → Backend Whisper → Transcribed Text → Evaluators → Scores
**Metrics Flow**: AudioRecorder (real-time) → audioAnalyzer → Interruption Detection → LiveWarnings/Interruptions
**Evaluation Flow**: Answer → Round Evaluator (5 dimensions) → Claim Extractor → Interruption Analysis → Final Decision
**Report Flow**: All Evaluations → final_report.py → Aggregate Scores → Heatmap/Radar → SessionDetail display
```

---

## 🎯 ADDING NEW FEATURES

### Step-by-Step Guide
1. **Define Data Model**: Create new Pydantic model in `/backend/models/` (e.g., `NewFeatureModel`)
2. **Implement Logic**: Add business logic in appropriate engine/service file in `/backend/engines/` or `/backend/`
3. **Create API Endpoint**: Add route in `/backend/main.py` that calls your logic, returns JSON response
4. **Add Frontend Component**: Create new React component in `/frontend/src/components/` or utility in `/frontend/src/utils/`
5. **Connect via API**: Use `apiUtils.js` functions (`apiGet()`, `apiPost()`) to call backend endpoint
6. **Test**: Add unit tests in `/backend/test_*.py` and verify frontend integration
7. **Update Prompt Templates**: If feature requires LLM calls, add prompts in `/backend/prompt_templates/`

### Example: Add New Evaluation Dimension
1. Add dimension to `ScoringThresholds` in `/backend/models/evaluation_models.py`
2. Implement scoring logic in `/backend/engines/round_evaluators/hr_evaluator.py` (or appropriate evaluator)
3. Update evaluation prompts in `/backend/prompt_templates/evaluation_prompts.py`
4. Modify frontend score display in `/frontend/src/components/FeedbackScreen.js` to show new dimension
5. Test with `/backend/test_STANDALONE.py`

### **Switching LLM Provider** (No Code Changes Required!)
- Change `LLM_PROVIDER` value in `.env` file (ollama → openai or vice versa)
- Set `OPENAI_API_KEY` if using OpenAI
- Set `OLLAMA_BASE_URL` if using Ollama (default: http://localhost:11434)
- All `llm_service.py` calls automatically use new provider
- Restart backend server - no code modifications needed!

### **Adding New Evaluation Round Type**
1. Add round type to `RoundType` enum in `/backend/models/state_models.py`
2. Create new evaluator class in `/backend/engines/round_evaluators/new_evaluator.py`
3. Update `answer_analyzer.py` to route to new evaluator based on round type
4. Add round to frontend `PersonaSelector.js` options
5. Update prompt templates for new evaluation criteria

