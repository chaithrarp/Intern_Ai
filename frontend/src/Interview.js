import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './Interview.css';
import AudioRecorder from './AudioRecorder';
import MiniAIOrb from './components/MiniAIOrb';
import InterruptionAlert from './InterruptionAlert';
import LiveWarning from './components/LiveWarning';
import FeedbackScreen from './components/FeedbackScreen';
import SessionHistory from './components/SessionHistory';
import SessionDetail from './components/SessionDetail';
import PersonaSelector from './components/PersonaSelector';
import soundEffects from './utils/soundEffects';
import voiceService from './utils/voiceService';

function Interview({ resumeData, onBack, onViewHistory }) {
  // Session State
  const [sessionId, setSessionId] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [questionNumber, setQuestionNumber] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(6);
  const [isComplete, setIsComplete] = useState(false);
  const [loading, setLoading] = useState(false);
  const [currentPhase, setCurrentPhase] = useState(null);

  // Persona / Round State
  const [showPersonaSelector, setShowPersonaSelector] = useState(true);
  const [selectedPersona, setSelectedPersona] = useState(null);
  const [roundType, setRoundType] = useState(null);

  // History State
  const [showHistory, setShowHistory] = useState(false);
  const [selectedSessionId, setSelectedSessionId] = useState(null);

  // AI State
  const [aiState, setAiState] = useState('idle');

  // Interruption State
  const [interruptionData, setInterruptionData] = useState(null);
  const [showInterruptionAlert, setShowInterruptionAlert] = useState(false);
  const [originalQuestion, setOriginalQuestion] = useState(null);

  // Warning State
  const [liveWarning, setLiveWarning] = useState(null);

  // Feedback State
  const [lastFeedback, setLastFeedback] = useState(null);
  const [showFeedback, setShowFeedback] = useState(false);

  // Voice State
  const [isQuestionSpeaking, setIsQuestionSpeaking] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);

  // Refs
  const pendingNextQuestion = useRef(null);
  const lastReadQuestionId = useRef(null);
  const isProcessingAnswer = useRef(false);

  // ============================================================
  // INIT
  // ============================================================
  useEffect(() => {
    const initSound = () => {
      soundEffects.initAudioContext();
      document.removeEventListener('click', initSound);
    };
    document.addEventListener('click', initSound);
    return () => {
      document.removeEventListener('click', initSound);
      voiceService.stop();
    };
  }, []);

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
    // Don't auto-read the introduction card — it's already spoken in handleStartInterview
    if (currentQuestion?.is_introduction) return;

    lastReadQuestionId.current = questionId;
    setIsQuestionSpeaking(true);

    voiceService.speak(currentQuestion.text)
      .then(() => setIsQuestionSpeaking(false))
      .catch(() => setIsQuestionSpeaking(false));
  }, [currentQuestion, isRecording, voiceEnabled]);

  // ============================================================
  // VOICE TOGGLE
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
  // START INTERVIEW (via PersonaSelector)
  // ============================================================
  const handleStartInterviewWithPersona = async (personaId) => {
    setLoading(true);
    setAiState('thinking');
    setShowPersonaSelector(false);

    try {
      const response = await fetch('http://localhost:8000/interview/start-with-persona', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          persona: personaId,
          resume_context: resumeData?.resume_context || null
        })
      });

      const data = await response.json();

      setSessionId(data.session_id);
      setSelectedPersona(data.persona);
      setRoundType(data.round_type || personaId);
      setTotalQuestions(data.total_questions_allowed || 6);
      setCurrentPhase(data.current_phase);

      lastReadQuestionId.current = null;
      isProcessingAnswer.current = false;
      pendingNextQuestion.current = null;

      // Show introduction text as a card, speak it, then queue Q0
      if (data.introduction) {
        setAiState('speaking');
        setCurrentQuestion({
          text: data.introduction,
          question_number: -1,
          is_introduction: true
        });

        try {
          await voiceService.speak(data.introduction);
        } catch (e) {
          console.error('Voice error:', e);
        }

        // Queue the real Q0 ("introduce yourself") to show after intro card
        if (data.question) {
          pendingNextQuestion.current = {
            question: data.question,
            questionNumber: data.question_number ?? 0,
            phase: data.current_phase
          };
        }
      } else {
        // No introduction — go straight to Q0
        if (data.question) {
          setCurrentQuestion(data.question);
          setQuestionNumber(data.question_number ?? 0);
        }
      }

      setAiState('idle');
      soundEffects.playSuccess();
      setLoading(false);

    } catch (error) {
      console.error('Error starting interview:', error);
      alert('Failed to start interview. Is the backend running?');
      setLoading(false);
      setAiState('idle');
      setShowPersonaSelector(true);
    }
  };

  // ============================================================
  // HANDLE INTERRUPTION
  // ============================================================
  const handleInterruption = (interruption) => {
    soundEffects.playInterruption();
    voiceService.stop();
    if (currentQuestion) {
      setOriginalQuestion({
        text: currentQuestion.text || currentQuestion.question,
        id: currentQuestion.question_number || currentQuestion.id
      });
    }
    setInterruptionData(interruption);
    setShowInterruptionAlert(true);
    setAiState('speaking');
  };

  const handleInterruptionAcknowledged = () => {
    setShowInterruptionAlert(false);
    if (interruptionData) {
      setCurrentQuestion({
        text: interruptionData.followup_question,
        question: interruptionData.followup_question,
        question_number: currentQuestion?.question_number || questionNumber,
        id: currentQuestion?.id,
        is_followup: true
      });
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
  // SUBMIT ANSWER
  // ============================================================
  const handleAudioSubmitted = async (audioData) => {
    soundEffects.playSuccess();

    if (!currentQuestion) {
      alert('Error: No active question. Please refresh and try again.');
      return;
    }

    setAiState('thinking');
    setLoading(true);
    isProcessingAnswer.current = true;

    const questionId = currentQuestion.question_number ?? currentQuestion.id ?? questionNumber;

    try {
      const response = await fetch('http://localhost:8000/interview/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          question_id: questionId,
          answer_text: audioData.transcript,
          recording_duration: audioData.recording_duration || 0,
          was_interrupted: interruptionData !== null,
          is_followup_answer: currentQuestion?.is_followup || false
        })
      });

      const data = await response.json();

      setInterruptionData(null);
      setOriginalQuestion(null);
      setLiveWarning(null);

      // ── Q0 intro response: no feedback, jump straight to Q1 ──
      if (data.is_intro_response) {
        if (data.next_question) {
          setCurrentQuestion(data.next_question);
          setQuestionNumber(data.question_number ?? 1);
          if (data.current_phase) setCurrentPhase(data.current_phase);
          lastReadQuestionId.current = null;
        }
        isProcessingAnswer.current = false;
        setLoading(false);
        setAiState('idle');
        return;
      }

      // ── COMPLETED ──
      if (data.completed) {
        setIsComplete(true);
        setAiState('idle');
        soundEffects.playComplete();
        setLoading(false);
        isProcessingAnswer.current = false;
        return;
      }

      // ── FOLLOW-UP ──
      if (data.requires_followup && data.followup_question) {
        setCurrentQuestion({
          text: data.followup_question,
          question: data.followup_question,
          question_number: questionId,
          is_followup: true
        });
        lastReadQuestionId.current = null;
        isProcessingAnswer.current = false;

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

      // ── NEXT QUESTION: stash it, show feedback, then reveal ──
      if (data.question || data.next_question) {
        const nextQ = data.question || data.next_question;
        pendingNextQuestion.current = {
          question: nextQ,
          questionNumber: data.question_number,
          phase: data.current_phase
        };
      }

      if (data.immediate_feedback) {
        setLastFeedback(data.immediate_feedback);
        setShowFeedback(true);
        setLoading(false);
        setAiState('idle');

        setTimeout(() => {
          setShowFeedback(false);
          setTimeout(advanceToNextQuestion, 300);
        }, 4000);
      } else {
        setLoading(false);
        advanceToNextQuestion();
      }

    } catch (error) {
      console.error('Error submitting answer:', error);
      alert('Failed to submit answer');
      setLoading(false);
      setAiState('idle');
      isProcessingAnswer.current = false;
    }
  };

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
  const handleResetInterview = () => {
    voiceService.stop();
    setSessionId(null);
    setCurrentQuestion(null);
    setQuestionNumber(0);
    setTotalQuestions(6);
    setIsComplete(false);
    setAiState('idle');
    setInterruptionData(null);
    setShowInterruptionAlert(false);
    setOriginalQuestion(null);
    setLiveWarning(null);
    setShowFeedback(false);
    setLastFeedback(null);
    setShowPersonaSelector(true);
    setSelectedPersona(null);
    setRoundType(null);
    lastReadQuestionId.current = null;
    isProcessingAnswer.current = false;
    pendingNextQuestion.current = null;
  };

  // ============================================================
  // RENDER: SESSION HISTORY
  // ============================================================
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
        onViewSession={(id) => setSelectedSessionId(id)}
      />
    );
  }

  // ============================================================
  // RENDER: PERSONA SELECTOR
  // ============================================================
  if (showPersonaSelector) {
    return (
      <PersonaSelector
        onPersonaSelected={handleStartInterviewWithPersona}
        onBack={onBack}
      />
    );
  }

  // ============================================================
  // RENDER: LOADING
  // ============================================================
  if (loading && !currentQuestion) {
    return (
      <div className="interview-container">
        <motion.div
          className="loading-interview-screen"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <motion.div
            className="loading-orb"
            animate={{ scale: [1, 1.2, 1], rotate: [0, 180, 360] }}
            transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
          >
            {selectedPersona ? selectedPersona.emoji : '🤖'}
          </motion.div>
          <h2>Your interviewer is preparing...</h2>
          <p className="loading-subtitle">
            {selectedPersona
              ? `${selectedPersona.name} is generating your first question`
              : 'Generating your first question'}
          </p>
          <div className="loading-dots">
            {[0, 0.3, 0.6].map((delay, i) => (
              <motion.span
                key={i}
                animate={{ opacity: [0, 1, 0] }}
                transition={{ duration: 1.5, repeat: Infinity, delay }}
              >●</motion.span>
            ))}
          </div>
        </motion.div>
      </div>
    );
  }

  // ============================================================
  // RENDER: COMPLETE
  // ============================================================
  if (isComplete) {
    return (
      <FeedbackScreen
        sessionId={sessionId}
        onNewInterview={handleResetInterview}
        onViewHistory={() => setShowHistory(true)}
      />
    );
  }

  // ============================================================
  // RENDER: ACTIVE INTERVIEW
  // ============================================================

  // Resolve question text — handles both old {question} and new {text} shapes
  const questionText = currentQuestion?.text || currentQuestion?.question || '';
  const isIntroCard = currentQuestion?.is_introduction === true;

  return (
    <div className="interview-container">

      {/* Interruption Alert */}
      {showInterruptionAlert && interruptionData && (
        <InterruptionAlert
          interruption={interruptionData}
          onAcknowledge={handleInterruptionAcknowledged}
        />
      )}

      {/* Live Warning */}
      {liveWarning && <LiveWarning warning={liveWarning} />}

      {/* Immediate Feedback Popup */}
      <AnimatePresence>
        {showFeedback && lastFeedback && (
          <motion.div
            className="immediate-feedback-popup"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <div className="feedback-score">
              {lastFeedback.emoji} {lastFeedback.overall_score}/100
            </div>
            <div className="feedback-level">{lastFeedback.performance_level}</div>
            {lastFeedback.key_strength && (
              <div className="feedback-strength">✅ {lastFeedback.key_strength}</div>
            )}
            {lastFeedback.key_weakness && (
              <div className="feedback-weakness">⚠️ {lastFeedback.key_weakness}</div>
            )}
            <div className="feedback-hint">
              Next question loading...
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* AI Orb */}
      <div className="ai-orb-container">
        <MiniAIOrb state={isQuestionSpeaking ? 'speaking' : aiState} />
        <div className={`ai-status ai-status-${isQuestionSpeaking ? 'speaking' : aiState}`}>
          {isQuestionSpeaking && '🔊 Reading...'}
          {!isQuestionSpeaking && aiState === 'listening' && 'Listening...'}
          {!isQuestionSpeaking && aiState === 'thinking' && 'Analyzing...'}
          {!isQuestionSpeaking && aiState === 'speaking' && 'Speaking...'}
          {!isQuestionSpeaking && aiState === 'idle' && 'Ready'}
        </div>
      </div>

      {/* Main Interview Content */}
      <motion.div
        className="interview-content"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        {/* Header */}
        <div className="interview-header">
          <h2>
            {selectedPersona
              ? `${selectedPersona.emoji} ${selectedPersona.name}`
              : 'Interview in Progress'}
          </h2>
          <p className="progress">
            {isIntroCard
              ? 'Introduction'
              : `Question ${questionNumber} • Phase: ${currentPhase || 'Active'}`}
          </p>
        </div>

        {/* Question Card */}
        <AnimatePresence mode="wait">
          {currentQuestion && (
            <motion.div
              key={currentQuestion.question_number ?? currentQuestion.id ?? 'intro'}
              className={`question-card ${isQuestionSpeaking ? 'speaking' : ''}`}
              initial={{ x: -50, opacity: 0, scale: 0.95 }}
              animate={{ x: 0, opacity: 1, scale: 1 }}
              exit={{ x: 50, opacity: 0, scale: 0.95 }}
              transition={{ type: 'spring', stiffness: 100, damping: 20 }}
            >
              {/* Voice toggle — hide on intro card */}
              {!isIntroCard && (
                <motion.button
                  className={`voice-control-btn ${isQuestionSpeaking ? 'speaking' : ''}`}
                  onClick={handleVoiceToggle}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  title={isQuestionSpeaking ? 'Stop reading' : 'Read question aloud'}
                >
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    {isQuestionSpeaking ? (
                      <>
                        <rect x="6" y="4" width="4" height="16" />
                        <rect x="14" y="4" width="4" height="16" />
                      </>
                    ) : (
                      <>
                        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                        <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
                        <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
                      </>
                    )}
                  </svg>
                </motion.button>
              )}

              {/* Interruption badge */}
              {originalQuestion && (
                <motion.div
                  className="interruption-badge"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <span className="badge-icon">⚡</span>
                  <span className="badge-text">
                    Interrupted from: "{originalQuestion.text?.substring(0, 50)}..."
                  </span>
                </motion.div>
              )}

              {/* Label */}
              <p className="question-label">
                {isIntroCard ? '👋 Interviewer' : 'Interviewer:'}
              </p>

              {/* Question text */}
              <motion.p
                className="question-text"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2, duration: 0.4 }}
              >
                {questionText}
              </motion.p>

              {/* Intro card: "Start Interview" button to advance to Q0 */}
              {isIntroCard && (
                <motion.button
                  className="btn-continue-intro"
                  onClick={() => {
                    voiceService.stop();
                    setIsQuestionSpeaking(false);
                    advanceToNextQuestion();
                  }}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.8 }}
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.97 }}
                >
                  Start Interview →
                </motion.button>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Answer Section — hidden during intro card */}
        {!isIntroCard && (
          <motion.div
            className="answer-section"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.4 }}
          >
            <label>Your Answer (Voice):</label>
            {currentQuestion && sessionId && (
              <AudioRecorder
                sessionId={sessionId}
                questionId={currentQuestion.question_number ?? currentQuestion.id ?? questionNumber}
                currentQuestionText={questionText}
                onAudioReady={handleAudioSubmitted}
                onRecordingStateChange={handleRecordingStateChange}
                onInterruption={handleInterruption}
                onLiveWarning={handleLiveWarning}
              />
            )}
          </motion.div>
        )}

      </motion.div>
    </div>
  );
}

export default Interview;