<<<<<<< Updated upstream
import React, { useState } from 'react';
=======
import React, { useState, useRef, useEffect, useCallback } from 'react';
>>>>>>> Stashed changes
import { motion, AnimatePresence } from 'framer-motion';
import './Interview.css';
import AudioRecorder from './AudioRecorder';
import MiniAIOrb from './components/MiniAIOrb';
import InterruptionAlert from './InterruptionAlert';
import FeedbackScreen from './components/FeedbackScreen';
import SessionHistory from './components/SessionHistory';
import SessionDetail from './components/SessionDetail';
import PersonaSelector from './components/PersonaSelector';
import VoiceControls from './components/VoiceControls';
import soundEffects from './utils/soundEffects';
import voiceService from './utils/voiceService';
import { useEffect } from "react";

<<<<<<< Updated upstream
// ← ADD PROPS HERE
function Interview({ resumeData, onBack }) {
=======
/**
 * Interview Component - OPTIMIZED FOR SPEED
 *
 * KEY CHANGE: Next question arrives in the /interview/answer response
 * and is stored immediately. When feedback closes it appears instantly —
 * no extra API call, no extra Ollama round-trip.
 */
function Interview({ resumeData, onBack, onViewHistory }) {
  // Session State
>>>>>>> Stashed changes
  const [sessionId, setSessionId] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [questionNumber, setQuestionNumber] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const [loading, setLoading] = useState(false);
  const [aiState, setAiState] = useState('idle'); // idle, listening, thinking, speaking
  const [showHistory, setShowHistory] = useState(false);
  const [selectedSessionId, setSelectedSessionId] = useState(null);
  // PHASE 5: Interruption State
  const [interruptionData, setInterruptionData] = useState(null);
  const [showInterruptionAlert, setShowInterruptionAlert] = useState(false);
  const [originalQuestion, setOriginalQuestion] = useState(null);
  const [showPersonaSelector, setShowPersonaSelector] = useState(true);
  const [selectedPersona, setSelectedPersona] = useState(null);
  // PHASE 8: Voice State
  const [isQuestionSpeaking, setIsQuestionSpeaking] = useState(false);
<<<<<<< Updated upstream

  // Initialize sound effects on first interaction
=======
  const [isRecording, setIsRecording] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);

  // ── KEY: store the pre-fetched next question so it displays instantly ──
  const pendingNextQuestion = useRef(null);
  const lastReadQuestionId = useRef(null);
  const isProcessingAnswer = useRef(false);

  // ============================================================
  // INIT
  // ============================================================
>>>>>>> Stashed changes
  useEffect(() => {
    const initSound = () => {
      soundEffects.initAudioContext();
      document.removeEventListener('click', initSound);
    };
    
    document.addEventListener('click', initSound);
<<<<<<< Updated upstream
    
=======
>>>>>>> Stashed changes
    return () => {
      document.removeEventListener('click', initSound);
    };
  }, []);

  // Cleanup voice when component unmounts
  useEffect(() => {
    return () => {
      voiceService.stop();
    };
  }, []);

<<<<<<< Updated upstream
  const handleStartInterviewWithPersona = async (personaId) => {
=======
  // ============================================================
  // READ QUESTION ALOUD
  // ============================================================
  useEffect(() => {
    const questionId = currentQuestion?.question_number;
    if (!currentQuestion?.text) return;
    if (isRecording) return;
    if (!voiceEnabled) return;
    if (questionId === lastReadQuestionId.current) return;
    if (isProcessingAnswer.current) return;

    console.log('🔊 Reading question:', questionId);
    lastReadQuestionId.current = questionId;
    setIsQuestionSpeaking(true);

    voiceService.speak(currentQuestion.text)
      .then(() => setIsQuestionSpeaking(false))
      .catch(() => setIsQuestionSpeaking(false));
  }, [currentQuestion, isRecording, voiceEnabled]);

  // ============================================================
  // VOICE TOGGLE BUTTON
  // ============================================================
  const handleVoiceToggle = () => {
    if (isQuestionSpeaking) {
      voiceService.stop();
      setIsQuestionSpeaking(false);
    } else if (currentQuestion?.text) {
      setIsQuestionSpeaking(true);
      voiceService.speak(currentQuestion.text)
        .then(() => setIsQuestionSpeaking(false))
        .catch(() => setIsQuestionSpeaking(false));
    }
  };

  // ============================================================
  // ADVANCE TO NEXT QUESTION (called after feedback closes)
  // ============================================================
  const advanceToNextQuestion = useCallback(() => {
    const next = pendingNextQuestion.current;
    if (!next) return;

    pendingNextQuestion.current = null;
    lastReadQuestionId.current = null;
    isProcessingAnswer.current = false;

    setCurrentQuestion(next.question);
    setQuestionNumber(next.questionNumber);
    if (next.phase) setCurrentPhase(next.phase);

    setAiState('speaking');
    setTimeout(() => setAiState('idle'), 1500);
  }, []);

  // ============================================================
  // START INTERVIEW
  // ============================================================
  const handleStartInterview = async (selectedRoundType) => {
>>>>>>> Stashed changes
    setLoading(true);
    setAiState('thinking');
    setShowPersonaSelector(false);

    try {
      const response = await fetch(`http://localhost:8000/interview/start-with-persona`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          persona: personaId,
          resume_context: resumeData?.resume_context || null
        })
      });
      const data = await response.json();
<<<<<<< Updated upstream
      
=======
      if (!data.success) throw new Error('Failed to start interview');

>>>>>>> Stashed changes
      setSessionId(data.session_id);
      setCurrentQuestion(data.question);
      setQuestionNumber(data.question_number);
<<<<<<< Updated upstream
      setTotalQuestions(data.total_questions);
      setSelectedPersona(data.persona);
      setAiState('speaking');
=======
      setTotalQuestions(6);
      setCurrentPhase(data.current_phase);

      lastReadQuestionId.current = null;
      isProcessingAnswer.current = false;
      pendingNextQuestion.current = null;

      if (data.introduction) {
      setAiState('speaking');
      // Show introduction as a "question card" first
      setCurrentQuestion({
        text: data.introduction,
        question_number: 0,
        is_introduction: true
      });
      try {
        await voiceService.speak(data.introduction);
      } catch (e) {
        console.error('Voice error:', e);
      }
      // After intro finishes speaking, show real Q1
      // Store Q1 as pending so user sees intro first
      pendingNextQuestion.current = {
        question: data.question,
        questionNumber: data.question_number,
        phase: data.current_phase
      };
    } else {
      setCurrentQuestion(data.question);
    }

      setAiState('idle');
      soundEffects.playSuccess();
>>>>>>> Stashed changes
      setLoading(false);
      
      setTimeout(() => setAiState('idle'), 3000);
    } catch (error) {
      console.error('Error starting interview:', error);
      alert('Failed to start interview. Is the backend running?');
      setLoading(false);
      setAiState('idle');
      setShowPersonaSelector(true);
    }
  };

<<<<<<< Updated upstream
  // PHASE 5: Handle Interruption
  const handleInterruption = (interruption) => {
    console.log('🔥 INTERRUPTION RECEIVED IN INTERVIEW:', interruption);
    
    soundEffects.playInterruption();
    voiceService.stop();
    
    if (!currentQuestion) {
      console.error('❌ Cannot interrupt: currentQuestion is null');
      return;
    }
    
    setOriginalQuestion({
      text: currentQuestion.question,
      id: currentQuestion.id
    });
    
=======
  // ============================================================
  // HANDLE INTERRUPTION
  // ============================================================
  const handleInterruption = (interruption) => {
    soundEffects.playInterruption();
    voiceService.stop();
    if (currentQuestion) {
      setOriginalQuestion({ text: currentQuestion.text, id: currentQuestion.question_number });
    }
>>>>>>> Stashed changes
    setInterruptionData(interruption);
    setShowInterruptionAlert(true);
    setAiState('speaking');
  };

  // PHASE 5: User Acknowledges Interruption
  const handleInterruptionAcknowledged = () => {
<<<<<<< Updated upstream
    console.log('✅ User acknowledged interruption');
    
    setShowInterruptionAlert(false);
    
    if (currentQuestion && interruptionData) {
=======
    setShowInterruptionAlert(false);
    if (interruptionData) {
>>>>>>> Stashed changes
      setCurrentQuestion({
        id: currentQuestion.id,
        question: interruptionData.followup_question,
        category: 'interruption_followup',
        is_followup: true
      });
<<<<<<< Updated upstream
    }
    
    setAiState('idle');
  };

  // Handle Audio Submission
  const handleAudioSubmitted = async (audioData) => {
    console.log('Submitting transcript:', audioData.transcript);
    
=======
      lastReadQuestionId.current = null;
      isProcessingAnswer.current = false;
    }
    setAiState('idle');
  };

  // ============================================================
  // LIVE WARNING
  // ============================================================
  const handleLiveWarning = (warning) => {
    setLiveWarning(warning);
    setTimeout(() => setLiveWarning(null), 5000);
  };

  // ============================================================
  // SUBMIT ANSWER — OPTIMIZED
  // ============================================================
  const handleAudioSubmitted = async (audioData) => {
    console.log('📝 Submitting answer...');
>>>>>>> Stashed changes
    soundEffects.playSuccess();
    
    if (!currentQuestion) {
      console.error('❌ Cannot submit: currentQuestion is null');
      alert('Error: No active question. Please refresh and try again.');
      return;
    }
      
    setAiState('thinking');
    const answerText = audioData.transcript;
    
    setLoading(true);
<<<<<<< Updated upstream
    
    try {
      const response = await fetch(
        `http://localhost:8000/interview/answer?session_id=${sessionId}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            question_id: currentQuestion.id,
            answer_text: answerText,
            was_interrupted: interruptionData !== null,
            recording_duration: audioData.recording_duration
          }),
        }
      );
      
=======
    isProcessingAnswer.current = true;

    try {
      const response = await fetch('http://localhost:8000/interview/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          question_id: currentQuestion?.question_number || questionNumber,
          answer_text: audioData.transcript,
          recording_duration: audioData.recording_duration,
          was_interrupted: interruptionData !== null,
          is_followup_answer: currentQuestion?.is_followup || false
        })
      });

>>>>>>> Stashed changes
      const data = await response.json();
      if (!data.success) throw new Error('Failed to submit answer');

<<<<<<< Updated upstream
      setLoading(false);
=======
      console.log('✅ Answer response received');
>>>>>>> Stashed changes

      setInterruptionData(null);
      setOriginalQuestion(null);

<<<<<<< Updated upstream
=======
      // ── COMPLETED ────────────────────────────────────────────
>>>>>>> Stashed changes
      if (data.completed) {
        setIsComplete(true);
        setAiState('idle');
        soundEffects.playComplete();
<<<<<<< Updated upstream
      } else {
        setAiState('speaking');
        setCurrentQuestion(data.question);
        setQuestionNumber(data.question_number);
        
        setTimeout(() => setAiState('idle'), 1000);
      }
=======
        setLoading(false);
        isProcessingAnswer.current = false;
        return;
      }

      // ── FOLLOW-UP ─────────────────────────────────────────────
      if (data.requires_followup && data.followup_question) {
        console.log('🔍 Follow-up required');

        // Store the NEXT real question (pre-fetched, arrives later via separate answer)
        // For now just show the follow-up
        setCurrentQuestion({
          text: data.followup_question,
          question_number: currentQuestion?.question_number,
          is_followup: true
        });
        lastReadQuestionId.current = null;
        isProcessingAnswer.current = false;

        // Show feedback briefly
        if (data.immediate_feedback) {
          setLastFeedback(data.immediate_feedback);
          setShowFeedback(true);
          setTimeout(() => setShowFeedback(false), 4000);
        }

        setAiState('speaking');
        setTimeout(() => setAiState('idle'), 1500);
        setLoading(false);
        return;
      }

      // ── NEXT QUESTION — store it, show feedback, then reveal ──
      if (data.question) {
        // Stash the next question — DO NOT set it yet
        pendingNextQuestion.current = {
          question: data.question,
          questionNumber: data.question_number,
          phase: data.current_phase
        };
      }

      // Show feedback popup
      if (data.immediate_feedback) {
        setLastFeedback(data.immediate_feedback);
        setShowFeedback(true);
        setLoading(false);
        setAiState('idle');

        // After feedback auto-closes, advance instantly (no extra API call)
        setTimeout(() => {
          setShowFeedback(false);
          // Small buffer so the fade-out looks clean
          setTimeout(advanceToNextQuestion, 300);
        }, 4000); // 4s feedback display

      } else {
        // No feedback — advance immediately
        setLoading(false);
        advanceToNextQuestion();
      }

>>>>>>> Stashed changes
    } catch (error) {
      console.error('Error submitting answer:', error);
      alert('Failed to submit answer');
      setLoading(false);
      setAiState('idle');
    }
  };

<<<<<<< Updated upstream
  // Reset Interview - goes back to persona selector
=======
  // ============================================================
  // RECORDING STATE
  // ============================================================
  const handleRecordingStateChange = (recordingState) => {
    setIsRecording(recordingState);
    if (recordingState) {
      setAiState('listening');
      voiceService.stop();
      setIsQuestionSpeaking(false);
      setLiveWarning(null);
    } else if (!loading) {
      setAiState('idle');
    }
  };

  // ============================================================
  // RESET
  // ============================================================
>>>>>>> Stashed changes
  const handleResetInterview = () => {
    voiceService.stop();
    setSessionId(null);
    setCurrentQuestion(null);
    setQuestionNumber(0);
    setTotalQuestions(0);
    setIsComplete(false);
    setAiState('idle');
    setInterruptionData(null);
    setShowInterruptionAlert(false);
    setOriginalQuestion(null);
<<<<<<< Updated upstream
    setShowPersonaSelector(true);
    setSelectedPersona(null);
  };

  // Handle back from persona selector - returns to App welcome
  const handleBackFromPersona = () => {
    voiceService.stop();
    if (onBack) {
      onBack(); // ← Add safety check
    }
  };

  // Track recording state
  const handleRecordingStateChange = (isRecording) => {
    if (isRecording) {
      setAiState('listening');
      voiceService.stop();
    } else if (!loading) {
      setAiState('idle');
    }
  };

  // PHASE 8: Handle voice speaking state
  const handleVoiceSpeakingChange = (isSpeaking) => {
    setIsQuestionSpeaking(isSpeaking);
    if (isSpeaking) {
      setAiState('speaking');
    } else if (!loading) {
      setAiState('idle');
    }
  };

  // ===========================================
  // RENDER VIEWS
  // ===========================================
  
  // View 0: Session History
  if (showHistory) {
    if (selectedSessionId) {
      return (
        <SessionDetail 
          sessionId={selectedSessionId}
          onBack={() => setSelectedSessionId(null)}
        />
      );
    }
    
    return (
      <SessionHistory 
        onBack={() => setShowHistory(false)}
        onViewSession={(sessionId) => setSelectedSessionId(sessionId)}
      />
    );
  }

  // View 0: Persona Selection
  if (showPersonaSelector) {
    return (
      <PersonaSelector 
        onPersonaSelected={handleStartInterviewWithPersona}
        onBack={handleBackFromPersona}
      />
    );
  }

  // Loading Screen
  if (loading && sessionId === null) {
    return (
      <div className="interview-container">
        <motion.div 
          className="loading-interview-screen"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4 }}
        >
          <motion.div 
            className="loading-orb"
            animate={{ 
              scale: [1, 1.2, 1],
              rotate: [0, 180, 360]
            }}
            transition={{ 
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          >
            {selectedPersona ? selectedPersona.emoji : '🤖'}
          </motion.div>
          <motion.h2
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            Your interviewer is preparing...
          </motion.h2>
          <motion.p 
            className="loading-subtitle"
            initial={{ y: 10, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            {selectedPersona && `${selectedPersona.name} is generating your first question`}
          </motion.p>
          <div className="loading-dots">
            <motion.span
              animate={{ opacity: [0, 1, 0] }}
              transition={{ duration: 1.5, repeat: Infinity, delay: 0 }}
            >●</motion.span>
            <motion.span
              animate={{ opacity: [0, 1, 0] }}
              transition={{ duration: 1.5, repeat: Infinity, delay: 0.3 }}
            >●</motion.span>
            <motion.span
              animate={{ opacity: [0, 1, 0] }}
              transition={{ duration: 1.5, repeat: Infinity, delay: 0.6 }}
            >●</motion.span>
          </div>
=======
    setLiveWarning(null);
    setShowFeedback(false);
    setLastFeedback(null);
    setShowRoundSelector(true);
    setRoundType(null);
    lastReadQuestionId.current = null;
    isProcessingAnswer.current = false;
    pendingNextQuestion.current = null;
  };

  // ============================================================
  // RENDER: ROUND SELECTOR
  // ============================================================
  if (showRoundSelector) {
    return (
      <div className="interview-container">
        <motion.div className="round-selector" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}>
          <h2>Select Interview Round</h2>
          <p className="round-subtitle">Choose the type of interview you want to practice</p>
          <div className="round-options">
            <motion.button className="round-option hr-round" onClick={() => handleStartInterview('hr')} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <div className="round-icon">👔</div>
              <h3>HR / Behavioral</h3>
              <p>STAR method, storytelling, soft skills</p>
              <div className="round-focus"><span>• Problem-solving stories</span><span>• Team dynamics</span><span>• Career goals</span></div>
            </motion.button>
            <motion.button className="round-option technical-round" onClick={() => handleStartInterview('technical')} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <div className="round-icon">💻</div>
              <h3>Technical</h3>
              <p>Algorithms, data structures, coding concepts</p>
              <div className="round-focus"><span>• Technical depth</span><span>• Problem decomposition</span><span>• Trade-offs & complexity</span></div>
            </motion.button>
            <motion.button className="round-option sysdesign-round" onClick={() => handleStartInterview('system_design')} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <div className="round-icon">🏗️</div>
              <h3>System Design</h3>
              <p>Architecture, scalability, distributed systems</p>
              <div className="round-focus"><span>• High-level architecture</span><span>• Scalability strategies</span><span>• Bottleneck identification</span></div>
            </motion.button>
          </div>
          {resumeData && <div className="resume-badge">✅ Resume uploaded - questions will be personalized</div>}
          <button className="btn-back" onClick={onBack}>← Back to Home</button>
        </motion.div>
      </div>
    );
  }

  // ============================================================
  // RENDER: LOADING
  // ============================================================
  if (loading && !currentQuestion) {
    return (
      <div className="interview-container">
        <motion.div className="loading-interview-screen" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <motion.div className="loading-orb" animate={{ scale: [1, 1.2, 1], rotate: [0, 180, 360] }} transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}>🤖</motion.div>
          <h2>AI Interviewer is preparing...</h2>
          <p className="loading-subtitle">Generating your first {roundType} question</p>
>>>>>>> Stashed changes
        </motion.div>
      </div>
    );
  }

<<<<<<< Updated upstream
  // View 2: Interview Complete - Show Feedback
  if (isComplete) {
    return (
      <FeedbackScreen 
        sessionId={sessionId}
        onNewInterview={handleResetInterview}
        onViewHistory={() => setShowHistory(true)}
      />
    );
  }

  // View 3: Active Interview
  return (
    <div className="interview-container">
      
      {/* PHASE 5: Interruption Alert Overlay */}
      {showInterruptionAlert && interruptionData && (
        <InterruptionAlert 
          interruption={interruptionData}
          onAcknowledge={handleInterruptionAcknowledged}
        />
      )}

      {/* AI Orb in top-right corner */}
=======
  // ============================================================
  // RENDER: COMPLETE
  // ============================================================
  if (isComplete) {
    return <FeedbackScreen sessionId={sessionId} onNewInterview={handleResetInterview} onViewHistory={onViewHistory} />;
  }

  // ============================================================
  // RENDER: ACTIVE INTERVIEW
  // ============================================================
  return (
    <div className="interview-container">

      {showInterruptionAlert && interruptionData && (
        <InterruptionAlert interruption={interruptionData} onAcknowledge={handleInterruptionAcknowledged} />
      )}

      {liveWarning && <LiveWarning warning={liveWarning} />}

      {/* Immediate feedback popup */}
      <AnimatePresence>
        {showFeedback && lastFeedback && (
          <motion.div
            className="immediate-feedback-popup"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <div className="feedback-score">{lastFeedback.emoji} {lastFeedback.overall_score}/100</div>
            <div className="feedback-level">{lastFeedback.performance_level}</div>
            {lastFeedback.key_strength && <div className="feedback-strength">✅ {lastFeedback.key_strength}</div>}
            {lastFeedback.key_weakness && <div className="feedback-weakness">⚠️ {lastFeedback.key_weakness}</div>}
            <div className="feedback-hint" style={{ fontSize: '0.75rem', opacity: 0.6, marginTop: '8px' }}>
              Next question loading...
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* AI Orb */}
>>>>>>> Stashed changes
      <div className="ai-orb-container">
        <MiniAIOrb state={aiState} />
        <div className={`ai-status ai-status-${aiState}`}>
          {aiState === 'listening' && 'Listening...'}
          {aiState === 'thinking' && 'Thinking...'}
          {aiState === 'speaking' && 'Speaking...'}
          {aiState === 'idle' && 'Waiting...'}
        </div>
      </div>

      {/* Interview Content */}
<<<<<<< Updated upstream
      <motion.div 
        className="interview-content"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        
        {/* Header */}
        <motion.div 
          className="interview-header"
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <h2>Interview in Progress</h2>
          <p className="progress">
            Question {questionNumber} of {totalQuestions}
          </p>
        </motion.div>
        
        {/* Persona Badge */}
        {selectedPersona && (
          <motion.div 
            className="persona-badge-active"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <span className="persona-emoji-small">{selectedPersona.emoji}</span>
            <span className="persona-name-small">{selectedPersona.name}</span>
          </motion.div>
        )}
=======
      <motion.div className="interview-content" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>

        <div className="interview-header">
          <h2>{roundType?.toUpperCase()} Interview</h2>
          <p className="progress">Question {questionNumber} • Phase: {currentPhase || 'Active'}</p>
        </div>
>>>>>>> Stashed changes

        <AnimatePresence mode="wait">
          {currentQuestion && (
            <motion.div 
              key={currentQuestion.id}
              className={`question-card ${isQuestionSpeaking ? 'speaking' : ''}`}
              initial={{ x: -50, opacity: 0, scale: 0.95 }}
              animate={{ x: 0, opacity: 1, scale: 1 }}
              exit={{ x: 50, opacity: 0, scale: 0.95 }}
              transition={{ 
                type: 'spring', 
                stiffness: 100, 
                damping: 20,
                duration: 0.5 
              }}
            >
<<<<<<< Updated upstream
              {/* PHASE 5: Show interruption badge if this is a follow-up */}
=======
              <motion.button
                className={`voice-control-btn ${isQuestionSpeaking ? 'speaking' : ''}`}
                onClick={handleVoiceToggle}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                title={isQuestionSpeaking ? "Stop reading" : "Read question aloud"}
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  {isQuestionSpeaking ? (
                    <><rect x="6" y="4" width="4" height="16" /><rect x="14" y="4" width="4" height="16" /></>
                  ) : (
                    <><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" /><path d="M15.54 8.46a5 5 0 0 1 0 7.07" /><path d="M19.07 4.93a10 10 0 0 1 0 14.14" /></>
                  )}
                </svg>
              </motion.button>

>>>>>>> Stashed changes
              {originalQuestion && (
                <motion.div
                  className="interruption-badge"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <span className="badge-icon">⚡</span>
                  <span className="badge-text">
                    Interrupted from: "{originalQuestion.text.substring(0, 50)}..."
                  </span>
                </motion.div>
              )}

<<<<<<< Updated upstream
              <p className="question-label">Interviewer:</p>
              <motion.p 
                className="question-text"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3, duration: 0.5 }}
              >
                {currentQuestion.question}
              </motion.p>

              {/* PHASE 8: Voice Controls */}
              <VoiceControls 
                text={currentQuestion.question}
                autoPlay={true}
                onSpeakingChange={handleVoiceSpeakingChange}
              />
=======
              <p className="question-label">
              {currentQuestion?.is_introduction ? '👋 Introduction' : 'Interviewer:'}
            </p>
              <p className="question-text">{currentQuestion.text}</p>
>>>>>>> Stashed changes
            </motion.div>
          )}
        </AnimatePresence>

<<<<<<< Updated upstream
        {/* Answer Section */}
        <motion.div 
          className="answer-section"
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.5 }}
        >
=======
        <div className="answer-section">
>>>>>>> Stashed changes
          <label>Your Answer (Voice):</label>
          {currentQuestion && (
            <AudioRecorder 
              sessionId={sessionId}
              questionId={currentQuestion.id}
              currentQuestionText={currentQuestion.question}
              onAudioReady={handleAudioSubmitted}
              onRecordingStateChange={handleRecordingStateChange}
              onInterruption={handleInterruption}
            />
          )}
        </motion.div>

      </motion.div>
    </div>
  );
}

export default Interview;