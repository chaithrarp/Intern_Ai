import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './FeedbackScreen.css';

/**
 * FeedbackScreen - FIXED VERSION
 *
 * Calls /interview/final-report/{sessionId} (LLM-generated analysis)
 * instead of /metrics/summary (raw numbers only).
 *
 * Shows:
 * - Overall score with correct color
 * - Per-dimension scores with bars
 * - Specific mistakes with evidence
 * - Concepts to study
 * - Actionable next steps
 */
function FeedbackScreen({ sessionId, onNewInterview, onViewHistory }) {
  const [report, setReport]   = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  const fetchReport = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `http://localhost:8000/interview/final-report/${sessionId}`
      );

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      const data = await response.json();

      if (data.success && data.report) {
        setReport(data.report);
      } else {
        throw new Error(data.detail || 'Failed to load report');
      }
    } catch (err) {
      console.error('Error fetching final report:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchReport();
  }, [fetchReport]);

  // ── Helpers ────────────────────────────────────────────────────

  const getScoreStyle = (score) => {
    if (score >= 80) return { color: '#10b981', label: 'Strong' };
    if (score >= 65) return { color: '#3b82f6', label: 'Good' };
    if (score >= 50) return { color: '#f59e0b', label: 'Fair' };
    return { color: '#ef4444', label: 'Needs Work' };
  };

  const getOverallBadge = (score) => {
    if (score >= 85) return { emoji: '🌟', level: 'EXCELLENT',  color: '#10b981' };
    if (score >= 70) return { emoji: '👍', level: 'GOOD',       color: '#3b82f6' };
    if (score >= 50) return { emoji: '📊', level: 'AVERAGE',    color: '#f59e0b' };
    return             { emoji: '📚', level: 'NEEDS WORK',  color: '#ef4444' };
  };

  const dimensionLabels = {
    technical_depth:       'Technical Depth',
    concept_accuracy:      'Concept Accuracy',
    structured_thinking:   'Structured Thinking',
    communication_clarity: 'Communication Clarity',
    confidence_consistency:'Confidence & Consistency',
  };

  // ── Loading ───────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="feedback-container">
        <div className="loading-feedback">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
            style={{ fontSize: '2.5rem', display: 'inline-block' }}
          >
            🤖
          </motion.div>
          <h2>Generating your performance report...</h2>
          <p style={{ opacity: 0.6, marginTop: '8px' }}>
            The AI is analysing all your answers — this takes a few seconds.
          </p>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="feedback-container">
        <div className="error-feedback">
          <p style={{ fontSize: '2rem' }}>⚠️</p>
          <h2>Could not load report</h2>
          <p style={{ opacity: 0.7, marginBottom: '20px' }}>{error}</p>
          <button className="btn-primary" onClick={fetchReport}>Try Again</button>
          <button className="btn-secondary" onClick={onNewInterview} style={{ marginLeft: '12px' }}>
            New Interview
          </button>
        </div>
      </div>
    );
  }

  const badge      = getOverallBadge(report.overall_score);
  const dimScores  = report.dimension_scores || {};
  const mistakes   = report.critical_mistakes || [];
  const topics     = report.recommended_topics || [];
  const nextSteps  = report.next_steps || [];
  const strongAreas = report.strong_areas || [];
  const improvAreas = report.improvement_areas || [];

  // ── Render ────────────────────────────────────────────────────

  return (
    <motion.div
      className="feedback-container"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="feedback-content">

        {/* ── HEADER ── */}
        <motion.div className="feedback-header" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}>
          <h1>🎯 Interview Performance Report</h1>
          <p className="session-info">
            Session: {sessionId} &nbsp;•&nbsp; {report.questions_asked} questions &nbsp;•&nbsp;
            {report.interview_duration ? ` ${Math.floor(report.interview_duration / 60)}m ${Math.floor(report.interview_duration % 60)}s` : ''}
          </p>
        </motion.div>

        {/* ── OVERALL SCORE BADGE ── */}
        <motion.div
          className="performance-badge"
          style={{ borderColor: badge.color }}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: 'spring', stiffness: 180 }}
        >
          <span className="performance-emoji">{badge.emoji}</span>
          <div className="score-circle" style={{ borderColor: badge.color }}>
            <span className="score-number" style={{ color: badge.color }}>{report.overall_score}</span>
            <span className="score-denom">/100</span>
          </div>
          <h2 style={{ color: badge.color }}>{badge.level}</h2>
          <p className="performance-subtitle">{report.overall_assessment}</p>
        </motion.div>

        {/* ── TABS ── */}
        <div className="report-tabs">
          {['overview', 'breakdown', 'mistakes', 'study'].map(tab => (
            <button
              key={tab}
              className={`tab-btn ${activeTab === tab ? 'active' : ''}`}
              onClick={() => setActiveTab(tab)}
            >
              {{ overview: '📊 Overview', breakdown: '🔬 Breakdown', mistakes: '⚠️ Mistakes', study: '📚 Study Plan' }[tab]}
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">

          {/* ── TAB: OVERVIEW ── */}
          {activeTab === 'overview' && (
            <motion.div key="overview" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>

              {/* Dimension scores */}
              <div className="report-section">
                <h3>📈 Dimension Scores</h3>
                {Object.entries(dimScores).map(([dim, score]) => {
                  const style = getScoreStyle(score);
                  return (
                    <div key={dim} className="dim-row">
                      <span className="dim-label">{dimensionLabels[dim] || dim}</span>
                      <div className="dim-bar-wrap">
                        <motion.div
                          className="dim-bar"
                          style={{ backgroundColor: style.color }}
                          initial={{ width: 0 }}
                          animate={{ width: `${score}%` }}
                          transition={{ duration: 0.8, ease: 'easeOut' }}
                        />
                      </div>
                      <span className="dim-score" style={{ color: style.color }}>{score}/100</span>
                    </div>
                  );
                })}
              </div>

              {/* Strong / Improve */}
              <div className="two-col">
                <div className="report-section strengths-section">
                  <h3>✅ Strong Areas</h3>
                  {strongAreas.length > 0
                    ? strongAreas.map((s, i) => <p key={i} className="area-item">• {s}</p>)
                    : <p className="area-item muted">Keep practising to build strong areas.</p>
                  }
                </div>
                <div className="report-section improve-section">
                  <h3>🎯 Needs Improvement</h3>
                  {improvAreas.length > 0
                    ? improvAreas.map((s, i) => <p key={i} className="area-item">• {s}</p>)
                    : <p className="area-item muted">No major gaps detected — great work!</p>
                  }
                </div>
              </div>

            </motion.div>
          )}

          {/* ── TAB: BREAKDOWN ── */}
          {activeTab === 'breakdown' && (
            <motion.div key="breakdown" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <div className="report-section">
                <h3>🔬 Detailed Dimension Analysis</h3>
                {report.skill_assessments && report.skill_assessments.length > 0 ? (
                  report.skill_assessments.map((skill, i) => (
                    <div key={i} className="skill-card">
                      <div className="skill-header">
                        <span className="skill-name">{skill.skill_name}</span>
                        <span className={`skill-level skill-${skill.proficiency_level}`}>
                          {skill.proficiency_level?.toUpperCase()}
                        </span>
                        <span className="skill-score">{skill.score}/100</span>
                      </div>
                      {skill.evidence && skill.evidence.length > 0 && (
                        <div className="skill-evidence">
                          {skill.evidence.slice(0, 2).map((e, j) => (
                            <p key={j} className="evidence-text">"{e}"</p>
                          ))}
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="muted">Detailed skill breakdown not available for this session.</p>
                )}
              </div>

              {/* Round breakdown */}
              {report.round_breakdown && Object.keys(report.round_breakdown).length > 0 && (
                <div className="report-section">
                  <h3>🎯 Round Performance</h3>
                  {Object.entries(report.round_breakdown).map(([round, data]) => (
                    <div key={round} className="round-card">
                      <div className="round-header">
                        <span className="round-name">{round.replace('_', ' ').toUpperCase()}</span>
                        <span className="round-score" style={{ color: getScoreStyle(data.score).color }}>
                          {data.score}/100
                        </span>
                        <span className="round-qs">{data.questions_asked} questions</span>
                      </div>
                      {data.strengths?.length > 0 && (
                        <p className="round-detail">✅ {data.strengths[0]}</p>
                      )}
                      {data.weaknesses?.length > 0 && (
                        <p className="round-detail">⚠️ {data.weaknesses[0]}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {/* ── TAB: MISTAKES ── */}
          {activeTab === 'mistakes' && (
            <motion.div key="mistakes" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <div className="report-section">
                <h3>⚠️ Critical Mistakes & Evidence</h3>
                {mistakes.length > 0 ? (
                  mistakes.map((m, i) => (
                    <div key={i} className="mistake-card">
                      <div className="mistake-header">
                        <span className="mistake-q">{m.question}</span>
                        <span className="mistake-impact">{m.impact}</span>
                      </div>
                      <p className="mistake-text">{m.mistake}</p>
                    </div>
                  ))
                ) : (
                  <div className="no-mistakes">
                    <span style={{ fontSize: '2rem' }}>🎉</span>
                    <p>No critical mistakes detected. Excellent performance!</p>
                  </div>
                )}
              </div>

              {/* Interruption summary */}
              {report.interruption_summary && report.interruption_summary.total_interruptions > 0 && (
                <div className="report-section">
                  <h3>⚡ Interruption Analysis</h3>
                  <div className="interruption-grid">
                    <div className="int-stat">
                      <span className="int-num">{report.interruption_summary.total_interruptions}</span>
                      <span className="int-label">Total Interruptions</span>
                    </div>
                    <div className="int-stat">
                      <span className="int-num">{report.interruption_summary.primary_trigger?.replace(/_/g, ' ')}</span>
                      <span className="int-label">Primary Trigger</span>
                    </div>
                    <div className="int-stat">
                      <span className="int-num">{report.interruption_summary.recovery_quality}</span>
                      <span className="int-label">Recovery</span>
                    </div>
                  </div>
                  <p className="int-notes">{report.interruption_summary.notes}</p>
                </div>
              )}
            </motion.div>
          )}

          {/* ── TAB: STUDY PLAN ── */}
          {activeTab === 'study' && (
            <motion.div key="study" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>

              {topics.length > 0 && (
                <div className="report-section">
                  <h3>📚 Concepts to Study</h3>
                  <p className="section-sub">Based on gaps detected in your answers</p>
                  {topics.map((topic, i) => (
                    <div key={i} className="topic-item">
                      <span className="topic-num">{i + 1}</span>
                      <span className="topic-text">{topic}</span>
                    </div>
                  ))}
                </div>
              )}

              {nextSteps.length > 0 && (
                <div className="report-section">
                  <h3>🚀 Action Plan</h3>
                  <p className="section-sub">Concrete steps before your next interview</p>
                  {nextSteps.map((step, i) => (
                    <div key={i} className="step-item">
                      <span className="step-check">☐</span>
                      <span className="step-text">{step}</span>
                    </div>
                  ))}
                </div>
              )}

              {topics.length === 0 && nextSteps.length === 0 && (
                <div className="no-mistakes">
                  <span style={{ fontSize: '2rem' }}>⭐</span>
                  <p>Outstanding performance — no major study gaps identified!</p>
                </div>
              )}

            </motion.div>
          )}

        </AnimatePresence>

        {/* ── ACTION BUTTONS ── */}
        <motion.div
          className="feedback-actions"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          {onViewHistory && (
            <button className="btn-secondary" onClick={onViewHistory}>
              📊 View History
            </button>
          )}
          <button className="btn-primary" onClick={onNewInterview}>
            🔄 New Interview
          </button>
        </motion.div>

      </div>
    </motion.div>
  );
}

export default FeedbackScreen;