import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import './SessionDetail.css';

function SessionDetail({ sessionId, onBack }) {
  const [sessionData, setSessionData] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchSessionDetails();
  }, [sessionId]);

  const fetchSessionDetails = async () => {
    try {
      // Fetch both summary and detailed metrics
      const [summaryRes, metricsRes] = await Promise.all([
        fetch(`http://localhost:8000/metrics/summary/${sessionId}`),
        fetch(`http://localhost:8000/metrics/session/${sessionId}`)
      ]);

      const summaryData = await summaryRes.json();
      const metricsData = await metricsRes.json();

      if (summaryData.success && metricsData.success) {
        setSummary(summaryData.summary);
        setSessionData(metricsData.metrics);
      } else {
        setError('Failed to load session details');
      }
    } catch (err) {
      console.error('Error fetching session details:', err);
      setError('Failed to load session details');
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
    const thresholds = {
      hesitation: { excellent: 10, good: 25 },
      wpm: { excellent: 120, good: 90 },
      fillers: { excellent: 5, good: 10 }
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
    return '';
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const getSessionDuration = (startedAt, completedAt) => {
    if (!startedAt || !completedAt) return 'N/A';
    const start = new Date(startedAt);
    const end = new Date(completedAt);
    const durationMs = end - start;
    const minutes = Math.floor(durationMs / 60000);
    const seconds = Math.floor((durationMs % 60000) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="detail-container">
        <div className="loading-detail">
          <div className="spinner"></div>
          <p>Loading session details...</p>
        </div>
      </div>
    );
  }

  if (error || !summary || !sessionData) {
    return (
      <div className="detail-container">
        <div className="error-detail">
          <p>❌ {error || 'Session not found'}</p>
          <button onClick={onBack}>← Back to History</button>
        </div>
      </div>
    );
  }

  const performance = getPerformanceLevel(summary.avg_hesitation_score);
  const duration = getSessionDuration(summary.started_at, summary.completed_at);

  return (
    <motion.div 
      className="detail-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="detail-content">
        
        {/* Header */}
        <motion.div 
          className="detail-header"
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <h1>Session Details</h1>
          <p className="session-meta">
            {sessionId}
          </p>
          <p className="session-meta-sub">
            {formatDate(summary.completed_at)} • Duration: {duration}
          </p>
        </motion.div>

        {/* Overall Performance */}
        <motion.div 
          className="overall-performance"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <h2>📊 Overall Performance</h2>
          <div 
            className="performance-badge-large"
            style={{ borderColor: performance.color }}
          >
            <span className="perf-emoji">{performance.emoji}</span>
            <span className="perf-level" style={{ color: performance.color }}>
              {performance.level}
            </span>
          </div>
        </motion.div>

        {/* Summary Metrics */}
        <motion.div 
          className="summary-metrics"
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4 }}
        >
          <h3>Performance Metrics</h3>
          <div className="metrics-grid-detail">
            <div className="metric-box">
              <span className="metric-label">Hesitation Score</span>
              <span className="metric-value">
                {summary.avg_hesitation_score.toFixed(2)}/100
              </span>
            </div>
            <div className="metric-box">
              <span className="metric-label">Speaking Pace</span>
              <span className="metric-value">
                {summary.avg_words_per_minute.toFixed(0)} WPM
              </span>
            </div>
            <div className="metric-box">
              <span className="metric-label">Filler Words</span>
              <span className="metric-value">
                {summary.total_filler_words} total
              </span>
            </div>
            {summary.avg_recovery_time && (
              <div className="metric-box">
                <span className="metric-label">Avg Recovery</span>
                <span className="metric-value">
                  {summary.avg_recovery_time.toFixed(2)}s
                </span>
              </div>
            )}
          </div>
        </motion.div>

        {/* Question by Question Breakdown */}
        <motion.div 
          className="question-breakdown"
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <h3>📝 Question-by-Question Breakdown</h3>
          
          {sessionData.map((answer, index) => (
            <motion.div
              key={answer.answer_id}
              className="answer-card"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.6 + (index * 0.1) }}
            >
              {/* Question Header */}
              <div className="answer-header">
                <h4>Q{index + 1}: {answer.question_text}</h4>
                {answer.was_interrupted && (
                  <span className="interrupted-label">⚡ INTERRUPTED</span>
                )}
              </div>

              {/* Answer Metrics */}
              <div className="answer-metrics">
                <div className="answer-metric">
                  <span className="am-label">Duration:</span>
                  <span className="am-value">{answer.recording_duration.toFixed(0)}s</span>
                </div>
                <div className="answer-metric">
                  <span className="am-label">Hesitation:</span>
                  <span className="am-value">
                    {answer.hesitation_score.toFixed(1)}/100 {getMetricStatus(answer.hesitation_score, 'hesitation')}
                  </span>
                </div>
                <div className="answer-metric">
                  <span className="am-label">WPM:</span>
                  <span className="am-value">
                    {answer.words_per_minute.toFixed(0)} {getMetricStatus(answer.words_per_minute, 'wpm')}
                  </span>
                </div>
                <div className="answer-metric">
                  <span className="am-label">Fillers:</span>
                  <span className="am-value">
                    {answer.filler_word_count} {getMetricStatus(answer.filler_word_count, 'fillers')}
                  </span>
                </div>
                {answer.recovery_time && (
                  <div className="answer-metric">
                    <span className="am-label">Recovery:</span>
                    <span className="am-value">{answer.recovery_time.toFixed(2)}s</span>
                  </div>
                )}
              </div>

              {/* Answer Text Preview */}
              <div className="answer-transcript">
                <p className="transcript-label">Your Answer:</p>
                <p className="transcript-text">
                  "{answer.answer_text.substring(0, 150)}
                  {answer.answer_text.length > 150 ? '...' : ''}"
                </p>
              </div>

              {/* Filler Words List (if any) */}
              {answer.filler_words_list && answer.filler_words_list.length > 0 && (
                <div className="filler-list">
                  <span className="filler-label">Filler words used:</span>
                  <span className="filler-words">{answer.filler_words_list}</span>
                </div>
              )}
            </motion.div>
          ))}
        </motion.div>

        {/* Future: Performance Trends Chart */}
        <motion.div 
          className="trends-placeholder"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
        >
          <h3>📈 Performance Trends</h3>
          <p className="placeholder-text">
            Visual trend charts and comparison with previous sessions coming in Phase 8!
          </p>
        </motion.div>

        {/* Back Button */}
        <motion.div 
          className="detail-footer"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.9 }}
        >
          <button className="btn-back" onClick={onBack}>
            ← Back to History
          </button>
        </motion.div>

      </div>
    </motion.div>
  );
}

export default SessionDetail;