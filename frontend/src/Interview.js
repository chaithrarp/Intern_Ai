import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './Interview.css';
import AudioRecorder from './AudioRecorder';
import MiniAIOrb from './components/MiniAIOrb';
import InterruptionAlert from './InterruptionAlert';
import FeedbackScreen from './components/FeedbackScreen';
import soundEffects from './utils/soundEffects';
import voiceService from './utils/voiceService';
import AIInterviewer from './components/AIInterviewer';
import InterviewerAvatar from './components/InterviewerAvatar';

// ════════════════════════════════════════════════════════════════
// MAIN INTERVIEW COMPONENT
// ════════════════════════════════════════════════════════════════

function Interview({ resumeData, onBack, onViewHistory }) {
  const [sessionId, setSessionId]                   = useState(null);
  const [currentQuestion, setCurrentQuestion]       = useState(null);
  const [questionNumber, setQuestionNumber]         = useState(0);
  const [totalQuestions, setTotalQuestions]         = useState(6);
  const [isComplete, setIsComplete]                 = useState(false);
  const [loading, setLoading]                       = useState(false);
  const [roundType, setRoundType]                   = useState(null);
  const [showRoundSelector, setShowRoundSelector]   = useState(true);
  const [currentPhase, setCurrentPhase]             = useState(null);
  const [aiState, setAiState]                       = useState('idle');
  const [interruptionData, setInterruptionData]     = useState(null);
  const [showInterruptionAlert, setShowInterruptionAlert] = useState(false);
  const [originalQuestion, setOriginalQuestion]     = useState(null);
  const [lastFeedback, setLastFeedback]             = useState(null);
  const [showFeedback, setShowFeedback]             = useState(false);
  const [isQuestionSpeaking, setIsQuestionSpeaking] = useState(false);
  const [isRecording, setIsRecording]               = useState(false);
  const [voiceEnabled]                              = useState(true);
  const [answerIndex, setAnswerIndex]               = useState(0);
  // liveVisionData kept for feedback popup only — not displayed in main UI
  const [liveVisionData, setLiveVisionData]         = useState(null);

  const webcamRef           = useRef(null);
  const pendingNextQuestion = useRef(null);
  const pendingFollowup     = useRef(null);
  const lastReadQuestionId  = useRef(null);
  const isProcessingAnswer  = useRef(false);

  /* sound init */
  useEffect(() => {
    const init = () => { soundEffects.initAudioContext(); document.removeEventListener('click', init); };
    document.addEventListener('click', init);
    return () => { document.removeEventListener('click', init); voiceService.stop(); };
  }, []);
  useEffect(() => () => webcamRef.current?.cleanup?.(), []);

  /* auto-speak question */
  useEffect(() => {
    const qid = currentQuestion?.question_number;
    if (!currentQuestion?.text || isRecording || !voiceEnabled) return;
    if (qid === lastReadQuestionId.current || isProcessingAnswer.current || showFeedback) return;
    lastReadQuestionId.current = qid;
    setIsQuestionSpeaking(true);
    voiceService.speak(currentQuestion.text)
      .then(() => setIsQuestionSpeaking(false))
      .catch(() => setIsQuestionSpeaking(false));
  }, [currentQuestion, isRecording, voiceEnabled, showFeedback]);

  const handleVoiceToggle = () => {
    if (isQuestionSpeaking) { voiceService.stop(); setIsQuestionSpeaking(false); }
    else if (currentQuestion?.text) {
      setIsQuestionSpeaking(true);
      voiceService.speak(currentQuestion.text)
        .then(() => setIsQuestionSpeaking(false))
        .catch(() => setIsQuestionSpeaking(false));
    }
  };

  const advanceToNextQuestion = useCallback(() => {
    setShowFeedback(false); setLastFeedback(null); isProcessingAnswer.current = false;
    if (pendingFollowup.current) {
      const fu = pendingFollowup.current; pendingFollowup.current = null;
      lastReadQuestionId.current = null; setCurrentQuestion(fu);
      setAiState('speaking'); setTimeout(() => setAiState('idle'), 1500); return;
    }
    const next = pendingNextQuestion.current; if (!next) return;
    pendingNextQuestion.current = null; lastReadQuestionId.current = null;
    setCurrentQuestion(next.question); setQuestionNumber(next.questionNumber);
    if (next.phase) setCurrentPhase(next.phase);
    setAiState('speaking'); setTimeout(() => setAiState('idle'), 1500);
  }, []);

  const handleStartInterview = async (type) => {
    setLoading(true); setAiState('thinking'); setShowRoundSelector(false); setRoundType(type);
    try {
      const data = await fetch('http://localhost:8000/interview/start', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ round_type: type, resume_context: resumeData?.resume_context || null }),
      }).then(r => r.json());
      if (!data.success) throw new Error();
      setSessionId(data.session_id); setQuestionNumber(data.question_number);
      setTotalQuestions(6); setCurrentPhase(data.current_phase); setAnswerIndex(0);
      lastReadQuestionId.current = null; isProcessingAnswer.current = false;
      pendingNextQuestion.current = null; pendingFollowup.current = null;
      if (data.introduction) {
        setAiState('speaking');
        setCurrentQuestion({ text: data.introduction, question_number: 0, is_introduction: true });
        try { await voiceService.speak(data.introduction); } catch {}
        pendingNextQuestion.current = { question: data.question, questionNumber: data.question_number, phase: data.current_phase };
      } else setCurrentQuestion(data.question);
      setAiState('idle'); soundEffects.playSuccess(); setLoading(false);
    } catch {
      alert('Failed to start interview. Make sure backend is running.');
      setLoading(false); setAiState('idle'); setShowRoundSelector(true);
    }
  };

  const handleInterruption = (interruption) => {
    soundEffects.playInterruption?.(); voiceService.stop();
    if (currentQuestion) setOriginalQuestion({ text: currentQuestion.text, id: currentQuestion.question_number });
    setInterruptionData(interruption); setShowInterruptionAlert(true); setAiState('speaking');
  };

  const handleInterruptionAcknowledged = () => {
    setShowInterruptionAlert(false);
    if (interruptionData) {
      const fq = { text: interruptionData.followup_question, question_number: currentQuestion?.question_number, is_followup: true };
      lastReadQuestionId.current = fq.question_number; setCurrentQuestion(fq); isProcessingAnswer.current = false;
    }
    setAiState('idle');
  };

  const showFeedbackPopup = useCallback((fd) => {
    setShowFeedback(false); setLastFeedback(null);
    requestAnimationFrame(() => { setLastFeedback(fd); setShowFeedback(true); });
  }, []);

  const handleAudioSubmitted = async (audioData) => {
    soundEffects.playSuccess(); setAiState('thinking'); setLoading(true); isProcessingAnswer.current = true;
    webcamRef.current?.requestAnswerSummary(answerIndex);
    try {
      const data = await fetch('http://localhost:8000/interview/answer', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          question_id: currentQuestion?.question_number || questionNumber,
          answer_text: audioData.transcript,
          recording_duration: audioData.recording_duration,
          was_interrupted: interruptionData !== null,
          is_followup_answer: currentQuestion?.is_followup || false,
        }),
      }).then(r => r.json());
      if (!data.success) throw new Error();
      setInterruptionData(null); setOriginalQuestion(null);
      setLoading(false); setAiState('idle'); setAnswerIndex(p => p + 1);
      if (data.completed) {
        webcamRef.current?.requestSessionReport(); setIsComplete(true);
        soundEffects.playComplete?.(); isProcessingAnswer.current = false; return;
      }
      if (data.requires_followup && data.followup_question) {
        pendingFollowup.current = { text: data.followup_question, question_number: currentQuestion?.question_number, is_followup: true };
        pendingNextQuestion.current = null;
        if (data.immediate_feedback) showFeedbackPopup(data.immediate_feedback); else advanceToNextQuestion();
        return;
      }
      if (data.question) pendingNextQuestion.current = { question: data.question, questionNumber: data.question_number, phase: data.current_phase };
      pendingFollowup.current = null;
      if (data.immediate_feedback) showFeedbackPopup(data.immediate_feedback); else advanceToNextQuestion();
    } catch {
      alert('Failed to submit answer'); setLoading(false); setAiState('idle'); isProcessingAnswer.current = false;
    }
  };

  const handleRecordingStateChange = (rec) => {
    setIsRecording(rec);
    if (rec) { setAiState('listening'); voiceService.stop(); setIsQuestionSpeaking(false); }
    else if (!loading) setAiState('idle');
  };

  const handleResetInterview = () => {
    voiceService.stop(); webcamRef.current?.cleanup?.();
    setSessionId(null); setCurrentQuestion(null); setQuestionNumber(0); setAnswerIndex(0);
    setIsComplete(false); setAiState('idle'); setInterruptionData(null); setOriginalQuestion(null);
    setShowFeedback(false); setLastFeedback(null); setLiveVisionData(null);
    setShowRoundSelector(true); setRoundType(null);
    lastReadQuestionId.current = null; isProcessingAnswer.current = false;
    pendingNextQuestion.current = null; pendingFollowup.current = null;
  };

  // Vision data stored for feedback popup; toasts are handled inside AIInterviewer
  const handleFrameAnalysis = useCallback((fa) => {
    setLiveVisionData(fa);
  }, []);

  const handleVisionSummary = useCallback((data) => { console.log('[Vision]', data); }, []);

  const currentAiState = isQuestionSpeaking ? 'speaking' : aiState;
  const progressPct    = Math.round((questionNumber / totalQuestions) * 100);

  /* ── Round selector ─────────────────────────────────────────── */
  if (showRoundSelector) return (
    <div className="interview-container">
      <div className="round-selector">
        <h2>Select Interview Round</h2>
        <p className="round-subtitle">Choose the type of interview you want to practice</p>
        <div className="round-options">
          {[
            { type: 'hr',            icon: '👔', label: 'HR / Behavioral',  desc: 'STAR method, storytelling, soft skills',        points: ['Problem-solving stories', 'Team dynamics', 'Career goals'] },
            { type: 'technical',     icon: '💻', label: 'Technical',         desc: 'Algorithms, data structures, coding concepts',   points: ['Technical depth', 'Problem decomposition', 'Trade-offs'] },
            { type: 'system_design', icon: '🏗️', label: 'System Design',     desc: 'Architecture, scalability, distributed systems', points: ['High-level architecture', 'Scalability', 'Bottlenecks'] },
          ].map(({ type, icon, label, desc, points }) => (
            <motion.div key={type} className={`round-option ${type}-round`}
              onClick={() => handleStartInterview(type)}
              whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.97 }}
            >
              <div className="round-icon">{icon}</div>
              <h3>{label}</h3>
              <p>{desc}</p>
              <div className="round-focus">{points.map(p => <span key={p}>• {p}</span>)}</div>
            </motion.div>
          ))}
        </div>
        {resumeData && <div className="resume-badge">✅ Resume uploaded — questions will be personalized</div>}
        <button className="btn-back" onClick={onBack}>← Back to Home</button>
      </div>
    </div>
  );

  /* ── Loading ────────────────────────────────────────────────── */
  if (loading && !currentQuestion) return (
    <div className="interview-container">
      <div className="loading-interview-screen">
        <div className="loading-orb">🤖</div>
        <h2>AI Interviewer is preparing...</h2>
        <p className="loading-subtitle">Generating your first {roundType} question</p>
      </div>
    </div>
  );

  if (isComplete) return <FeedbackScreen />;

  /* ════════════════════════════════════════════════════════════
     MAIN SPLIT LAYOUT — TWO COLUMNS (cam | question)
  ════════════════════════════════════════════════════════════ */
  return (
    <div className="iv-root">
      {showInterruptionAlert && interruptionData && (
        <InterruptionAlert interruption={interruptionData} onAcknowledge={handleInterruptionAcknowledged} />
      )}

      {/* ── Feedback popup ── */}
      <AnimatePresence>
        {showFeedback && lastFeedback && (
          <>
            <motion.div className="feedback-backdrop"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} />
            <motion.div className="immediate-feedback-popup"
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
            >
              <div className="ifp-header">
                <span className="ifp-emoji">{lastFeedback.emoji}</span>
                <div className="ifp-title-group">
                  <div className="ifp-headline">{lastFeedback.headline || lastFeedback.performance_level}</div>
                  <div className="ifp-score" style={{ color: lastFeedback.overall_score >= 80 ? '#10b981' : lastFeedback.overall_score >= 60 ? '#3b82f6' : lastFeedback.overall_score >= 40 ? '#f59e0b' : '#ef4444' }}>
                    {lastFeedback.overall_score}/100
                  </div>
                </div>
              </div>

              <div className="ifp-score-bar-wrap">
                <div className="ifp-score-bar" style={{
                  width: `${lastFeedback.overall_score}%`,
                  background: lastFeedback.overall_score >= 80 ? '#10b981' : lastFeedback.overall_score >= 60 ? '#3b82f6' : lastFeedback.overall_score >= 40 ? '#f59e0b' : '#ef4444',
                }} />
              </div>

              {lastFeedback.messages?.length > 0 && (
                <div className="ifp-messages">
                  {lastFeedback.messages.map((msg, i) => <p key={i} className="ifp-msg">{msg}</p>)}
                </div>
              )}
              {lastFeedback.red_flags?.length > 0 && (
                <div className="ifp-flags">
                  {lastFeedback.red_flags.map((f, i) => <span key={i} className="ifp-flag">🚨 {f}</span>)}
                </div>
              )}
              {lastFeedback.encouragement && <p className="ifp-encouragement">{lastFeedback.encouragement}</p>}

              {/* Compact vision line in feedback — only if data exists */}
              {liveVisionData?.frame_score !== undefined && (
                <div className="ifp-vision-pill" style={{ '--vc': liveVisionData.frame_score >= 75 ? '#22dd77' : liveVisionData.frame_score >= 50 ? '#f97316' : '#ef4444' }}>
                  👁️ <span>Presence: {Math.round(liveVisionData.frame_score)}/100</span>
                </div>
              )}

              <button className="ifp-next-btn" onClick={advanceToNextQuestion}>
                {pendingFollowup.current ? 'Answer Follow-up →' : 'Next Question →'}
              </button>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* ═══════════════════════════════════════════
          TWO-COLUMN SPLIT: cam (55%) | question (45%)
      ═══════════════════════════════════════════ */}
      <div className="iv-split">

        {/* ── LEFT: Camera panel ── */}
        <div className="iv-cam-panel">
          {/* Topbar with round badge + AI status */}
          <div className="iv-cam-topbar">
            <div className="iv-cam-topbar-left">
              <span className="iv-round-badge">{roundType?.toUpperCase()}</span>
              <span className="iv-phase-label">{currentPhase || 'Active'}</span>
              <div className="iv-q-counter">

                {Array.from({ length: totalQuestions }, (_, i) => (
                  <span
                    key={i}
                    className={`iv-q-dot ${i < questionNumber ? 'iv-q-dot--done' : i === questionNumber ? 'iv-q-dot--active' : ''}`}
                  />
                ))}
                
                <div className="iv-waveform">
                  {Array.from({ length: 8 }, (_, i) => (
                    <span
                      key={i}
                      className={`iv-waveform-bar ${currentAiState === 'speaking' ? 'iv-waveform-bar--active' : ''}`}
                      style={{ animationDelay: `${i * 0.08}s` }}
                    />
                  ))}
                </div>

                
              </div>
            </div>
            <InterviewerAvatar state={currentAiState} />
          </div>

          {/* Full-bleed camera body */}
          <div className="iv-cam-body">
            <AIInterviewer
              ref={webcamRef}
              sessionId={sessionId}
              answerIndex={answerIndex}
              isRecording={isRecording}
              onFrameAnalysis={handleFrameAnalysis}
              onAnswerSummary={handleVisionSummary}
            />
          </div>
        </div>

        {/* ── RIGHT: Question + Answer panel ── */}
        <div className="iv-right-panel">
          <div className="iv-progress-track">
            <div className="iv-progress-fill" style={{ width: `${progressPct}%` }} />
          </div>
          <div className="iv-progress-label">
            <span>Question {questionNumber} of {totalQuestions}</span>
            <span>{progressPct}%</span>
          </div>

          <div className="iv-question-wrap">
            {currentQuestion && (
              <div className="iv-question-card" {...(isQuestionSpeaking ? { 'data-speaking': true } : {})}>
                {/* Voice toggle */}
                <button
                  className={`voice-control-btn${isQuestionSpeaking ? ' speaking' : ''}`}
                  onClick={handleVoiceToggle}
                  title={isQuestionSpeaking ? 'Stop reading' : 'Read aloud'}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                    {isQuestionSpeaking
                      ? <><rect x="6" y="4" width="4" height="16" /><rect x="14" y="4" width="4" height="16" /></>
                      : <polygon points="5,3 19,12 5,21" />}
                  </svg>
                </button>

                {/* Interruption label */}
                {originalQuestion && (
                  <div className="interruption-badge">
                    ⚡ Follow-up: "{originalQuestion.text.substring(0, 40)}..."
                  </div>
                )}

                <div className="iv-q-label">
                  {currentQuestion?.is_introduction ? '👋 Introduction' : 'Interviewer'}
                </div>
                <p className="iv-q-text">{currentQuestion.text}</p>
                {isQuestionSpeaking && <div className="iv-speaking-glow" />}
              </div>
            )}
          </div>

          <div className="iv-answer-wrap">
            {currentQuestion && sessionId && !showFeedback ? (
               <AudioRecorder
                sessionId={sessionId}
                questionId={currentQuestion?.question_number || questionNumber}
                onAudioReady={handleAudioSubmitted}           // ← FIXED: matches AudioRecorder's prop
                onRecordingStateChange={handleRecordingStateChange}
                onInterruption={handleInterruption}
                currentQuestionText={currentQuestion?.text}  // ← BONUS: was missing, needed for interruption check
                disabled={loading}
              />
            ) : showFeedback ? (
              <div className="feedback-waiting-hint">
                📋 Read your feedback, then click{' '}
                <strong>{pendingFollowup.current ? 'Answer Follow-up →' : 'Next Question →'}</strong>
              </div>
            ) : null}
          </div>
        </div>

      </div>
    </div>
  );
}

export default Interview;