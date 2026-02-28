import React, {
  useEffect, useRef, useState, useCallback,
  forwardRef, useImperativeHandle,
} from 'react';

// ─── Config ───────────────────────────────────────────────────────────────────
const WS_BASE_URL          = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
const FRAME_INTERVAL_REC   = 2500;   // ms — during answer recording (for analysis)
const FRAME_INTERVAL_IDLE  = 4000;   // ms — always-on posture monitoring
const FRAME_W              = 320;
const FRAME_H              = 240;
const JPEG_QUALITY         = 0.6;
const MIN_LANDMARKS_FOR_TOAST = 10;  // must detect ≥10 face landmarks before showing any toast
const WARMUP_MS            = 3000;   // ignore warnings for 3s after WS connects

const GLOBAL_STYLES = `
  @keyframes cam-pulse-ring {
    0%, 100% { opacity: 0.2; }
    50%       { opacity: 0.7; }
  }
  @keyframes cam-blink {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0; }
  }
  @keyframes cam-toast-in {
    0%   { opacity: 0; transform: translateX(-50%) translateY(-12px) scale(0.93); }
    100% { opacity: 1; transform: translateX(-50%) translateY(0)      scale(1);   }
  }
  @keyframes cam-toast-out {
    0%   { opacity: 1; transform: translateX(-50%) translateY(0)    scale(1);    }
    100% { opacity: 0; transform: translateX(-50%) translateY(-8px) scale(0.93); }
  }
`;

// ─── Parse warning text → visual config ──────────────────────────────────────
function parseToast(text) {
  if (!text) return null;
  const w = text.toLowerCase();
  if (w.includes('posture') || w.includes('slouch') || w.includes('sit') || w.includes('straight') || w.includes('back'))
    return { icon: '🪑', color: '#f97316', label: 'POSTURE' };
  if (w.includes('eye') || w.includes('look') || w.includes('camera') || w.includes('gaze') || w.includes('contact'))
    return { icon: '👁️', color: '#3b82f6', label: 'EYE CONTACT' };
  if (w.includes('head') || w.includes('face') || w.includes('turn') || w.includes('tilt'))
    return { icon: '↔️', color: '#a78bfa', label: 'HEAD POSITION' };
  if (w.includes('breath') || w.includes('nervous') || w.includes('calm') || w.includes('relax'))
    return { icon: '😌', color: '#22dd77', label: 'COMPOSURE' };
  if (w.includes('confident') || w.includes('confidence'))
    return { icon: '💪', color: '#f59e0b', label: 'CONFIDENCE' };
  return { icon: '⚠️', color: '#f97316', label: 'TIP' };
}

// ─── Floating in-camera toast ─────────────────────────────────────────────────
function CamToast({ text, visible }) {
  const t = parseToast(text);
  if (!t || !text) return null;
  return (
    <div style={{
      position: 'absolute', top: 14, left: '50%',
      zIndex: 20, display: 'flex', alignItems: 'center', gap: 8,
      padding: '7px 16px 7px 10px', borderRadius: 999,
      background: 'rgba(5,12,26,0.92)',
      border: `1px solid ${t.color}44`,
      boxShadow: `0 0 24px ${t.color}28, 0 4px 20px rgba(0,0,0,0.6)`,
      backdropFilter: 'blur(14px)',
      pointerEvents: 'none', whiteSpace: 'nowrap',
      animation: visible
        ? 'cam-toast-in 0.3s cubic-bezier(0.34,1.4,0.64,1) forwards'
        : 'cam-toast-out 0.22s ease forwards',
    }}>
      <span style={{ width: 7, height: 7, borderRadius: '50%', background: t.color, flexShrink: 0, boxShadow: `0 0 8px ${t.color}` }} />
      <span style={{ fontSize: 14, lineHeight: 1 }}>{t.icon}</span>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        <span style={{ fontSize: 7, fontWeight: 800, letterSpacing: 2, textTransform: 'uppercase', color: t.color, fontFamily: 'system-ui', lineHeight: 1 }}>{t.label}</span>
        <span style={{ fontSize: 11, fontWeight: 600, color: '#e2e8f0', fontFamily: 'system-ui', lineHeight: 1.3 }}>{text}</span>
      </div>
    </div>
  );
}

// ─── Particle orb — intro screen only ────────────────────────────────────────
export function AIParticleOrb({ state = 'idle' }) {
  const canvasRef = useRef(null);
  const particlesRef = useRef([]);
  const waveBarCountRef = useRef(60);
  const waveHeightsRef = useRef([]);
  const animFrameRef = useRef(null);
  const COUNT = 150;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    canvas.width = 500; canvas.height = 300;
    const ctx = canvas.getContext('2d');
    const cx = 250, cy = 150;

    particlesRef.current = Array.from({ length: COUNT }, () => ({
      angle: Math.random() * Math.PI * 2, radius: Math.random() * 180 + 60,
      orbitSpeed: (Math.random() - 0.5) * 0.015, size: Math.random() * 3 + 1,
      opacity: Math.random() * 0.7 + 0.3, colorOffset: Math.random() * 80,
    }));
    waveHeightsRef.current = Array.from({ length: 60 }, () => Math.random());

    const draw = () => {
      ctx.clearRect(0, 0, 500, 300);
      const t = Date.now() * 0.001, bw = 500 / 60;
      for (let i = 0; i < 60; i++) {
        const th = (Math.sin(t * 2 + i * 0.2) * 0.5 + 0.5) * 0.8 + 0.2;
        waveHeightsRef.current[i] += (th - waveHeightsRef.current[i]) * 0.1;
        const bh = waveHeightsRef.current[i] * 180, x = i * bw, y = (300 - bh) / 2;
        const g = ctx.createLinearGradient(x, y, x, y + bh);
        g.addColorStop(0, 'rgba(0,240,255,0.1)'); g.addColorStop(0.5, 'rgba(99,102,241,0.15)'); g.addColorStop(1, 'rgba(0,240,255,0.1)');
        ctx.fillStyle = g; ctx.fillRect(x, y, bw - 2, bh); ctx.shadowBlur = 15; ctx.shadowColor = 'rgba(0,240,255,0.3)';
      }
      ctx.shadowBlur = 0;
      particlesRef.current.forEach((p, i) => {
        p.angle += p.orbitSpeed;
        const pulse = Math.sin(t * 1.5 + i * 0.1) * 10;
        const x = cx + Math.cos(p.angle) * (p.radius + pulse);
        const y = cy + Math.sin(p.angle) * (p.radius + pulse);
        const sp = Math.sin(t * 2 + i * 0.15) * 0.5 + 1;
        const hue = 180 + p.colorOffset + Math.sin(t + i) * 20;
        ctx.shadowBlur = 20; ctx.shadowColor = `hsla(${hue},100%,60%,0.9)`;
        ctx.beginPath(); ctx.arc(x, y, p.size * sp, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${hue},100%,70%,${p.opacity})`; ctx.fill();
        particlesRef.current.forEach((o, oi) => {
          if (oi <= i) return;
          const op = Math.sin(t * 1.5 + oi * 0.1) * 10;
          const ox = cx + Math.cos(o.angle) * (o.radius + op);
          const oy = cy + Math.sin(o.angle) * (o.radius + op);
          const d = Math.sqrt((x - ox) ** 2 + (y - oy) ** 2);
          if (d < 100) {
            ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(ox, oy);
            ctx.strokeStyle = `hsla(${hue},100%,60%,${0.2 * (1 - d / 100)})`;
            ctx.lineWidth = 1; ctx.shadowBlur = 5; ctx.stroke();
          }
        });
      });
      animFrameRef.current = requestAnimationFrame(draw);
    };
    draw();
    return () => { if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current); };
  }, [state]);

  return <canvas ref={canvasRef} style={{ maxWidth: '100%', height: 'auto', filter: 'blur(0.3px)' }} />;
}

// ─── WebcamPanel ─────────────────────────────────────────────────────────────
export const WebcamPanel = forwardRef(function WebcamPanel(
  { sessionId, answerIndex, isRecording, onFrameAnalysis, onAnswerSummary },
  ref
) {
  const videoRef      = useRef(null);
  const canvasRef     = useRef(null);
  const wsRef         = useRef(null);
  const recTimerRef   = useRef(null);
  const idleTimerRef  = useRef(null);
  const streamRef     = useRef(null);
  const toastTimerRef = useRef(null);
  const wsConnectedAt = useRef(null);

  // ── FIX 1: Use refs for values read inside WS callbacks to avoid stale closures ──
  const faceDetectedRef   = useRef(false);   // authoritative value for toast gating
  const onFrameAnalysisRef = useRef(onFrameAnalysis);
  const onAnswerSummaryRef = useRef(onAnswerSummary);

  // Keep refs in sync with latest props
  useEffect(() => { onFrameAnalysisRef.current = onFrameAnalysis; }, [onFrameAnalysis]);
  useEffect(() => { onAnswerSummaryRef.current = onAnswerSummary; }, [onAnswerSummary]);

  // State only used for rendering
  const [connected, setConnected]       = useState(false);
  const [cameraReady, setCameraReady]   = useState(false);
  const [toastText, setToastText]       = useState('');
  const [toastVisible, setToastVis]     = useState(false);
  const [faceDetected, setFaceDetected] = useState(false); // for rendering only

  useImperativeHandle(ref, () => ({
    requestAnswerSummary: (idx) => send({ action: 'get_answer_summary', answer_index: idx }),
    requestSessionReport: ()    => send({ action: 'get_session_report' }),
    cleanup:              ()    => { send({ action: 'cleanup' }); stopAll(); },
  }));

  const send = useCallback((msg) => {
    if (wsRef.current?.readyState === WebSocket.OPEN)
      wsRef.current.send(JSON.stringify(msg));
  }, []);

  // ── FIX 2: showToast reads from ref, not stale state ──────────────────────
  const showToast = useCallback((text) => {
    if (!text) return;
    if (!faceDetectedRef.current) return;  // read from ref — always fresh
    const now = Date.now();
    if (wsConnectedAt.current && (now - wsConnectedAt.current) < WARMUP_MS) return;
    clearTimeout(toastTimerRef.current);
    setToastText(text);
    setToastVis(true);
    toastTimerRef.current = setTimeout(() => setToastVis(false), 4500);
  }, []); // no deps needed — reads from refs

  // Capture frame + send to WS
  const captureFrame = useCallback((context = 'idle') => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return;
    const video = videoRef.current;
    if (!video || video.readyState < 2) return;
    const off = document.createElement('canvas');
    off.width = FRAME_W; off.height = FRAME_H;
    off.getContext('2d').drawImage(video, 0, 0, FRAME_W, FRAME_H);
    send({
      session_id: sessionId,
      answer_index: answerIndex,
      frame_b64: off.toDataURL('image/jpeg', JPEG_QUALITY).split(',')[1],
      timestamp: Date.now() / 1000,
      context,
    });
  }, [sessionId, answerIndex, send]);

  // Camera init
  useEffect(() => {
    let cancelled = false;
    navigator.mediaDevices?.getUserMedia({
      video: { width: FRAME_W, height: FRAME_H, facingMode: 'user' },
      audio: false,
    }).then(stream => {
      if (cancelled) { stream.getTracks().forEach(t => t.stop()); return; }
      streamRef.current = stream;
      if (videoRef.current) { videoRef.current.srcObject = stream; videoRef.current.play(); }
      setCameraReady(true);
    }).catch(() => setCameraReady(false));
    return () => { cancelled = true; };
  }, []);

  // ── FIX 3: WebSocket onmessage uses refs — no stale closure problem ────────
  useEffect(() => {
    if (!sessionId) return;
    const ws = new WebSocket(`${WS_BASE_URL}/ws/vision/${sessionId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      wsConnectedAt.current = Date.now();
    };
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);

        // Answer summary or session report
        if (data.answer_summaries !== undefined || data.feedback_lines !== undefined) {
          onAnswerSummaryRef.current?.(data);
          return;
        }

        // Frame analysis response
        if (data.frame_analysis) {
          const fa       = data.frame_analysis;
          const faceLms  = data.face_landmarks_2d || [];
          const poseLms  = data.pose_landmarks_2d || [];

          // ── FIX 4: Update ref FIRST, then state ──────────────────────────
          // The ref update is synchronous and immediately visible to showToast.
          // The state update is async (for re-render only).
          const faceNowDetected = faceLms.length >= MIN_LANDMARKS_FOR_TOAST;
          faceDetectedRef.current = faceNowDetected;  // sync — for logic
          setFaceDetected(faceNowDetected);            // async — for render

          // Now showToast will correctly see the updated faceDetectedRef
          if (fa.live_warning) showToast(fa.live_warning);

          drawOverlay(faceLms, poseLms, fa);
          onFrameAnalysisRef.current?.(fa);  // use ref, not stale closure
        }
      } catch (err) {
        console.error('[Vision WS] parse error:', err);
      }
    };

    return () => ws.close();
  }, [sessionId, showToast]); // showToast is stable (no deps), safe to include

  // ── Recording loop (2.5s) ─────────────────────────────────────────────────
  useEffect(() => {
    clearInterval(recTimerRef.current);
    if (!isRecording) return;
    recTimerRef.current = setInterval(() => captureFrame('recording'), FRAME_INTERVAL_REC);
    return () => clearInterval(recTimerRef.current);
  }, [isRecording, captureFrame]);

  // ── Always-on idle loop (4s) ──────────────────────────────────────────────
  useEffect(() => {
    if (!sessionId) return;
    idleTimerRef.current = setInterval(() => {
      if (!isRecording) captureFrame('idle');
    }, FRAME_INTERVAL_IDLE);
    return () => clearInterval(idleTimerRef.current);
  }, [sessionId, isRecording, captureFrame]);

  // ── Canvas overlay ────────────────────────────────────────────────────────
  const drawOverlay = useCallback((faceLms, poseLms, fa) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const w = canvas.width, h = canvas.height;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, w, h);

    // Face dots — subtle green
    if (faceLms.length >= MIN_LANDMARKS_FOR_TOAST) {
      ctx.fillStyle = 'rgba(0,255,170,0.28)';
      faceLms.forEach(([nx, ny]) => {
        ctx.beginPath();
        ctx.arc(nx * w, ny * h, 1, 0, Math.PI * 2);
        ctx.fill();
      });
    }

    // Pose skeleton — orange lines
    if (poseLms.length >= 6) {
      const pts = poseLms.map(([nx, ny]) => [nx * w, ny * h]);
      ctx.strokeStyle = 'rgba(249,115,22,0.4)';
      ctx.lineWidth = 1.5;
      [[0,1],[0,2],[1,3],[2,3],[4,0],[5,1]].forEach(([a, b]) => {
        if (!pts[a] || !pts[b]) return;
        ctx.beginPath();
        ctx.moveTo(pts[a][0], pts[a][1]);
        ctx.lineTo(pts[b][0], pts[b][1]);
        ctx.stroke();
      });
      ctx.fillStyle = 'rgba(249,115,22,0.6)';
      pts.forEach(([px, py]) => {
        ctx.beginPath();
        ctx.arc(px, py, 3, 0, Math.PI * 2);
        ctx.fill();
      });
    }

    // Bottom-right status dot: green = good, orange = issue
    if (faceLms.length >= MIN_LANDMARKS_FOR_TOAST) {
      const ok = fa.posture !== 'slouching' && fa.gaze === 'direct' && fa.head_pose === 'neutral';
      ctx.fillStyle = ok ? 'rgba(34,221,119,0.9)' : 'rgba(249,115,22,0.9)';
      ctx.beginPath();
      ctx.arc(w - 10, h - 10, 5, 0, Math.PI * 2);
      ctx.fill();
    }
  }, []);

  function stopAll() {
    clearInterval(recTimerRef.current);
    clearInterval(idleTimerRef.current);
    clearTimeout(toastTimerRef.current);
    streamRef.current?.getTracks().forEach(t => t.stop());
  }
  useEffect(() => () => stopAll(), []); // eslint-disable-line

  return (
    <>
      <style>{GLOBAL_STYLES}</style>
      <div style={{ width: '100%', height: '100%', position: 'relative', background: '#040810', overflow: 'hidden' }}>

        {/* Video */}
        <video
          ref={videoRef}
          style={{
            position: 'absolute', inset: 0, width: '100%', height: '100%',
            objectFit: 'cover', transform: 'scaleX(-1)',
          }}
          muted playsInline width={FRAME_W} height={FRAME_H}
        />

        {/* Overlay canvas */}
        <canvas
          ref={canvasRef}
          style={{
            position: 'absolute', inset: 0, width: '100%', height: '100%',
            transform: 'scaleX(-1)', pointerEvents: 'none',
          }}
          width={FRAME_W} height={FRAME_H}
        />

        {/* No camera */}
        {!cameraReady && (
          <div style={{
            position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center', gap: 12,
          }}>
            <span style={{ fontSize: 44, opacity: 0.2 }}>📷</span>
            <span style={{ fontSize: 12, color: '#3a5070', fontFamily: 'system-ui' }}>Camera unavailable</span>
          </div>
        )}

        {/* Toast — reads faceDetected STATE for render, but logic uses ref */}
        {toastText && faceDetected && <CamToast text={toastText} visible={toastVisible} />}

        {/* Recording ring */}
        {isRecording && (
          <div style={{
            position: 'absolute', inset: 0,
            border: '2px solid rgba(239,68,68,0.5)',
            pointerEvents: 'none',
            animation: 'cam-pulse-ring 2s ease-in-out infinite',
          }} />
        )}

        {/* REC badge */}
        {isRecording && (
          <div style={{
            position: 'absolute', top: 12, right: 12,
            background: 'rgba(220,30,30,0.82)', backdropFilter: 'blur(6px)',
            color: '#fff', fontSize: 9, fontWeight: 800,
            padding: '3px 9px', borderRadius: 4,
            display: 'flex', alignItems: 'center', gap: 5,
            letterSpacing: 1.5, pointerEvents: 'none',
          }}>
            <span style={{
              width: 5, height: 5, borderRadius: '50%', background: '#fff',
              animation: 'cam-blink 1s step-start infinite',
            }} />
            REC
          </div>
        )}

        {/* WS connection dot — bottom left */}
        <div style={{
          position: 'absolute', bottom: 9, left: 9,
          width: 6, height: 6, borderRadius: '50%',
          background: connected ? '#22dd77' : '#2a3a50',
          transition: 'background 0.5s', pointerEvents: 'none',
        }} />

      </div>
    </>
  );
});

// ─── Default export ───────────────────────────────────────────────────────────
const AIInterviewer = forwardRef(function AIInterviewer(
  { sessionId = null, answerIndex = 0, isRecording = false, onFrameAnalysis = null, onAnswerSummary = null },
  ref
) {
  return (
    <WebcamPanel
      ref={ref}
      sessionId={sessionId}
      answerIndex={answerIndex}
      isRecording={isRecording}
      onFrameAnalysis={onFrameAnalysis}
      onAnswerSummary={onAnswerSummary}
    />
  );
});

export default AIInterviewer;