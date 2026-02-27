import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './Interview.css';
import AudioRecorder from './AudioRecorder';
import MiniAIOrb from './components/MiniAIOrb';
import InterruptionAlert from './InterruptionAlert';
import LiveWarning from './components/LiveWarning';
import FeedbackScreen from './components/FeedbackScreen';
import soundEffects from './utils/soundEffects';
import voiceService from './utils/voiceService';

function Interview({ resumeData, onBack, onViewHistory }) {
  const [sessionId, setSessionId]               = useState(null);
  const [currentQuestion, setCurrentQuestion]   = useState(null);
  const [questionNumber, setQuestionNumber]     = useState(0);
  const [totalQuestions, setTotalQuestions]     = useState(6);
  const [isComplete, setIsComplete]             = useState(false);
  const [loading, setLoading]                   = useState(false);
  const [roundType, setRoundType]               = useState(null);
  const [showRoundSelector, setShowRoundSelector] = useState(true);
  const [currentPhase, setCurrentPhase]         = useState(null);
  const [aiState, setAiState]                   = useState('idle');
  const [interruptionData, setInterruptionData] = useState(null);
  const [showInterruptionAlert, setShowInterruptionAlert] = useState(false);
  const [originalQuestion, setOriginalQuestion] = useState(null);
  const [liveWarning, setLiveWarning]           = useState(null);
  const [lastFeedback, setLastFeedback]         = useState(null);
  const [showFeedback, setShowFeedback]         = useState(false);
  const [isQuestionSpeaking, setIsQuestionSpeaking] = useState(false);
  const [isRecording, setIsRecording]           = useState(false);
  const [voiceEnabled]                          = useState(true);

  // pendingNextQuestion: the NEXT question to show after feedback is dismissed
  const pendingNextQuestion   = useRef(null);
  // pendingFollowup: set when requires_followup=true, so feedback "Next" shows the follow-up
  const pendingFollowup       = useRef(null);
  const lastReadQuestionId    = useRef(null);
  const isProcessingAnswer    = useRef(false);

  // ── Sound init ────────────────────────────────────────────────────────────
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

  // ── Speak question aloud ──────────────────────────────────────────────────
  useEffect(() => {
    const questionId = currentQuestion?.question_number;
    if (!currentQuestion?.text) return;
    if (isRecording) return;
    if (!voiceEnabled) return;
    if (questionId === lastReadQuestionId.current) return;
    if (isProcessingAnswer.current) return;
    if (showFeedback) return;

    lastReadQuestionId.current = questionId;
    setIsQuestionSpeaking(true);
    voiceService.speak(currentQuestion.text)
      .then(() => setIsQuestionSpeaking(false))
      .catch(() => setIsQuestionSpeaking(false));
  }, [currentQuestion, isRecording, voiceEnabled, showFeedback]);

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

  // ── Advance to the next question (called by "Next Question →" button) ─────
  // Handles BOTH cases:
  //   1. Normal flow  → pendingNextQuestion has the next regular question
  //   2. Follow-up flow → pendingFollowup has the follow-up question
  const advanceToNextQuestion = useCallback(() => {
    setShowFeedback(false);
    setLastFeedback(null);
    isProcessingAnswer.current = false;

    // Case 1: follow-up is waiting
    if (pendingFollowup.current) {
      const followup = pendingFollowup.current;
      pendingFollowup.current = null;
      lastReadQuestionId.current = null;
      setCurrentQuestion(followup);
      setAiState('speaking');
      setTimeout(() => setAiState('idle'), 1500);
      return;
    }

    // Case 2: normal next question
    const next = pendingNextQuestion.current;
    if (!next) return;
    pendingNextQuestion.current = null;
    lastReadQuestionId.current = null;
    setCurrentQuestion(next.question);
    setQuestionNumber(next.questionNumber);
    if (next.phase) setCurrentPhase(next.phase);
    setAiState('speaking');
    setTimeout(() => setAiState('idle'), 1500);
  }, []);

  // ── Start interview ───────────────────────────────────────────────────────
  const handleStartInterview = async (selectedRoundType) => {
    setLoading(true);
    setAiState('thinking');
    setShowRoundSelector(false);
    setRoundType(selectedRoundType);
    try {
      const response = await fetch('http://localhost:8000/interview/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          round_type: selectedRoundType,
          resume_context: resumeData?.resume_context || null,
        }),
      });
      const data = await response.json();
      if (!data.success) throw new Error('Failed to start interview');

      setSessionId(data.session_id);
      setQuestionNumber(data.question_number);
      setTotalQuestions(6);
      setCurrentPhase(data.current_phase);
      lastReadQuestionId.current  = null;
      isProcessingAnswer.current  = false;
      pendingNextQuestion.current = null;
      pendingFollowup.current     = null;

      if (data.introduction) {
        setAiState('speaking');
        setCurrentQuestion({ text: data.introduction, question_number: 0, is_introduction: true });
        try { await voiceService.speak(data.introduction); } catch (e) {}
        pendingNextQuestion.current = {
          question: data.question,
          questionNumber: data.question_number,
          phase: data.current_phase,
        };
      } else {
        setCurrentQuestion(data.question);
      }

      setAiState('idle');
      soundEffects.playSuccess();
      setLoading(false);
    } catch (error) {
      alert('Failed to start interview. Make sure backend is running.');
      setLoading(false);
      setAiState('idle');
      setShowRoundSelector(true);
    }
  };

  // ── Interruption handlers ─────────────────────────────────────────────────
  const handleInterruption = (interruption) => {
    soundEffects.playInterruption?.();
    voiceService.stop();
    if (currentQuestion) {
      setOriginalQuestion({ text: currentQuestion.text, id: currentQuestion.question_number });
    }
    setInterruptionData(interruption);
    setShowInterruptionAlert(true);
    setAiState('speaking');
  };

  const handleInterruptionAcknowledged = () => {
    setShowInterruptionAlert(false);
    if (interruptionData) {
      const followupQuestion = {
        text: interruptionData.followup_question,
        question_number: currentQuestion?.question_number,
        is_followup: true,
      };
      lastReadQuestionId.current = followupQuestion.question_number;
      setCurrentQuestion(followupQuestion);
      isProcessingAnswer.current = false;
    }
    setAiState('idle');
  };

  const handleLiveWarning = (warning) => {
    setLiveWarning(warning);
    setTimeout(() => setLiveWarning(null), 5000);
  };

  // ── Show feedback popup ───────────────────────────────────────────────────
  const showFeedbackPopup = useCallback((feedbackData) => {
    setShowFeedback(false);
    setLastFeedback(null);
    // Use requestAnimationFrame to guarantee a fresh render cycle
    requestAnimationFrame(() => {
      setLastFeedback(feedbackData);
      setShowFeedback(true);
    });
  }, []);

  // ── Submit answer ─────────────────────────────────────────────────────────
  const handleAudioSubmitted = async (audioData) => {
    soundEffects.playSuccess();
    setAiState('thinking');
    setLoading(true);
    isProcessingAnswer.current = true;

    try {
      const response = await fetch('http://localhost:8000/interview/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id:        sessionId,
          question_id:       currentQuestion?.question_number || questionNumber,
          answer_text:       audioData.transcript,
          recording_duration: audioData.recording_duration,
          was_interrupted:   interruptionData !== null,
          is_followup_answer: currentQuestion?.is_followup || false,
        }),
      });
      const data = await response.json();
      if (!data.success) throw new Error('Failed to submit answer');

      setInterruptionData(null);
      setOriginalQuestion(null);
      setLiveWarning(null);
      setLoading(false);
      setAiState('idle');

      // ── Interview complete ─────────────────────────────────────────────────
      if (data.completed) {
        setIsComplete(true);
        soundEffects.playComplete?.();
        isProcessingAnswer.current = false;
        return;
      }

      // ── Follow-up required ────────────────────────────────────────────────
      // Store the follow-up in pendingFollowup so advanceToNextQuestion
      // can present it after the user dismisses the feedback popup.
      if (data.requires_followup && data.followup_question) {
        pendingFollowup.current = {
          text: data.followup_question,
          question_number: currentQuestion?.question_number,
          is_followup: true,
        };
        // Clear the next-question stash so advance goes to follow-up, not a new Q
        pendingNextQuestion.current = null;

        if (data.immediate_feedback) {
          showFeedbackPopup(data.immediate_feedback);
        } else {
          // No feedback — go straight to the follow-up
          advanceToNextQuestion();
        }
        return;
      }

      // ── Normal flow: stash next question, show feedback ───────────────────
      if (data.question) {
        pendingNextQuestion.current = {
          question: data.question,
          questionNumber: data.question_number,
          phase: data.current_phase,
        };
      }
      // Clear follow-up stash (this was a normal answer, not a follow-up path)
      pendingFollowup.current = null;

      if (data.immediate_feedback) {
        showFeedbackPopup(data.immediate_feedback);
      } else {
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

  const handleResetInterview = () => {
    voiceService.stop();
    setSessionId(null);
    setCurrentQuestion(null);
    setQuestionNumber(0);
    setIsComplete(false);
    setAiState('idle');
    setInterruptionData(null);
    setOriginalQuestion(null);
    setLiveWarning(null);
    setShowFeedback(false);
    setLastFeedback(null);
    setShowRoundSelector(true);
    setRoundType(null);
    lastReadQuestionId.current  = null;
    isProcessingAnswer.current  = false;
    pendingNextQuestion.current = null;
    pendingFollowup.current     = null;
  };

  // ── Round selector ────────────────────────────────────────────────────────
  if (showRoundSelector) {
    return (
      <div className="interview-container">
        <motion.div
          className="round-selector"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <h2>Select Interview Round</h2>
          <p className="round-subtitle">Choose the type of interview you want to practice</p>
          <div className="round-options">
            {[
              { type: 'hr',            icon: '👔', label: 'HR / Behavioral',  desc: 'STAR method, storytelling, soft skills',              points: ['Problem-solving stories', 'Team dynamics', 'Career goals'] },
              { type: 'technical',     icon: '💻', label: 'Technical',         desc: 'Algorithms, data structures, coding concepts',         points: ['Technical depth', 'Problem decomposition', 'Trade-offs & complexity'] },
              { type: 'system_design', icon: '🏗️', label: 'System Design',     desc: 'Architecture, scalability, distributed systems',       points: ['High-level architecture', 'Scalability strategies', 'Bottleneck identification'] },
            ].map(({ type, icon, label, desc, points }) => (
              <motion.button
                key={type}
                className={`round-option ${type}-round`}
                onClick={() => handleStartInterview(type)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <div className="round-icon">{icon}</div>
                <h3>{label}</h3>
                <p>{desc}</p>
                <div className="round-focus">
                  {points.map(p => <span key={p}>• {p}</span>)}
                </div>
              </motion.button>
            ))}
          </div>
          {resumeData && (
            <div className="resume-badge">✅ Resume uploaded — questions will be personalized</div>
          )}
          <button className="btn-back" onClick={onBack}>← Back to Home</button>
        </motion.div>
      </div>
    );
  }

  if (loading && !currentQuestion) {
    return (
      <div className="interview-container">
        <motion.div className="loading-interview-screen" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <motion.div
            className="loading-orb"
            animate={{ scale: [1, 1.2, 1], rotate: [0, 180, 360] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            🤖
          </motion.div>
          <h2>AI Interviewer is preparing...</h2>
          <p className="loading-subtitle">Generating your first {roundType} question</p>
        </motion.div>
      </div>
    );
  }

  if (isComplete) {
    return (
      <FeedbackScreen
        sessionId={sessionId}
        onNewInterview={handleResetInterview}
        onViewHistory={onViewHistory}
      />
    );
  }

  return (
    <div className="interview-container">
      {showInterruptionAlert && interruptionData && (
        <InterruptionAlert
          interruption={interruptionData}
          onAcknowledge={handleInterruptionAcknowledged}
        />
      )}
      {liveWarning && <LiveWarning warning={liveWarning} />}

      {/* ── Feedback popup ─────────────────────────────────────────────────── */}
      <AnimatePresence>
        {showFeedback && lastFeedback && (
          <>
            <motion.div
              className="feedback-backdrop"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            />
            <motion.div
              className="immediate-feedback-popup"
              initial={{ opacity: 0, y: -30, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -20, scale: 0.95 }}
              transition={{ type: 'spring', stiffness: 260, damping: 22 }}
            >
              <div className="ifp-header">
                <span className="ifp-emoji">{lastFeedback.emoji}</span>
                <div className="ifp-title-group">
                  <span className="ifp-headline">
                    {lastFeedback.headline || lastFeedback.performance_level}
                  </span>
                  <span
                    className="ifp-score"
                    style={{
                      color:
                        lastFeedback.overall_score >= 80 ? '#10b981' :
                        lastFeedback.overall_score >= 60 ? '#3b82f6' :
                        lastFeedback.overall_score >= 40 ? '#f59e0b' : '#ef4444',
                    }}
                  >
                    {lastFeedback.overall_score}/100
                  </span>
                </div>
              </div>

              <div className="ifp-score-bar-wrap">
                <motion.div
                  className="ifp-score-bar"
                  initial={{ width: 0 }}
                  animate={{ width: `${lastFeedback.overall_score}%` }}
                  transition={{ duration: 0.8, ease: 'easeOut', delay: 0.2 }}
                  style={{
                    backgroundColor:
                      lastFeedback.overall_score >= 80 ? '#10b981' :
                      lastFeedback.overall_score >= 60 ? '#3b82f6' :
                      lastFeedback.overall_score >= 40 ? '#f59e0b' : '#ef4444',
                  }}
                />
              </div>

              {lastFeedback.messages?.length > 0 && (
                <div className="ifp-messages">
                  {lastFeedback.messages.map((msg, i) => (
                    <p key={i} className={`ifp-msg ${msg.startsWith('⚠️') ? 'ifp-msg--warning' : ''}`}>
                      {msg}
                    </p>
                  ))}
                </div>
              )}

              {lastFeedback.red_flags?.length > 0 && (
                <div className="ifp-flags">
                  {lastFeedback.red_flags.map((flag, i) => (
                    <span key={i} className="ifp-flag">🚨 {flag}</span>
                  ))}
                </div>
              )}

              {lastFeedback.encouragement && (
                <p className="ifp-encouragement">{lastFeedback.encouragement}</p>
              )}

              {/* Label changes based on whether a follow-up is waiting */}
              <motion.button
                className="ifp-next-btn"
                onClick={advanceToNextQuestion}
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
              >
                {pendingFollowup.current
                  ? 'Answer Follow-up →'
                  : 'Next Question →'}
              </motion.button>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* AI Orb */}
      <div className="ai-orb-container">
        <MiniAIOrb state={isQuestionSpeaking ? 'speaking' : aiState} />
        <div className={`ai-status ai-status--${isQuestionSpeaking ? 'speaking' : aiState}`}>
          {isQuestionSpeaking ? '🔊 Reading Question...' :
           aiState === 'listening' ? '🎙 Listening...' :
           aiState === 'thinking'  ? '⚙️ Analyzing...' :
           aiState === 'speaking'  ? '🔊 Speaking...' : 'Ready'}
        </div>
      </div>

      <motion.div className="interview-content" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <div className="interview-header">
          <h2>{roundType?.toUpperCase()} Interview</h2>
          <p className="progress">{currentPhase || 'Active'}</p>
        </div>

        <AnimatePresence mode="wait">
          {currentQuestion && (
            <motion.div
              key={currentQuestion.question_number}
              className="question-card"
              initial={{ x: -50, opacity: 0 }}
              animate={{ x: 0,   opacity: 1 }}
              exit={{   x: 50,  opacity: 0 }}
              transition={{ type: 'spring', stiffness: 100 }}
            >
              <motion.button
                className={`voice-control-btn ${isQuestionSpeaking ? 'speaking' : ''}`}
                onClick={handleVoiceToggle}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  {isQuestionSpeaking
                    ? <><rect x="6" y="4" width="4" height="16" /><rect x="14" y="4" width="4" height="16" /></>
                    : <><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" /><path d="M15.54 8.46a5 5 0 0 1 0 7.07" /><path d="M19.07 4.93a10 10 0 0 1 0 14.14" /></>
                  }
                </svg>
              </motion.button>

              {originalQuestion && (
                <div className="interruption-badge">
                  ⚡ Follow-up from: "{originalQuestion.text.substring(0, 40)}..."
                </div>
              )}

              <p className="question-label">
                {currentQuestion?.is_introduction ? '👋 Introduction' : 'Interviewer:'}
              </p>
              <p className="question-text">{currentQuestion.text}</p>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="answer-section">
          <label>Your Answer (Voice):</label>
          {currentQuestion && sessionId && !showFeedback && (
            <AudioRecorder
              sessionId={sessionId}
              questionId={currentQuestion.question_number || questionNumber}
              currentQuestionText={currentQuestion.text}
              onAudioReady={handleAudioSubmitted}
              onRecordingStateChange={handleRecordingStateChange}
              onInterruption={handleInterruption}
              onLiveWarning={handleLiveWarning}
            />
          )}
          {showFeedback && (
            <div className="feedback-waiting-hint">
              📋 Read your feedback, then click{' '}
              <strong>
                {pendingFollowup.current ? 'Answer Follow-up →' : 'Next Question →'}
              </strong>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}

export default Interview;