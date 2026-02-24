# InternAI - Comprehensive Project Structure & Feature Documentation

## 📋 Overview

**InternAI** is an advanced AI-powered mock interview system designed to simulate realistic interview pressure with intelligent behavioral conditioning. Unlike traditional interview prep, InternAI trains **performance under pressure** through adaptive, multi-round interviews with real-time feedback and behavioral analysis.

The system uses a **Python FastAPI backend** for all intelligent logic combined with a **React frontend** for interactive user experience. AI is powered by LLMs (Ollama for local/free, OpenAI for advanced) with OpenAI Whisper for high-quality speech-to-text conversion.

---

## 🎯 Core System Features (Phase 4 - Current)

### **1. Voice-Powered Interviews**
- **Real-time Audio Recording**: React-based audio capture with browser Web Audio API
- **Speech-to-Text**: OpenAI Whisper integration for accurate transcription
- **Natural Interaction**: Candidates answer questions by speaking naturally
- **Audio Management**: Audio files stored and processed efficiently

### **2. Adaptive Interview Engine**
- **Multi-Phase Interview Structure**: 6 distinct interview phases
  - Phase 1: Resume Deep Dive (verify skills from resume)
  - Phase 2: Core Skill Assessment (test fundamental knowledge)
  - Phase 3: Scenario/Problem Solving (real-world challenges)
  - Phase 4: Stress Testing (high-pressure scenarios)
  - Phase 5: Claim Verification (follow-up on vague claims)
  - Phase 6: Wrap-up (final assessment question)

- **Dynamic Question Generation**: 
  - Resume-based questions extracted from uploaded resume
  - Round-specific questions (HR, Technical, System Design)
  - Context-aware follow-up questions based on previous answers

- **Smart Phase Transitions**: Phases progress based on:
  - Performance scores (must exceed thresholds to advance)
  - Phase duration limits (min/max questions per phase)
  - Intelligent progression metrics

### **3. Multi-Dimensional Evaluation**
InternAI evaluates candidates across **5 core dimensions**:

1. **Technical Depth** (30% weight) - Complexity, precision, depth of knowledge
2. **Concept Accuracy** (25% weight) - Correctness and relevance of technical content
3. **Structured Thinking** (20% weight) - Logical flow, STAR method adherence (in HR rounds)
4. **Communication Clarity** (15% weight) - Articulation, conciseness, understandability
5. **Confidence & Consistency** (10% weight) - Self-assurance, contradiction-free responses

Each dimension scored 0-100, with overall score calculated as weighted average.

### **4. Round-Specific Evaluation**
System supports 3 distinct interview round types, each with tailored evaluation:

- **HR Round**: Emphasizes STAR method (Situation, Task, Action, Result), behavioral aspects
- **Technical Round**: Focuses on depth, accuracy, technical reasoning
- **System Design Round**: Evaluates architecture, scalability, trade-off analysis

### **5. Intelligent Interruption System** ⚡NEW
- **Multi-Layer Detection**: 
  - Audio layer (pauses, hesitations, volume analysis)
  - Content layer (rambling detection, vagueness assessment)
  - Context layer (contradiction detection, off-topic analysis)
  - Behavioral layer (filler words, uncertainty markers)

- **Smart Interruption Levels**:
  - CRITICAL (interrupt immediately): False claims, contradictions, completely off-topic
  - HIGH (warn once, interrupt on repeat): Dodging questions, excessive rambling, excessive pausing
  - MEDIUM (warn twice, interrupt on third): Vague answers, lack of specifics, high uncertainty
  - LOW (warning only): Minor issues, speaking too long

- **Non-Interrupting Warnings** (shown live to user): Alerts without stopping recording
- **Interruption Cooldown**: Prevents warning spam with configurable cooldown periods

### **6. Real-Time Feedback System**
- **Immediate Feedback**: Shown right after each answer transcription
  - Quick score summary
  - Top 2 strengths
  - Top 2 improvement areas
  - Red flags (if critical issues detected)

- **Final Comprehensive Report** (at interview completion):
  - Overall performance score
  - Dimension breakdown with radar chart data
  - Skill heatmap visualization
  - Specific mistakes with evidence citations
  - Round-by-round breakdown
  - Recommended focus topics for improvement
  - Next steps and development plan

### **7. Resume Analysis & Integration**
- **Multi-Format Support**: PDF, DOCX, TXT resume parsing
- **Claim Extraction**: Automatically identifies all claims from resume
- **Resume-Based Questions**: Generates interview questions directly from resume claims
- **Claim Verification Phase**: Dedicated phase to verify and challenge resume claims
- **Context Awareness**: AI interviewer references resume throughout interview

### **8. Authentication & User Management**
- **Secure JWT Tokens**: OAuth2 password bearer authentication
- **User Accounts**: Registration, login, profile management
- **Session Persistence**: Token-based session management (7-day expiration)
- **Protected Endpoints**: All interview/session endpoints require authentication

### **9. Session Management & History**
- **Active Session Tracking**: JSON-based session state persistence
- **Session History**: Users can review past interview sessions
- **Detailed Session Records**: Complete conversation history, scores, feedback
- **Session Export**: Generate detailed reports for review

### **10. Flexible LLM Support**
- **Ollama Integration** (Free, Local): Run locally without API costs
- **OpenAI Integration** (Premium): Advanced reasoning and accuracy
- **Provider Abstraction**: Easy to switch between providers via config
- **Configurable Models**: Select specific models (e.g., mistral, gpt-4)

---

## 🏗️ PROJECT ARCHITECTURE

```
InternAI/
├── backend/                    # Python FastAPI backend
│   ├── engines/               # Core interview logic engines
│   ├── models/                # Pydantic data models
│   ├── config/                # Configuration files
│   ├── prompt_templates/      # LLM prompt definitions
│   ├── round_evaluators/      # Round-specific evaluators (HR, Technical, SysDesign)
│   ├── Main services (main.py, llm_service.py, etc.)
│   └── Supporting services (auth, resume, whisper, etc.)
│
├── frontend/                   # React web application
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── utils/             # Helper functions
│   │   ├── App.js             # Main app component
│   │   └── Interview.js       # Interview flow component
│   └── public/
│
└── Documentation files
```

---

# 🔧 BACKEND STRUCTURE - DETAILED

## Core Application Files

### **main.py** (730+ lines)
**Purpose**: Main FastAPI application entry point and comprehensive API endpoint routing

**Key Responsibilities**:
- **Initialization**: FastAPI app setup with CORS middleware for frontend-backend communication
- **Session Management**:
  - `POST /interview/start`: Initiate new interview session
  - `POST /interview/submit-answer`: Process and evaluate candidate answers
  - `GET /sessions/{session_id}`: Retrieve session details
  - `GET /history`: Get user's interview history
  
- **Resume Processing**:
  - `POST /resume/upload`: Upload and parse resume (PDF/DOCX/TXT)
  - Resume text extraction and storage
  
- **Audio Processing**:
  - `POST /audio/upload`: Process audio recordings
  - Whisper transcription integration
  - Audio file management

- **Results & Feedback**:
  - `GET /results/{session_id}`: Retrieve final report
  - Real-time feedback generation
  - Score aggregation and analysis

- **Service Integration**: Orchestrates interaction between:
  - Interview Orchestrator (interview flow)
  - Round Evaluators (answer evaluation)
  - LLM Service (AI responses)
  - Feedback Generators (immediate & final)
  - Interruption Analyzer (behavioral analysis)

**Architecture**: Async FastAPI endpoints for non-blocking performance

---

## 🔐 Authentication System

### **auth.py** (234 lines)
**Purpose**: JWT token generation, validation, and password security

**Functionality**:
- JWT token creation with expiration (default 7 days)
- Token validation via OAuth2 dependency injection
- Password hashing using industry-standard algorithms
- Token payload encoding (user_id, username)
- Security scopes for different endpoint access levels

**Key Functions**:
- `create_access_token()`: Generate JWT for authenticated user
- `verify_token()`: Validate token and extract user info
- `hash_password()` / `verify_password()`: Password cryptography

---

### **auth_endpoints.py** (256+ lines)
**Purpose**: REST API endpoints for user authentication

**Endpoints**:
- `POST /auth/register`: Create new user account
  - Username/email validation
  - Password strength enforcement
  - Account creation and storage
  
- `POST /auth/login`: User authentication
  - Credentials verification
  - JWT token generation
  - Session initialization
  
- `GET /auth/me`: Get current user profile
  - Returns authenticated user info
  - Requires valid JWT token
  
- `POST /auth/logout`: Session termination (optional, can be client-side only)

**Security**:
- All endpoints validate input data via Pydantic models
- Passwords never transmitted in plain text
- CORS-protected endpoints

---

### **auth_database.py** (60+ lines)
**Purpose**: SQLite database operations for user authentication

**Operations**:
- User table initialization with proper schema
- New user registration with password hashing
- User lookup by username or email
- Credential verification for login
- Profile data retrieval

**Database Schema**:
```
users table:
- id (primary key)
- username (unique)
- email (unique)
- hashed_password
- created_at
- updated_at
```

---

## 🎙️ Audio & Speech Processing

### **whisper_service.py** (56 lines)
**Purpose**: Speech-to-text conversion using OpenAI Whisper

**Functionality**:
- Whisper model loading (base model for balance of speed/accuracy)
- Audio file transcription
- Transcription quality metrics
- Multi-language support (English primary)

**Usage Flow**:
1. Frontend captures audio WAV
2. Sends to backend `/audio/upload`
3. Whisper transcribes to text
4. Text sent to LLM for evaluation

---

## 🤖 Interview Orchestration Engine

### **engines/interview_orchestrator.py** (951+ lines) ⭐ CORE ENGINE
**Purpose**: Main orchestrator managing entire interview flow and state

**Key Responsibilities**:

1. **Interview State Management**:
   - Tracks SessionState object with complete interview data
   - Persists session state to JSON for recovery
   - Maintains conversation history (Q&A pairs)
   - Tracks current phase and round type

2. **Phase-Based Interview Flow**:
   ```
   NOT_STARTED
       ↓
   RESUME_DEEP_DIVE (Phase 1)
       ↓ (if score > threshold)
   CORE_SKILL_ASSESSMENT (Phase 2)
       ↓
   SCENARIO_SOLVING (Phase 3)
       ↓
   STRESS_TESTING (Phase 4)
       ↓
   CLAIM_VERIFICATION (Phase 5) - Conditional verification of vague claims
       ↓
   WRAP_UP (Phase 6)
       ↓
   COMPLETED
   ```

3. **Question Generation**:
   - Resume questions (Phase 1)
   - Round-specific questions (HR, Technical, System Design)
   - Context-aware follow-up questions based on previous answers
   - Claim-based verification questions (Phase 5)

4. **Question Tracking** (Fixed for demo mode):
   - Intro question (Q0) - not counted toward total
   - Main questions (Q1-Q5 in demo, configurable in production)
   - Follow-ups don't count toward main question total
   - Hard stop at configured maximum

5. **Answer Evaluation**:
   - Routes answers to appropriate round evaluator
   - Stores evaluation in session history
   - Triggers interruption analysis
   - Determines phase transitions

6. **Session Persistence**:
   - Auto-saves to `active_sessions.json`
   - Loads previous sessions on restart
   - Supports session recovery

**Key Methods**:
- `initialize_session()`: Create new interview session
- `get_next_question()`: Generate/retrieve next question
- `submit_answer()`: Process candidate answer and evaluate
- `should_transition_phase()`: Decide if phase change needed
- `end_interview()`: Finalize session with report
- `save_session()` / `load_sessions()`: Persistence

---

## 📊 Evaluation Engines

### **engines/answer_analyzer.py**
**Purpose**: Analyzes candidate answers for content accuracy and quality

**Functions**:
- Content validation against question intent
- Claim extraction from answers
- Key point identification
- Preparation assessment (how prepared candidate is)

---

### **engines/claim_extractor.py**
**Purpose**: Intelligent claim extraction from answers and resumes

**Functions**:
- Parse resume for all explicit/implicit claims
- Extract claims from real-time answers
- Categorize claims by type (technical, behavioral, achievement)
- Store claims for verification phase

---

### **engines/claim_analyzer.py**
**Purpose**: Analyze claims for contradictions, falsity, vagueness

**Functions**:
- Compare answer claims against resume claims
- Detect contradictions or inconsistencies
- Assess claim specificity (vague vs detailed)
- Flag false or unsubstantiated claims

---

### **Round Evaluators** (engines/round_evaluators/):

#### **technical_evaluator.py** (503+ lines)
**Purpose**: Evaluates answers in technical interview rounds

**Evaluation Focus**:
- Technical Depth (most important, 30% of score)
- Concept Accuracy (25%)
- Structured Thinking (20%)
- Communication Clarity (15%)
- Confidence & Consistency (10%)

**Red Flags Detected**:
- Incorrect technical concepts
- Missing important details
- No trade-off analysis
- Low specificity
- Uncertainty in core concepts

**Scoring**: Returns AnswerEvaluation with detailed breakdown

---

#### **hr_evaluator.py**
**Purpose**: Evaluates behavioral and HR-focused answers

**Evaluation Focus**:
- STAR method adherence (Situation, Task, Action, Result)
- Specific metrics and outcomes
- Ownership/accountability  
- Communication Clarity
- Confidence & Consistency

**Red Flags**:
- No specific examples
- Blaming others
- Vague generalizations
- No measurable results
- Inconsistent values

---

#### **sysdesign_evaluator.py**
**Purpose**: Evaluates system design and architecture answers

**Evaluation Focus**:
- Architectural thinking
- Scalability considerations
- Trade-off analysis
- Technical Depth
- Communication Clarity

**Red Flags**:
- Single-point failures not addressed
- No scalability considerations
- Missing SLA/latency requirements
- Overly simplistic design
- Incomplete monitoring strategy

---

### **engines/immediate_feedback.py** (261+ lines)
**Purpose**: Generates quick, actionable feedback shown immediately after answer transcription

**Feedback Components**:
- Overall score (0-100)
- Top 2 strengths from the answer
- Top 2 improvement suggestions
- Any critical red flags needing attention

**Timing**: Shown to candidate BEFORE final report, enables course correction

**Output Format**:
```json
{
  "overall_score": 72,
  "strengths": ["Specific examples", "Clear logic"],
  "improvements": ["Add numbers/metrics", "Discuss trade-offs"],
  "red_flags": ["Seemed uncertain about core concept"]
}
```

---

### **engines/final_report.py** (608+ lines)
**Purpose**: Generates comprehensive final report at interview completion

**Report Contents**:
1. **Overall Performance Summary**:
   - Final score (0-100)
   - Performance level (Excellent/Good/Average/Needs Improvement)
   - Interview breakdown by round

2. **Multi-Dimensional Analysis**:
   - Scores for each 5 dimensions
   - Radar chart data for visualization
   - Dimension-specific feedback

3. **Skill Assessment Heatmap**:
   - Technical skills evaluated
   - Strength levels per skill
   - Weak areas for focus

4. **Critical Mistakes**:
   - List of significant errors
   - Evidence and specific quotes
   - Impact on score

5. **Area Analysis**:
   - Strong areas (well-demonstrated)
   - Improvement areas (needs work)
   - Growth opportunities

6. **Actionable Recommendations**:
   - Specific topics to study
   - Practice focus areas
   - Development suggestions

7. **Next Steps**:
   - Retry interview recommendation
   - Suggested study time
   - Success probability estimate

---

### **engines/interruption_analyzer.py** (729+ lines) ⚡ NEW FEATURE
**Purpose**: Multi-layer intelligent interruption detection system

**Multi-Layer Interruption Detection**:

1. **Audio Layer**: Analyzes voice mechanics
   - Pause detection and duration
   - Hesitation patterns
   - Volume/confidence indicators
   - Speaking pace

2. **Content Layer**: LLM-powered analysis
   - Rambling detection
   - Vagueness assessment
   - Specificity checking
   - Claim validation

3. **Context Layer**: Conversation-aware
   - Contradiction detection (vs resume/previous answers)
   - Off-topic detection
   - Question dodging
   - Inconsistency flagging

4. **Behavioral Layer**: Marker detection
   - Filler words ("um", "uh", "like")
   - Uncertainty markers ("I think", "maybe", "probably")
   - Hedging phrases ("to be honest", "from what I recall")
   - Confidence assessment

**Interruption Severity Levels** (auto-configured):

| Severity | Examples | Threshold | Action |
|----------|----------|-----------|--------|
| CRITICAL (Weight 90-100) | False claims, contradictions, completely off-topic | Interrupt immediately | Halt recording, show interruption |
| HIGH (Weight 75-85) | Dodging question, excessive rambling, excessive pausing | 2nd occurrence | Warn once, interrupt on repeat |
| MEDIUM (Weight 60-70) | Vague answers, lack of specifics, high uncertainty | 3rd occurrence | Warn twice, interrupt third time |
| LOW (Weight 20-30) | Minor rambling, speaking too long | Warning only | Never interrupt, show warning |

**Cooldown System**: Prevents warning spam with configurable cooldown periods (default 10 seconds)

---

### **engines/live_warning_generator.py** (230+ lines) ⚡ NEW FEATURE
**Purpose**: Real-time non-interrupting warnings during recording

**Warnings Displayed**:
- "You're going off track"
- "Be more specific"
- "Your answer seems to contradict what you said earlier"
- "Try to provide concrete examples"
- "You're speaking too fast/slow"

**Delivery Mechanism**:
- Shown in UI without stopping audio recording
- Gentle visual/audio alert
- Encourages self-correction without interruption
- Configurable cooldown prevents spam

---

## 🧠 Data Models

### **models/state_models.py** (425+ lines)
**Purpose**: Pydantic models defining interview state and progression

**Key Models**:

#### `InterviewPhase` Enum:
- `NOT_STARTED`
- `RESUME_DEEP_DIVE`
- `CORE_SKILL_ASSESSMENT`
- `SCENARIO_SOLVING`
- `STRESS_TESTING`
- `CLAIM_VERIFICATION`
- `WRAP_UP`
- `COMPLETED`

#### `RoundType` Enum:
- `HR`
- `TECHNICAL`
- `SYSTEM_DESIGN`

#### `SessionState` (Main state object):
```python
{
  "session_id": "uuid",
  "user_id": "int",
  "current_phase": "InterviewPhase",
  "current_round_type": "RoundType",
  "current_question_id": int,
  "current_question_text": str,
  "resume_context": str,
  "resume_uploaded": bool,
  "conversation_history": [
    {
      "question_id": int,
      "question_text": str,
      "answer_text": str,
      "evaluation": AnswerEvaluation,
      "timestamp": datetime
    }
  ],
  "interruptions_triggered": List[InterruptionRecord],
  "created_at": datetime,
  "completed_at": Optional[datetime]
}
```

#### `PhaseConfig`:
- Defines min/max questions per phase
- Score thresholds for progression
- Interruption probabilities
- Difficulty levels

---

### **models/evaluation_models.py** (432+ lines)
**Purpose**: Pydantic models for evaluation results and scoring

**Key Models**:

#### `EvaluationScore`:
```python
{
  "dimension": "technical_depth|concept_accuracy|structured_thinking|communication_clarity|confidence_consistency",
  "score": 0-100,
  "evidence": "What justified this score",
  "improvement": "How to improve if < 70"
}
```

#### `AnswerEvaluation` (returned by evaluators):
```python
{
  "question_id": int,
  "round_type": "hr|technical|system_design",
  "scores": {
    "technical_depth": 75,
    "concept_accuracy": 82,
    "structured_thinking": 68,
    "communication_clarity": 70,
    "confidence_consistency": 65
  },
  "score_details": [EvaluationScore, ...],
  "overall_score": 71,
  "strengths": ["Specific examples", "Clear logic"],
  "weaknesses": ["Missing trade-offs", "Vague on edge cases"],
  "red_flags": ["Contradicted resume claim"]
}
```

#### `InterruptionRecord`:
```python
{
  "timestamp": datetime,
  "reason": InterruptionReason,
  "severity": str,
  "message": str,
  "evidence": str
}
```

#### `FinalReport`:
```python
{
  "session_id": str,
  "overall_score": int,
  "performance_level": str,
  "dimension_scores": Dict[str, int],
  "skill_assessments": [SkillAssessment, ...],
  "strong_areas": [str, ...],
  "improvement_areas": [str, ...],
  "critical_mistakes": [str, ...],
  "recommended_topics": [str, ...],
  "report_generated_at": datetime
}
```

---

### **models/interruption_models.py**
**Purpose**: Models for interruption analysis data

**Key Models**:
- `InterruptionReason` (enum of all interruption types)
- `InterruptionAnalysis` (result of interruption analysis)
- `ContentAnalysis` (content layer findings)
- `AudioMetrics` (audio layer metrics)

---

## 🧠 Configuration System

### **config/evaluation_config.py** (569+ lines)
**Purpose**: Centralizes all evaluation constants and scoring rules

**Key Configurations**:

#### `DIMENSION_WEIGHTS`:
```python
{
  "technical_depth": 0.30,        # 30% - Most important
  "concept_accuracy": 0.25,       # 25% - Critical
  "structured_thinking": 0.20,    # 20% - Important
  "communication_clarity": 0.15,  # 15% - Moderate
  "confidence_consistency": 0.10  # 10% - Supporting
}
```

#### `ScoreLevel`:
- `EXCELLENT` = 85 (85-100)
- `GOOD` = 70 (70-84)
- `AVERAGE` = 50 (50-69)
- `NEEDS_WORK` = 0 (0-49)

#### `ROUND_EVALUATION_FOCUS`:
Per-round evaluation criteria for HR, Technical, System Design

#### `PHASE_TRANSITION_RULES`:
Configuration for demo mode vs production mode
- Demo: 5 total questions (Q0 intro + Q1-Q2 resume + Q3-Q5 round)
- Production: Customizable per phase

---

## 🎤 Prompt Templates

### **prompt_templates/evaluation_prompts.py**
Pre-written LLM prompts for evaluations:
- Technical evaluation prompts
- Behavioral evaluation prompts
- System design evaluation prompts
- Dimension-specific scoring prompts

### **prompt_templates/interruption_prompts.py**
Prompts for interruption analysis:
- Content analysis prompts
- Contradiction detection prompts
- Off-topic detection prompts
- Claim validation prompts

### **prompt_templates/claim_prompts.py**
Prompts for claim extraction and analysis:
- Resume claim extraction
- Answer claim extraction
- Contradiction discovery
- Specificity assessment prompts

---

## 🤖 LLM Service

### **llm_service.py** (163+ lines)
**Purpose**: Unified interface for LLM providers

**Supported Providers**:
- **Ollama** (Local, free, fully private)
  - Base URL: `http://localhost:11434`
  - Models: mistral, llama2, neural-chat, etc.
  
- **OpenAI** (Cloud, paid, advanced reasoning)
  - Models: gpt-4, gpt-3.5-turbo, etc.
  - Requires API key

**Key Functions**:
- `get_llm_client()`: Provider-agnostic client factory
- `get_llm_response()`: Send messages and get responses
  - Supports temperature adjustment (randomness)
  - Configurable max_tokens
  - Automatic retries on failure

**Configuration** (in config.py):
```python
LLM_PROVIDER = "ollama"  # or "openai"
OLLAMA_BASE_URL = "http://localhost:11434"
OPENAI_API_KEY = "sk-..."
LLM_MODEL = "mistral"  # Ollama model name
```

---

## 📝 Supporting Services

### **resume_parser.py** (83+ lines)
**Purpose**: Parse and extract text from resumes

**Supported Formats**:
- PDF (.pdf)
- Word (.docx, .doc)
- Text (.txt)

**Extraction Process**:
1. File upload detection
2. Format validation
3. Text extraction using PyPDF2 (PDF) or python-docx (DOCX)
4. Parsed text returned and stored

---

### **resume_question_generator.py**
**Purpose**: Generate interview questions from resume content

**Process**:
1. Parse resume text
2. Extract key skills and experiences
3. Generate challenging questions about those areas
4. Return questions for Phase 1 (Resume Deep Dive)

---

### **database.py**
**Purpose**: SQLite database operations (interview data storage)

**Tables**:
- `sessions`: Interview session records
- `answers`: Individual answer evaluations
- `feedback`: Generated feedback
- `interruptions`: Interruption events

---

### **metrics_analyzer.py** & **metrics_storage.py**
**Purpose**: Track and store interview metrics

**Metrics Tracked**:
- Performance scores over time
- Response quality metrics
- Interruption frequency
- Improvement trends

---

# 🎨 FRONTEND STRUCTURE

## Main Components

### **App.js** (198 lines)
**Purpose**: Main React application component

**State Management**:
- `isAuthenticated`: User login state
- `currentUser`: Logged-in user data
- `showInterview`: Interview screen toggle
- `showResumeUpload`: Resume upload panel
- `resumeData`: Parsed resume content

**Authentication Flow**:
- Checks for stored JWT token on load
- Verifies token validity with `/auth/me` endpoint
- Handles login/register/logout flows
- Maintains session across page refreshes

---

### **Interview.js**
**Purpose**: Main interview flow component

**Interactions**:
1. Audio recording capture
2. Submit answer to backend
3. Display evaluation feedback
4. Navigate to next question
5. End interview and show results

**Features**:
- Real-time audio level visualization
- Answer submission and loading states
- Feedback display
- Session information display

---

### **components/AIInterviewer.js**
**Purpose**: AI interviewer display component

**Shows**:
- Current question
- Interview progress (Question X of Y)
- Round type indicator
- Time spent on current question

---

### **components/AudioRecorder.js** & **AudioRecorder.css**
**Purpose**: Audio capture and recording UI

**Features**:
- Browser Web Audio API integration
- Real-time audio level meter
- Record/Stop buttons
- Waveform visualization
- File size display

---

### **components/FeedbackScreen.js** & **FeedbackScreen.css**
**Purpose**: Display immediate feedback after each answer

**Content**:
- Overall score with visual indicator
- Strengths (top 2)
- Improvements (top 2)
- Red flags (if any)
- Next question button

---

### **components/LiveWarning.js** & **LiveWarning.css**
**Purpose**: Display live warnings during answer recording

**Warning Types**:
- "You're going off track"
- "Be more specific"
- "Your answer seems vague"
- Animated alert with sound option

---

### **components/ResumeUpload.js** & **ResumeUpload.css**
**Purpose**: Resume file upload interface

**Functionality**:
- File drag-and-drop
- File type validation (PDF/DOCX/TXT)
- Upload progress indicator
- Resume text preview

---

### **components/SessionDetail.js** & **SessionDetail.css**
**Purpose**: Display detailed session results

**Shows**:
- Final overall score
- Dimension breakdown (radar chart)
- Round-by-round breakdown
- Red flags summary
- Recommended topics

---

### **components/SessionHistory.js** & **SessionHistory.css**
**Purpose**: List of past interview sessions

**Displays**:
- Session list with dates
- Final scores
- Round types
- Duration
- Click to view detailed results

---

### **components/Login.js** & **components/Register.js**
**Purpose**: Authentication UI

**Login Flow**:
- Username/email and password input
- Submit to `/auth/login`
- Store JWT token and user data
- Redirect to interview

**Register Flow**:
- Username, email, password input
- Submit to `/auth/register`
- Auto-login after registration

---

### **components/VoiceControls.js** & **VoiceControls.css**
**Purpose**: Voice control buttons and visualization

**Controls**:
- Record/Stop buttons
- Playback button (review answer)
- Submit button
- Cancel button

---

### **components/MiniAIOrb.js**
**Purpose**: Animated AI avatar indicator

**Shows**:
- AI "thinking" animation
- Processing state
- Ready state

---

### **components/WelcomeScreen.js** & **WelcomeScreen.css**
**Purpose**: Landing/welcome screen before interview

**Content**:
- Welcome message
- Start interview button
- View history button
- Resume upload option

---

### **components/PersonaSelector.js** & **PersonaSelector.css**
**Purpose**: Select interview type/round

**Options**:
- HR Round (behavioral)
- Technical Round (technical)
- System Design Round (architecture)

---

### **components/RecoveryCurveChart.js** & **RecoveryCurveChart.css**
**Purpose**: Visualize performance improvement over time

**Chart**:
- Score improvement curve
- Dimension scores over multiple interviews
- Trend analysis

---

### **components/SoundToggle.js** & **SoundToggle.css**
**Purpose**: Enable/disable notification sounds

**Controls**:
- Sound on/off toggle
- Sound volume control

---

### **components/UserMenu.js** & **UserMenu.css**
**Purpose**: User profile and logout menu

**Options**:
- View profile
- View history
- Logout
- Account settings

---

## Utility Functions

### **utils/** folder
Helper functions for:
- API calls (fetch wrappers)
- Audio processing
- Data formatting
- LocalStorage management
- Authentication token handling

---

# 📦 Key External Dependencies

## Python (Backend)
```
FastAPI - Web framework
Pydantic - Data validation
PyJWT - Token generation/validation
PyPDF2 - PDF parsing
python-docx - DOCX parsing
openai - LLM integration (Ollama & OpenAI)
python-dotenv - Environment variables
SQLite3 - Database
```

## JavaScript (Frontend)
```
React - UI framework
axios/fetch - HTTP requests
charts.js - Data visualization
Web Audio API - Audio recording
```

---

# 🔄 Data Flow Examples

## Interview Session Flow
```
1. User logs in
   → POST /auth/login
   → Returns JWT token
   
2. User uploads resume
   → POST /resume/upload
   → Backend parses and stores
   
3. User starts interview
   → POST /interview/start
   → Backend creates SessionState
   → Returns first question
   
4. User answers question (via audio)
   → POST /audio/upload (audio file)
   → Whisper transcribes to text
   → POST /submit-answer (transcribed text)
   
5. Backend evaluates answer
   → Routes to appropriate evaluator
   → LLM generates evaluation
   → Checks for interruptions
   → Returns feedback + next question
   
6. Repeat steps 4-5 until interview complete
   → POST /interview/end
   → Final report generated
   → Score aggregation
   
7. User reviews results
   → GET /results/{session_id}
   → FinalReport returned
```

## Answer Evaluation Flow
```
1. Answer received as text
2. InterviewOrchestrator routes to evaluator
3. Evaluator selects prompt template
4. LLM generates multi-dimensional scores
5. Parser converts raw response to AnswerEvaluation
6. Interruption analyzer runs (separate)
7. ImmediateFeedbackGenerator creates quick feedback
8. Feedback sent to frontend
9. SessionState updated with evaluation
10. Next question fetched/generated
```

## Interruption Detection Flow
```
1. Frontend captures audio metrics (pauses, volume)
2. User transcribes via Whisper
3. InterruptionAnalyzer runs multi-layer analysis:
   → Audio layer (from frontend metrics)
   → Content layer (LLM analyzes transcript)
   → Context layer (checks conversation history)
   → Behavioral layer (detects filler words, etc)
4. Determines if interruption needed
5. Returns InterruptionAnalysis result
6. Frontendreceivesinterruptioninstanceifawarenessishighthreshold
7. Either:
   → Shows live warning (non-interrupting)
   → Stops recording with interruption message
```

---

# 🎯 Demo Mode vs Production Mode

## Demo Mode Configuration (Current):
```
Max Questions: 5 total
- Q0: Introduction (not counted)
- Q1-Q2: Resume questions (2)
- Q3-Q5: Round-specific questions (3)
Total: EXACTLY 5 main questions
```

## Production Mode Configuration (Planned):
```
Phase-based with variable questions:
- Resume Deep Dive: 2-3 questions
- Core Skill Assessment: 3-4 questions
- Scenario Solving: 2-3 questions
- Stress Testing: 1-2 questions
- Claim Verification: 1-2 (as needed)
- Wrap Up: 1 question
```

---

# 🚀 Deployment Architecture

## Backend Deployment:
```
Python FastAPI on:
- Localhost:8000 (development)
- Production server with gunicorn/uvicorn
- Environment variables for config
- SQLite or PostgreSQL for data
```

## Frontend Deployment:
```
React app built and served:
- Localhost:3000 (development)
- Static build deployed to CDN or web server
- Environment config for backend URL
- CORS enabled for API calls
```

---

# 🔐 Security Features

1. **JWT Authentication**: Secure token-based authentication
2. **Password Hashing**: Bcrypt/PBKDF2 password security
3. **CORS Protection**: Frontend origin validation
4. **OAuth2 Scopes**: Fine-grained permission control
5. **Token Expiration**: 7-day token lifetime
6. **Protected Endpoints**: All interview endpoints require auth
7. **Input Validation**: Pydantic schema validation
8. **Audio Security**: Temporary file cleanup
9. **Resume Security**: Stored securely with user association

---

# 📊 Performance Optimizations

1. **Async/Await**: Non-blocking FastAPI endpoints
2. **Lazy Loading**: LLM models loaded once
3. **Session Caching**: JSON-based session persistence
4. **Frontend Optimization**: React component memoization
5. **Audio Compression**: Efficient audio file handling
6. **Parallel Processing**: Concurrent evaluations (planned)

---

# 🐛 Error Handling & Recovery

1. **Session Recovery**: Auto-loads from JSON if interrupted
2. **LLM Fallbacks**: Retry logic with exponential backoff
3. **Token Refresh**: Automatic token validation
4. **Audio Validation**: File format and size checks
5. **Evaluation Errors**: Graceful fallback scoring
6. **Network Errors**: Frontend retry with user feedback

---

# 🎓 Use Cases

**Primary Use**: Interview preparation and behavioral conditioning
- Practice for tech interviews
- Prepare for behavioral rounds
- Get accustomed to pressure
- Receive detailed feedback

**Secondary Uses**:
- Hiring team interview simulation
- Training platform
- Performance assessment tool
- Skills evaluation system

---

# 📈 Future Enhancements (Phase 5+)

- Timed interruutions (strict time limits)
- Multi-session statistics and trends
- Personalized recommendations based on weak areas
- Video recording with facial expression analysis
- Peer comparison and benchmarking
- Custom question libraries
- Interview templates by company
- Integration with Zoom/Teams
- Mobile app version


- Transcribe audio files to text
- Handle audio file validation
- Error handling for missing/corrupted files
- Return transcription results with confidence

**Used By**: Interview submission endpoint to convert recorded answers to text

---

## 📄 Resume Processing

### **resume_parser.py** (83 lines)
**Purpose**: Extract and parse resume content from multiple file formats

**Responsibilities**:
- Extract text from PDF files (PyPDF2)
- Extract text from DOCX files (python-docx)
- Extract text from TXT files
- Clean and normalize extracted text
- Parse resume for keywords (companies, skills, projects)
- Store parsed resumes

**Formats Supported**: PDF, DOCX, TXT

**Returns**: Plain text resume content for question generation

---

### **resume_question_generator.py** (116 lines)
**Purpose**: Generate customized interview questions based on resume content

**Responsibilities**:
- Extract keywords from parsed resume (companies, skills, education, projects)
- Generate context-specific questions for each extracted element
- Question templates for different resume sections:
  - Experience questions (about companies/roles)
  - Skills questions (technical and applied knowledge)
  - Education questions (degree relevance)
  - Project questions (specific contributions)
  - General fit questions
- Ensure questions are personalized and relevant

**Example**: If resume mentions "Python" and "Data Analysis", generates targeted questions about those skills

---

## 🧠 LLM Integration

### **llm_service.py** (163 lines)
**Purpose**: Unified interface for all LLM providers (Ollama, OpenAI)

**Responsibilities**:
- Initialize appropriate LLM client based on config (Ollama or OpenAI)
- Handle API authentication (API keys, endpoints)
- Send prompts to LLM and get responses
- Manage model selection and parameters
- Handle errors and retries
- Support streaming responses (optional)

**Supported Providers**:
- **Ollama**: Local, free LLM (llama3 by default)
- **OpenAI**: Cloud-based, paid LLM (gpt-4o-mini)

**Used By**: Every module that needs AI intelligence (evaluators, question generators, interruption analyzer)

---

### **config.py** (59 lines)
**Purpose**: Central configuration for backend settings

**Responsibilities**:
- Define LLM provider selection (Ollama or OpenAI)
- Ollama settings (base URL, model, temperature, max tokens)
- OpenAI settings (API key, model selection)
- Load environment variables from `.env` file
- Database settings
- Server settings (port, host)

---

## 💾 Database

### **database.py** (398 lines)
**Purpose**: SQLite database schema and core database operations

**Responsibilities**:
- Initialize SQLite database with all required tables:
  - `sessions`: Interview session records
  - `answers`: Individual answer records
  - `questions`: Question bank
  - `audio_files`: Uploaded audio metadata
  - `resume_data`: Parsed resume information
- Create, read, update interview sessions
- Save user answers with scores
- Store audio file paths
- Store resume data linked to users
- Query historical data

**Database Path**: `internai.db`

---

### **metrics_storage.py** (424 lines)
**Purpose**: Persistent storage of behavioral metrics and interruption data

**Responsibilities**:
- Save behavioral metrics to database:
  - Pause counts and durations
  - Filler word counts
  - Volume patterns
  - Silence durations
- Store interruption records:
  - Interruption reason
  - Timestamp
  - Severity level
  - Recovery time
- Retrieve metrics for analysis and reporting
- Link metrics to answer records
- Support metrics trending and comparison

---

### **interview_data.py**
**Purpose**: Data models and utilities for interview-related data

**Responsibilities**:
- Define interview data structures
- Serialize/deserialize interview data
- Data validation helpers

---

## 📊 Evaluation & Analysis

### **metrics_analyzer.py** (406 lines)
**Purpose**: Analyze audio transcripts and candidate delivery for behavioral metrics

**Responsibilities**:
- **Pause Detection**: Identify and measure silence/pauses
- **Filler Word Detection**: Count "um", "uh", "like", etc.
- **Volume Analysis**: Track speech volume patterns
- **Speech Patterns**: Identify stuttering, repetition
- **Recovery Analysis**: Measure how quickly candidate recovers from mistakes
- **Confidence Indicators**: Detect hesitation markers
- **Presence Scoring**: Overall communication quality
- Generate metrics dictionary for storage and evaluation

**Outputs**: Behavioral metrics used by evaluators and interruption analyzer

---

## ⚙️ Interview Engines

### **engines/interview_orchestrator.py** (731 lines)
**Purpose**: Main orchestrator managing the complete interview flow and progression

**Responsibilities**:
- **Session Management**: Create, load, persist interview sessions
- **Round Selection**: Choose between HR, Technical, System Design rounds
- **Phase Progression**: Manage 6 interview phases:
  1. Resume Deep Dive (2-3 questions)
  2. Core Skill Assessment (3-4 questions)
  3. Scenario/Problem Solving (2-3 questions)
  4. Stress/Edge Case Testing (1-2 questions)
  5. Claim Verification (adaptive)
  6. Wrap-up (1 question)
- **Question Generation**: Get questions from appropriate round
- **Answer Evaluation**: Route answers to correct evaluator
- **Difficulty Adjustment**: Adapt difficulty based on performance
- **Round Transitions**: Decide when to move to next round
- **Session Persistence**: Save/load sessions to survive server restarts

**Key Decision Points**:
- When to move to next phase
- When to switch rounds
- When interview is complete

---

### **engines/answer_analyzer.py** (362 lines)
**Purpose**: Main orchestrator routing answers to appropriate round evaluators

**Responsibilities**:
- Route answers to correct evaluator based on round type (HR, Technical, System Design)
- Integrate claim extraction for comprehensive evaluation
- Combine multiple evaluation perspectives
- Generate unified AnswerEvaluation object
- Extract claims from answers for verification
- Detect contradictions with previous answers
- Aggregate scores across dimensions

**Uses**: All round evaluators, claim extractor

---

### **engines/round_evaluators/hr_evaluator.py** (405 lines)
**Purpose**: Evaluate behavioral/HR interview answers

**Responsibilities**:
- Score HR answers on 5 core dimensions:
  1. **Technical Depth**: Industry knowledge
  2. **Concept Accuracy**: Understanding of concepts
  3. **Structured Thinking**: STAR method application
  4. **Communication Clarity**: Articulation quality
  5. **Confidence & Consistency**: Assurance level
- Provide text evidence for each score
- Identify strengths and weaknesses
- Generate constructive feedback
- Flag red flags (dishonesty, disrespect, etc.)

**Scoring Range**: 0-100 per dimension (auto-scaled to 0-10 for display)

---

### **engines/round_evaluators/technical_evaluator.py** (503 lines)
**Purpose**: Evaluate technical interview answers

**Responsibilities**:
- Score technical answers on 5 core dimensions
- Detect technical accuracy/inaccuracy
- Identify gaps in knowledge
- Verify technical claims
- Check for common mistakes
- Score problem-solving approach
- Provide technical feedback and corrections
- Suggest learning resources
- Flag overconfidence without knowledge

---

### **engines/round_evaluators/sysdesign_evaluator.py**
**Purpose**: Evaluate system design interview answers

**Responsibilities**:
- Score system design approaches on 5 core dimensions
- Evaluate architecture choices (scalability, reliability)
- Analyze trade-off discussions
- Check for missed considerations (edge cases, security)
- Score communication of design thinking
- Identify gaps in distributed systems knowledge
- Provide design feedback and improvements

---

## 🎯 Intelligent Features

### **engines/claim_extractor.py** (431 lines)
**Purpose**: Extract and categorize verifiable claims from candidate answers

**Responsibilities**:
- Extract all claims from answers (technical, metrics, experience claims)
- Categorize claims by type:
  - Technical claims (tools, frameworks, languages)
  - Metrics claims (performance, impact numbers)
  - Experience claims (roles, responsibilities)
  - Achievement claims
- Assess claim verifiability:
  - Verifiable: Specific, measurable, checkable
  - Vague: Unclear, general statements
  - Suspicious: Unlikely or exaggerated
  - Contradictory: Conflicts with previous answers
- Generate targeted verification questions
- Detect contradictions with earlier answers
- Prioritize claims for verification focus

**Example**: 
- Input: "I optimized the API to be 50% faster"
- Extract: Metric claim (50% faster), Technical claim (API optimization)
- Verifiability: "How did you measure the improvement?"

---

### **engines/interruption_analyzer.py** (729 lines)
**Purpose**: Multi-layer intelligent interruption detection system

**Responsibilities**:
- **Layer 1 - Audio Analysis**: Detect pauses, hesitations, volume changes
- **Layer 2 - Content Analysis**: Identify rambling, vagueness, lack of specifics
- **Layer 3 - Context Analysis**: Detect contradictions, off-topic answers, question dodging
- **Layer 4 - Behavioral Analysis**: Identify filler words, uncertainty markers
- Assign severity levels to interruption triggers:
  - **CRITICAL** (weight 100): Always interrupt (false claims, contradictions)
  - **HIGH** (weight 85-80): Warn once, interrupt on second occurrence
  - **MEDIUM** (weight 70-65): Warn twice, interrupt on third
  - **LOW**: Non-interrupting warnings
- Track interruption history per session
- Decide if candidate should be interrupted
- Return interruption decision with reason and phrase

**Interruption Reasons**:
- FALSE_CLAIM, CONTRADICTION, COMPLETELY_OFF_TOPIC
- DODGING_QUESTION, EXCESSIVE_RAMBLING, EXCESSIVE_PAUSING
- VAGUE_ANSWER, LACK_OF_SPECIFICS, HIGH_UNCERTAINTY

---

### **engines/interruption_decision.py** (286 lines)
**Purpose**: Central decision engine for interruption actions

**Responsibilities**:
- Consolidate audio metrics, content analysis, history
- Make final interruption decision (yes/no)
- Determine interruption severity level
- Select appropriate interruption phrase
- Route to follow-up generator
- Respect interruption limits (max 5 per session)
- Consider current interview phase (more lenient early on)

---

### **engines/immediate_feedback.py** (261 lines)
**Purpose**: Generate immediate post-answer feedback shown to candidate

**Responsibilities**:
- Extract quick feedback from AnswerEvaluation
- Format feedback for immediate display:
  - Quick score summary (0-10 scale)
  - Top 2 strengths from answer
  - Top 2 improvement areas
  - Any red flags detected
- Keep feedback concise and actionable (30-60 seconds read time)
- Highlight specific evidence from answer

**Display Timing**: Shown after transcription completes, before next question

---

### **engines/followup_generator.py** (595 lines)
**Purpose**: Generate targeted follow-up questions after interruptions

**Responsibilities**:
- Route interruption reason to specific follow-up strategy
- Generate context-aware follow-up questions that:
  - Reference what candidate just said
  - Probe the specific weakness detected
  - Are brief and direct (1 sentence)
  - Maintain professional but firm tone
  - Push for specifics, not generalities
- Examples:
  - FALSE_CLAIM: "How can you verify that claim?"
  - DODGING_QUESTION: "Can you directly answer my question?"
  - VAGUE_ANSWER: "Can you give me a concrete example?"

---

### **engines/live_warning_generator.py** (230 lines)
**Purpose**: Generate non-interrupting warnings during recording

**Responsibilities**:
- Generate real-time warnings for behavioral issues (without interrupting)
- Prevent warning spam with cooldown system (10 seconds between same warnings)
- Generate warnings for:
  - Excessive pausing
  - Detected filler words
  - Off-topic drift
  - Going too long without clarity
- Display warnings as visual/audio cues
- Track warning frequency to identify patterns

---

### **engines/final_report.py** (604 lines)
**Purpose**: Generate comprehensive final interview report at session end

**Responsibilities**:
- Compile all answer evaluations into session summary
- Generate overall performance score (0-100)
- Break down performance by:
  - **Round**: HR vs Technical vs System Design scores
  - **Phase**: How performance evolved
  - **Dimension**: Technical Depth, Concept Accuracy, Structured Thinking, Communication, Confidence
- Create skill heatmap (radar chart data)
- Identify top 3 strengths and weaknesses with evidence
- List specific mistakes with corrections needed
- Recommend focus areas for improvement
- Suggest learning resources
- Provide "next steps" for interview prep
- Track session metadata (duration, interruption count, questions asked)

---

## 📦 Data Models

### **models/state_models.py** (426 lines)
**Purpose**: Define interview state, phases, and session management

**Responsibilities**:
- Define **InterviewPhase** enum (6 phases from resume deep dive to wrap-up)
- Define **RoundType** enum (HR, Technical, System Design)
- Define **SessionState** class:
  - Track session ID, user ID, start/end times
  - Current phase and round
  - Question history and answers
  - Overall scores
  - Interruption count
  - Interview metadata (resume used, duration)
- Define **RoundEvaluationState** (scores, feedback per round)
- Define **DEFAULT_PHASE_CONFIGS** (questions per phase, difficulty progression)
- Implement phase transitions and progression logic

---

### **models/evaluation_models.py** (432 lines)
**Purpose**: Define evaluation scoring models and criteria

**Responsibilities**:
- Define **5 Core Scoring Dimensions**:
  1. Technical Depth (0-100)
  2. Concept Accuracy (0-100)
  3. Structured Thinking (0-100)
  4. Communication Clarity (0-100)
  5. Confidence & Consistency (0-100)
- Define **EvaluationScore** class (dimension + evidence + confidence)
- Define **AnswerEvaluation** class (complete evaluation of one answer)
  - Scores across all dimensions
  - Text feedback
  - Strengths and weaknesses
  - Red flags
  - Verifiable claims extracted
- Define **FinalReport** class (comprehensive session report)
- Define **ScoringThresholds** (thresholds for performance levels)

---

### **models/interview_models.py**
**Purpose**: Define interview-specific data models

**Responsibilities**:
- Define **Question** model (question text, type, difficulty, round)
- Define **Answer** model (answer text, question ID, timestamp)
- Define **ExtractedClaim** model (claim text, type, verifiability)
- Define **ClaimType** enum (technical, metric, experience, achievement)
- Define **ClaimVerifiability** enum (verifiable, vague, suspicious, contradictory)

---

### **models/interruption_models.py** (131 lines)
**Purpose**: Define interruption-related data models

**Responsibilities**:
- Define **InterruptionReason** enum (false claim, contradiction, rambling, etc.)
- Define **SeverityLevel** enum (critical, high, medium, low)
- Define **ActionType** enum (interrupt, warn, none)
- Define **InterruptionDecision** class:
  - Should interrupt or not
  - Reason for decision
  - Severity level
  - Interruption phrase (what to say)
  - Suggested follow-up question
  - Timestamp
- Define **AudioMetrics** (pause data, filler words, volume)

---

## 📋 Prompt Templates

### **prompt_templates/evaluation_prompts.py**
**Purpose**: LLM prompts for evaluating answers on 5 dimensions

**Responsibilities**:
- Provide evaluation prompts for each round type (HR, Technical, System Design)
- Prompt structure includes:
  - Question and answer context
  - Evaluation criteria (technical depth, clarity, etc.)
  - Scoring format (JSON with dimension scores 0-100)
  - Evidence requirement (why this score)
- Parse LLM response into AnswerEvaluation object
- Handle partial responses gracefully

---

### **prompt_templates/interruption_prompts.py**
**Purpose**: LLM prompts for interruption detection and analysis

**Responsibilities**:
- Prompt for content analysis (rambling detection, vagueness detection)
- Prompt for contradiction detection
- Prompt for off-topic detection
- Prompt for question dodging detection
- Parse LLM response to extract interruption reason and confidence

---

### **prompt_templates/claim_prompts.py**
**Purpose**: LLM prompts for claim extraction and verification

**Responsibilities**:
- Prompt for claim extraction from answer
- Prompt for claim categorization (technical, metric, experience)
- Prompt for verifiability assessment
- Prompt for contradiction detection
- Prompt for verification question generation

---

## 🔌 Integrations

### **config/evaluation_config.py**
**Purpose**: Evaluation system configuration constants

**Responsibilities**:
- Define evaluation thresholds
- Define scoring weights for different criteria
- Define claim priority rules
- Define evaluation timeouts

---

---

# ⚛️ FRONTEND STRUCTURE

## Main Application

### **src/App.js** (198 lines)
**Purpose**: Root React component managing app-wide state and navigation

**Responsibilities**:
- Authentication state management (login/register/logout)
- Main screen routing:
  - Login/Register screens
  - Welcome screen
  - Resume upload flow
  - Interview main component
  - Session history
- User session persistence (localStorage)
- Token validation on app load
- Navigation between main sections

**Key States**:
- `isAuthenticated`: User login status
- `showInterview`: Currently in interview
- `showResumeUpload`: Upload resume
- `currentUser`: Logged-in user info

---

## Interview Components

### **src/Interview.js** (644 lines)
**Purpose**: Main interview component orchestrating the complete interview experience

**Responsibilities**:
- **Session Management**: Start session, track progress
- **Round Selection**: Allow user to choose interview type (HR, Technical, System Design)
- **Question Display**: Show current question and track progress
- **Audio Recording**: Integrate AudioRecorder component
- **Answer Submission**: Send recorded audio to backend
- **Real-time Feedback**: Display interruptions and warnings
- **Navigation**: Move between questions, end session
- **State management**: Track:
  - Current question and phase
  - Session ID
  - Round type
  - AI state (idle, listening, thinking, speaking)
  - Interruption data
  - Feedback display

**Integration Points**:
- Calls `/interview/start` to create session
- Calls `/interview/submit-answer` to evaluate answers
- Handles interruptions and live warnings
- Displays immediate feedback

---

### **src/AudioRecorder.js** (596 lines)
**Purpose**: Audio recording and real-time analysis component

**Responsibilities**:
- **Recording Control**: Start, stop, cancel recording
- **Audio Capture**: Use browser MediaRecorder API
- **Real-time Transcription**: Web Speech API for live transcript
- **Filler Word Detection**: Detect "um", "uh", "like" in real-time
- **Silence Detection**: Warn on excessive silence
- **Recording Metrics**:
  - Record time
  - Pause count
  - Filler word count
  - Volume levels
- **Audio Analysis**: Instantiate AudioAnalyzer for deep metrics
- **Transcription**: Send audio to backend for Whisper transcription
- **Processing States**: Show transcription progress

**Features**:
- Real-time feedback while recording
- Warning for excessive pauses
- Filler word detection and alerts
- Audio quality monitoring
- Ready state indicator

---

## Components

### **src/components/Login.js** (195 lines)
**Purpose**: User login form component

**Responsibilities**:
- Authentication form with username/password fields
- Form validation
- API call to `/auth/login` endpoint
- Token storage in localStorage
- Error handling and display
- Loading state during submission
- Navigation to register if user doesn't have account

---

### **src/components/Register.js**
**Purpose**: User registration form component

**Responsibilities**:
- Registration form with username, email, password fields
- Form validation (password confirmation, email format)
- API call to `/auth/register` endpoint
- Error handling for duplicate username/email
- Success message and redirect to login
- Loading state during submission

---

### **src/components/ResumeUpload.js**
**Purpose**: Resume file upload component

**Responsibilities**:
- File drag-and-drop zone or file picker
- Resume file validation (PDF, DOCX, TXT)
- File size validation
- Upload progress indicator
- API call to `/interview/upload-resume` endpoint
- Parse and display extracted resume content
- Confirmation before proceeding to interview

---

### **src/components/PersonaSelector.js**
**Purpose**: Interview round selection component

**Responsibilities**:
- Display 3 interview type options:
  1. HR Round (behavioral questions)
  2. Technical Round (technical questions)
  3. System Design Round (design questions)
- Description of each round
- Selection and confirmation
- Visual indicators (cards with icons)
- Difficulty/intensity indicators

---

### **src/components/FeedbackScreen.js**
**Purpose**: Display immediate feedback after answer submission

**Responsibilities**:
- Show quick score (0-10 scale)
- Display top 2 strengths identified
- Display top 2 improvement areas
- Show any red flags detected
- Display evidence/quotes from answer
- Show time on current screen (auto-advance after ~30 seconds)
- Styling with visual indicators (green for strengths, orange for improvements)

---

### **src/components/LiveWarning.js**
**Purpose**: Real-time warning display during recording

**Responsibilities**:
- Display non-interrupting warnings:
  - "You're pausing a lot"
  - "Filler words detected"
  - "Try to be more specific"
- Show warning message and icon
- Auto-dismiss after few seconds
- Queue multiple warnings if needed
- Styling to be visible but not alarming

---

### **src/components/InterruptionAlert.js**
**Purpose**: Display interruption alert when candidate is stopped

**Responsibilities**:
- Show interruption message (fromollama/LLM)
- Provide follow-up question
- Interrupt reason explanation
- Options:
  - Try again
  - Skip question
  - End interview
- Styling to indicate serious interruption (red, bold)
- Sound effect trigger

---

### **src/components/AIInterviewer.js**
**Purpose**: AI avatar/orb component showing AI state

**Responsibilities**:
- Animated AI avatar (visual representation)
- State indicators:
  - Idle: Waiting for answer
  - Listening: Recording user's voice
  - Thinking: Processing answer
  - Speaking: AI speaking introduction/feedback
- Visual feedback via animations
- Sound wave indicators for audio input
- Expression changes based on state

---

### **src/components/MiniAIOrb.js**
**Purpose**: Smaller version of AI avatar for corner display

**Responsibilities**:
- Compact AI avatar for smaller screens
- State indication via color/animation
- Show listening indicator
- Minimal UI footprint

---

### **src/components/SoundToggle.js**
**Purpose**: Toggle sound effects on/off

**Responsibilities**:
- Toggle button for sound effects
- Save preference to localStorage
- Icon indicating current state (muted/unmuted)
- Clean, accessible UI

---

### **src/components/UserMenu.js**
**Purpose**: User profile and navigation menu

**Responsibilities**:
- Display logged-in user name
- Navigation menu options:
  - View session history
  - Profile settings
  - Logout
- Logout functionality
- User avatar/initial display

---

### **src/components/SessionHistory.js**
**Purpose**: Display past interview sessions

**Responsibilities**:
- Fetch user's session history from backend
- Display session list with:
  - Date and time
  - Round type (HR/Technical/System Design)
  - Overall score
  - Duration
- Click to view session details
- Filter by round type or date
- Delete old sessions

---

### **src/components/SessionDetail.js**
**Purpose**: Detailed view of a completed interview session

**Responsibilities**:
- Display final report:
  - Overall score and breakdown by round
  - Skill assessment radar chart
  - Strengths and weaknesses
- List all questions and answers
- Show score for each answer
- Display feedback for problematic answers
- Export/share report option
- Navigation back to history

---

### **src/components/WelcomeScreen.js**
**Purpose**: Landing page shown to authenticated user

**Responsibilities**:
- Greeting with user's name
- Brief explanation of interview system
- Action buttons:
  - "Start New Interview" (resume upload)
  - "View Past Sessions"
  - "Practice (no resume)"
- Display tips or motivation
- Visual design and animations

---

### **src/components/VoiceControls.js**
**Purpose**: Voice control interface component

**Responsibilities**:
- Visual display of recording controls
- Microphone permission request handling
- Voice button indicators
- Recording time display
- Cancel/submit buttons for recording

---

## Utilities

### **src/utils/apiUtils.js** (207 lines)
**Purpose**: Helper functions for authenticated API calls

**Responsibilities**:
- `getAuthHeaders()`: Get headers with bearer token
- `apiGet()`: Make authenticated GET request
- `apiPost()`: Make authenticated POST request with JSON
- `apiPostFormData()`: Make POST with file uploads
- `apiDelete()`: Make authenticated DELETE request
- Error handling for 401 (expired token)
- Automatic token refresh if needed
- Default API base URL

**Example Usage**:
```javascript
const response = await apiPost('/interview/submit-answer', {
  answer: transcript,
  questionId: 123
});
```

---

### **src/utils/audioAnalyzer.js** (255 lines)
**Purpose**: Real-time audio analysis without needing transcript

**Responsibilities**:
- Create audio context and analyzer from MediaRecorder
- Analyze audio frequency/volume patterns
- **Pause Detection**:
  - Track silence duration
  - Identify "long pauses" (>2 seconds)
  - Count excessive pauses (>3 seconds)
- **Sound Segment Analysis**:
  - Track speaking vs silence segments
  - Calculate ratio of actual speaking time
- **Volume Monitoring**:
  - Track volume history
  - Detect unusual volume drops
- **Metrics Generation**: Return object with:
  - Pause count
  - Total pause duration
  - Average pause duration
  - Long pause count
  - Volume statistics
- Used by AudioRecorder for real-time detection

---

### **src/utils/soundEffects.js**
**Purpose**: Sound effect management for user feedback

**Responsibilities**:
- Provide methods to play different sound effects:
  - Start recording "beep"
  - Stop recording "beep"
  - Interruption alert (warning sound)
  - Success/celebration sound
  - Error sound
  - Filler word detection beep
- Respect user's sound toggle preference
- Handle browser audio permissions
- Preload audio files for low latency

---

### **src/utils/voiceService.js**
**Purpose**: Text-to-speech service for AI responses

**Responsibilities**:
- Convert text to speech for AI interviewer responses
- Use browser Web Speech API
- Speaking rate, pitch, volume control
- Handle voice selection
- Start/stop/pause speech
- Voice readiness state
- Used when AI needs to ask questions or give feedback

---

## App Styling

### **src/App.css**
**Purpose**: Global styles for main App component

**Responsibilities**:
- Layout structure
- Navigation styling
- Responsive design
- Color scheme
- Typography
- Global animations

---

### **src/Interview.css**
**Purpose**: Styles for Interview component

**Responsibilities**:
- Interview layout and positioning
- Question display styling
- Progress indicator
- Audio recorder positioning
- Feedback screen styling
- Animation keyframes

---

### **src/AudioRecorder.css**
**Purpose**: Styles for audio recording component

**Responsibilities**:
- Recording button styling
- Recording indicator animation
- Timer display
- Microphone icon states
- Recording controls layout
- Waveform visualization (if applicable)

---

### Component CSS Files
Each component has a corresponding `.css` file:

- **Auth.css**: Login/Register form styling
- **PersonaSelector.css**: Round selection cards
- **FeedbackScreen.css**: Feedback display
- **LiveWarning.css**: Warning alert styling
- **InterruptionAlert.css**: Interruption modal
- **SessionHistory.css**: Session list styling
- **SessionDetail.css**: Report visualization
- **SoundToggle.css**: Toggle button styling
- **MiniAIOrb.css**: Compact AI avatar styling
- **VoiceControls.css**: Control interface styling
- **RecoveryCurveChart.css**: Performance curve chart

---

## Package Configuration

### **package.json**
**Purpose**: Node.js/npm project configuration

**Responsibilities**:
- List of npm dependencies:
  - react, react-dom: Core React library
  - framer-motion: Animation library
  - axios: HTTP client (alternative to fetch)
  - Chart.js / react-chartjs-2: Charts for reports
  - Testing libraries: jest, @testing-library/react
- Scripts:
  - `npm start`: Start development server
  - `npm build`: Production build
  - `npm test`: Run tests
- Project metadata (name, version, license)
- Development settings

---

# 📁 CONFIGURATION FILES

### **.env** (Environment Variables)
**Purpose**: Store sensitive configuration not committed to git

**Variables**:
- `LLM_PROVIDER`: Which LLM to use (ollama or openai)
- `OPENAI_API_KEY`: OpenAI API key (if using OpenAI)
- `OLLAMA_BASE_URL`: Ollama server URL (default: http://localhost:11434/v1)
- `DATABASE_URL`: Database connection string
- `JWT_SECRET_KEY`: Secret for JWT token signing
- `FRONTEND_URL`: Frontend URL (for CORS)

**Example**:
```
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
JWT_SECRET_KEY=your-secret-key-here
```

---

### **requirements.txt** (Python Dependencies)
**Purpose**: List Python packages for pip installation

**Key Packages**:
- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `pydantic`: Data validation
- `openai`: LLM API client
- `whisper`: Speech-to-text
- `python-jose`: JWT handling
- `passlib`: Password hashing
- `PyPDF2`: PDF parsing
- `python-docx`: DOCX parsing
- `sqlite3`: Database (built-in)

**Usage**: `pip install -r requirements.txt`

---

### **setup.md**
**Purpose**: Installation and setup instructions

**Covers**:
- System prerequisites (Node.js, Python, Ollama)
- Backend setup (venv, dependencies, config)
- Frontend setup (npm install)
- Database initialization
- Running the server locally
- Troubleshooting common issues

---

### **readme.md**
**Purpose**: Project overview and quick start guide

**Contains**:
- Project description
- Features overview
- Tech stack
- Prerequisites
- Quick start commands
- Project structure
- Contributing guidelines
- License

---

---

# 🧪 TESTING & VALIDATION

### **test_whisper.py**
**Purpose**: Test Whisper audio transcription functionality

**Tests**:
- Load Whisper model successfully
- Transcribe sample audio files
- Handle missing files gracefully
- Return properly formatted transcription

---

### **test_intelligent_interruptions.py**
**Purpose**: Test interruption detection system

**Tests**:
- Multilaer interruption detection
- Claim extraction accuracy
- Contradiction detection
- Severity level assignment
- Interruption phrase generation

---

### **test_STANDALONE.py**
**Purpose**: Standalone integration test

**Tests**:
- Full interview flow simulation
- End-to-end backend integration
- Database operations
- Response format validation

---

### **validate_integration.py**
**Purpose**: Validate backend integration

**Tests**:
- All components can be imported
- LLM service works
- Database initializes
- Required models exist
- API endpoints are defined

---

# 📊 BACKUP & LEGACY

### **backup_old_system/**
**Purpose**: Archive of previous system implementation

**Contains**:
- Old interview engine (`interview_engine.py`)
- Old interruption analyzer (`interruption_analyzer_OLD.py`)
- Old pressure engine (`pressure_engine.py`)
- Previous main.py version

**Status**: Deprecated (kept for reference only)

---

---

# 🔑 KEY DATA FLOWS

## 1. **User Registration Flow**
1. User fills registration form in `Login.js`
2. Form submitted to `/auth/register` endpoint in `main.py`
3. `auth_endpoints.py` router handles request
4. `auth_database.py` creates user record
5. Response sent back to frontend
6. User redirected to login

---

## 2. **Interview Session Flow**
1. User uploads resume via `ResumeUpload.js`
2. Resume sent to `/interview/upload-resume` endpoint
3. `resume_parser.py` extracts text
4. `resume_question_generator.py` generates questions
5. User selects round type via `PersonaSelector.js`
6. `/interview/start` creates session via `interview_orchestrator.py`
7. First question loaded and displayed
8. User records answer via `AudioRecorder.js`
9. Audio sent to backend along with session/question ID
10. Backend transcribes with `whisper_service.py`
11. `answer_analyzer.py` evaluates via appropriate round evaluator
12. Check for interruptions via `interruption_analyzer.py`
13. Generate immediate feedback via `immediate_feedback.py`
14. Return evaluation to frontend
15. Display feedback via `FeedbackScreen.js`
16. Process repeats for next question

---

## 3. **Interruption Flow**
1. Answer submitted to backend
2. `interruption_analyzer.py` analyzes answer for triggers
3. Multi-layer detection (audio, content, context, behavioral)
4. `interruption_decision.py` makes final decision
5. If interrupt, generate interruption phrase and follow-up
6. Return interruption data to frontend
7. `InterruptionAlert.js` displays interruption message
8. User can retry, skip, or end
9. `followup_generator.py` generates tailored follow-up question if retry

---

## 4. **Session Report Flow**
1. Interview ends (all rounds/phases complete)
2. `final_report.py` compiles all scores and feedback
3. Generates overall score, dimension breakdown, heatmap
4. Identifies top strengths/weaknesses with evidence
5. Recommends focus areas
6. Saves report to database
7. Return report to frontend
8. `SessionDetail.js` displays final report
9. User can view charts, download, or start new session

---

---

# 📈 DATA MODELS OVERVIEW

## Session State Flow
```
Interview Start
    ↓
Phase 1: Resume Deep Dive (2-3 Q)
    ↓
Phase 2: Core Skill Assessment (3-4 Q)
    ↓
Phase 3: Scenario/Problem Solving (2-3 Q)
    ↓
Phase 4: Stress/Edge Case Testing (1-2 Q)
    ↓
Phase 5: Claim Verification (adaptive)
    ↓
Phase 6: Wrap-up (1 Q)
    ↓
Generate Final Report
    ↓
Interview Complete
```

## Answer Evaluation Lifecycle
```
Answer Text Received
    ↓
Speech-to-Text (Whisper)
    ↓
Claim Extraction
    ↓
Route to Round Evaluator (HR/Tech/SysDesign)
    ↓
Score on 5 Dimensions (0-100 each)
    ↓
Interruption Analysis (should we stop?)
    ↓
Generate Immediate Feedback
    ↓
Return to Frontend
    ↓
Display Feedback & Move to Next Q
```

---

# 🎯 EVALUATION DIMENSIONS (5 Core Metrics)

1. **Technical Depth (0-100)**
   - How much technical knowledge demonstrated
   - Depth vs surface-level understanding
   - Industry Knowledge specificity

2. **Concept Accuracy (0-100)**
   - Correctness of stated concepts
   - No misconceptions
   - Proper terminology usage

3. **Structured Thinking (0-100)**
   - STAR method application
   - Logical flow and organization
   - Breaking complex problems down

4. **Communication Clarity (0-100)**
   - Articulation quality
   - Easy to follow
   - Appropriate pace and depth

5. **Confidence & Consistency (0-100)**
   - Tone and conviction
   - No contradictions
   - Consistency with previous answers

---

---

# 🚀 DEVELOPMENT NOTES

## To Add a New Feature
1. Define data model in `/backend/models/`
2. Add backend logic in appropriate engine or service
3. Add API endpoint in `main.py`
4. Create frontend component/utility in `/frontend/src/`
5. Connect component to backend via `apiUtils.js`
6. Test with provided test files

## To Modify Evaluation Criteria
1. Update 5 dimensions in evaluation prompts
2. Modify scoring weights in `evaluation_config.py`  
3. Update evaluator classes in `round_evaluators/`
4. Adjust thresholds for interruptions
5. Run tests to verify changes

## LLM Provider Switch
Change in `config.py`:
- Set `LLM_PROVIDER = "openai"` or `"ollama"`
- Configure appropriate API key/URL
- All LLM calls automatically use selected provider

---

---

# 📞 COMPONENT COMMUNICATION MAP

```
Frontend (React)
    ├─ App.js (root)
    ├─ Interview.js (main interview orchestrator)
    │   ├─ AudioRecorder.js (captures audio)
    │   ├─ FeedbackScreen.js (shows feedback)
    │   ├─ InterruptionAlert.js (shows interruptions)
    │   ├─ LiveWarning.js (non-interrupting warnings)
    │   └─ PersonaSelector.js (round selection)
    ├─ Login.js / Register.js (authentication)
    ├─ ResumeUpload.js (resume upload)
    ├─ SessionHistory.js (past sessions)
    └─ SessionDetail.js (view results)
            ↓ HTTP/JSON (apiUtils.js)
Backend (Python FastAPI)
    └─ main.py (API)
        ├─ auth_endpoints.py (auth routes)
        ├─ interview_orchestrator.py (session management)
        ├─ answer_analyzer.py (evaluation routing)
        ├─ whisper_service.py (transcription)
        ├─ resume_parser.py (resume parsing)
        ├─ llm_service.py (LLM queries)
        ├─ interruption_analyzer.py (interruption detection)
        └─ database.py (data persistence)
```

---

This completes the comprehensive project structure documentation for InternAI. Each file serves a specific purpose in creating an intelligent interview simulation system.
