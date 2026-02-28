/**
 * VisionFeedbackCard.js
 *
 * Reusable card to display vision analysis results.
 * Works for both:
 *   - Per-answer feedback (AnswerVisionSummary shape)
 *   - Final report section (SessionVisionReport shape)
 *
 * Usage in FeedbackScreen.js (per-answer):
 *   import VisionFeedbackCard from './VisionFeedbackCard';
 *   <VisionFeedbackCard data={visionSummary} mode="answer" />
 *
 * Usage in FinalReport / ResultsScreen:
 *   <VisionFeedbackCard data={sessionVisionReport} mode="session" />
 */

import React, { useState } from 'react';

// ─── Score color helper ──────────────────────────────────
function scoreColor(score) {
  if (score >= 75) return '#22CC66';
  if (score >= 50) return '#FFAA00';
  return '#FF4444';
}

// ─── Circular score badge ────────────────────────────────
function ScoreBadge({ score, size = 64, label }) {
  const color = scoreColor(score);
  const r = (size / 2) - 4;
  const circumference = 2 * Math.PI * r;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <svg width={size} height={size}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#333" strokeWidth={5} />
        <circle
          cx={size/2} cy={size/2} r={r}
          fill="none" stroke={color} strokeWidth={5}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform={`rotate(-90 ${size/2} ${size/2})`}
          style={{ transition: 'stroke-dashoffset 0.8s ease' }}
        />
        <text x="50%" y="54%" textAnchor="middle" fill={color} fontSize={size * 0.24} fontWeight="bold">
          {Math.round(score)}
        </text>
      </svg>
      {label && <span style={{ fontSize: 10, color: '#888', textAlign: 'center' }}>{label}</span>}
    </div>
  );
}

// ─── Stat bar ────────────────────────────────────────────
function StatBar({ label, value, maxVal = 100, color }) {
  const pct = Math.min(100, (value / maxVal) * 100);
  const barColor = color || scoreColor(pct);
  return (
    <div style={styles.statRow}>
      <span style={styles.statLabel}>{label}</span>
      <div style={styles.barBg}>
        <div style={{ ...styles.barFill, width: `${pct}%`, background: barColor }} />
      </div>
      <span style={{ ...styles.statValue, color: barColor }}>{Math.round(value)}%</span>
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────
export default function VisionFeedbackCard({ data, mode = 'answer' }) {
  const [expanded, setExpanded] = useState(false);

  if (!data) return null;

  const isSession = mode === 'session';

  // ── Session mode ──
  if (isSession) {
    const report = data;
    return (
      <div style={styles.card}>
        <div style={styles.header}>
          <span style={styles.headerIcon}>👁️</span>
          <span style={styles.headerTitle}>Body Language & Presence</span>
          <ScoreBadge score={report.overall_vision_score || 0} size={52} label="Overall" />
        </div>

        <p style={styles.summary}>{report.summary}</p>

        <div style={styles.scoresRow}>
          <ScoreBadge score={report.avg_posture_score || 0} size={56} label="Posture" />
          <ScoreBadge score={report.avg_gaze_score || 0}    size={56} label="Eye Contact" />
          <ScoreBadge score={report.avg_expression_score || report.overall_vision_score || 0} size={56} label="Expression" />
        </div>

        {report.strengths?.length > 0 && (
          <div style={styles.section}>
            <div style={styles.sectionTitle}>✅ Strengths</div>
            {report.strengths.map((s, i) => (
              <div key={i} style={{ ...styles.feedbackLine, color: '#88EE99' }}>• {s}</div>
            ))}
          </div>
        )}

        {report.improvements?.length > 0 && (
          <div style={styles.section}>
            <div style={styles.sectionTitle}>📈 Areas to Improve</div>
            {report.improvements.map((s, i) => (
              <div key={i} style={{ ...styles.feedbackLine, color: '#FFCC77' }}>• {s}</div>
            ))}
          </div>
        )}

        {report.answer_summaries?.length > 0 && (
          <>
            <button style={styles.expandBtn} onClick={() => setExpanded(e => !e)}>
              {expanded ? '▲ Hide per-answer details' : '▼ Show per-answer details'}
            </button>
            {expanded && report.answer_summaries.map((s, i) => (
              <VisionFeedbackCard key={i} data={s} mode="answer" />
            ))}
          </>
        )}
      </div>
    );
  }

  // ── Answer mode ──
  const summary = data;
  return (
    <div style={{ ...styles.card, padding: '14px 16px' }}>
      <div style={styles.header}>
        <span style={styles.headerIcon}>🎥</span>
        <div style={{ flex: 1 }}>
          <div style={styles.headerTitle}>
            {summary.answer_index !== undefined ? `Answer ${summary.answer_index + 1} — ` : ''}
            {summary.headline}
          </div>
          <div style={{ fontSize: 11, color: '#888' }}>
            {summary.total_frames_analyzed} frames analyzed
          </div>
        </div>
        <ScoreBadge score={summary.overall_vision_score || 0} size={48} />
      </div>

      <div style={styles.statsGrid}>
        <StatBar label="Upright posture"  value={summary.posture_upright_pct || 0} />
        <StatBar label="Eye contact"      value={summary.gaze_direct_pct    || 0} />
        <StatBar label="Head neutral"     value={summary.head_neutral_pct   || 0} />
      </div>

      {summary.dominant_expression && (
        <div style={styles.exprRow}>
          <span style={styles.statLabel}>Dominant expression:</span>
          <span style={styles.exprChip}>{EXPR_EMOJI[summary.dominant_expression] || '😐'} {summary.dominant_expression}</span>
        </div>
      )}

      {summary.feedback_lines?.length > 0 && (
        <div style={styles.section}>
          {summary.feedback_lines.map((line, i) => (
            <div key={i} style={styles.feedbackLine}>{line}</div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Emoji map ───────────────────────────────────────────
const EXPR_EMOJI = {
  happy: '😊', neutral: '😐', nervous: '😰',
  confused: '😕', angry: '😠', sad: '😞', surprised: '😲', unknown: '❓',
};

// ─── Styles ──────────────────────────────────────────────
const styles = {
  card: {
    background:   '#1a1f2e',
    border:       '1px solid #2a3045',
    borderRadius: 12,
    padding:      '16px 20px',
    marginBottom: 16,
    color:        '#DDD',
    fontFamily:   'sans-serif',
  },
  header: {
    display:     'flex',
    alignItems:  'center',
    gap:         12,
    marginBottom: 12,
  },
  headerIcon: { fontSize: 22 },
  headerTitle: {
    flex:       1,
    fontWeight: 'bold',
    fontSize:   14,
    color:      '#EEE',
  },
  summary: {
    fontSize:     13,
    color:        '#BBB',
    marginBottom: 14,
    lineHeight:   1.5,
  },
  scoresRow: {
    display:        'flex',
    justifyContent: 'space-around',
    marginBottom:   16,
  },
  statsGrid: {
    marginBottom: 10,
  },
  statRow: {
    display:     'flex',
    alignItems:  'center',
    gap:         8,
    marginBottom: 6,
  },
  statLabel: {
    width:    110,
    fontSize: 11,
    color:    '#999',
    flexShrink: 0,
  },
  barBg: {
    flex:         1,
    height:       8,
    background:   '#2a2a3a',
    borderRadius: 4,
    overflow:     'hidden',
  },
  barFill: {
    height:       '100%',
    borderRadius: 4,
    transition:   'width 0.6s ease',
  },
  statValue: {
    width:     36,
    fontSize:  11,
    textAlign: 'right',
  },
  section: {
    marginTop: 10,
  },
  sectionTitle: {
    fontSize:     12,
    fontWeight:   'bold',
    color:        '#AAA',
    marginBottom: 6,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  feedbackLine: {
    fontSize:     12,
    color:        '#CCC',
    marginBottom: 4,
    lineHeight:   1.4,
  },
  exprRow: {
    display:     'flex',
    alignItems:  'center',
    gap:         8,
    marginTop:   8,
    marginBottom: 4,
  },
  exprChip: {
    background:   '#2a3045',
    padding:      '2px 10px',
    borderRadius: 20,
    fontSize:     12,
    textTransform: 'capitalize',
  },
  expandBtn: {
    marginTop:    10,
    background:   'transparent',
    border:       '1px solid #3a4055',
    color:        '#888',
    borderRadius: 6,
    padding:      '4px 12px',
    fontSize:     11,
    cursor:       'pointer',
    width:        '100%',
  },
};