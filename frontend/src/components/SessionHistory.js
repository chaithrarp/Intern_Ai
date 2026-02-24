import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './SessionHistory.css';

/**
 * SessionHistory - FIXED VERSION
 *
 * Calls /interview/sessions/history (new backend endpoint)
 * Displays overall_score not avg_hesitation_score
 */
function SessionHistory({ onBack, onStartNew }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedSession, setExpandedSession] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/interview/sessions/history');
      const data = await response.json();

      if (data.success) {
        setHistory(data.history || []);
      } else {
        setError(data.error || 'Failed to load history');
      }
    } catch (err) {
      console.error('Error fetching history:', err);
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  const getPerformanceBadge = (score) => {
    if (score >= 85) return { level: 'EXCELLENT', emoji: '🌟', color: '#10b981' };
    if (score >= 70) return { level: 'GOOD',      emoji: '👍', color: '#3b82f6' };
    if (score >= 50) return { level: 'AVERAGE',   emoji: '📊', color: '#f59e0b' };
    return               { level: 'NEEDS WORK', emoji: '📚', color: '#ef4444' };
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown date';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins  = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays  = Math.floor(diffMs / 86400000);

    let relative = '';
    if (diffMins < 60)       relative = `${diffMins}m ago`;
    else if (diffHours < 24) relative = `${diffHours}h ago`;
    else if (diffDays < 7)   relative = `${diffDays}d ago`;
    else                     relative = date.toLocaleDateString();

    const full = date.toLocaleString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: 'numeric', minute: '2-digit', hour12: true
    });
    return { relative, full };
  };

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const dimLabel = {
    technical_depth: 'Technical',
    concept_accuracy: 'Accuracy',
    structured_thinking: 'Structure',
    communication_clarity: 'Clarity',
    confidence_consistency: 'Confidence',
  };

  // ── Loading ──────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="history-container">
        <div className="loading-history">
          <motion.div animate={{ rotate: 360 }} transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }} style={{ fontSize: '2rem' }}>
            🤖
          </motion.div>
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
          <button className="btn-back" onClick={onBack}>← Back</button>
        </div>
      </div>
    );
  }

  return (
    <motion.div className="history-container" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="history-content">

        {/* Header */}
        <motion.div className="history-header" initial={{ y: -20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }}>
          <h1>📚 Interview History</h1>
          <p className="history-subtitle">
            {history.length} session{history.length !== 1 ? 's' : ''} completed
            {history.length > 0 && ` • Last: ${formatDate(history[0].completed_at).relative}`}
          </p>
        </motion.div>

        {/* Empty state */}
        {history.length === 0 ? (
          <motion.div className="empty-history" initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.3 }}>
            <p className="empty-icon">📝</p>
            <h2>No interviews yet</h2>
            <p>Complete your first interview to start tracking progress!</p>
            <button className="btn-primary" onClick={onStartNew}>Start Interview</button>
          </motion.div>
        ) : (
          <div className="sessions-list">
            <AnimatePresence>
              {history.map((session, index) => {
                const score    = session.overall_score || 0;
                const badge    = getPerformanceBadge(score);
                const dateInfo = formatDate(session.completed_at);
                const isExpanded = expandedSession === session.session_id;

                return (
                  <motion.div
                    key={session.session_id}
                    className="session-card"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 + index * 0.07 }}
                    whileHover={{ scale: 1.01 }}
                  >
                    {/* Card header */}
                    <div className="session-header" onClick={() => setExpandedSession(isExpanded ? null : session.session_id)}>
                      <div className="session-title">
                        <h3>{session.round_type?.toUpperCase() || 'Interview'} Round</h3>
                        <p className="session-date">{dateInfo.full}</p>
                      </div>
                      <div className="session-right">
                        <div className="score-badge" style={{ borderColor: badge.color }}>
                          <span style={{ color: badge.color }}>{badge.emoji} {score}/100</span>
                          <small style={{ color: badge.color }}>{badge.level}</small>
                        </div>
                        <span className="expand-icon">{isExpanded ? '▲' : '▼'}</span>
                      </div>
                    </div>

                    {/* Card stats row */}
                    <div className="session-stats">
                      <span className="stat-pill">📝 {session.total_questions || 0} questions</span>
                      <span className="stat-pill">⏱ {formatDuration(session.duration_seconds)}</span>
                      {session.total_interruptions > 0 && (
                        <span className="stat-pill warning">⚡ {session.total_interruptions} interruptions</span>
                      )}
                      {session.round_type && (
                        <span className="stat-pill">{session.round_type}</span>
                      )}
                    </div>

                    {/* Expanded dimension breakdown */}
                    <AnimatePresence>
                      {isExpanded && session.dimension_scores && (
                        <motion.div
                          className="session-expanded"
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                        >
                          <div className="dim-mini-grid">
                            {Object.entries(session.dimension_scores).map(([dim, score]) => (
                              <div key={dim} className="dim-mini">
                                <span className="dim-mini-label">{dimLabel[dim] || dim}</span>
                                <div className="dim-mini-bar-wrap">
                                  <div
                                    className="dim-mini-bar"
                                    style={{
                                      width: `${score}%`,
                                      backgroundColor: score >= 70 ? '#10b981' : score >= 50 ? '#f59e0b' : '#ef4444'
                                    }}
                                  />
                                </div>
                                <span className="dim-mini-score">{score}</span>
                              </div>
                            ))}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>

                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        )}

        {/* Footer */}
        <motion.div className="history-footer" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}>
          <button className="btn-back" onClick={onBack}>← Back</button>
          {onStartNew && (
            <button className="btn-primary" onClick={onStartNew}>🎯 New Interview</button>
          )}
        </motion.div>

      </div>
    </motion.div>
  );
}

export default SessionHistory;