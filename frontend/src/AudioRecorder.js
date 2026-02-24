import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './AudioRecorder.css';
import soundEffects from './utils/soundEffects';
import AudioAnalyzer from './utils/audioAnalyzer';
import LiveWarning from './components/LiveWarning';

function AudioRecorder({ onAudioReady, questionId, sessionId, onRecordingStateChange, onInterruption ,currentQuestionText}) {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [transcribing, setTranscribing] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [wasInterrupted, setWasInterrupted] = useState(false);
  const [liveWarning, setLiveWarning] = useState(null);
  const [audioAnalyzer, setAudioAnalyzer] = useState(null);
  const audioAnalyzerRef = useRef(null);
  const realtimeTranscriptRef = useRef('');
  // PHASE 5: Real-time detection states
  const [realtimeTranscript, setRealtimeTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [fillerWarning, setFillerWarning] = useState(null);
  const [silenceWarning, setSilenceWarning] = useState(false);
  
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);
  const recordingStartTime = useRef(null);
  const interruptionCheckInterval = useRef(null);
  
  // PHASE 5: Web Speech API for real-time detection
  const recognitionRef = useRef(null);
  const lastSpeechTime = useRef(null);
  const silenceCheckInterval = useRef(null);
  const manuallyStoppedRef = useRef(false);
  

  const interruptedRef = useRef(false);
  // PHASE 5: Filler word detection
  const FILLER_WORDS = ['um', 'uh', 'like', 'you know', 'basically', 'actually', 'literally', 'kind of', 'sort of'];
  const SILENCE_THRESHOLD = 5000; // 5 seconds of silence (increased from 4)

  // Detect filler words in real-time transcript
  const detectFillers = (text) => {
    const lowerText = text.toLowerCase();
    const words = lowerText.split(' ');
    const recentWords = words.slice(-10); // Check last 10 words
    
    // Count filler words in recent speech
    const fillerCount = recentWords.filter(word => 
      FILLER_WORDS.some(filler => word.includes(filler))
    ).length;
    
    // If 3+ fillers in last 10 words, show warning
    if (fillerCount >= 3) {
      return { type: 'filler', message: 'Avoid filler words' };
    }
    
    // Check for repetition
    const wordCounts = {};
    recentWords.forEach(word => {
      if (word.length > 3) { // Only check meaningful words
        wordCounts[word] = (wordCounts[word] || 0) + 1;
      }
    });
    
    // If any word repeated 3+ times
    for (let word in wordCounts) {
      if (wordCounts[word] >= 3) {
        return { type: 'repetition', message: "You're repeating yourself" };
      }
    }
    
    return null;
  };

  // PHASE 5: Setup Web Speech API for real-time detection
  useEffect(() => {
    if (isRecording) {
      // Check if browser supports Web Speech API
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      
      if (!SpeechRecognition) {
        console.warn('Web Speech API not supported - filler detection disabled');
        return;
      }
      
      // Initialize speech recognition
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';
      
      recognition.onresult = (event) => {
      let finalTranscript = '';
      let interimTranscript = '';
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript + ' ';
        } else {
          interimTranscript += transcript;
        }
      }
      
      // Update confirmed text + show interim text live
      realtimeTranscriptRef.current += finalTranscript;
      setRealtimeTranscript(realtimeTranscriptRef.current);
      setInterimTranscript(interimTranscript); // ← new state
      
      lastSpeechTime.current = Date.now();
      setSilenceWarning(false);
      
      // Filler detection (unchanged)
      const fillerDetection = detectFillers(finalTranscript + interimTranscript);
      if (fillerDetection) {
        setFillerWarning(fillerDetection);
        soundEffects.playWarning();
        setTimeout(() => setFillerWarning(null), 2000);
      }
    };
      
      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        // Don't try to restart on errors - let onend handle it
      };
      
      recognition.onend = () => {
        // Restart if still recording
        if (isRecording && recognitionRef.current) {
          setTimeout(() => {
            if (isRecording && recognitionRef.current) {
              try {
                recognitionRef.current.start();
              } catch (e) {
                // Already started, ignore
                if (e.name !== 'InvalidStateError') {
                  console.error('Recognition restart error:', e);
                }
              }
            }
          }, 200);
        }
      };
      
      // Start recognition
      try {
        recognition.start();
        recognitionRef.current = recognition;
        lastSpeechTime.current = Date.now();
      } catch (e) {
        console.error('Failed to start speech recognition:', e);
      }
      
      // Check for silence every second
      silenceCheckInterval.current = setInterval(() => {
        if (lastSpeechTime.current && realtimeTranscript.length > 10) {
          // Only check silence if they've actually said something (>10 chars)
          const silenceDuration = Date.now() - lastSpeechTime.current;
          const timeSinceRecordingStart = Date.now() - recordingStartTime.current;
          
          // Only show silence warning if:
          // 1. Been recording for at least 8 seconds
          // 2. Silent for 4+ seconds
          // 3. They've spoken at least 10 characters worth
          if (timeSinceRecordingStart > 8000 && silenceDuration > SILENCE_THRESHOLD) {
            setSilenceWarning(true);
          } else {
            setSilenceWarning(false);
          }
        }
      }, 1000);
      
    } else {
      // Stop speech recognition when not recording
      if (recognitionRef.current) {
        recognitionRef.current.stop();
        recognitionRef.current = null;
      }
      if (silenceCheckInterval.current) {
        clearInterval(silenceCheckInterval.current);
      }
      setRealtimeTranscript('');
      setFillerWarning(null);
      setSilenceWarning(false);
    }
    
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (silenceCheckInterval.current) {
        clearInterval(silenceCheckInterval.current);
      }
    };
  }, [isRecording]);

  // PHASE 5: Check for interruptions during recording
  useEffect(() => {
  if (!isRecording) {
    if (interruptionCheckInterval.current) {
      clearInterval(interruptionCheckInterval.current);
    }
    return;
  }

  // Start checking immediately, don't wait for audioAnalyzer state
  interruptionCheckInterval.current = setInterval(async () => {
    const duration = (Date.now() - recordingStartTime.current) / 1000;
    
    // Use ref directly — always has latest value
    const audioReport = audioAnalyzerRef.current 
      ? audioAnalyzerRef.current.getAnalysisReport() 
      : {};
    
    const transcriptForCheck = realtimeTranscriptRef.current || '';

    console.log('🔍 Checking interruption:', {
      duration,
      transcriptLength: transcriptForCheck.length,
      hasAudioData: !!audioAnalyzerRef.current,
      detectedIssues: audioReport?.detected_issues?.length || 0
    });

    try {
      const response = await fetch(
        `http://localhost:8000/interview/check-interruption`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: sessionId,
            recording_duration: duration,
            partial_transcript: transcriptForCheck,
            audio_metrics: audioReport
          })
        }
      );
      
      const data = await response.json();
      
      if (data.should_warn && data.warning) {
        console.log('⚠️ Live warning:', data.warning.message);
        setLiveWarning(data.warning);
        setTimeout(() => setLiveWarning(null), (data.warning.show_duration || 3) * 1000);
      }
      
      if (data.should_interrupt && !manuallyStoppedRef.current && !interruptedRef.current) {
        interruptedRef.current = true; // ← ADD THIS as first line inside
        console.log('🔥 INTERRUPTION TRIGGERED!', data);
        
        // Stop recording immediately when interrupted
        if (mediaRecorderRef.current && isRecording) {
          // Stop everything completely
          if (audioAnalyzerRef.current) {
            audioAnalyzerRef.current.stop();
            audioAnalyzerRef.current.cleanup();
            audioAnalyzerRef.current = null;
            setAudioAnalyzer(null);
          }
          if (recognitionRef.current) {
            recognitionRef.current.stop();
            recognitionRef.current = null;
          }
          mediaRecorderRef.current.stop();
          setIsRecording(false);
          clearInterval(timerRef.current);
          clearInterval(interruptionCheckInterval.current);
        }
        // Save transcript but DON'T show playback screen
        const partialText = realtimeTranscriptRef.current.trim();
        if (partialText) {
          setTranscript(partialText);
        }
        // Don't set audioBlob — keeps UI clean for interruption
        
        setWasInterrupted(true);
        if (onInterruption) {
          onInterruption(data, realtimeTranscriptRef.current);
        }
        if (interruptionCheckInterval.current) {
          clearInterval(interruptionCheckInterval.current);
        }
      }
    } catch (error) {
      console.error('Error checking interruption:', error);
    }
  }, 3000);

  return () => {
    if (interruptionCheckInterval.current) {
      clearInterval(interruptionCheckInterval.current);
    }
  };
}, [isRecording, sessionId, questionId, onInterruption]);

  // Start Recording
  const startRecording = async () => {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert('Your browser does not support audio recording. Please use Chrome or Edge.');
        return;
      }

      console.log('Requesting microphone access...');
      
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });
      
      console.log('Microphone access granted!');
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      const analyzer = new AudioAnalyzer();
      const initialized = await analyzer.initialize(stream);
      if (initialized) {
      analyzer.start();
      audioAnalyzerRef.current = analyzer;
      setAudioAnalyzer(analyzer);
      console.log('✅ Audio analyzer initialized and started');
    } else {
      console.warn('⚠️ Audio analyzer failed to initialize - using fallback detection');
    }

      chunksRef.current = [];
      recordingStartTime.current = Date.now();
      setWasInterrupted(false);

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(track => track.stop());
        // Only show playback screen if NOT interrupted
        if (!interruptedRef.current) {
          const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
          setAudioBlob(blob);
          if (onRecordingStateChange) {
            onRecordingStateChange(false);
          }
        }
        // If interrupted, don't call onRecordingStateChange
        // so voiceService.stop() never gets called
      };

       mediaRecorder.start();
       setIsRecording(true);
       setRecordingTime(0);
    
    // PHASE 8: Play recording start sound
       soundEffects.playRecordingStart();

      // Notify parent that recording started
      if (onRecordingStateChange) {
        onRecordingStateChange(true);
      }

      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);

      

    } catch (error) {
      console.error('Microphone error:', error);
      
      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        alert('❌ Microphone permission denied.\n\nPlease:\n1. Click the camera/mic icon in the address bar\n2. Allow microphone access\n3. Refresh the page');
      } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
        alert('❌ No microphone found.\n\nPlease:\n1. Connect a microphone\n2. Check Windows sound settings\n3. Refresh the page');
      } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
        alert('❌ Microphone is being used by another application.\n\nPlease:\n1. Close other apps using the microphone (Zoom, Teams, etc.)\n2. Refresh the page');
      } else {
        alert(`❌ Microphone error: ${error.message}\n\nCheck browser console (F12) for details.`);
      }
    }
  };

  // Stop Recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      manuallyStoppedRef.current = true;
      
      if (audioAnalyzerRef.current) {
        audioAnalyzerRef.current.stop();
        audioAnalyzerRef.current.cleanup();
        audioAnalyzerRef.current = null;
        setAudioAnalyzer(null);
      }
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      clearInterval(timerRef.current);
      soundEffects.playRecordingStop();
      if (interruptionCheckInterval.current) {
        clearInterval(interruptionCheckInterval.current);
      }

      // Use live transcript directly — skip Whisper entirely
      const finalText = realtimeTranscript.trim();
      if (finalText) {
        console.log('✅ Using live transcript directly:', finalText);
        setTranscript(finalText);
      }

      console.log(`Recording stopped. Was interrupted: ${wasInterrupted}`);
    }
  };

  const transcribeAudio = async (blob) => {
    setTranscribing(true);
    
    try {
      const formData = new FormData();
      formData.append('audio_file', blob, 'recording.webm');

      console.log('Transcribing audio with Whisper...');

      const response = await fetch(
        `http://localhost:8000/interview/upload-audio?session_id=${sessionId}&question_id=${questionId}`,
        {
          method: 'POST',
          body: formData,
        }
      );

      const data = await response.json();
      console.log('Backend response:', JSON.stringify(data));
      console.log('Transcription response:', data);

      if (data.success) {
        setTranscript(data.transcript);
        console.log('Final Whisper transcript:', data.transcript);
      } else {
        alert('Transcription failed: ' + (data.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Transcription error:', error);
      alert('Failed to transcribe audio');
    } finally {
      setTranscribing(false);
    }
  };

  const submitAnswer = () => {
    if (!transcript) {
      alert('Transcript is empty. Please try re-recording.');
      return;
    }

    onAudioReady({
      transcript: transcript,
      language: 'en',
      recording_duration: recordingTime,
      was_interrupted: wasInterrupted
    });
    
    resetRecording();
  };

  const resetRecording = () => {
    setAudioBlob(null);
    setRecordingTime(0);
    setTranscript('');
    setTranscribing(false);
    setWasInterrupted(false);
    setRealtimeTranscript('');
    setFillerWarning(null);
    setSilenceWarning(false);
    setLiveWarning(null);
    setInterimTranscript('');
    realtimeTranscriptRef.current = '';
    manuallyStoppedRef.current = false;
    interruptedRef.current = false;
    
    
    if (audioAnalyzerRef.current) {
      audioAnalyzerRef.current.cleanup();
      audioAnalyzerRef.current = null;
      setAudioAnalyzer(null);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

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
              <motion.div 
                className="recording-indicator"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
              >
                <div className="pulse-dot"></div>
                <span>Recording... {formatTime(recordingTime)}</span>
              </motion.div>
              
              {/* PHASE 5: Real-time warnings */}
              <AnimatePresence>
                {fillerWarning && (
                  <motion.div
                    className="filler-warning"
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                  >
                    {fillerWarning.type === 'filler' && '⚠️'}
                    {fillerWarning.type === 'repetition' && '🔄'}
                    {' '}{fillerWarning.message}
                  </motion.div>
                )}
                
                {silenceWarning && (
                  <motion.div
                    className="silence-warning"
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                  >
                    ⏸️ Still there?
                  </motion.div>
                )}
              </AnimatePresence>
              {/* STEP 3.2: Live Warning Component */}
              <LiveWarning warning={liveWarning} />
              {/* LIVE TRANSCRIPT */}
              {(realtimeTranscript || interimTranscript) && (
                <motion.div className="live-transcript" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                  <p className="live-transcript-label">🎙️ Live transcript:</p>
                  <p className="live-transcript-text">
                    {realtimeTranscript}
                    <span style={{ color: 'rgba(255,255,255,0.45)' }}>{interimTranscript}</span>
                  </p>
                </motion.div>
              )}
              
              {/* Show if interrupted (but keep recording!) */}
              {wasInterrupted && (
                <motion.div
                  className="interrupted-badge"
                  
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  ⚡ Interrupted - Keep answering the follow-up!
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
          transition={{ duration: 0.4 }}
        >
          <p className="recording-info">
            ✅ Recording captured ({formatTime(recordingTime)})
            {wasInterrupted && <span className="interrupted-label"> - Answered follow-up</span>}
          </p>
          
          <audio controls src={URL.createObjectURL(audioBlob)} className="audio-player" />
          
          {transcribing && (
            <motion.div 
              className="transcribing-indicator"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <div className="spinner"></div>
              <p>Transcribing your answer...</p>
            </motion.div>
          )}
          
          {transcript && !transcribing && (
            <motion.div 
              className="transcript-preview"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <p className="transcript-label">📝 What I heard:</p>
              <p className="transcript-text">{transcript}</p>
            </motion.div>
          )}
          
          <div className="action-buttons">
            <motion.button 
              className="btn-rerecord" 
              onClick={resetRecording}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
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