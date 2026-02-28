import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './AudioRecorder.css';
import soundEffects from './utils/soundEffects';

/**
 * AudioRecorder - HYBRID LIVE TRANSCRIPT VERSION
 * ================================================
 * Two parallel systems running during recording:
 *
 * 1. Web Speech API → shows text AS YOU SPEAK (instant, imperfect)
 *    Used only for display — gives the "typing in real time" feel
 *
 * 2. Whisper chunks every 6s → accurate transcript sent to LLM
 *    Used for interruption decisions — reliable for phone speaker audio
 *
 * Display shows Web Speech API interim text (feels live)
 * Whisper confirmed chunks replace/correct the display every 6s
 * LLM interruption check uses only the Whisper-confirmed text
 */

const CHUNK_INTERVAL_MS = 6000;
const MIN_CHUNK_DURATION_MS = 4000;
const MIN_TRANSCRIPT_FOR_CHECK = 80;
const FIRST_CHECK_DELAY_MS = 12000;
const MAX_INTERRUPTIONS = 3;

function AudioRecorder({
  onAudioReady,
  questionId,
  sessionId,
  onRecordingStateChange,
  onInterruption,
  onLiveWarning,
  currentQuestionText
}) {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [transcribing, setTranscribing] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [wasInterrupted, setWasInterrupted] = useState(false);
  const [chunkStatus, setChunkStatus] = useState('');

  // ── Two-layer transcript display ──────────────────────────────────────────
  // confirmedText: Whisper-verified text (accurate, used for LLM)
  // interimText:   Web Speech API live text (instant, imperfect, display only)
  const [confirmedText, setConfirmedText] = useState('');
  const [interimText, setInterimText] = useState('');

  // Refs
  const mediaRecorderRef = useRef(null);
  const fullChunksRef = useRef([]);
  const chunkRecorderRef = useRef(null);
  const chunkDataRef = useRef([]);
  const timerRef = useRef(null);
  const chunkTimerRef = useRef(null);
  const recordingStartRef = useRef(null);
  const chunkStartRef = useRef(null);
  const chunkIndexRef = useRef(0);

  // Whisper confirmed text ref (always fresh for interruption checks)
  const confirmedTextRef = useRef('');

  // Web Speech API refs
  const recognitionRef = useRef(null);
  const isRecordingRef = useRef(false);

  // Interruption refs
  const interruptionFiredRef = useRef(false);
  const interruptionCountRef = useRef(0);

  // Transcript box scroll ref
  const transcriptBoxRef = useRef(null);

  // ── Auto-scroll transcript box to bottom as text grows ───────────────────
  useEffect(() => {
    if (transcriptBoxRef.current) {
      transcriptBoxRef.current.scrollTop = transcriptBoxRef.current.scrollHeight;
    }
  }, [confirmedText, interimText]);

  // ── Reset ─────────────────────────────────────────────────────────────────
  const resetAll = useCallback(() => {
    setAudioBlob(null);
    setRecordingTime(0);
    setTranscript('');
    setTranscribing(false);
    setWasInterrupted(false);
    setConfirmedText('');
    setInterimText('');
    setChunkStatus('');
    confirmedTextRef.current = '';
    interruptionFiredRef.current = false;
    interruptionCountRef.current = 0;
    chunkIndexRef.current = 0;
    fullChunksRef.current = [];
    chunkDataRef.current = [];
  }, []);

  // ── Web Speech API — live interim display ─────────────────────────────────
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
    if (!SpeechRecognition) return; // silently skip if not supported

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
      let interim = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const text = event.results[i][0].transcript;
        if (!event.results[i].isFinal) {
          interim += text;
        }
        // Note: we don't accumulate final results here
        // Whisper handles the accurate final text
        // Web Speech API is display-only
      }
      // Show: confirmed Whisper text + live interim from Web Speech
      setInterimText(interim);
    };

    recognition.onerror = (e) => {
      if (e.error !== 'no-speech' && e.error !== 'aborted') {
        console.warn('Speech recognition error:', e.error);
      }
    };

    recognition.onend = () => {
      // Restart while still recording
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

  // ── Check interruption (uses Whisper-confirmed text only) ─────────────────
  const checkInterruption = useCallback(async (durationSeconds) => {
    if (interruptionFiredRef.current) return;
    if (interruptionCountRef.current >= MAX_INTERRUPTIONS) return;
    if (confirmedTextRef.current.length < MIN_TRANSCRIPT_FOR_CHECK) return;

    try {
      const res = await fetch('http://localhost:8000/interview/check-interruption', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          question_id: questionId,
          recording_duration: durationSeconds,
          partial_transcript: confirmedTextRef.current,
          current_question_text: currentQuestionText || '',
          audio_metrics: {}
        })
      });

      const data = await res.json();

      if (data.should_interrupt && !interruptionFiredRef.current) {
        console.log('🔥 INTERRUPTION!', data.reason);
        interruptionFiredRef.current = true;
        interruptionCountRef.current += 1;
        setWasInterrupted(true);
        soundEffects.playInterruption?.();
        onInterruption?.(data);
      } else if (data.should_warn && data.warning) {
        onLiveWarning?.(data.warning);
      }
    } catch (err) {
      console.error('Interruption check error:', err);
    }
  }, [sessionId, questionId, currentQuestionText, onInterruption, onLiveWarning]);

  // ── Send Whisper chunk ────────────────────────────────────────────────────
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

        // Append to confirmed (Whisper) text
        confirmedTextRef.current = (confirmedTextRef.current + ' ' + newText).trim();
        setConfirmedText(confirmedTextRef.current);

        // Clear interim — Whisper just confirmed this segment
        setInterimText('');

        console.log(`⚡ Chunk ${idx} (${data.elapsed?.toFixed(1)}s): "${newText.substring(0, 60)}"`);

        // Run interruption check
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

  // ── Start one 6s chunk cycle ──────────────────────────────────────────────
  const startChunkCycle = useCallback((stream) => {
    if (!isRecordingRef.current) return;

    chunkDataRef.current = [];
    chunkStartRef.current = Date.now();

    let rec;
    try {
      rec = new MediaRecorder(stream, { mimeType: 'audio/webm' });
    } catch (e) {
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
        const idx = chunkIndexRef.current++;
        sendChunk(blob, idx); // fire and forget — start next cycle immediately
      }
      if (isRecordingRef.current) startChunkCycle(stream);
    };

    rec.start();
    chunkTimerRef.current = setTimeout(() => {
      if (rec.state === 'recording') rec.stop();
    }, CHUNK_INTERVAL_MS);
  }, [sendChunk]);

  // ── Start recording ───────────────────────────────────────────────────────
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: false,  // OFF — pick up phone speaker in room
          noiseSuppression: false,  // OFF — don't filter room audio
          autoGainControl: false,
          sampleRate: 16000         // Whisper's native rate
        }
      });

      fullChunksRef.current = [];
      const main = new MediaRecorder(stream);
      mediaRecorderRef.current = main;

      main.ondataavailable = (e) => {
        if (e.data.size > 0) fullChunksRef.current.push(e.data);
      };
      main.onstop = async () => {
        const blob = new Blob(fullChunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        stream.getTracks().forEach(t => t.stop());
        onRecordingStateChange?.(false);
        await transcribeFinal(blob);
      };
      main.start();

      resetAll();
      isRecordingRef.current = true;
      recordingStartRef.current = Date.now();
      setIsRecording(true);

      soundEffects.playRecordingStart?.();
      onRecordingStateChange?.(true);
      timerRef.current = setInterval(() => setRecordingTime(p => p + 1), 1000);

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

  // ── Stop recording ────────────────────────────────────────────────────────
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
    if (chunkRecorderRef.current?.state === 'recording') {
      chunkRecorderRef.current.stop();
    }
    mediaRecorderRef.current?.stop();
    soundEffects.playRecordingStop?.();
  };

  // ── Final Whisper transcription ───────────────────────────────────────────
  const transcribeFinal = async (blob) => {
    setTranscribing(true);
    try {
      const formData = new FormData();
      formData.append('audio_file', blob, 'recording.webm');
      const res = await fetch(
        `http://localhost:8000/interview/upload-audio?session_id=${sessionId}&question_id=${questionId}`,
        { method: 'POST', body: formData }
      );
      const data = await res.json();
      if (data.success) {
        setTranscript(data.transcript);
      } else {
        alert('Transcription failed: ' + (data.error || 'Unknown'));
      }
    } catch (err) {
      alert('Failed to transcribe audio');
    } finally {
      setTranscribing(false);
    }
  };

  const submitAnswer = () => {
    if (!transcript) { alert('Transcript empty — please re-record.'); return; }
    onAudioReady({
      transcript,
      language: 'en',
      recording_duration: recordingTime,
      was_interrupted: wasInterrupted
    });
    resetAll();
  };

  const formatTime = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;

  // Combined display text: confirmed + interim
  const displayText = confirmedText + (interimText ? ' ' + interimText : '');

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="audio-recorder">
      {!audioBlob ? (
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
              {/* Recording timer + chunk status */}
              <motion.div
                className="recording-indicator"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <div className="pulse-dot"></div>
                <span>Recording... {formatTime(recordingTime)}</span>
                {chunkStatus === 'transcribing' && (
                  <span className="chunk-status">⚡ transcribing...</span>
                )}
                {chunkStatus === 'done' && (
                  <span className="chunk-status chunk-done">✓</span>
                )}
              </motion.div>

              {/* Live transcript box */}
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
                    <div
                      className="live-transcript-scroll"
                      ref={transcriptBoxRef}
                    >
                      {/* Confirmed Whisper text (solid) */}
                      <span className="confirmed-text">{confirmedText}</span>
                      {/* Interim Web Speech text (faded, live typing effect) */}
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
        <motion.div
          className="playback-interface"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <p className="recording-info">
            ✅ Recording captured ({formatTime(recordingTime)})
            {wasInterrupted && <span className="interrupted-label"> — Answered follow-up</span>}
          </p>

          <audio controls src={URL.createObjectURL(audioBlob)} className="audio-player" />

          {transcribing && (
            <motion.div className="transcribing-indicator" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <span className="transcribing-label">Transcribing your answer</span>
              <div className="transcribing-lines">
                <div className="transcribing-line" />
                <div className="transcribing-line" />
                <div className="transcribing-line" />
              </div>
              <div className="transcribing-status">
                <span className="transcribing-dots">
                  <span /><span /><span />
                </span>
                Processing audio...
              </div>
            </motion.div>
          )}

          {transcript && !transcribing && (
            <motion.div className="transcript-preview" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <p className="transcript-label">📝 Final transcript:</p>
              <p className="transcript-text">{transcript}</p>
            </motion.div>
          )}

          <div className="action-buttons">
            <motion.button className="btn-rerecord" onClick={resetAll} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              🔄 Re-record
            </motion.button>
            <motion.button
              className="btn-upload"
              onClick={submitAnswer}
              disabled={transcribing || !transcript}
              whileHover={!transcribing && transcript ? { scale: 1.05 } : {}}
              whileTap={!transcribing && transcript ? { scale: 0.95 } : {}}
            >
              {transcribing ? 'Processing...' : '✅ Submit Answer'}
            </motion.button>
          </div>
        </motion.div>
      )}
    </div>
  );
}

export default AudioRecorder;