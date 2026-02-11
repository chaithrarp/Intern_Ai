import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import './FeedbackScreen.css';
import RecoveryCurveChart from './RecoveryCurveChart';
import soundEffects from '../utils/soundEffects';

function FeedbackScreen({ sessionId, onNewInterview, onViewHistory }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSessionSummary();
  }, [sessionId]);
  

// NEW: Add this useEffect for celebration
useEffect(() => {
  if (summary && summary.avg_hesitation_score < 15) {
    // Excellent performance! Play celebration
    setTimeout(() => {
      soundEffects.playCelebration();
    }, 1000);
  }
}, [summary]);
  const fetchSessionSummary = async () => {
    try {
      const response = await fetch(`http://localhost:8000/metrics/summary/${sessionId}`);
      const data = await response.json();
      
      if (data.success) {
        setSummary(data.summary);
      } else {
        console.error('Failed to fetch summary:', data.error);
      }
    } catch (error) {
      console.error('Error fetching summary:', error);
    } finally {
      setLoading(false);
    }
  };

  const getPerformanceLevel = (hesitationScore) => {
    if (hesitationScore < 10) return { level: 'EXCELLENT', emoji: '⭐', color: '#10b981' };
    if (hesitationScore < 25) return { level: 'GOOD', emoji: '👍', color: '#3b82f6' };
    if (hesitationScore < 50) return { level: 'FAIR', emoji: '📊', color: '#f59e0b' };
    return { level: 'NEEDS WORK', emoji: '📈', color: '#ef4444' };
  };

  const getMetricStatus = (metric, type) => {
    // Define what's "good" for each metric
    const thresholds = {
      hesitation: { excellent: 10, good: 25 },
      wpm: { excellent: 120, good: 90 },
      fillers: { excellent: 5, good: 10 },
      recovery: { excellent: 2, good: 4 }
    };

    if (type === 'hesitation') {
      if (metric < thresholds.hesitation.excellent) return '✅';
      if (metric < thresholds.hesitation.good) return '👍';
      return '⚠️';
    }
    if (type === 'wpm') {
      if (metric >= thresholds.wpm.excellent) return '✅';
      if (metric >= thresholds.wpm.good) return '👍';
      return '⚠️';
    }
    if (type === 'fillers') {
      if (metric <= thresholds.fillers.excellent) return '✅';
      if (metric <= thresholds.fillers.good) return '👍';
      return '⚠️';
    }
    if (type === 'recovery') {
      if (metric <= thresholds.recovery.excellent) return '✅';
      if (metric <= thresholds.recovery.good) return '👍';
      return '⚠️';
    }
    return '';
  };

  const generateStrengths = (summary) => {
    const strengths = [];
    
    if (summary.avg_hesitation_score < 10) {
      strengths.push('Minimal hesitation - very confident delivery');
    }
    if (summary.avg_words_per_minute >= 120) {
      strengths.push('Excellent speaking pace - clear and articulate');
    }
    if (summary.total_filler_words <= 5) {
      strengths.push('Minimal filler words - professional communication');
    }
    if (summary.total_interruptions > 0 && summary.avg_recovery_time && summary.avg_recovery_time < 3) {
      strengths.push('Quick recovery after interruptions');
    }
    if (summary.total_long_pauses === 0) {
      strengths.push('No awkward pauses - maintained flow');
    }

    return strengths.length > 0 ? strengths : ['Completed the interview successfully'];
  };

  const generateImprovements = (summary) => {
    const improvements = [];
    
    if (summary.avg_hesitation_score >= 25) {
      improvements.push('Work on reducing hesitation - practice common questions');
    }
    if (summary.avg_words_per_minute < 90) {
      improvements.push('Speak a bit faster - aim for 100-130 words per minute');
    }
    if (summary.total_filler_words > 10) {
      improvements.push('Reduce filler words ("um", "like", "you know")');
    }
    if (summary.avg_recovery_time && summary.avg_recovery_time > 4) {
      improvements.push('Practice recovering faster after interruptions (aim for <3s)');
    }
    if (summary.total_long_pauses > 2) {
      improvements.push('Avoid long pauses - keep momentum in your answers');
    }

    return improvements.length > 0 ? improvements : ['Keep practicing to maintain this level!'];
  };

  if (loading) {
    return (
      <div className="feedback-container">
        <div className="loading-feedback">
          <div className="spinner"></div>
          <p>Analyzing your performance...</p>
        </div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="feedback-container">
        <div className="error-feedback">
          <p>❌ Unable to load feedback</p>
          <button onClick={onNewInterview}>Start New Interview</button>
        </div>
      </div>
    );
  }

  const performance = getPerformanceLevel(summary.avg_hesitation_score);
  const strengths = generateStrengths(summary);
  const improvements = generateImprovements(summary);

  return (
    <motion.div 
      className="feedback-container"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <div className="feedback-content">
        
        {/* Header */}
        <motion.div 
          className="feedback-header"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <h1>🎯 Interview Performance Summary</h1>
          <p className="session-info">
            Session: {sessionId} • {summary.total_answers} questions answered
          </p>
        </motion.div>

        {/* Overall Performance */}
        <motion.div 
          className="performance-badge"
          style={{ borderColor: performance.color }}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.4, type: 'spring', stiffness: 200 }}
        >
          <span className="performance-emoji">{performance.emoji}</span>
          <h2 style={{ color: performance.color }}>{performance.level}</h2>
          <p className="performance-subtitle">Overall Performance</p>
        </motion.div>

        {/* Key Metrics */}
        <motion.div 
          className="metrics-grid"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <h3>📊 Key Metrics</h3>
          
          <div className="metric-row">
            <span className="metric-label">Hesitation Score:</span>
            <span className="metric-value">
              {summary.avg_hesitation_score}/100 {getMetricStatus(summary.avg_hesitation_score, 'hesitation')}
            </span>
          </div>

          <div className="metric-row">
            <span className="metric-label">Speaking Pace:</span>
            <span className="metric-value">
              {summary.avg_words_per_minute} WPM {getMetricStatus(summary.avg_words_per_minute, 'wpm')}
            </span>
          </div>

          <div className="metric-row">
            <span className="metric-label">Filler Words:</span>
            <span className="metric-value">
              {summary.total_filler_words} total {getMetricStatus(summary.total_filler_words, 'fillers')}
            </span>
          </div>

          <div className="metric-row">
            <span className="metric-label">Long Pauses:</span>
            <span className="metric-value">
              {summary.total_long_pauses} {summary.total_long_pauses === 0 ? '✅' : '⚠️'}
            </span>
          </div>
        </motion.div>

        {/* Pressure Handling */}
        {summary.total_interruptions > 0 && (
          <motion.div 
            className="pressure-section"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
          >
            <h3>⚡ Pressure Handling</h3>
            
            <div className="metric-row">
              <span className="metric-label">Interruptions Faced:</span>
              <span className="metric-value">{summary.total_interruptions}</span>
            </div>

            {summary.avg_recovery_time && (
              <div className="metric-row">
                <span className="metric-label">Avg Recovery Time:</span>
                <span className="metric-value">
                  {summary.avg_recovery_time}s {getMetricStatus(summary.avg_recovery_time, 'recovery')}
                </span>
              </div>
            )}
          </motion.div>
        )}

        {/* Strengths */}
        <motion.div 
          className="insights-section strengths"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 1.0 }}
        >
          <h3>💡 Strengths</h3>
          <ul>
            {strengths.map((strength, index) => (
              <motion.li
                key={index}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 1.0 + (index * 0.1) }}
              >
                {strength}
              </motion.li>
            ))}
          </ul>
        </motion.div>

        {/* Areas to Improve */}
        <motion.div 
          className="insights-section improvements"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 1.2 }}
        >
          <h3>🎯 Areas to Improve</h3>
          <ul>
            {improvements.map((improvement, index) => (
              <motion.li
                key={index}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 1.2 + (index * 0.1) }}
              >
                {improvement}
              </motion.li>
            ))}
          </ul>
        </motion.div>
      
      {/* PHASE 8: Recovery Curve Visualization */}
      {summary.total_interruptions > 0 && (
        <motion.div
          className="recovery-visualization-section"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.6 }}
        >
          <RecoveryCurveChart sessionId={sessionId} />
        </motion.div>
      )}


        {/* Action Buttons */}
        <motion.div 
          className="feedback-actions"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.4 }}
        >
          <button className="btn-secondary" onClick={onViewHistory}>
            📊 View History
          </button>
          <button className="btn-primary" onClick={onNewInterview}>
            🔄 New Interview
          </button>
        </motion.div>

      </div>
    </motion.div>
  );
}

export default FeedbackScreen;