import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './Interview.css';
import AudioRecorder from './AudioRecorder';
import MiniAIOrb from './components/MiniAIOrb';

function Interview() {
  const [sessionId, setSessionId] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [questionNumber, setQuestionNumber] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const [loading, setLoading] = useState(false);
  const [aiState, setAiState] = useState('idle'); // idle, listening, thinking, speaking

  // Start Interview
  const handleStartInterview = async () => {
    setLoading(true);
    setAiState('thinking');
    
    try {
      const response = await fetch('http://localhost:8000/interview/start', {
        method: 'POST',
      });
      const data = await response.json();
      
      setSessionId(data.session_id);
      setCurrentQuestion(data.question);
      setQuestionNumber(data.question_number);
      setTotalQuestions(data.total_questions);
      setAiState('speaking');
      setLoading(false);
      
      // After 2 seconds, switch to waiting
      setTimeout(() => setAiState('idle'), 2000);
    } catch (error) {
      console.error('Error starting interview:', error);
      alert('Failed to start interview. Is the backend running?');
      setLoading(false);
      setAiState('idle');
    }
  };

  // Handle Audio Submission
  const handleAudioSubmitted = async (audioData) => {
    console.log('Submitting transcript:', audioData.transcript);
    
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
          }),
        }
      );
      const data = await response.json();

      setLoading(false);

      // Wait 2 seconds so user can see transcript
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Check if interview is complete
      if (data.completed) {
        setIsComplete(true);
        setAiState('idle');
      } else {
        setAiState('speaking');
        setCurrentQuestion(data.question);
        setQuestionNumber(data.question_number);
        
        // After 2 seconds, switch to waiting
        setTimeout(() => setAiState('idle'), 2000);
      }
    } catch (error) {
      console.error('Error submitting answer:', error);
      alert('Failed to submit answer');
      setLoading(false);
      setAiState('idle');
    }
  };

  // Reset Interview
  const handleResetInterview = () => {
    setSessionId(null);
    setCurrentQuestion(null);
    setQuestionNumber(0);
    setTotalQuestions(0);
    setIsComplete(false);
    setAiState('idle');
  };

  // Track recording state
  const handleRecordingStateChange = (isRecording) => {
    if (isRecording) {
      setAiState('listening');
    } else if (!loading) {
      setAiState('idle');
    }
  };

  // ===========================================
  // RENDER VIEWS
  // ===========================================

  // View 1: Start Screen
  if (!sessionId) {
    return (
      <div className="interview-container">
        <motion.div 
          className="start-screen"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6 }}
        >
          <motion.h1
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.5 }}
          >
            Ready to Begin?
          </motion.h1>
          <motion.p 
            className="subtitle"
            initial={{ y: -10, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.4, duration: 0.5 }}
          >
            The AI interviewer is ready for you
          </motion.p>
          <motion.button 
            className="btn-primary" 
            onClick={handleStartInterview}
            disabled={loading}
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.6, duration: 0.5 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            {loading ? 'Starting...' : 'Start Interview'}
          </motion.button>
        </motion.div>
      </div>
    );
  }

  // View 2: Interview Complete
  if (isComplete) {
    return (
      <div className="interview-container">
        <motion.div 
          className="complete-screen"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6 }}
        >
          <motion.h1
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
          >
            ✅ Interview Complete!
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
          >
            You answered {totalQuestions} questions.
          </motion.p>
          <motion.p 
            className="note"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
          >
            In later phases, you'll see detailed feedback and performance metrics here.
          </motion.p>
          <motion.button 
            className="btn-primary" 
            onClick={handleResetInterview}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Start New Interview
          </motion.button>
        </motion.div>
      </div>
    );
  }

  // View 3: Active Interview
  return (
    <div className="interview-container">
      
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

        {/* Question Card */}
        <AnimatePresence mode="wait">
          <motion.div 
            key={currentQuestion?.id}
            className="question-card"
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
            <p className="question-label">Interviewer:</p>
            <motion.p 
              className="question-text"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3, duration: 0.5 }}
            >
              {currentQuestion.question}
            </motion.p>
          </motion.div>
        </AnimatePresence>

        {/* Answer Section */}
        <motion.div 
          className="answer-section"
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.5 }}
        >
          <label>Your Answer (Voice):</label>
          <AudioRecorder 
            sessionId={sessionId}
            questionId={currentQuestion.id}
            onAudioReady={handleAudioSubmitted}
            onRecordingStateChange={handleRecordingStateChange}
          />
        </motion.div>

      </motion.div>
    </div>
  );
}

export default Interview;