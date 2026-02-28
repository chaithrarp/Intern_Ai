import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './FeedbackScreen.css';

/**
 * FeedbackScreen — with Vision Analysis tab
 *
 * New tab: "👁️ Presence" — shows body language scores, posture/gaze/expression
 * breakdown from the vision_report field returned by /interview/final-report.
 *
 * Vision data lives at: data.report.vision_report
 * Shape: SessionVisionReport (see vision_models.py)
 *
 * Everything else is your original code, untouched.
 */
function FeedbackScreen({ sessionId, onNewInterview, onViewHistory }) {
  const [report, setReport]       = useState(null);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  const fetchReport = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `http://localhost:8000/interview/final-report/${sessionId}`
      );

      if (!response.ok) throw new Error(`Server returned ${response.status}`);

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

  useEffect(() => { fetchReport(); }, [fetchReport]);

  // ── Helpers ─────────────────────────────────────────────────────────────────
  const getScoreStyle = (score) => {
    if (score >= 80) return { color: '#10b981', label: 'Strong' };
    if (score >= 65) return { color: '#3b82f6', label: 'Good' };
    if (score >= 50) return { color: '#f59e0b', label: 'Fair' };
    return               { color: '#ef4444', label: 'Needs Work' };
  };

  const getOverallBadge = (score) => {
    if (score >= 85) return { emoji: '🌟', level: 'EXCELLENT',  color: '#10b981' };
    if (score >= 70) return { emoji: '👍', level: 'GOOD',       color: '#3b82f6' };
    if (score >= 50) return { emoji: '📊', level: 'AVERAGE',    color: '#f59e0b' };
    return             { emoji: '📚', level: 'NEEDS WORK',  color: '#ef4444' };
  };

  const dimensionLabels = {
    technical_depth:        'Technical Depth',
    concept_accuracy:       'Concept Accuracy',
    structured_thinking:    'Structured Thinking',
    communication_clarity:  'Communication Clarity',
    confidence_consistency: 'Confidence & Consistency',
  };

  // ── Vision helpers ───────────────────────────────────────────────────────────
  function visionScoreColor(s) {
    if (s >= 75) return '#10b981';
    if (s >= 50) return '#f59e0b';
    return '#ef4444';
  }

  function VisionBar({ label, value, color }) {
    const pct = Math.min(100, Math.max(0, value));
    const c = color || visionScoreColor(pct);
    return (
      <div style={vStyles.barRow}>
        <span style={vStyles.barLabel}>{label}</span>
        <div style={vStyles.barBg}>
          <motion.div
            style={{ ...vStyles.barFill, background: c }}
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.9, ease: 'easeOut' }}
          />
        </div>
        <span style={{ ...vStyles.barVal, color: c }}>{Math.round(pct)}%</span>
      </div>
    );
  }

  function VisionScoreCircle({ score, label, size = 72 }) {
    const c = visionScoreColor(score);
    const r = size / 2 - 5;
    const circ = 2 * Math.PI * r;
    const offset = circ - (score / 100) * circ;
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
        <svg width={size} height={size}>
          <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#1e2435" strokeWidth={6} />
          <circle
            cx={size/2} cy={size/2} r={r}
            fill="none" stroke={c} strokeWidth={6}
            strokeDasharray={circ} strokeDashoffset={offset}
            strokeLinecap="round"
            transform={`rotate(-90 ${size/2} ${size/2})`}
            style={{ transition: 'stroke-dashoffset 1s ease' }}
          />
          <text x="50%" y="54%" textAnchor="middle" fill={c} fontSize={size * 0.22} fontWeight="bold">
            {Math.round(score)}
          </text>
        </svg>
        <span style={{ fontSize: 10, color: '#666', textAlign: 'center', maxWidth: size }}>{label}</span>
      </div>
    );
  }

  const EXPR_EMOJI = {
    happy: '😊', neutral: '😐', nervous: '😰',
    confused: '😕', angry: '😠', sad: '😞',
    surprised: '😲', unknown: '❓',
  };

  // ── Loading ──────────────────────────────────────────────────────────────────
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

  const badge       = getOverallBadge(report.overall_score);
  const dimScores   = report.dimension_scores || {};
  const mistakes    = report.critical_mistakes || [];
  const topics      = report.recommended_topics || [];
  const nextSteps   = report.next_steps || [];
  const strongAreas = report.strong_areas || [];
  const improvAreas = report.improvement_areas || [];

  // Vision data from the new vision_report field
  const vr          = report.vision_report;   // SessionVisionReport | null
  const hasVision   = !!vr && vr.total_frames_analyzed > 0;

  // Tab list: add "presence" only if vision data exists
  const tabs = [
    { id: 'overview',   label: '📊 Overview' },
    { id: 'breakdown',  label: '🔬 Breakdown' },
    { id: 'mistakes',   label: '⚠️ Mistakes' },
    { id: 'study',      label: '📚 Study Plan' },
    ...(hasVision ? [{ id: 'presence', label: '👁️ Presence' }] : []),
  ];

  // ── Render ───────────────────────────────────────────────────────────────────
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
            {report.interview_duration
              ? ` ${Math.floor(report.interview_duration / 60)}m ${Math.floor(report.interview_duration % 60)}s`
              : ''}
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

          {/* Mini vision score badge alongside overall score */}
          {hasVision && (
            <div style={vStyles.miniVisionBadge}>
              <span style={{ fontSize: 13 }}>👁️</span>
              <span style={{ fontSize: 11, color: visionScoreColor(vr.overall_vision_score), fontWeight: 700 }}>
                {Math.round(vr.overall_vision_score)}/100
              </span>
              <span style={{ fontSize: 10, color: '#555' }}>Presence</span>
            </div>
          )}
        </motion.div>

        {/* ── TABS ── */}
        <div className="report-tabs">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">

          {/* ── TAB: OVERVIEW ── */}
          {activeTab === 'overview' && (
            <motion.div key="overview" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
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
                      {data.strengths?.length > 0 && <p className="round-detail">✅ {data.strengths[0]}</p>}
                      {data.weaknesses?.length > 0 && <p className="round-detail">⚠️ {data.weaknesses[0]}</p>}
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

          {/* ── TAB: PRESENCE (VISION) ── */}
          {activeTab === 'presence' && hasVision && (
            <motion.div key="presence" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>

              {/* Overall vision score row */}
              <div className="report-section">
                <h3>👁️ Body Language & Presence Score</h3>
                <p style={{ fontSize: 13, color: '#888', marginBottom: 20 }}>{vr.summary}</p>

                <div style={vStyles.scoreRow}>
                  <VisionScoreCircle score={vr.overall_vision_score} label="Overall Presence" size={80} />
                  <VisionScoreCircle score={vr.avg_posture_score}    label="Posture"          size={68} />
                  <VisionScoreCircle score={vr.avg_gaze_score}       label="Eye Contact"      size={68} />
                  <VisionScoreCircle
                    score={vr.answer_summaries?.length > 0
                      ? vr.answer_summaries.reduce((acc, s) => acc + s.overall_vision_score, 0) / vr.answer_summaries.length
                      : 0}
                    label="Expressions"
                    size={68}
                  />
                </div>
              </div>

              {/* Strengths / improvements */}
              <div className="two-col">
                <div className="report-section strengths-section">
                  <h3>✅ Presence Strengths</h3>
                  {vr.strengths?.length > 0
                    ? vr.strengths.map((s, i) => <p key={i} className="area-item">• {s}</p>)
                    : <p className="area-item muted">Keep practising to build confident body language.</p>
                  }
                </div>
                <div className="report-section improve-section">
                  <h3>🎯 Presence Improvements</h3>
                  {vr.improvements?.length > 0
                    ? vr.improvements.map((s, i) => <p key={i} className="area-item">• {s}</p>)
                    : <p className="area-item muted">No major presence issues detected!</p>
                  }
                </div>
              </div>

              {/* Per-answer breakdown */}
              {vr.answer_summaries?.length > 0 && (
                <div className="report-section">
                  <h3>📋 Per-Answer Body Language</h3>
                  {vr.answer_summaries.map((ans, i) => (
                    <div key={i} style={vStyles.answerCard}>
                      <div style={vStyles.answerHeader}>
                        <span style={vStyles.answerTitle}>Answer {ans.answer_index + 1}</span>
                        <span style={vStyles.answerHeadline}>{ans.headline}</span>
                        <span style={{ ...vStyles.answerScore, color: visionScoreColor(ans.overall_vision_score) }}>
                          {Math.round(ans.overall_vision_score)}/100
                        </span>
                      </div>

                      <VisionBar label="Upright posture"  value={ans.posture_upright_pct} />
                      <VisionBar label="Eye contact"      value={ans.gaze_direct_pct}     />
                      <VisionBar label="Head neutral"     value={ans.head_neutral_pct}    />

                      {ans.dominant_expression && (
                        <div style={vStyles.exprRow}>
                          <span style={{ fontSize: 10, color: '#666' }}>Dominant expression:</span>
                          <span style={vStyles.exprChip}>
                            {EXPR_EMOJI[ans.dominant_expression] || '😐'} {ans.dominant_expression}
                          </span>
                        </div>
                      )}

                      {ans.feedback_lines?.length > 0 && (
                        <div style={vStyles.feedbackLines}>
                          {ans.feedback_lines.map((line, j) => (
                            <p key={j} style={{ fontSize: 12, color: '#aaa', margin: '3px 0' }}>{line}</p>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              <p style={{ fontSize: 11, color: '#444', marginTop: 12, textAlign: 'center' }}>
                {vr.total_frames_analyzed} video frames analysed across the session
              </p>
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

// ── Vision-specific styles (scoped, don't pollute FeedbackScreen.css) ──────────
const vStyles = {
  scoreRow: {
    display: 'flex', justifyContent: 'space-around',
    alignItems: 'flex-end', flexWrap: 'wrap', gap: 16,
    marginBottom: 8,
  },
  miniVisionBadge: {
    display: 'flex', alignItems: 'center', gap: 6,
    marginTop: 12,
    background: '#0d1117',
    border: '1px solid #1e2435',
    borderRadius: 20,
    padding: '4px 12px',
  },
  barRow: {
    display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8,
  },
  barLabel: {
    width: 120, fontSize: 11, color: '#888', flexShrink: 0,
  },
  barBg: {
    flex: 1, height: 8, background: '#1a1f2e', borderRadius: 4, overflow: 'hidden',
  },
  barFill: {
    height: '100%', borderRadius: 4,
  },
  barVal: {
    width: 40, fontSize: 11, textAlign: 'right',
  },
  answerCard: {
    background: '#0d1117',
    border: '1px solid #1e2435',
    borderRadius: 10,
    padding: '12px 16px',
    marginBottom: 12,
  },
  answerHeader: {
    display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10,
  },
  answerTitle: {
    fontSize: 11, fontWeight: 800, color: '#555', letterSpacing: 1,
    textTransform: 'uppercase', flexShrink: 0,
  },
  answerHeadline: {
    flex: 1, fontSize: 12, color: '#bbb',
  },
  answerScore: {
    fontSize: 13, fontWeight: 700, flexShrink: 0,
  },
  exprRow: {
    display: 'flex', alignItems: 'center', gap: 8, marginTop: 8,
  },
  exprChip: {
    background: '#1a1f2e',
    padding: '2px 10px',
    borderRadius: 20,
    fontSize: 11,
    color: '#ccc',
    textTransform: 'capitalize',
  },
  feedbackLines: {
    marginTop: 8,
    paddingTop: 8,
    borderTop: '1px solid #1a1f2e',
  },
};

export default FeedbackScreen;