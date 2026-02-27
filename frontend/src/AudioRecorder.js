import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './AudioRecorder.css';
import soundEffects from './utils/soundEffects';

const CHUNK_INTERVAL_MS        = 6000;
const MIN_CHUNK_DURATION_MS    = 4000;
const MIN_TRANSCRIPT_FOR_CHECK = 60;
const FIRST_CHECK_DELAY_MS     = 10000;

function AudioRecorder({
  onAudioReady,
  questionId,
  sessionId,
  onRecordingStateChange,
  onInterruption,
  onLiveWarning,
  currentQuestionText,
}) {
  const [isRecording, setIsRecording]       = useState(false);
  const [recordingTime, setRecordingTime]   = useState(0);
  const [transcript, setTranscript]         = useState('');
  const [wasInterrupted, setWasInterrupted] = useState(false);
  const [chunkStatus, setChunkStatus]       = useState('');
  const [confirmedText, setConfirmedText]   = useState('');
  const [interimText, setInterimText]       = useState('');
  const [recordingDone, setRecordingDone]   = useState(false);

  const streamRef         = useRef(null);
  const chunkRecorderRef  = useRef(null);
  const chunkDataRef      = useRef([]);
  const timerRef          = useRef(null);
  const chunkTimerRef     = useRef(null);
  const recordingStartRef = useRef(null);
  const chunkStartRef     = useRef(null);
  const chunkIndexRef     = useRef(0);
  const confirmedTextRef  = useRef('');
  const recognitionRef    = useRef(null);
  const isRecordingRef    = useRef(false);
  const recordingTimeRef  = useRef(0);

  // Interruption tracking
  const interruptionFiredRef  = useRef(false);
  const interruptionCountRef  = useRef(0);
  const maxInterruptionsRef   = useRef(2);

  // Pause tracking
  const lastSoundTimeRef  = useRef(Date.now());
  const pauseCountRef     = useRef(0);
  const longPauseCountRef = useRef(0);

  const transcriptBoxRef = useRef(null);

  // Keep recordingTimeRef in sync for use in callbacks
  useEffect(() => {
    recordingTimeRef.current = recordingTime;
  }, [recordingTime]);

  useEffect(() => {
    if (transcriptBoxRef.current) {
      transcriptBoxRef.current.scrollTop = transcriptBoxRef.current.scrollHeight;
    }
  }, [confirmedText, interimText]);

  // ── Reset interruption state on new question ───────────────────────────────
  useEffect(() => {
    interruptionFiredRef.current = false;
    interruptionCountRef.current = 0;
  }, [questionId]);

  // ── Reset all ──────────────────────────────────────────────────────────────
  const resetAll = useCallback(() => {
    setRecordingDone(false);
    setRecordingTime(0);
    setTranscript('');
    setWasInterrupted(false);
    setConfirmedText('');
    setInterimText('');
    setChunkStatus('');
    confirmedTextRef.current     = '';
    interruptionFiredRef.current = false;
    interruptionCountRef.current = 0;
    chunkIndexRef.current        = 0;
    chunkDataRef.current         = [];
    pauseCountRef.current        = 0;
    longPauseCountRef.current    = 0;
    recordingTimeRef.current     = 0;
  }, []);

  // ── Web Speech API — interim display only ─────────────────────────────────
  useEffect(() => {
    if (!isRecording) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
        recognitionRef.current = null;
      }
      setInterimText('');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    const recognition = new SpeechRecognition();
    recognition.continuous      = true;
    recognition.interimResults  = true;
    recognition.lang            = 'en-US';
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
      let interim = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (!event.results[i].isFinal) {
          interim += event.results[i][0].transcript;
        }
      }
      setInterimText(interim);
      lastSoundTimeRef.current = Date.now();
    };

    recognition.onerror = (e) => {
      if (e.error !== 'no-speech' && e.error !== 'aborted') {
        console.warn('Speech recognition error:', e.error);
      }
    };

    recognition.onend = () => {
      if (isRecordingRef.current) {
        setTimeout(() => {
          if (isRecordingRef.current && recognitionRef.current) {
            try { recognitionRef.current.start(); } catch (_) {}
          }
        }, 200);
      }
    };

    recognitionRef.current = recognition;
    try { recognition.start(); } catch (e) {
      console.warn('Could not start speech recognition:', e);
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
        recognitionRef.current = null;
      }
    };
  }, [isRecording]);

  // ── Pause tracker ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (!isRecording) return;
    const interval = setInterval(() => {
      const silenceSecs = (Date.now() - lastSoundTimeRef.current) / 1000;
      if (silenceSecs > 3) {
        pauseCountRef.current += 1;
        if (silenceSecs > 5) longPauseCountRef.current += 1;
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [isRecording]);

  // ── Build audio_metrics ────────────────────────────────────────────────────
  const buildAudioMetrics = useCallback((durationSeconds) => {
    const issues = [];
    if (longPauseCountRef.current >= 2) {
      issues.push({ type: 'EXCESSIVE_PAUSING', evidence: `${longPauseCountRef.current} long pauses` });
    }
    if (durationSeconds > 90) {
      issues.push({ type: 'SPEAKING_TOO_LONG', evidence: `Speaking for ${Math.round(durationSeconds)}s` });
    }
    return {
      recording_duration: durationSeconds,
      pause_count: pauseCountRef.current,
      long_pause_count: longPauseCountRef.current,
      detected_issues: issues,
    };
  }, []);

  // ── Check interruption ─────────────────────────────────────────────────────
  const checkInterruption = useCallback(async (durationSeconds) => {
    if (interruptionFiredRef.current) return;
    if (interruptionCountRef.current >= maxInterruptionsRef.current) return;
    if (confirmedTextRef.current.length < MIN_TRANSCRIPT_FOR_CHECK) return;

    try {
      const res = await fetch('http://localhost:8000/interview/check-interruption', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id:            sessionId,
          question_id:           questionId,
          recording_duration:    durationSeconds,
          partial_transcript:    confirmedTextRef.current,
          current_question_text: currentQuestionText || '',
          audio_metrics:         buildAudioMetrics(durationSeconds),
        }),
      });

      const data = await res.json();

      if (data.should_interrupt && !interruptionFiredRef.current) {
        console.log('🔥 INTERRUPTION!', data.reason, '|', data.display_reason);
        interruptionFiredRef.current = true;
        interruptionCountRef.current += 1;
        if (data.max_interruptions) maxInterruptionsRef.current = data.max_interruptions;
        setWasInterrupted(true);
        soundEffects.playInterruption?.();
        onInterruption?.(data);
      } else if (data.should_warn && data.warning) {
        onLiveWarning?.(data.warning);
      }
    } catch (err) {
      console.error('Interruption check error:', err);
    }
  }, [sessionId, questionId, currentQuestionText, buildAudioMetrics, onInterruption, onLiveWarning]);

  // ── Send Whisper chunk ─────────────────────────────────────────────────────
  const sendChunk = useCallback(async (blob, idx) => {
    if (!blob || blob.size < 1000) return;

    setChunkStatus('transcribing');
    try {
      const formData = new FormData();
      formData.append('audio_chunk', blob, `chunk_${idx}.webm`);

      const res = await fetch(
        `http://localhost:8000/interview/transcribe-chunk` +
        `?session_id=${sessionId}&question_id=${questionId}&chunk_index=${idx}`,
        { method: 'POST', body: formData }
      );
      const data = await res.json();

      setChunkStatus('done');
      setTimeout(() => setChunkStatus(''), 800);

      if (data.success && data.text?.trim()) {
        const newText = data.text.trim();
        confirmedTextRef.current = (confirmedTextRef.current + ' ' + newText).trim();
        setConfirmedText(confirmedTextRef.current);
        setInterimText('');

        const elapsed = (Date.now() - recordingStartRef.current) / 1000;
        if (elapsed * 1000 >= FIRST_CHECK_DELAY_MS) {
          await checkInterruption(elapsed);
        }
      }
    } catch (err) {
      console.error('Chunk error:', err);
      setChunkStatus('');
    }
  }, [sessionId, questionId, checkInterruption]);

  // ── Chunk cycle ────────────────────────────────────────────────────────────
  const startChunkCycle = useCallback((stream) => {
    if (!isRecordingRef.current) return;

    chunkDataRef.current  = [];
    chunkStartRef.current = Date.now();

    let rec;
    try {
      rec = new MediaRecorder(stream, { mimeType: 'audio/webm' });
    } catch {
      rec = new MediaRecorder(stream);
    }
    chunkRecorderRef.current = rec;

    rec.ondataavailable = (e) => {
      if (e.data.size > 0) chunkDataRef.current.push(e.data);
    };
    rec.onstop = async () => {
      const duration = Date.now() - chunkStartRef.current;
      if (duration >= MIN_CHUNK_DURATION_MS && chunkDataRef.current.length > 0) {
        const blob = new Blob(chunkDataRef.current, { type: 'audio/webm' });
        const idx  = chunkIndexRef.current++;
        sendChunk(blob, idx);
      }
      if (isRecordingRef.current) startChunkCycle(stream);
    };

    rec.start();
    chunkTimerRef.current = setTimeout(() => {
      if (rec.state === 'recording') rec.stop();
    }, CHUNK_INTERVAL_MS);
  }, [sendChunk]);

  // ── Start recording ────────────────────────────────────────────────────────
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl:  false,
          sampleRate: 16000,
        },
      });

      streamRef.current = stream;

      resetAll();
      isRecordingRef.current    = true;
      recordingStartRef.current = Date.now();
      lastSoundTimeRef.current  = Date.now();
      setIsRecording(true);

      soundEffects.playRecordingStart?.();
      onRecordingStateChange?.(true);
      timerRef.current = setInterval(() => {
        setRecordingTime(p => p + 1);
      }, 1000);

      // Start chunk cycle after 1s
      setTimeout(() => {
        if (isRecordingRef.current) startChunkCycle(stream);
      }, 1000);

    } catch (err) {
      console.error('Mic error:', err);
      alert(err.name === 'NotAllowedError'
        ? 'Microphone permission denied. Allow mic access and refresh.'
        : `Microphone error: ${err.message}`
      );
    }
  };

  // ── Stop recording ─────────────────────────────────────────────────────────
  const stopRecording = () => {
    if (!isRecording) return;

    isRecordingRef.current = false;
    setIsRecording(false);
    clearInterval(timerRef.current);
    clearTimeout(chunkTimerRef.current);

    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }

    // Stop chunk recorder (sends last chunk)
    if (chunkRecorderRef.current?.state === 'recording') {
      chunkRecorderRef.current.stop();
    }

    // Stop mic stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }

    soundEffects.playRecordingStop?.();
    onRecordingStateChange?.(false);

    // Use accumulated live transcript as the final transcript — no second Whisper call
    const finalTranscript = confirmedTextRef.current.trim();
    setTranscript(finalTranscript);
    setRecordingDone(true);
  };

  // ── Submit answer ──────────────────────────────────────────────────────────
  const submitAnswer = () => {
    const finalTranscript = transcript || confirmedTextRef.current.trim();
    if (!finalTranscript) {
      alert('No transcript yet — please wait a moment or re-record.');
      return;
    }
    onAudioReady({
      transcript: finalTranscript,
      language: 'en',
      recording_duration: recordingTimeRef.current,
      was_interrupted: wasInterrupted,
    });
    resetAll();
  };

  const formatTime = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
  const displayText = confirmedText + (interimText ? ' ' + interimText : '');

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="audio-recorder">
      {!recordingDone ? (
        <div className="recording-interface">
          {!isRecording ? (
            <motion.button
              className="btn-record"
              onClick={startRecording}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <span className="mic-icon">🎤</span>
              <span>Start Recording</span>
            </motion.button>
          ) : (
            <>
              <motion.div
                className="recording-indicator"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <div className="pulse-dot" />
                <span>Recording... {formatTime(recordingTime)}</span>
                {chunkStatus === 'transcribing' && (
                  <span className="chunk-status">⚡ transcribing...</span>
                )}
                {chunkStatus === 'done' && (
                  <span className="chunk-status chunk-done">✓</span>
                )}
              </motion.div>

              <AnimatePresence>
                {displayText ? (
                  <motion.div
                    key="transcript-box"
                    className="live-transcript-box"
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                  >
                    <div className="live-transcript-header">
                      <span className="live-label">🎙 Live transcript</span>
                      {chunkStatus === 'transcribing' && (
                        <span className="whisper-badge">⚡ Whisper updating...</span>
                      )}
                    </div>
                    <div className="live-transcript-scroll" ref={transcriptBoxRef}>
                      <span className="confirmed-text">{confirmedText}</span>
                      {interimText && (
                        <span className="interim-text"> {interimText}</span>
                      )}
                      <span className="cursor-blink">|</span>
                    </div>
                  </motion.div>
                ) : recordingTime > 4 ? (
                  <motion.div
                    key="waiting"
                    className="live-transcript-waiting"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: [0.4, 1, 0.4] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                  >
                    ● ● ●&nbsp; Listening...
                  </motion.div>
                ) : null}
              </AnimatePresence>

              {wasInterrupted && (
                <motion.div
                  className="interrupted-badge"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  ⚡ Interrupted — answer the follow-up!
                </motion.div>
              )}

              <motion.button
                className="btn-stop"
                onClick={stopRecording}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                ⏹ Stop Recording
              </motion.button>
            </>
          )}
        </div>
      ) : (
        /* ── Post-recording: show transcript, submit or re-record ── */
        <motion.div
          className="playback-interface"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <p className="recording-info">
            ✅ Recording captured ({formatTime(recordingTime)})
            {wasInterrupted && <span className="interrupted-label"> — Answered follow-up</span>}
          </p>

          {transcript ? (
            <motion.div
              className="transcript-preview"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <p className="transcript-label">📝 Your answer:</p>
              <p className="transcript-text">{transcript}</p>
            </motion.div>
          ) : (
            <motion.div
              className="transcribing-indicator"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <span className="transcribing-label">Finalising transcript...</span>
            </motion.div>
          )}

          <div className="action-buttons">
            <motion.button
              className="btn-rerecord"
              onClick={resetAll}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              🔄 Re-record
            </motion.button>
            <motion.button
              className="btn-upload"
              onClick={submitAnswer}
              disabled={!transcript}
              whileHover={transcript ? { scale: 1.05 } : {}}
              whileTap={transcript ? { scale: 0.95 } : {}}
            >
              ✅ Submit Answer
            </motion.button>
          </div>
        </motion.div>
      )}
    </div>
  );
}

export default AudioRecorder;