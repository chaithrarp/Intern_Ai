import React, { useEffect, useRef, useState } from 'react';

/**
 * InterviewerAvatar — Animated SVG interviewer character
 * Reacts to: idle | speaking | listening | thinking
 * Pure CSS + SVG — no extra libraries needed
 */

const avatarStyles = `
  @keyframes av-blink {
    0%, 90%, 100% { transform: scaleY(1); }
    95%            { transform: scaleY(0.08); }
  }
  @keyframes av-mouth-talk {
    0%, 100% { d: path('M 82 118 Q 100 126 118 118'); }
    50%       { d: path('M 82 118 Q 100 132 118 118'); }
  }
  @keyframes av-float {
    0%, 100% { transform: translateY(0px); }
    50%       { transform: translateY(-4px); }
  }
  @keyframes av-think-dot {
    0%, 80%, 100% { opacity: 0.2; transform: scale(0.8); }
    40%           { opacity: 1;   transform: scale(1.2); }
  }
  @keyframes av-halo-pulse {
    0%, 100% { opacity: 0.3; r: 72; }
    50%       { opacity: 0.7; r: 76; }
  }
  @keyframes av-halo-speak {
    0%, 100% { opacity: 0.5; r: 72; }
    50%       { opacity: 1.0; r: 80; }
  }
  @keyframes av-ear-glow {
    0%, 100% { opacity: 0.2; }
    50%       { opacity: 0.9; }
  }
  @keyframes av-ring-spin {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
  }
  @keyframes av-ring-spin-rev {
    from { transform: rotate(0deg); }
    to   { transform: rotate(-360deg); }
  }
  @keyframes av-scan {
    0%   { stroke-dashoffset: 400; opacity: 0.8; }
    100% { stroke-dashoffset: 0;   opacity: 0.2; }
  }

  .av-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 8px 0 4px;
    flex-shrink: 0;
  }

  .av-svg-wrap {
    animation: av-float 3.5s ease-in-out infinite;
    filter: drop-shadow(0 8px 24px rgba(0,0,0,0.5));
  }

  .av-eye-group {
    transform-origin: center;
    animation: av-blink 4s ease-in-out infinite;
  }
  .av-eye-group--right {
    animation: av-blink 4s ease-in-out infinite 0.15s;
  }

  /* Mouth states */
  .av-mouth--idle {
    transition: d 0.3s ease;
  }
  .av-mouth--speaking {
    animation: av-mouth-talk 0.28s ease-in-out infinite;
  }

  /* Thinking dots */
  .av-think-dot:nth-child(1) { animation: av-think-dot 1.2s ease-in-out infinite 0s; }
  .av-think-dot:nth-child(2) { animation: av-think-dot 1.2s ease-in-out infinite 0.2s; }
  .av-think-dot:nth-child(3) { animation: av-think-dot 1.2s ease-in-out infinite 0.4s; }

  /* Halo ring */
  .av-halo--idle    { animation: av-halo-pulse  3s ease-in-out infinite; }
  .av-halo--speaking{ animation: av-halo-speak  0.5s ease-in-out infinite; }
  .av-halo--listening{ animation: av-halo-speak 1.2s ease-in-out infinite; }
  .av-halo--thinking{ animation: av-halo-pulse  1.8s ease-in-out infinite; }

  /* Spin rings */
  .av-spin-cw  {
    transform-origin: 100px 100px;
    animation: av-ring-spin     6s linear infinite;
  }
  .av-spin-ccw {
    transform-origin: 100px 100px;
    animation: av-ring-spin-rev 4s linear infinite;
  }
  .av-spin-cw--fast  {
    transform-origin: 100px 100px;
    animation: av-ring-spin     1.5s linear infinite;
  }
  .av-spin-ccw--fast {
    transform-origin: 100px 100px;
    animation: av-ring-spin-rev 2s linear infinite;
  }

  /* Ear glow when listening */
  .av-ear-glow { animation: av-ear-glow 0.8s ease-in-out infinite; }

  /* Scan line when thinking */
  .av-scan-line {
    stroke-dasharray: 400;
    animation: av-scan 1.5s linear infinite;
  }

  .av-state-label {
    font-size: 8px;
    font-weight: 800;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    padding: 2px 10px;
    border-radius: 20px;
    border: 1px solid;
    font-family: 'DM Mono', monospace;
  }
`;

// State → visual config
const STATE_CONFIG = {
  idle: {
    haloColor:   '#00d4ff',
    ringColor:   'rgba(0,212,255,0.25)',
    ring2Color:  'rgba(0,212,255,0.12)',
    faceColor:   '#1e3f6a',
    faceStroke:  '#00d4ff',
    eyeColor:    '#00d4ff',
    labelColor:  '#00d4ff',
    labelBg:     'rgba(0,212,255,0.1)',
    labelBorder: 'rgba(0,212,255,0.3)',
    label:       '● Ready',
    mouthPath:   'M 84 116 Q 100 122 116 116',
    eyebrowOff:  0,
  },
  speaking: {
    haloColor:   '#a78bfa',
    ringColor:   'rgba(167,139,250,0.3)',
    ring2Color:  'rgba(167,139,250,0.15)',
    faceColor:   '#1a1040',
    faceStroke:  '#a78bfa',
    eyeColor:    '#c4b5fd',
    labelColor:  '#a78bfa',
    labelBg:     'rgba(167,139,250,0.1)',
    labelBorder: 'rgba(167,139,250,0.35)',
    label:       '🔊 Speaking',
    mouthPath:   'M 84 116 Q 100 128 116 116',
    eyebrowOff:  -1,
  },
  listening: {
    haloColor:   '#22dd77',
    ringColor:   'rgba(34,221,119,0.3)',
    ring2Color:  'rgba(34,221,119,0.12)',
    faceColor:   '#0d2018',
    faceStroke:  '#22dd77',
    eyeColor:    '#4ade80',
    labelColor:  '#22dd77',
    labelBg:     'rgba(34,221,119,0.1)',
    labelBorder: 'rgba(34,221,119,0.3)',
    label:       '🎙 Listening',
    mouthPath:   'M 88 116 Q 100 119 112 116',
    eyebrowOff:  1,
  },
  thinking: {
    haloColor:   '#f97316',
    ringColor:   'rgba(249,115,22,0.3)',
    ring2Color:  'rgba(249,115,22,0.12)',
    faceColor:   '#1a0e05',
    faceStroke:  '#f97316',
    eyeColor:    '#fb923c',
    labelColor:  '#f97316',
    labelBg:     'rgba(249,115,22,0.1)',
    labelBorder: 'rgba(249,115,22,0.3)',
    label:       '⚙️ Analyzing',
    mouthPath:   'M 88 118 Q 100 115 112 118',
    eyebrowOff:  -2,
  },
};

export default function InterviewerAvatar({ state = 'idle' }) {
  const cfg = STATE_CONFIG[state] || STATE_CONFIG.idle;
  const isSpeaking  = state === 'speaking';
  const isListening = state === 'listening';
  const isThinking  = state === 'thinking';

  // Blinking state
  const [blink, setBlink] = useState(false);
  useEffect(() => {
    const interval = setInterval(() => {
      setBlink(true);
      setTimeout(() => setBlink(false), 150);
    }, 3200 + Math.random() * 1000);
    return () => clearInterval(interval);
  }, []);

  // Mouth open amount for speaking
  const [mouthOpen, setMouthOpen] = useState(0);
  useEffect(() => {
    if (!isSpeaking) { setMouthOpen(0); return; }
    const iv = setInterval(() => {
      setMouthOpen(Math.random() * 10 + 2);
    }, 140);
    return () => clearInterval(iv);
  }, [isSpeaking]);

  const eyeScaleY = blink ? 0.05 : 1;
  const mouthPathD = isSpeaking
    ? `M 84 116 Q 100 ${116 + mouthOpen} 116 116`
    : cfg.mouthPath;

  return (
    <>
      <style>{avatarStyles}</style>
      <div className="av-wrapper">
        <div className="av-svg-wrap">
          <svg width="130" height="130" viewBox="20 20 160 160" xmlns="http://www.w3.org/2000/svg">
            <defs>
              {/* Face gradient */}
              <radialGradient id="faceGrad" cx="45%" cy="38%" r="60%">
                <stop offset="0%"   stopColor={cfg.faceColor} stopOpacity="1" />
                <stop offset="100%" stopColor="#050c1a"       stopOpacity="1" />
              </radialGradient>
              {/* Halo glow */}
              <radialGradient id="haloGrad" cx="50%" cy="50%" r="50%">
                <stop offset="60%"  stopColor={cfg.haloColor} stopOpacity="0" />
                <stop offset="100%" stopColor={cfg.haloColor} stopOpacity="0.18" />
              </radialGradient>
              {/* Eye glow */}
              <filter id="eyeGlow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="2" result="blur" />
                <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
              </filter>
              {/* Face shadow */}
              <filter id="faceShadow" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="4" stdDeviation="8" floodColor={cfg.haloColor} floodOpacity="0.25" />
              </filter>
              {/* Scan clip */}
              <clipPath id="faceClip">
                <circle cx="100" cy="100" r="52" />
              </clipPath>
            </defs>

            {/* ── Outer ambient glow disc ── */}
            <circle cx="100" cy="100" r="72" fill="url(#haloGrad)" />

            {/* ── Spinning orbit rings ── */}
            {(isSpeaking || isListening) ? (
              <>
                <circle
                  className="av-spin-cw--fast"
                  cx="100" cy="100" r="76"
                  fill="none"
                  stroke={cfg.ringColor}
                  strokeWidth="1"
                  strokeDasharray="12 8"
                />
                <circle
                  className="av-spin-ccw--fast"
                  cx="100" cy="100" r="82"
                  fill="none"
                  stroke={cfg.ring2Color}
                  strokeWidth="1"
                  strokeDasharray="6 14"
                />
              </>
            ) : (
              <>
                <circle
                  className="av-spin-cw"
                  cx="100" cy="100" r="76"
                  fill="none"
                  stroke={cfg.ringColor}
                  strokeWidth="1"
                  strokeDasharray="8 10"
                />
                <circle
                  className="av-spin-ccw"
                  cx="100" cy="100" r="82"
                  fill="none"
                  stroke={cfg.ring2Color}
                  strokeWidth="1"
                  strokeDasharray="4 16"
                />
              </>
            )}

            {/* ── Halo pulse circle ── */}
            <circle
              className={`av-halo--${state}`}
              cx="100" cy="100" r="72"
              fill="none"
              stroke={cfg.haloColor}
              strokeWidth="1.5"
            />

            {/* ── Neck ── */}
            <rect x="90" y="147" width="20" height="16" rx="4"
              fill={cfg.faceColor}
              stroke={cfg.faceStroke}
              strokeWidth="0.5"
              strokeOpacity="0.4"
            />

            {/* ── Shoulders / collar ── */}
            <path
              d="M 60 168 Q 75 155 90 152 L 110 152 Q 125 155 140 168 Q 130 162 100 162 Q 70 162 60 168 Z"
              fill={cfg.faceColor}
              stroke={cfg.faceStroke}
              strokeWidth="0.5"
              strokeOpacity="0.3"
            />
            {/* Collar tie hint */}
            <path
              d="M 96 152 L 100 160 L 104 152 Z"
              fill={cfg.haloColor}
              opacity="0.5"
            />

            {/* ── Main face circle ── */}
            <circle
              cx="100" cy="100" r="52"
              fill="url(#faceGrad)"
              stroke={cfg.faceStroke}
              strokeWidth="1.5"
              strokeOpacity="0.6"
              filter="url(#faceShadow)"
            />

            {/* ── Thinking scan line ── */}
            {isThinking && (
              <line
                x1="48" y1="95" x2="152" y2="95"
                stroke={cfg.haloColor}
                strokeWidth="1"
                opacity="0.4"
                className="av-scan-line"
                clipPath="url(#faceClip)"
              />
            )}

            {/* ── Ears ── */}
            <ellipse cx="48" cy="100" rx="5" ry="8"
              fill={cfg.faceColor}
              stroke={cfg.faceStroke}
              strokeWidth="1"
              strokeOpacity={isListening ? "0.9" : "0.3"}
              className={isListening ? "av-ear-glow" : ""}
            />
            <ellipse cx="152" cy="100" rx="5" ry="8"
              fill={cfg.faceColor}
              stroke={cfg.faceStroke}
              strokeWidth="1"
              strokeOpacity={isListening ? "0.9" : "0.3"}
              className={isListening ? "av-ear-glow" : ""}
            />

            {/* ── Eyebrows ── */}
            <path
              d={`M 78 ${84 + cfg.eyebrowOff} Q 87 ${80 + cfg.eyebrowOff} 93 ${83 + cfg.eyebrowOff}`}
              fill="none"
              stroke={cfg.eyeColor}
              strokeWidth="2"
              strokeLinecap="round"
              strokeOpacity="0.7"
              style={{ transition: 'd 0.3s ease' }}
            />
            <path
              d={`M 107 ${83 + cfg.eyebrowOff} Q 113 ${80 + cfg.eyebrowOff} 122 ${84 + cfg.eyebrowOff}`}
              fill="none"
              stroke={cfg.eyeColor}
              strokeWidth="2"
              strokeLinecap="round"
              strokeOpacity="0.7"
              style={{ transition: 'd 0.3s ease' }}
            />

            {/* ── Left eye ── */}
            <g style={{ transformOrigin: '87px 94px', transform: `scaleY(${eyeScaleY})`, transition: 'transform 0.08s ease' }}>
              {/* Eye white */}
              <ellipse cx="87" cy="94" rx="9" ry="9"
                fill="rgba(255,255,255,0.06)"
                stroke={cfg.eyeColor}
                strokeWidth="1"
                strokeOpacity="0.4"
              />
              {/* Iris */}
              <circle cx="87" cy="94" r="5.5"
                fill={cfg.eyeColor}
                opacity="0.85"
                filter="url(#eyeGlow)"
              />
              {/* Pupil */}
              <circle cx="87" cy="94" r="2.5" fill="#050c1a" />
              {/* Highlight */}
              <circle cx="89" cy="92" r="1.2" fill="rgba(255,255,255,0.7)" />
            </g>

            {/* ── Right eye ── */}
            <g style={{ transformOrigin: '113px 94px', transform: `scaleY(${eyeScaleY})`, transition: 'transform 0.08s ease' }}>
              <ellipse cx="113" cy="94" rx="9" ry="9"
                fill="rgba(255,255,255,0.06)"
                stroke={cfg.eyeColor}
                strokeWidth="1"
                strokeOpacity="0.4"
              />
              <circle cx="113" cy="94" r="5.5"
                fill={cfg.eyeColor}
                opacity="0.85"
                filter="url(#eyeGlow)"
              />
              <circle cx="113" cy="94" r="2.5" fill="#050c1a" />
              <circle cx="115" cy="92" r="1.2" fill="rgba(255,255,255,0.7)" />
            </g>

            {/* ── Nose (subtle) ── */}
            <path
              d="M 100 102 Q 96 109 98 111 Q 100 112 102 111 Q 104 109 100 102 Z"
              fill="none"
              stroke={cfg.eyeColor}
              strokeWidth="1"
              strokeOpacity="0.25"
              strokeLinejoin="round"
            />

            {/* ── Mouth ── */}
            <path
              d={mouthPathD}
              fill="none"
              stroke={cfg.eyeColor}
              strokeWidth="2.5"
              strokeLinecap="round"
              style={{ transition: isSpeaking ? 'none' : 'd 0.4s ease' }}
            />
            {/* Mouth fill (open when speaking) */}
            {isSpeaking && mouthOpen > 4 && (
              <path
                d={`M 84 116 Q 100 ${116 + mouthOpen} 116 116 Q 100 ${114 + mouthOpen * 0.3} 84 116 Z`}
                fill="#050c1a"
                opacity="0.6"
              />
            )}

            {/* ── Thinking dots (above face) ── */}
            {isThinking && (
              <g>
                <circle className="av-think-dot" cx="118" cy="62" r="4" fill={cfg.haloColor} />
                <circle className="av-think-dot" cx="130" cy="54" r="5" fill={cfg.haloColor} />
                <circle className="av-think-dot" cx="144" cy="48" r="6" fill={cfg.haloColor} />
              </g>
            )}

            {/* ── Listening sound waves ── */}
            {isListening && (
              <g opacity="0.6">
                <path d="M 155 90 Q 160 100 155 110" fill="none" stroke={cfg.haloColor} strokeWidth="2" strokeLinecap="round" />
                <path d="M 161 85 Q 168 100 161 115" fill="none" stroke={cfg.haloColor} strokeWidth="1.5" strokeLinecap="round" opacity="0.6" />
                <path d="M 44 90 Q 39 100 44 110" fill="none" stroke={cfg.haloColor} strokeWidth="2" strokeLinecap="round" />
                <path d="M 38 85 Q 31 100 38 115" fill="none" stroke={cfg.haloColor} strokeWidth="1.5" strokeLinecap="round" opacity="0.6" />
              </g>
            )}

            {/* ── Speaking sound waves ── */}
            {isSpeaking && (
              <g opacity="0.5">
                <path d="M 155 88 Q 162 100 155 112" fill="none" stroke={cfg.haloColor} strokeWidth="2" strokeLinecap="round" />
                <path d="M 162 82 Q 171 100 162 118" fill="none" stroke={cfg.haloColor} strokeWidth="1.5" strokeLinecap="round" opacity="0.7" />
                <path d="M 169 77 Q 180 100 169 123" fill="none" stroke={cfg.haloColor} strokeWidth="1" strokeLinecap="round" opacity="0.4" />
              </g>
            )}
          </svg>
        </div>

        {/* State label pill */}
        <div
          className="av-state-label"
          style={{
            color:       cfg.labelColor,
            background:  cfg.labelBg,
            borderColor: cfg.labelBorder,
          }}
        >
          {cfg.label}
        </div>
      </div>
    </>
  );
}