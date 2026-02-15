import React, { useState, useEffect,useCallback } from 'react';
import { motion } from 'framer-motion';
import './FeedbackScreen.css';
import RecoveryCurveChart from './RecoveryCurveChart';
import soundEffects from '../utils/soundEffects';

function FeedbackScreen({ sessionId, onNewInterview, onViewHistory }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null); 

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
  const fetchSessionSummary = useCallback(async () => {
  try {
    const response = await fetch(`http://localhost:8000/metrics/summary/${sessionId}`);
    const data = await response.json();
    
    if (data.success) {
      setSummary({
        overall_score: data.overall_score || 0,
        dimension_scores: data.dimension_scores || {},
        total_questions: data.total_questions || 0,
        total_interruptions: data.total_interruptions || 0,
        interruption_breakdown: data.interruption_breakdown || {},
        phases_completed: data.phases_completed || [],
        score_progression: data.score_progression || [],
        duration_seconds: data.duration_seconds || 0
      });
    } else {
      setError('Failed to load feedback data');
    }
  } catch (error) {
    console.error('Error fetching summary:', error);
    setError('Unable to connect to server');
  } finally {
    setLoading(false);
  }
}, [sessionId]);

useEffect(() => {
  fetchSessionSummary();
}, [fetchSessionSummary]); // ← FIXED: Now includes the function

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
  const scores = summary.dimension_scores;
  
  // Check each dimension
  if (scores.technical_depth >= 80) {
    strengths.push('Strong technical depth and understanding');
  }
  if (scores.structured_thinking >= 70) {
    strengths.push('Excellent structured thinking (STAR method)');
  }
  if (scores.communication_clarity >= 70) {
    strengths.push('Clear and articulate communication');
  }
  if (scores.confidence_consistency >= 80) {
    strengths.push('Confident and consistent delivery');
  }
  if (summary.total_interruptions === 0) {
    strengths.push('No interruptions - smooth performance throughout');
  } else if (summary.total_interruptions <= 2) {
    strengths.push('Handled pressure well with minimal interruptions');
  }

  return strengths.length > 0 ? strengths : ['Completed the interview successfully'];
};

const generateImprovements = (summary) => {
  const improvements = [];
  const scores = summary.dimension_scores;
  
  // Check each dimension for weaknesses
  if (scores.technical_depth < 60) {
    improvements.push('Focus on deepening technical knowledge and concepts');
  }
  if (scores.structured_thinking < 60) {
    improvements.push('Practice STAR method (Situation, Task, Action, Result)');
  }
  if (scores.communication_clarity < 60) {
    improvements.push('Work on clarity - avoid jargon and be more specific');
  }
  if (scores.concept_accuracy < 60) {
    improvements.push('Verify technical concepts before stating them as facts');
  }
  if (scores.confidence_consistency < 60) {
    improvements.push('Build confidence - reduce uncertainty markers');
  }
  if (summary.total_interruptions > 3) {
    improvements.push(`Reduce interruptions (you had ${summary.total_interruptions}) - be more concise`);
  }

  return improvements.length > 0 ? improvements : ['Keep practicing to improve further!'];
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