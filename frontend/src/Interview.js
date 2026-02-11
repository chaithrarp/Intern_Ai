import React, { useState } from 'react';
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

// ← ADD PROPS HERE
function Interview({ resumeData, onBack }) {
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

  // Initialize sound effects on first interaction
  useEffect(() => {
    const initSound = () => {
      soundEffects.initAudioContext();
      document.removeEventListener('click', initSound);
    };
    
    document.addEventListener('click', initSound);
    
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

  const handleStartInterviewWithPersona = async (personaId) => {
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
      
      setSessionId(data.session_id);
      setCurrentQuestion(data.question);
      setQuestionNumber(data.question_number);
      setTotalQuestions(data.total_questions);
      setSelectedPersona(data.persona);
      setAiState('speaking');
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
    
    setInterruptionData(interruption);
    setShowInterruptionAlert(true);
    setAiState('speaking');
  };

  // PHASE 5: User Acknowledges Interruption
  const handleInterruptionAcknowledged = () => {
    console.log('✅ User acknowledged interruption');
    
    setShowInterruptionAlert(false);
    
    if (currentQuestion && interruptionData) {
      setCurrentQuestion({
        id: currentQuestion.id,
        question: interruptionData.followup_question,
        category: 'interruption_followup',
        is_followup: true
      });
    }
    
    setAiState('idle');
  };

  // Handle Audio Submission
  const handleAudioSubmitted = async (audioData) => {
    console.log('Submitting transcript:', audioData.transcript);
    
    soundEffects.playSuccess();
    
    if (!currentQuestion) {
      console.error('❌ Cannot submit: currentQuestion is null');
      alert('Error: No active question. Please refresh and try again.');
      return;
    }
      
    setAiState('thinking');
    const answerText = audioData.transcript;
    
    setLoading(true);
    
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
      
      const data = await response.json();

      setLoading(false);

      setInterruptionData(null);
      setOriginalQuestion(null);

      if (data.completed) {
        setIsComplete(true);
        setAiState('idle');
        soundEffects.playComplete();
      } else {
        setAiState('speaking');
        setCurrentQuestion(data.question);
        setQuestionNumber(data.question_number);
        
        setTimeout(() => setAiState('idle'), 1000);
      }
    } catch (error) {
      console.error('Error submitting answer:', error);
      alert('Failed to submit answer');
      setLoading(false);
      setAiState('idle');
    }
  };

  // Reset Interview - goes back to persona selector
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
        </motion.div>
      </div>
    );
  }

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

        {/* Question Card */}
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
              {/* PHASE 5: Show interruption badge if this is a follow-up */}
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
            </motion.div>
          )}
        </AnimatePresence>

        {/* Answer Section */}
        <motion.div 
          className="answer-section"
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.5 }}
        >
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