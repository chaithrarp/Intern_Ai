# 🎯 InternAI - AI-Powered Mock Interview System

**Transform interview preparation into continuous, high-pressure training.**

InternAI is an intelligent behavioral conditioning system that delivers short, adaptive interview sessions with real-time pressure simulation. We don't train answers — we train **performance under pressure**.

---

## 🌟 Features (Current: Phase 4)

✅ **Voice-Powered Interviews** - Speak your answers naturally  
✅ **AI Interviewer** - Dynamic questions that adapt to your responses  
✅ **Speech-to-Text** - Powered by OpenAI Whisper  
✅ **Context Memory** - AI remembers your entire conversation  
✅ **Professional Behavior** - STAR method behavioral interviewing  
✅ **Flexible LLM Support** - Works with Ollama (free) or OpenAI (paid)

🚧 **Coming Soon** (Phase 5+):
- Timed interruptions during answers
- Mid-answer pressure injection
- Behavioral metrics tracking
- Performance feedback and trends

---

## 🏗️ Tech Stack

- **Frontend:** React (Web)
- **Backend:** Python + FastAPI
- **Speech-to-Text:** OpenAI Whisper
- **AI Interviewer:** LLM (Ollama or OpenAI)
- **Database:** SQLite (planned)

---

## 📋 Prerequisites

Before you start, make sure you have these installed:

### Required Software

| Software | Version | Download Link |
|----------|---------|---------------|
| **Node.js** | v16+ | https://nodejs.org/ |
| **Python** | v3.8+ | https://www.python.org/ |
| **Ollama** | Latest | https://ollama.com/download |

### Verify Installations

```bash
# Check Node.js
node --version
# Expected: v16.0.0 or higher

# Check npm
npm --version
# Expected: 8.0.0 or higher

# Check Python
python --version
# Expected: Python 3.8.0 or higher

# Check pip
pip --version
# Expected: pip 20.0.0 or higher

# Check Ollama
ollama --version
# Expected: ollama version is 0.x.x
```

---

## 🚀 Installation Guide

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/InternAI.git
cd InternAI
```

### Step 2: Backend Setup

#### 2.1 Navigate to Backend

```bash
cd backend
```

#### 2.2 Create Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

#### 2.3 Install Python Dependencies

```bash
pip install fastapi uvicorn python-multipart openai python-dotenv openai-whisper torch
```

**Note:** If you're on a system without GPU, Whisper will use CPU (slower but works).

#### 2.4 Create Audio Upload Directory

```bash
# Windows
mkdir audio_uploads

# macOS/Linux
mkdir -p audio_uploads
```

#### 2.5 Set Up Ollama

**Install Ollama Model:**
```bash
ollama pull llama3
```

**Start Ollama Server:**

**Option A: Using Command (keeps terminal occupied)**
```bash
ollama serve
```

**Option B: Using Desktop App (Recommended for Windows)**
1. Search "Ollama" in Start Menu
2. Click to launch
3. Ollama will run in background (system tray)

**Verify Ollama is Running:**
```bash
ollama list
```

Expected output:
```
NAME             ID              SIZE      MODIFIED
llama3:latest    365c0bd3c000    4.7 GB    X months ago
```

#### 2.6 Configure Environment Variables

**Create `.env` file in `backend/` folder:**

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

**Edit `.env` file:**

Open `.env` in a text editor and add:

```env
LLM_PROVIDER=ollama
```

**Optional: If using OpenAI instead:**
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-your-actual-api-key-here
```

> **Getting OpenAI API Key:**
> 1. Go to https://platform.openai.com/api-keys
> 2. Sign up / Log in
> 3. Click "Create new secret key"
> 4. Copy the key to `.env` file

#### 2.7 Test Backend Setup

**Test LLM Connection:**
```bash
python llm_service.py
```

**Expected Output:**
```
==================================================
LLM SERVICE TEST
==================================================
✅ LLM Provider: ollama
   Model: llama3
🤖 Calling ollama (llama3)...
✅ LLM Response: Hello, InternAI is working!
✅ Test successful! Response: Hello, InternAI is working!

Success! ollama is working. Response: Hello, InternAI is working!
```

**Start Backend Server:**
```bash
uvicorn main:app --reload
```

**Expected Output:**
```
✅ LLM Provider: ollama
   Model: llama3
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Application startup complete.
```

**Test in Browser:**

Open: `http://localhost:8000/test/llm`

Expected JSON response:
```json
{
  "success": true,
  "message": "Success! ollama is working. Response: Hello, InternAI is working!"
}
```

---

### Step 3: Frontend Setup

**Open a NEW terminal** (keep backend running).

#### 3.1 Navigate to Frontend

```bash
cd frontend
```

#### 3.2 Install Dependencies

```bash
npm install
```

This will install:
- React
- Framer Motion (animations)
- And other dependencies from `package.json`

#### 3.3 Start Frontend

```bash
npm start
```

**Expected Output:**
```
Compiled successfully!

You can now view internai-frontend in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000
```

**Browser should automatically open:** `http://localhost:3000`

---

## 🧪 Testing the Application

### Test 1: Basic Connectivity

1. **Frontend loads** at `http://localhost:3000`
2. **Click "Start Interview"**
3. **Expected:** You see a question from the AI interviewer

### Test 2: Voice Recording

1. **Click "Start Recording"**
2. **Allow microphone access** when browser asks
3. **Speak for 5-10 seconds**
4. **Click "Stop Recording"**
5. **Expected:** Audio player appears with your recording

### Test 3: Speech-to-Text

1. **After recording**, wait for transcription
2. **Expected:** "📝 What I heard:" section shows your transcribed text
3. **Verify:** Transcript is accurate

### Test 4: AI Interview Flow

1. **Click "Submit Answer"**
2. **Watch backend terminal** - should see:
   ```
   🤖 Calling ollama (llama3)...
   ✅ LLM Response: [Next question]
   ```
3. **Expected:** Next question appears, related to your previous answer
4. **Repeat** for 5 questions total
5. **Expected:** Interview completes after 5 questions

### Test 5: Context Memory

1. **Answer question 1** - mention something specific (e.g., "I worked on React projects")
2. **Question 2** should reference your answer (e.g., "Tell me about one of those React projects")
3. **Verify:** Questions adapt to your responses

---

## 📁 Project Structure

```
InternAI/
│
├── backend/                    # Python FastAPI backend
│   ├── main.py                 # FastAPI routes
│   ├── config.py               # LLM configuration
│   ├── llm_service.py          # LLM abstraction layer
│   ├── interview_engine.py     # AI interview logic
│   ├── prompts.py              # Interview prompts
│   ├── whisper_service.py      # Speech-to-text
│   ├── interview_data.py       # Fallback questions
│   ├── .env                    # Environment variables (DO NOT COMMIT)
│   ├── .env.example            # Template for .env
│   ├── audio_uploads/          # Recorded audio files
│   └── requirements.txt        # Python dependencies (optional)
│
└── frontend/                   # React frontend
    ├── public/
    │   └── index.html
    ├── src/
    │   ├── App.js              # Main app component
    │   ├── Interview.js        # Interview screen
    │   ├── AudioRecorder.js    # Voice recording component
    │   └── components/
    │       ├── WelcomeScreen.js
    │       ├── MiniAIOrb.js    # AI status indicator
    │       └── AIInterviewer.js
    ├── package.json            # Node dependencies
    └── README.md
```

---

## ⚙️ Configuration

### Switch Between LLM Providers

Edit `backend/.env`:

**Use Ollama (Free, Local):**
```env
LLM_PROVIDER=ollama
```

**Use OpenAI (Paid, Cloud):**
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-your-key-here
```

### Adjust Interview Settings

Edit `backend/config.py`:

```python
# Number of questions per interview
MAX_QUESTIONS_PER_SESSION = 5

# LLM creativity (0.0 = deterministic, 1.0 = creative)
OLLAMA_TEMPERATURE = 0.7
OPENAI_TEMPERATURE = 0.7

# Max words per AI response
OLLAMA_MAX_TOKENS = 300
OPENAI_MAX_TOKENS = 300
```

---

## 🐛 Troubleshooting

### ❌ Issue: "Cannot connect to Ollama"

**Symptoms:**
```
❌ LLM Error: Connection refused
Cannot connect to Ollama
```

**Solutions:**

1. **Check if Ollama is running:**
   ```bash
   ollama list
   ```
   
2. **Start Ollama:**
   ```bash
   ollama serve
   ```
   Or launch Ollama desktop app

3. **Verify model is installed:**
   ```bash
   ollama pull llama3
   ```

---

### ❌ Issue: "Microphone permission denied"

**Symptoms:**
- Browser blocks microphone access
- No recording happens

**Solutions:**

1. **Click the camera/mic icon** in browser address bar
2. **Allow microphone access**
3. **Refresh the page** (`Ctrl+R` or `Cmd+R`)

**Chrome:** Settings → Privacy & Security → Site Settings → Microphone

**Edge:** Settings → Cookies and site permissions → Microphone

---

### ❌ Issue: "Module not found" errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'openai'
```

**Solutions:**

1. **Activate virtual environment:**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

2. **Reinstall dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
   Or manually:
   ```bash
   pip install fastapi uvicorn python-multipart openai python-dotenv openai-whisper torch
   ```

---

### ❌ Issue: "Port already in use"

**Symptoms:**
```
Error: listen tcp 127.0.0.1:8000: bind: address already in use
```

**Solutions:**

1. **Kill existing process:**
   ```bash
   # Windows
   netstat -ano | findstr :8000
   taskkill /PID <process_id> /F
   
   # macOS/Linux
   lsof -ti:8000 | xargs kill -9
   ```

2. **Use different port:**
   ```bash
   uvicorn main:app --reload --port 8001
   ```
   
   Then update frontend API calls to `http://localhost:8001`

---

### ❌ Issue: "Whisper is very slow"

**Symptoms:**
- Transcription takes 30+ seconds
- CPU usage is high

**Explanation:**
Whisper runs on CPU by default. This is normal without a GPU.

**Solutions:**

1. **Use smaller Whisper model** (edit `whisper_service.py`):
   ```python
   model = whisper.load_model("tiny")  # Faster, less accurate
   # or
   model = whisper.load_model("base")  # Balance
   ```

2. **Get a GPU** (NVIDIA) and install CUDA support

3. **Use cloud Whisper API** (future enhancement)

---

### ❌ Issue: "OpenAI API key invalid"

**Symptoms:**
```
Error code: 401 - Invalid API key
```

**Solutions:**

1. **Check `.env` file format:**
   ```env
   OPENAI_API_KEY=sk-proj-your-key-here
   ```
   No spaces, no quotes, no comments

2. **Verify key is valid:**
   - Go to https://platform.openai.com/api-keys
   - Check key status

3. **Switch to Ollama:**
   ```env
   LLM_PROVIDER=ollama
   ```

---

### ❌ Issue: ".env file not loading"

**Symptoms:**
```
⚠️ WARNING: LLM_PROVIDER is 'openai' but OPENAI_API_KEY is not set!
```

**Solutions:**

1. **Check file location:**
   - `.env` must be in `backend/` folder (same level as `main.py`)

2. **Check file name:**
   - Must be exactly `.env` (with the dot, no extension)
   - NOT `env.txt` or `.env.txt`

3. **Restart backend:**
   ```bash
   # Stop with Ctrl+C
   uvicorn main:app --reload
   ```

---

## 🔐 Security Best Practices

### Never Commit Sensitive Files

Make sure these are in `.gitignore`:

```gitignore
# Environment variables
.env

# Virtual environment
venv/
env/

# Audio files
audio_uploads/

# Python cache
__pycache__/
*.pyc

# Node modules
node_modules/

# OS files
.DS_Store
Thumbs.db
```

### API Key Safety

- ❌ Never commit `.env` to git
- ✅ Only commit `.env.example`
- ✅ Share API keys securely (encrypted)
- ✅ Rotate keys if exposed

---

## 📊 API Endpoints Reference

### Backend API (http://localhost:8000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/test/llm` | GET | Test LLM connection |
| `/interview/start` | POST | Start new interview |
| `/interview/answer` | POST | Submit answer, get next question |
| `/interview/upload-audio` | POST | Upload audio for transcription |
| `/interview/session/{id}` | GET | Get session data (debug) |

### Example API Calls

**Start Interview:**
```bash
curl -X POST http://localhost:8000/interview/start
```

**Get Session Data:**
```bash
curl http://localhost:8000/interview/session/session_1
```

---

## 🎯 Development Workflow

### Daily Development

**Terminal 1 - Backend:**
```bash
cd backend
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
uvicorn main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

**Terminal 3 - Ollama (if not using desktop app):**
```bash
ollama serve
```

### Testing Changes

1. **Backend changes:** Auto-reload enabled (`--reload` flag)
2. **Frontend changes:** Auto-refresh in browser
3. **LLM changes:** Restart backend

---

## 📚 How It Works

### Interview Flow

```
1. User clicks "Start Interview"
   ↓
2. Backend generates first AI question
   ↓
3. Frontend displays question
   ↓
4. User clicks "Start Recording"
   ↓
5. Browser captures audio
   ↓
6. User clicks "Stop Recording"
   ↓
7. Audio sent to backend
   ↓
8. Whisper transcribes audio → text
   ↓
9. Transcript sent to interview engine
   ↓
10. Interview engine builds context:
    - System prompt (how to behave)
    - Previous questions
    - Previous answers
   ↓
11. LLM generates next question based on context
   ↓
12. Question sent to frontend
   ↓
13. Repeat steps 4-12 for 5 questions
   ↓
14. Interview complete!
```

### AI Intelligence

The AI interviewer:

- **Remembers** everything you said
- **Adapts** questions to your answers
- **Probes** deeper when you're vague
- **Follows** STAR method (Situation, Task, Action, Result)
- **Maintains** professional tone

---

## 🚧 Current Limitations

- **No persistence:** Sessions lost on backend restart (Phase 7 will add database)
- **No metrics:** Can't track pauses, filler words yet (Phase 6)
- **No pressure:** AI is polite, no interruptions (Phase 5)
- **No feedback:** No post-interview analysis (Phase 7)

---

## 🗺️ Roadmap

```
✅ Phase 0 - Environment Setup
✅ Phase 1 - Basic Interview Flow
✅ Phase 2 - Voice Capture
✅ Phase 3 - Speech-to-Text (Whisper)
✅ Phase 4 - AI Interviewer

🚧 Phase 5 - Interruptions & Pressure (Next)
⏳ Phase 6 - Behavioral Metrics
⏳ Phase 7 - Feedback & Session History
⏳ Phase 8 - Polish & WOW Factors
```

---

## 🤝 Contributing

We welcome contributions! Here's how:

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/amazing-feature`
3. **Commit changes:** `git commit -m 'Add amazing feature'`
4. **Push to branch:** `git push origin feature/amazing-feature`
5. **Open a Pull Request**

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 💬 Support

Having issues? Here's how to get help:

1. **Check Troubleshooting section** above
2. **Search existing issues** on GitHub
3. **Open a new issue** with:
   - Error message (full text)
   - Steps to reproduce
   - Your OS and versions
   - Terminal output

---

## 👥 Team

**Project Lead:** [Your Name]  
**Contributors:** [List contributors]

---

## 🙏 Acknowledgments

- **OpenAI Whisper** - Speech recognition
- **Ollama** - Local LLM inference
- **FastAPI** - Modern Python web framework
- **React** - Frontend framework
- **Framer Motion** - Animations

---

## 📖 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Ollama Documentation](https://ollama.com/docs)
- [Whisper Documentation](https://github.com/openai/whisper)
- [React Documentation](https://react.dev/)

---

**Built with ❤️ for better interview preparation**

🚀 **Ready to train under pressure? Let's begin!**