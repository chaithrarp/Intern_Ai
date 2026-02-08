import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart, ReferenceLine } from 'recharts';
import { motion } from 'framer-motion';
import './RecoveryCurveChart.css';

function RecoveryCurveChart({ sessionId }) {
  const [metricsData, setMetricsData] = useState([]);
  const [interruptions, setInterruptions] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState('recovery'); // recovery, pauses, timeline

  useEffect(() => {
    fetchVisualizationData();
  }, [sessionId]);

  const fetchVisualizationData = async () => {
    try {
      // Fetch session metrics
      const metricsResponse = await fetch(`http://localhost:8000/metrics/session/${sessionId}`);
      const metricsData = await metricsResponse.json();

      // Fetch session summary
      const summaryResponse = await fetch(`http://localhost:8000/metrics/summary/${sessionId}`);
      const summaryData = await summaryResponse.json();

      if (metricsData.success && summaryData.success) {
        processMetricsForVisualization(metricsData.metrics);
        setSummary(summaryData.summary);
      }
    } catch (error) {
      console.error('Error fetching visualization data:', error);
    } finally {
      setLoading(false);
    }
  };

  const processMetricsForVisualization = (metrics) => {
    // Transform metrics into chart-friendly format
    const chartData = metrics.map((metric, index) => {
      // Calculate confidence score (inverse of hesitation)
      const confidenceScore = Math.max(0, 100 - metric.hesitation_score);
      
      return {
        questionNum: index + 1,
        hesitation: metric.hesitation_score,
        confidence: confidenceScore,
        wpm: metric.words_per_minute,
        fillers: metric.filler_word_count,
        pauses: metric.total_pauses,
        longPauses: metric.long_pauses,
        recoveryTime: metric.recovery_time || 0,
        wasInterrupted: metric.recovery_time !== null,
        questionText: `Q${index + 1}`,
      };
    });

    setMetricsData(chartData);

    // Extract interruption points
    const interruptionPoints = chartData
      .filter(d => d.wasInterrupted)
      .map(d => ({
        questionNum: d.questionNum,
        recoveryTime: d.recoveryTime,
        hesitationBefore: chartData[d.questionNum - 2]?.hesitation || 0,
        hesitationAfter: d.hesitation,
      }));

    setInterruptions(interruptionPoints);
  };

  // Custom tooltip for charts
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="custom-tooltip">
          <p className="tooltip-label">Question {label}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color }}>
              {entry.name}: <strong>{entry.value.toFixed(1)}</strong>
            </p>
          ))}
          {data.wasInterrupted && (
            <p className="tooltip-interruption">⚡ Interrupted (recovered in {data.recoveryTime}s)</p>
          )}
        </div>
      );
    }
    return null;
  };

  // Calculate recovery metrics
  const calculateRecoveryMetrics = () => {
    if (interruptions.length === 0) return null;

    const avgRecoveryTime = interruptions.reduce((sum, int) => sum + int.recoveryTime, 0) / interruptions.length;
    const hesitationDrop = interruptions.map(int => int.hesitationAfter - int.hesitationBefore);
    const avgHesitationImpact = hesitationDrop.reduce((sum, val) => sum + val, 0) / hesitationDrop.length;

    return {
      avgRecoveryTime: avgRecoveryTime.toFixed(2),
      avgHesitationImpact: avgHesitationImpact.toFixed(1),
      totalInterruptions: interruptions.length,
      fastestRecovery: Math.min(...interruptions.map(i => i.recoveryTime)).toFixed(2),
      slowestRecovery: Math.max(...interruptions.map(i => i.recoveryTime)).toFixed(2),
    };
  };

  const recoveryMetrics = calculateRecoveryMetrics();

  if (loading) {
    return (
      <div className="recovery-chart-container">
        <div className="loading-chart">
          <div className="spinner"></div>
          <p>Generating visualizations...</p>
        </div>
      </div>
    );
  }

  if (metricsData.length === 0) {
    return (
      <div className="recovery-chart-container">
        <p className="no-data">No metrics data available for visualization</p>
      </div>
    );
  }

  return (
    <motion.div 
      className="recovery-chart-container"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      {/* Header */}
      <div className="chart-header">
        <h2>📊 Performance Analytics</h2>
        <div className="view-selector">
          <button 
            className={activeView === 'recovery' ? 'active' : ''}
            onClick={() => setActiveView('recovery')}
          >
            Recovery Curve
          </button>
          <button 
            className={activeView === 'pauses' ? 'active' : ''}
            onClick={() => setActiveView('pauses')}
          >
            Pause Patterns
          </button>
          <button 
            className={activeView === 'timeline' ? 'active' : ''}
            onClick={() => setActiveView('timeline')}
          >
            Full Timeline
          </button>
        </div>
      </div>

      {/* Recovery Metrics Summary (if interruptions occurred) */}
      {recoveryMetrics && (
        <motion.div 
          className="recovery-summary"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="recovery-metric">
            <span className="metric-icon">⚡</span>
            <div>
              <p className="metric-value">{recoveryMetrics.totalInterruptions}</p>
              <p className="metric-label">Interruptions</p>
            </div>
          </div>
          <div className="recovery-metric">
            <span className="metric-icon">⏱️</span>
            <div>
              <p className="metric-value">{recoveryMetrics.avgRecoveryTime}s</p>
              <p className="metric-label">Avg Recovery</p>
            </div>
          </div>
          <div className="recovery-metric">
            <span className="metric-icon">🚀</span>
            <div>
              <p className="metric-value">{recoveryMetrics.fastestRecovery}s</p>
              <p className="metric-label">Fastest Recovery</p>
            </div>
          </div>
          <div className="recovery-metric">
            <span className="metric-icon">📈</span>
            <div>
              <p className="metric-value">{recoveryMetrics.avgHesitationImpact > 0 ? '+' : ''}{recoveryMetrics.avgHesitationImpact}</p>
              <p className="metric-label">Hesitation Impact</p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Chart Views */}
      <motion.div 
        className="chart-content"
        key={activeView}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.4 }}
      >
        {/* View 1: Recovery Curve (Confidence over time) */}
        {activeView === 'recovery' && (
          <div className="chart-section">
            <h3>🎯 Confidence Recovery Curve</h3>
            <p className="chart-description">
              Shows how your confidence (inverse of hesitation) changed throughout the interview.
              {interruptions.length > 0 && ' Red lines mark interruption points.'}
            </p>
            <ResponsiveContainer width="100%" height={350}>
              <AreaChart data={metricsData}>
                <defs>
                  <linearGradient id="confidenceGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.1}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="questionText" 
                  stroke="#6b7280"
                  style={{ fontSize: '12px' }}
                />
                <YAxis 
                  stroke="#6b7280"
                  style={{ fontSize: '12px' }}
                  label={{ value: 'Confidence Score', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                
                {/* Mark interruption points */}
                {interruptions.map((int, index) => (
                  <ReferenceLine 
                    key={index}
                    x={int.questionNum} 
                    stroke="#ef4444" 
                    strokeDasharray="3 3"
                    label={{ value: '⚡', position: 'top', fill: '#ef4444' }}
                  />
                ))}
                
                <Area 
                  type="monotone" 
                  dataKey="confidence" 
                  stroke="#10b981" 
                  strokeWidth={3}
                  fill="url(#confidenceGradient)"
                  name="Confidence"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* View 2: Pause Patterns */}
        {activeView === 'pauses' && (
          <div className="chart-section">
            <h3>⏸️ Pause Pattern Analysis</h3>
            <p className="chart-description">
              Tracks total pauses and long pauses ({">"} 2 seconds) across questions.
            </p>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={metricsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="questionText"
                  stroke="#6b7280"
                  style={{ fontSize: '12px' }}
                />
                <YAxis 
                  stroke="#6b7280"
                  style={{ fontSize: '12px' }}
                  label={{ value: 'Number of Pauses', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Bar dataKey="pauses" fill="#3b82f6" name="Total Pauses" />
                <Bar dataKey="longPauses" fill="#ef4444" name="Long Pauses" />
              </BarChart>
            </ResponsiveContainer>

            {/* Pause insights */}
            <div className="pause-insights">
              <div className="insight-card">
                <span className="insight-icon">📊</span>
                <div>
                  <p className="insight-value">
                    {(metricsData.reduce((sum, d) => sum + d.pauses, 0) / metricsData.length).toFixed(1)}
                  </p>
                  <p className="insight-label">Avg Pauses per Question</p>
                </div>
              </div>
              <div className="insight-card">
                <span className="insight-icon">⚠️</span>
                <div>
                  <p className="insight-value">
                    {metricsData.reduce((sum, d) => sum + d.longPauses, 0)}
                  </p>
                  <p className="insight-label">Total Long Pauses</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* View 3: Full Performance Timeline */}
        {activeView === 'timeline' && (
          <div className="chart-section">
            <h3>📈 Complete Performance Timeline</h3>
            <p className="chart-description">
              Comprehensive view: Hesitation, Speaking Pace, and Filler Words across all questions.
            </p>
            
            {/* Hesitation Timeline */}
            <div className="timeline-subsection">
              <h4>Hesitation Score</h4>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={metricsData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="questionText" stroke="#6b7280" style={{ fontSize: '11px' }} />
                  <YAxis stroke="#6b7280" style={{ fontSize: '11px' }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Line 
                    type="monotone" 
                    dataKey="hesitation" 
                    stroke="#f59e0b" 
                    strokeWidth={2}
                    dot={{ fill: '#f59e0b', r: 4 }}
                    name="Hesitation"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Speaking Pace Timeline */}
            <div className="timeline-subsection">
              <h4>Speaking Pace (WPM)</h4>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={metricsData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="questionText" stroke="#6b7280" style={{ fontSize: '11px' }} />
                  <YAxis stroke="#6b7280" style={{ fontSize: '11px' }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Line 
                    type="monotone" 
                    dataKey="wpm" 
                    stroke="#3b82f6" 
                    strokeWidth={2}
                    dot={{ fill: '#3b82f6', r: 4 }}
                    name="Words/Min"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Filler Words Timeline */}
            <div className="timeline-subsection">
              <h4>Filler Words</h4>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={metricsData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="questionText" stroke="#6b7280" style={{ fontSize: '11px' }} />
                  <YAxis stroke="#6b7280" style={{ fontSize: '11px' }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="fillers" fill="#8b5cf6" name="Fillers" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </motion.div>

      {/* Key Insights */}
      <motion.div 
        className="chart-insights"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <h3>💡 Key Insights</h3>
        <div className="insights-grid">
          {metricsData.length > 0 && (
            <>
              <div className="insight-item">
                <span className="insight-emoji">📊</span>
                <p>
                  {metricsData[metricsData.length - 1].confidence > metricsData[0].confidence
                    ? 'Confidence improved throughout the interview! 📈'
                    : 'Confidence started strong - maintain consistency. 💪'}
                </p>
              </div>
              
              {recoveryMetrics && parseFloat(recoveryMetrics.avgRecoveryTime) < 3 && (
                <div className="insight-item">
                  <span className="insight-emoji">⚡</span>
                  <p>Excellent recovery speed! You handle pressure well. 🎯</p>
                </div>
              )}
              
              {metricsData.some(d => d.longPauses === 0) && (
                <div className="insight-item">
                  <span className="insight-emoji">🎤</span>
                  <p>Great flow - minimal awkward pauses! ✨</p>
                </div>
              )}
            </>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}

export default RecoveryCurveChart;