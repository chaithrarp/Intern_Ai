import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './Interview.css';
import AudioRecorder from './AudioRecorder';
import MiniAIOrb from './components/MiniAIOrb';
import InterruptionAlert from './InterruptionAlert';
import LiveWarning from './components/LiveWarning';
import FeedbackScreen from './components/FeedbackScreen';
import soundEffects from './utils/soundEffects';
import voiceService from './utils/voiceService';

/**
 * Interview Component - FIXED VERSION
 * 
 * FIX: Questions now read aloud immediately when received
 */
function Interview({ resumeData, onBack }) {
  // Session State
  const [sessionId, setSessionId] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [questionNumber, setQuestionNumber] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(6);
  const [isComplete, setIsComplete] = useState(false);
  const [loading, setLoading] = useState(false);

  // Round Selection
  const [roundType, setRoundType] = useState(null);
  const [showRoundSelector, setShowRoundSelector] = useState(true);
  const [currentPhase, setCurrentPhase] = useState(null);

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
  
  // Track last read question to prevent duplicates
  const lastReadQuestionId = useRef(null);
  const isProcessingAnswer = useRef(false);

  // ============================================
  // INITIALIZATION
  // ============================================
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

  // ============================================
  // READ QUESTION ALOUD - FIXED VERSION
  // ============================================
  useEffect(() => {
    // SIMPLIFIED LOGIC - Read question when:
    // 1. Question exists
    // 2. Not recording
    // 3. Voice enabled
    // 4. Haven't read this exact question before
    // 5. Not currently processing an answer
    
    const questionId = currentQuestion?.question_number;
    
    if (!currentQuestion || !currentQuestion.text) {
      return; // No question to read
    }
    
    if (isRecording) {
      return; // Don't interrupt recording
    }
    
    if (!voiceEnabled) {
      return; // Voice disabled
    }
    
    if (questionId === lastReadQuestionId.current) {
      return; // Already read this question
    }
    
    if (isProcessingAnswer.current) {
      return; // Wait for answer processing to complete
    }

    // All conditions passed - READ THE QUESTION!
    console.log('🔊 Reading question:', questionId);
    lastReadQuestionId.current = questionId;
    setIsQuestionSpeaking(true);
    
    voiceService.speak(currentQuestion.text)
      .then(() => {
        console.log('✅ Finished reading question');
        setIsQuestionSpeaking(false);
      })
      .catch((error) => {
        console.error('❌ Voice error:', error);
        setIsQuestionSpeaking(false);
      });

    return () => {
      // Cleanup if question changes mid-read
      if (questionId !== currentQuestion?.question_number) {
        voiceService.stop();
      }
    };
  }, [currentQuestion, isRecording, voiceEnabled]);

  // ============================================
  // VOICE CONTROL BUTTON HANDLER
  // ============================================
  const handleVoiceToggle = () => {
    if (isQuestionSpeaking) {
      voiceService.stop();
      setIsQuestionSpeaking(false);
    } else if (currentQuestion && currentQuestion.text) {
      setIsQuestionSpeaking(true);
      
      voiceService.speak(currentQuestion.text)
        .then(() => {
          setIsQuestionSpeaking(false);
        })
        .catch((error) => {
          console.error('Voice error:', error);
          setIsQuestionSpeaking(false);
        });
    }
  };

  // ============================================
  // START INTERVIEW
  // ============================================
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
          resume_context: resumeData?.resume_context || null
        })
      });

      const data = await response.json();

      if (!data.success) {
        throw new Error('Failed to start interview');
      }

      console.log('✅ Interview started:', data);

      setSessionId(data.session_id);
      setRoundType(selectedRoundType);
      setQuestionNumber(data.question_number);
      setTotalQuestions(6);
      setCurrentPhase(data.current_phase);
      
      // Reset flags
      lastReadQuestionId.current = null;
      isProcessingAnswer.current = false;
      
      // FIX: Read introduction FIRST, then show question
      if (data.introduction) {
        console.log('🔊 Reading introduction...');
        setAiState('speaking');
        
        try {
          await voiceService.speak(data.introduction);
          console.log('✅ Finished reading introduction');
          
          // NOW set the question after introduction
          setCurrentQuestion(data.question);
          
        } catch (error) {
          console.error('Voice error:', error);
          // Still show question even if voice fails
          setCurrentQuestion(data.question);
        }
      } else {
        // No introduction, just show question
        setCurrentQuestion(data.question);
      }
      
      setAiState('idle');
      soundEffects.playSuccess();
      setLoading(false);

    } catch (error) {
      console.error('Error starting interview:', error);
      alert('Failed to start interview. Make sure backend is running.');
      setLoading(false);
      setAiState('idle');
      setShowRoundSelector(true);
    }
  };

  // ============================================
  // HANDLE INTERRUPTION
  // ============================================
  const handleInterruption = (interruption) => {
    console.log('🔥 INTERRUPTION:', interruption);

    soundEffects.playInterruption();
    voiceService.stop();

    if (currentQuestion) {
      setOriginalQuestion({
        text: currentQuestion.text,
        id: currentQuestion.question_number
      });
    }

    setInterruptionData(interruption);
    setShowInterruptionAlert(true);
    setAiState('speaking');
  };

  const handleInterruptionAcknowledged = () => {
    console.log('✅ Interruption acknowledged');

    setShowInterruptionAlert(false);

    // Update question to follow-up
    if (interruptionData) {
      setCurrentQuestion({
        text: interruptionData.followup_question,
        question_number: currentQuestion?.question_number || questionNumber,
        is_followup: true
      });
      
      // Reset to allow follow-up to be read
      lastReadQuestionId.current = null;
      isProcessingAnswer.current = false;
    }

    setAiState('idle');
  };

  // ============================================
  // HANDLE LIVE WARNING
  // ============================================
  const handleLiveWarning = (warning) => {
    console.log('⚠️ LIVE WARNING:', warning);
    setLiveWarning(warning);

    setTimeout(() => {
      setLiveWarning(null);
    }, 5000);
  };

  // ============================================
  // HANDLE AUDIO SUBMISSION - FIXED
  // ============================================
  const handleAudioSubmitted = async (audioData) => {
    console.log('📝 Submitting answer...');

    soundEffects.playSuccess();
    setAiState('thinking');
    setLoading(true);
    
    // Mark that we're processing an answer
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
          is_followup_answer: currentQuestion?.is_followup || false  // ← NEW: Track follow-ups
        })
      });

      const data = await response.json();

      if (!data.success) {
        throw new Error('Failed to submit answer');
      }

      console.log('✅ Answer submitted, response:', data);

      // Clear interruption state
      setInterruptionData(null);
      setOriginalQuestion(null);
      setLiveWarning(null);

      // Show immediate feedback
      if (data.immediate_feedback) {
        setLastFeedback(data.immediate_feedback);
        setShowFeedback(true);
        
        setTimeout(() => {
          setShowFeedback(false);
        }, 5000);
      }

      // Check if completed
      if (data.completed) {
        setIsComplete(true);
        setAiState('idle');
        soundEffects.playComplete();
        setLoading(false);
        isProcessingAnswer.current = false;
        return;
      }

      // ========================================
      // HANDLE FOLLOW-UP QUESTIONS - FIXED
      // ========================================
      if (data.requires_followup && data.followup_question) {
        console.log('🔍 Follow-up required:', data.followup_question);
        
        setCurrentQuestion({
          text: data.followup_question,
          question_number: currentQuestion?.question_number,
          is_followup: true
        });
        
        // Reset to allow follow-up to be read
        lastReadQuestionId.current = null;
        isProcessingAnswer.current = false;
        
        setAiState('speaking');
        setTimeout(() => setAiState('idle'), 2000);
        setLoading(false);
        return;
      }

      // ========================================
      // CONTINUE TO NEXT QUESTION - FIXED
      // ========================================
      setCurrentQuestion(data.question);
      setQuestionNumber(data.question_number);
      setCurrentPhase(data.current_phase);
      
      // Reset flags for new question
      lastReadQuestionId.current = null;
      isProcessingAnswer.current = false;
      
      setAiState('speaking');
      setTimeout(() => setAiState('idle'), 2000);
      setLoading(false);

    } catch (error) {
      console.error('Error submitting answer:', error);
      alert('Failed to submit answer');
      setLoading(false);
      setAiState('idle');
      isProcessingAnswer.current = false;
    }
  };

  // ============================================
  // RECORDING STATE CHANGE
  // ============================================
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

  // ============================================
  // RESET INTERVIEW
  // ============================================
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
    lastReadQuestionId.current = null;
    isProcessingAnswer.current = false;
  };

  // ============================================
  // RENDER: ROUND SELECTOR
  // ============================================
  if (showRoundSelector) {
    return (
      <div className="interview-container">
        <motion.div
          className="round-selector"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <h2>Select Interview Round</h2>
          <p className="round-subtitle">
            Choose the type of interview you want to practice
          </p>

          <div className="round-options">
            {/* HR Round */}
            <motion.button
              className="round-option hr-round"
              onClick={() => handleStartInterview('hr')}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <div className="round-icon">👔</div>
              <h3>HR / Behavioral</h3>
              <p>STAR method, storytelling, soft skills</p>
              <div className="round-focus">
                <span>• Problem-solving stories</span>
                <span>• Team dynamics</span>
                <span>• Career goals</span>
              </div>
            </motion.button>

            {/* Technical Round */}
            <motion.button
              className="round-option technical-round"
              onClick={() => handleStartInterview('technical')}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <div className="round-icon">💻</div>
              <h3>Technical</h3>
              <p>Algorithms, data structures, coding concepts</p>
              <div className="round-focus">
                <span>• Technical depth</span>
                <span>• Problem decomposition</span>
                <span>• Trade-offs & complexity</span>
              </div>
            </motion.button>

            {/* System Design Round */}
            <motion.button
              className="round-option sysdesign-round"
              onClick={() => handleStartInterview('system_design')}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <div className="round-icon">🏗️</div>
              <h3>System Design</h3>
              <p>Architecture, scalability, distributed systems</p>
              <div className="round-focus">
                <span>• High-level architecture</span>
                <span>• Scalability strategies</span>
                <span>• Bottleneck identification</span>
              </div>
            </motion.button>
          </div>

          {resumeData && (
            <div className="resume-badge">
              ✅ Resume uploaded - questions will be personalized
            </div>
          )}

          <button className="btn-back" onClick={onBack}>
            ← Back to Home
          </button>
        </motion.div>
      </div>
    );
  }

  // ============================================
  // RENDER: LOADING
  // ============================================
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
            🤖
          </motion.div>
          <h2>AI Interviewer is preparing...</h2>
          <p className="loading-subtitle">
            Generating your first {roundType} question
          </p>
        </motion.div>
      </div>
    );
  }

  // ============================================
  // RENDER: INTERVIEW COMPLETE
  // ============================================
  if (isComplete) {
    return (
      <FeedbackScreen
        sessionId={sessionId}
        onNewInterview={handleResetInterview}
      />
    );
  }

  // ============================================
  // RENDER: ACTIVE INTERVIEW
  // ============================================
  return (
    <div className="interview-container">
      
      {/* Interruption Alert Overlay */}
      {showInterruptionAlert && interruptionData && (
        <InterruptionAlert
          interruption={interruptionData}
          onAcknowledge={handleInterruptionAcknowledged}
        />
      )}

      {/* Live Warning (floating) */}
      {liveWarning && <LiveWarning warning={liveWarning} />}

      {/* Immediate Feedback (after answer) */}
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
            <div className="feedback-strength">
              ✅ {lastFeedback.key_strength}
            </div>
          )}
          {lastFeedback.key_weakness && (
            <div className="feedback-weakness">
              ⚠️ {lastFeedback.key_weakness}
            </div>
          )}
        </motion.div>
      )}

      {/* AI Orb */}
      <div className="ai-orb-container">
        <MiniAIOrb state={isQuestionSpeaking ? 'speaking' : aiState} />
        <div className={`ai-status ai-status-${isQuestionSpeaking ? 'speaking' : aiState}`}>
          {isQuestionSpeaking && '🔊 Reading Question...'}
          {!isQuestionSpeaking && aiState === 'listening' && 'Listening...'}
          {!isQuestionSpeaking && aiState === 'thinking' && 'Analyzing...'}
          {!isQuestionSpeaking && aiState === 'speaking' && 'Speaking...'}
          {!isQuestionSpeaking && aiState === 'idle' && 'Ready'}
        </div>
      </div>

      {/* Interview Content */}
      <motion.div
        className="interview-content"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        
        {/* Header */}
        <div className="interview-header">
          <h2>{roundType.toUpperCase()} Interview</h2>
          <p className="progress">
            Question {questionNumber} • Phase: {currentPhase || 'Active'}
          </p>
        </div>

        {/* Question Card */}
        <AnimatePresence mode="wait">
          {currentQuestion && (
            <motion.div
              key={currentQuestion.question_number}
              className="question-card"
              initial={{ x: -50, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 50, opacity: 0 }}
              transition={{ type: 'spring', stiffness: 100 }}
            >
              {/* Voice Control Button */}
              <motion.button
                className={`voice-control-btn ${isQuestionSpeaking ? 'speaking' : ''}`}
                onClick={handleVoiceToggle}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                title={isQuestionSpeaking ? "Stop reading" : "Read question aloud"}
              >
                <svg 
                  width="24" 
                  height="24" 
                  viewBox="0 0 24 24" 
                  fill="none" 
                  stroke="currentColor" 
                  strokeWidth="2" 
                  strokeLinecap="round" 
                  strokeLinejoin="round"
                >
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

              {/* Interruption Badge */}
              {originalQuestion && (
                <div className="interruption-badge">
                  ⚡ Follow-up from: "{originalQuestion.text.substring(0, 40)}..."
                </div>
              )}

              <p className="question-label">Interviewer:</p>
              <p className="question-text">{currentQuestion.text}</p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Answer Section */}
        <div className="answer-section">
          <label>Your Answer (Voice):</label>
          {currentQuestion && sessionId && (
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
        </div>

      </motion.div>
    </div>
  );
}

export default Interview;