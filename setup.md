# 🚀 InternAI - Quick Setup Guide

**Time to complete:** 15-20 minutes  
**Skill level:** Beginner-friendly

---

## ✅ Pre-Setup Checklist

Before you begin, download and install these:

- [ ] **Node.js** (v16+) → https://nodejs.org/
- [ ] **Python** (v3.8+) → https://www.python.org/
- [ ] **Ollama** → https://ollama.com/download
- [ ] **Git** → https://git-scm.com/

---

## 📥 Step 1: Get the Code

```bash
# Clone the repository
git clone https://github.com/yourusername/InternAI.git

# Navigate into the project
cd InternAI
```

---

## 🐍 Step 2: Backend Setup (Python)

### 2.1 Create Virtual Environment

**Windows:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

✅ You should see `(venv)` in your terminal

### 2.2 Install Dependencies

```bash
pip install -r requirements.txt
```

⏳ This takes 2-5 minutes

### 2.3 Create Required Folders

**Windows:**
```bash
mkdir audio_uploads
```

**macOS/Linux:**
```bash
mkdir -p audio_uploads
```

### 2.4 Setup Environment Variables

```bash
# Copy the template
copy .env.example .env    # Windows
# cp .env.example .env    # macOS/Linux
```

**Edit `.env` file:**
```env
LLM_PROVIDER=ollama
```

Save and close.

---

## 🤖 Step 3: Setup Ollama (AI Brain)

### 3.1 Install Llama3 Model

```bash
ollama pull llama3
```

⏳ This downloads ~4.7 GB (takes 5-15 minutes depending on internet)

### 3.2 Verify Installation

```bash
ollama list
```

✅ Should show:
```
NAME             ID              SIZE      MODIFIED
llama3:latest    365c0bd3c000    4.7 GB    ...
```

### 3.3 Start Ollama

**Option A: Desktop App (Recommended)**
- Launch Ollama from Start Menu (Windows) or Applications (Mac)
- It runs in background

**Option B: Command Line**
```bash
ollama serve
```
Keep this terminal open!

---

## 🧪 Step 4: Test Backend

### 4.1 Test LLM Connection

```bash
python llm_service.py
```

✅ **Expected Output:**
```
==================================================
LLM SERVICE TEST
==================================================
✅ LLM Provider: ollama
   Model: llama3
🤖 Calling ollama (llama3)...
✅ LLM Response: Hello, InternAI is working!
✅ Test successful!
```

❌ **If it fails:** Make sure Ollama is running (`ollama serve`)

### 4.2 Start Backend Server

```bash
uvicorn main:app --reload
```

✅ **Expected Output:**
```
✅ LLM Provider: ollama
   Model: llama3
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### 4.3 Test in Browser

Open: **http://localhost:8000/test/llm**

✅ Should see JSON:
```json
{"success": true, "message": "Success! ollama is working..."}
```

🎉 **Backend is working!**

---

## ⚛️ Step 5: Frontend Setup (React)

**Open a NEW terminal** (keep backend running)

### 5.1 Navigate to Frontend

```bash
cd frontend
```

### 5.2 Install Dependencies

```bash
npm install
```

⏳ This takes 2-5 minutes

### 5.3 Start Frontend

```bash
npm start
```

✅ **Expected:**
- Browser opens automatically
- Shows: http://localhost:3000
- You see "Ready to Begin?" screen

---

## 🎯 Step 6: First Interview Test

### Test the Full Flow

1. **Click "Start Interview"**
   - AI generates opening question
   - Backend terminal shows: `🤖 Calling ollama...`

2. **Click "Start Recording"**
   - Browser asks for microphone permission
   - **Click "Allow"**

3. **Speak for 5-10 seconds**
   - Say: "My name is [Name], I'm a software developer..."

4. **Click "Stop Recording"**
   - Audio player appears
   - Transcription happens automatically

5. **Wait for transcript**
   - Shows: "📝 What I heard: [your words]"

6. **Click "Submit Answer"**
   - AI generates next question
   - Question relates to your answer!

7. **Repeat 4 more times**
   - Interview has 5 questions total
   - Notice how AI adapts to your answers

✅ **Success!** InternAI is fully working!

---

## 🎛️ Quick Commands Reference

### Start Everything (Daily Use)

**Terminal 1 - Backend:**
```bash
cd backend
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
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

### Stop Everything

- Backend: `Ctrl + C` in terminal
- Frontend: `Ctrl + C` in terminal
- Ollama: Close desktop app or `Ctrl + C`

---

## 🐛 Common Issues & Fixes

### ❌ "Cannot connect to Ollama"

**Fix:**
```bash
ollama serve
# Or launch Ollama desktop app
```

### ❌ "Microphone permission denied"

**Fix:**
1. Click camera/mic icon in browser address bar
2. Allow microphone
3. Refresh page (`F5`)

### ❌ "Module not found"

**Fix:**
```bash
cd backend
venv\Scripts\activate
pip install -r requirements.txt
```

### ❌ "Port 8000 already in use"

**Fix:**
```bash
# Kill the process
netstat -ano | findstr :8000  # Windows
lsof -ti:8000 | xargs kill -9 # macOS/Linux

# Or use different port
uvicorn main:app --reload --port 8001
```

### ❌ Transcription is slow

**Explanation:** Whisper uses CPU by default (normal without GPU)

**Fix:** Just wait, it works! (10-30 seconds)

---

## 🎓 Next Steps

Once everything works:

1. **Try different answers** - see how AI adapts
2. **Start multiple interviews** - notice question variety
3. **Read README.md** - learn about all features
4. **Check project structure** - understand the code

---

## 📞 Need Help?

1. Re-read this guide carefully
2. Check the troubleshooting section
3. Open an issue on GitHub with:
   - Full error message
   - Steps you followed
   - Your OS and versions

---

## ✅ Setup Complete!

You now have:
- ✅ Voice recording working
- ✅ Speech-to-text working
- ✅ AI interviewer working
- ✅ Full interview flow working

**Welcome to InternAI! 🎉**

Ready to train under pressure? Start interviewing!

---

**Next Phase:** Phase 5 adds timed interruptions and pressure injection! 🚀