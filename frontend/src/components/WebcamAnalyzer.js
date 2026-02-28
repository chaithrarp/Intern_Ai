/**
 * WebcamAnalyzer.js
 *
 * Real-time webcam capture + vision analysis overlay component.
 *
 * Features:
 *  - Captures webcam via getUserMedia
 *  - Sends compressed JPEG frames to backend via WebSocket every FRAME_INTERVAL_MS
 *  - Draws live overlay on a <canvas> (face landmarks, pose landmarks, warning banner)
 *  - Shows live warning badge on screen
 *  - Exposes requestAnswerSummary() and requestSessionReport() for parent components
 *
 * Usage in Interview.js / AIInterviewer.js:
 *
 *   import WebcamAnalyzer from './components/WebcamAnalyzer';
 *
 *   <WebcamAnalyzer
 *     sessionId={sessionId}
 *     answerIndex={currentAnswerIndex}
 *     isRecording={isRecording}
 *     onFrameAnalysis={(analysis) => setLiveVisionData(analysis)}
 *     onAnswerSummary={(summary) => setAnswerVisionFeedback(summary)}
 *     ref={webcamRef}
 *   />
 *
 *   // When answer ends:
 *   webcamRef.current.requestAnswerSummary(answerIndex);
 *
 *   // When session ends:
 *   const report = await webcamRef.current.requestSessionReport();
 */

import React, {
  useEffect,
  useRef,
  useCallback,
  useImperativeHandle,
  forwardRef,
  useState,
} from 'react';

// ─── Config ───────────────────────────────────────────────
const WS_BASE_URL      = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
const FRAME_INTERVAL_MS = 2500;   // send a frame every 2.5 seconds
const FRAME_WIDTH       = 320;
const FRAME_HEIGHT      = 240;
const JPEG_QUALITY      = 0.6;

// Overlay colors
const COLOR_WARNING  = '#FF4444';
const COLOR_OK       = '#22CC66';
const COLOR_NEUTRAL  = '#4488FF';
const COLOR_LANDMARK = '#00FFAA';
const COLOR_POSE     = '#FF8800';

// ─── Component ────────────────────────────────────────────
const WebcamAnalyzer = forwardRef(function WebcamAnalyzer(
  { sessionId, answerIndex = 0, isRecording = false, onFrameAnalysis, onAnswerSummary },
  ref
) {
  const videoRef   = useRef(null);
  const canvasRef  = useRef(null);
  const wsRef      = useRef(null);
  const timerRef   = useRef(null);
  const streamRef  = useRef(null);

  const [liveWarning, setLiveWarning]     = useState('');
  const [statusLabel, setStatusLabel]     = useState('Initializing camera…');
  const [connected, setConnected]         = useState(false);
  const [expression, setExpression]       = useState('');
  const [postureOk, setPostureOk]         = useState(true);

  // ── Expose imperative methods to parent ──────────────────
  useImperativeHandle(ref, () => ({
    requestAnswerSummary: (idx) => requestFromServer({ action: 'get_answer_summary', answer_index: idx }),
    requestSessionReport: () => requestFromServer({ action: 'get_session_report' }),
    cleanup: () => {
      requestFromServer({ action: 'cleanup' });
      stopAll();
    },
  }));

  const requestFromServer = useCallback((msg) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  // ── Start webcam ─────────────────────────────────────────
  useEffect(() => {
    let cancelled = false;
    async function startCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: FRAME_WIDTH, height: FRAME_HEIGHT, facingMode: 'user' },
          audio: false,
        });
        if (cancelled) { stream.getTracks().forEach(t => t.stop()); return; }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }
        setStatusLabel('Camera ready');
      } catch (err) {
        setStatusLabel('Camera access denied');
        console.warn('[WebcamAnalyzer] Camera error:', err);
      }
    }
    startCamera();
    return () => { cancelled = true; };
  }, []);

  // ── Connect WebSocket ─────────────────────────────────────
  useEffect(() => {
    if (!sessionId) return;
    const wsUrl = `${WS_BASE_URL}/ws/vision/${sessionId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      setStatusLabel('Vision analysis active');
      console.info('[WebcamAnalyzer] WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Answer summary response
        if (data.answer_index !== undefined && data.feedback_lines !== undefined) {
          onAnswerSummary?.(data);
          return;
        }

        // Session report response
        if (data.answer_summaries !== undefined) {
          onAnswerSummary?.(data);
          return;
        }

        // Frame analysis response
        if (data.frame_analysis) {
          const fa = data.frame_analysis;
          handleFrameAnalysisResult(fa, data.face_landmarks_2d, data.pose_landmarks_2d);
          onFrameAnalysis?.(fa);
        }
      } catch (e) {
        console.warn('[WebcamAnalyzer] WS message parse error:', e);
      }
    };

    ws.onerror = (e) => {
      console.error('[WebcamAnalyzer] WebSocket error:', e);
      setStatusLabel('Vision connection error');
    };

    ws.onclose = () => {
      setConnected(false);
      setStatusLabel('Vision disconnected');
    };

    return () => {
      ws.close();
    };
  }, [sessionId]); // eslint-disable-line

  // ── Frame capture loop (only when recording) ─────────────
  useEffect(() => {
    if (!isRecording) {
      clearInterval(timerRef.current);
      return;
    }
    timerRef.current = setInterval(captureAndSend, FRAME_INTERVAL_MS);
    return () => clearInterval(timerRef.current);
  }, [isRecording, answerIndex]); // eslint-disable-line

  const captureAndSend = useCallback(() => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return;
    const video = videoRef.current;
    if (!video || video.readyState < 2) return;

    // Draw video to offscreen canvas → compress to JPEG
    const offscreen = document.createElement('canvas');
    offscreen.width  = FRAME_WIDTH;
    offscreen.height = FRAME_HEIGHT;
    const ctx = offscreen.getContext('2d');
    ctx.drawImage(video, 0, 0, FRAME_WIDTH, FRAME_HEIGHT);

    const dataUrl = offscreen.toDataURL('image/jpeg', JPEG_QUALITY);
    const b64 = dataUrl.split(',')[1];

    wsRef.current.send(JSON.stringify({
      session_id:   sessionId,
      answer_index: answerIndex,
      frame_b64:    b64,
      timestamp:    Date.now() / 1000,
    }));
  }, [sessionId, answerIndex]);

  // ── Handle analysis result: update overlay + state ────────
  const handleFrameAnalysisResult = useCallback((fa, faceLms, poseLms) => {
    setLiveWarning(fa.live_warning || '');
    setExpression(fa.expression || '');
    setPostureOk(fa.posture !== 'slouching' && fa.posture !== 'unknown');
    drawOverlay(faceLms || [], poseLms || [], fa);
  }, []);

  // ── Canvas overlay rendering ──────────────────────────────
  const drawOverlay = useCallback((faceLms, poseLms, fa) => {
    const canvas = canvasRef.current;
    const video  = videoRef.current;
    if (!canvas || !video) return;

    const w = canvas.width;
    const h = canvas.height;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, w, h);

    // Draw face landmarks as small dots
    if (faceLms.length > 0) {
      ctx.fillStyle = COLOR_LANDMARK;
      for (const [nx, ny] of faceLms) {
        ctx.beginPath();
        ctx.arc(nx * w, ny * h, 1.5, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // Draw pose landmarks as larger dots with connecting lines
    if (poseLms.length >= 6) {
      ctx.strokeStyle = COLOR_POSE;
      ctx.lineWidth   = 2;
      ctx.fillStyle   = COLOR_POSE;

      const pts = poseLms.map(([nx, ny]) => [nx * w, ny * h]);
      // shoulders: pts[0] (L) pts[1] (R)
      // hips: pts[2] (L) pts[3] (R)
      // ears: pts[4] (L) pts[5] (R)

      const connections = [[0,1],[0,2],[1,3],[2,3],[4,0],[5,1]];
      for (const [a, b] of connections) {
        if (pts[a] && pts[b]) {
          ctx.beginPath();
          ctx.moveTo(pts[a][0], pts[a][1]);
          ctx.lineTo(pts[b][0], pts[b][1]);
          ctx.stroke();
        }
      }
      for (const [px, py] of pts) {
        ctx.beginPath();
        ctx.arc(px, py, 4, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // Score badge (top-right)
    const score = Math.round(fa.frame_score || 0);
    const badgeColor = score >= 70 ? COLOR_OK : score >= 45 ? '#FFAA00' : COLOR_WARNING;
    ctx.fillStyle = badgeColor + 'CC';
    ctx.fillRect(w - 64, 8, 56, 28);
    ctx.fillStyle = '#FFF';
    ctx.font = 'bold 13px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(`${score}/100`, w - 36, 27);

    // Gaze indicator (top-left)
    const gazeOk = fa.gaze === 'direct';
    ctx.fillStyle = (gazeOk ? COLOR_OK : COLOR_WARNING) + 'CC';
    ctx.fillRect(8, 8, 28, 28);
    ctx.fillStyle = '#FFF';
    ctx.font = '16px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(gazeOk ? '👁️' : '👁️‍🗨️', 22, 27);

    // Warning banner (bottom)
    if (fa.live_warning) {
      ctx.fillStyle = COLOR_WARNING + 'DD';
      ctx.fillRect(0, h - 36, w, 36);
      ctx.fillStyle = '#FFF';
      ctx.font = 'bold 12px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(fa.live_warning, w / 2, h - 14);
    }
  }, []);

  // ── Cleanup ───────────────────────────────────────────────
  function stopAll() {
    clearInterval(timerRef.current);
    streamRef.current?.getTracks().forEach(t => t.stop());
  }

  useEffect(() => () => stopAll(), []); // cleanup on unmount

  // ── Render ────────────────────────────────────────────────
  return (
    <div style={styles.wrapper}>
      {/* Video element (hidden — we use canvas for display) */}
      <video
        ref={videoRef}
        style={styles.hiddenVideo}
        muted
        playsInline
        width={FRAME_WIDTH}
        height={FRAME_HEIGHT}
      />

      {/* Visible: video mirrored + canvas overlay stacked */}
      <div style={styles.videoContainer}>
        <video
          ref={videoRef}
          style={styles.videoDisplay}
          muted
          playsInline
          width={FRAME_WIDTH}
          height={FRAME_HEIGHT}
        />
        <canvas
          ref={canvasRef}
          style={styles.overlayCanvas}
          width={FRAME_WIDTH}
          height={FRAME_HEIGHT}
        />
      </div>

      {/* Status bar */}
      <div style={{ ...styles.statusBar, background: connected ? '#1a3a2a' : '#2a1a1a' }}>
        <span style={{ fontSize: 10, color: connected ? COLOR_OK : '#FF6666' }}>
          {connected ? '● LIVE' : '○ OFFLINE'}
        </span>
        <span style={styles.statusText}>{statusLabel}</span>
        {expression && (
          <span style={styles.exprBadge}>{EXPR_EMOJI[expression] || '😐'} {expression}</span>
        )}
        {!postureOk && (
          <span style={styles.postureBadge}>⚠️ Posture</span>
        )}
      </div>

      {/* Live warning overlay */}
      {liveWarning && (
        <div style={styles.warningToast}>
          {liveWarning}
        </div>
      )}
    </div>
  );
});

// ─── Expression emoji map ──────────────────────────────────
const EXPR_EMOJI = {
  happy:     '😊',
  neutral:   '😐',
  nervous:   '😰',
  confused:  '😕',
  angry:     '😠',
  sad:       '😞',
  surprised: '😲',
};

// ─── Styles ────────────────────────────────────────────────
const styles = {
  wrapper: {
    position:    'relative',
    display:     'inline-flex',
    flexDirection: 'column',
    borderRadius: 12,
    overflow:    'hidden',
    background:  '#111',
    boxShadow:   '0 4px 24px rgba(0,0,0,0.5)',
    userSelect:  'none',
  },
  hiddenVideo: {
    display: 'none',
  },
  videoContainer: {
    position: 'relative',
    width:    FRAME_WIDTH,
    height:   FRAME_HEIGHT,
  },
  videoDisplay: {
    position:  'absolute',
    top: 0, left: 0,
    width:     FRAME_WIDTH,
    height:    FRAME_HEIGHT,
    transform: 'scaleX(-1)',   // mirror effect
    objectFit: 'cover',
  },
  overlayCanvas: {
    position:  'absolute',
    top: 0, left: 0,
    width:     FRAME_WIDTH,
    height:    FRAME_HEIGHT,
    transform: 'scaleX(-1)',   // mirror to match video
    pointerEvents: 'none',
  },
  statusBar: {
    display:        'flex',
    alignItems:     'center',
    gap:            8,
    padding:        '4px 10px',
    background:     '#1a1a2a',
    borderTop:      '1px solid #333',
    minHeight:      28,
  },
  statusText: {
    flex:     1,
    fontSize: 11,
    color:    '#AAA',
  },
  exprBadge: {
    fontSize:     10,
    background:   '#2a3a4a',
    color:        '#CCC',
    padding:      '2px 6px',
    borderRadius: 8,
    textTransform: 'capitalize',
  },
  postureBadge: {
    fontSize:     10,
    background:   '#3a1a1a',
    color:        '#FF8888',
    padding:      '2px 6px',
    borderRadius: 8,
  },
  warningToast: {
    position:     'absolute',
    bottom:       40,
    left:         0, right: 0,
    textAlign:    'center',
    background:   'rgba(200,40,40,0.9)',
    color:        '#FFF',
    fontWeight:   'bold',
    fontSize:     12,
    padding:      '6px 12px',
    pointerEvents: 'none',
    animation:    'fadeIn 0.3s ease',
  },
};

export default WebcamAnalyzer;