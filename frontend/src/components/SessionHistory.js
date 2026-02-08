import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './SessionHistory.css';

function SessionHistory({ onBack, onViewSession }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await fetch('http://localhost:8000/metrics/history?limit=20');
      const data = await response.json();
      
      if (data.success) {
        setHistory(data.history);
      } else {
        setError(data.error);
      }
    } catch (err) {
      console.error('Error fetching history:', err);
      setError('Failed to load history');
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

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    // Relative time
    let relative = '';
    if (diffMins < 60) {
      relative = `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
      relative = `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else if (diffDays < 7) {
      relative = `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    } else {
      relative = date.toLocaleDateString();
    }

    // Full date
    const full = date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });

    return { relative, full };
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
      <div className="history-container">
        <div className="loading-history">
          <div className="spinner"></div>
          <p>Loading your interview history...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="history-container">
        <div className="error-history">
          <p>❌ {error}</p>
          <button onClick={onBack}>← Back</button>
        </div>
      </div>
    );
  }

  return (
    <motion.div 
      className="history-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="history-content">
        
        {/* Header */}
        <motion.div 
          className="history-header"
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <h1>📚 Interview History</h1>
          <p className="history-subtitle">
            Total Sessions: {history.length}
            {history.length > 0 && ` • Last practiced: ${formatDate(history[0].completed_at).relative}`}
          </p>
        </motion.div>

        {/* Session List */}
        {history.length === 0 ? (
          <motion.div 
            className="empty-history"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.4 }}
          >
            <p className="empty-icon">📝</p>
            <h2>No interview history yet</h2>
            <p>Complete your first interview to start tracking your progress!</p>
            <button className="btn-primary" onClick={onBack}>
              Start Interview
            </button>
          </motion.div>
        ) : (
          <motion.div 
            className="sessions-list"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            <AnimatePresence>
              {history.map((session, index) => {
                const performance = getPerformanceLevel(session.avg_hesitation_score);
                const dateInfo = formatDate(session.completed_at);
                const duration = getSessionDuration(session.started_at, session.completed_at);

                return (
                  <motion.div
                    key={session.session_id}
                    className="session-card"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 + (index * 0.1) }}
                    whileHover={{ scale: 1.02, boxShadow: '0 10px 30px rgba(0,0,0,0.15)' }}
                  >
                    {/* Session Header */}
                    <div className="session-header">
                      <div className="session-title">
                        <h3>{session.session_id}</h3>
                        <p className="session-date" title={dateInfo.full}>
                          {dateInfo.full} • {duration} duration
                        </p>
                      </div>
                      <div 
                        className="session-badge"
                        style={{ backgroundColor: performance.color }}
                      >
                        <span>{performance.emoji} {performance.level}</span>
                      </div>
                    </div>

                    {/* Session Stats */}
                    <div className="session-stats">
                      <div className="stat-group">
                        <div className="stat-item">
                          <span className="stat-label">Questions</span>
                          <span className="stat-value">{session.total_questions}</span>
                        </div>
                        <div className="stat-item">
                          <span className="stat-label">Hesitation</span>
                          <span className="stat-value">{session.avg_hesitation_score.toFixed(1)}</span>
                        </div>
                      </div>

                      <div className="stat-group">
                        <div className="stat-item">
                          <span className="stat-label">Pace (WPM)</span>
                          <span className="stat-value">{session.avg_words_per_minute.toFixed(0)}</span>
                        </div>
                        <div className="stat-item">
                          <span className="stat-label">Fillers</span>
                          <span className="stat-value">{session.total_filler_words}</span>
                        </div>
                      </div>

                      {session.interruption_count > 0 && (
                        <div className="stat-group">
                          <div className="stat-item">
                            <span className="stat-label">Interruptions</span>
                            <span className="stat-value">⚡ {session.interruption_count}</span>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* View Details Button */}
                    <button 
                      className="btn-view-details"
                      onClick={() => onViewSession(session.session_id)}
                    >
                      View Details →
                    </button>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </motion.div>
        )}

        {/* Back Button */}
        <motion.div 
          className="history-footer"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
        >
          <button className="btn-back" onClick={onBack}>
            ← Back to Interview
          </button>
        </motion.div>

      </div>
    </motion.div>
  );
}

export default SessionHistory;